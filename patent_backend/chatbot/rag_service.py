"""
RAG 검색 서비스
Runpod 모델 서버와 PostgreSQL pgvector 또는 FAISS를 사용한 특허 검색
"""
import os
import requests
import logging
from typing import List, Dict, Optional
from django.conf import settings
from patents.models import PatentRAGDocument

logger = logging.getLogger(__name__)


class RAGService:
    """RAG 검색 서비스 (PostgreSQL pgvector 또는 FAISS 자동 선택)"""

    def __init__(self):
        self.model_server_url = os.getenv('MODEL_SERVER_URL', 'http://localhost:8001')
        self.timeout = 30  # 타임아웃 30초
        self.use_faiss = os.getenv('USE_FAISS', 'false').lower() == 'true'
        self.faiss_service = None

        # FAISS 사용 설정이면 초기화 시도
        if self.use_faiss:
            try:
                from .faiss_rag_service import FAISSRAGService
                self.faiss_service = FAISSRAGService()
                if self.faiss_service.is_available():
                    logger.info("✅ FAISS RAG 서비스 활성화")
                else:
                    logger.warning("⚠️ FAISS 초기화 실패, PostgreSQL로 fallback")
                    self.use_faiss = False
            except Exception as e:
                logger.error(f"FAISS 로드 실패: {e}, PostgreSQL 사용")
                self.use_faiss = False

    def _get_embedding(self, text: str) -> List[float]:
        """
        Runpod 모델 서버에 텍스트를 전송하여 임베딩 벡터 획득
        """
        try:
            response = requests.post(
                f"{self.model_server_url}/embed",
                json={"text": text, "normalize": True},
                timeout=self.timeout
            )
            response.raise_for_status()
            data = response.json()
            return data['embedding']
        except requests.exceptions.RequestException as e:
            logger.error(f"임베딩 생성 실패: {e}")
            raise Exception(f"모델 서버 연결 실패: {e}")

    def search(self, query: str, top_k: int = 5) -> List[Dict]:
        """
        쿼리를 기반으로 유사한 특허 검색 (FAISS 또는 PostgreSQL 자동 선택)

        Args:
            query: 검색 쿼리
            top_k: 반환할 상위 결과 개수

        Returns:
            검색된 특허 문서 리스트
        """
        logger.info(f"RAG 검색 시작: '{query}' (top_k={top_k}, backend={'FAISS' if self.use_faiss else 'PostgreSQL'})")

        # FAISS 사용
        if self.use_faiss and self.faiss_service:
            return self.faiss_service.search(query, top_k)

        # PostgreSQL 사용 (기존 로직)

        try:
            # 1. 쿼리를 벡터로 변환
            query_embedding = self._get_embedding(query)
            logger.info(f"쿼리 임베딩 생성 완료 (차원: {len(query_embedding)})")

            # 2. PostgreSQL에서 벡터 유사도 검색
            # pgvector의 <=> 연산자: L2 거리 (작을수록 유사)
            # pgvector의 <#> 연산자: 내적 (클수록 유사, 정규화된 벡터에서는 코사인 유사도)
            # pgvector의 <-> 연산자: 코사인 거리 (작을수록 유사)

            from django.db import connection

            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT
                        doc_id,
                        application_number,
                        title_ko,
                        title_en,
                        ipc,
                        text,
                        source_ids,
                        (embedding <=> %s::vector) AS distance
                    FROM patent_rag_documents
                    ORDER BY distance
                    LIMIT %s
                """, [query_embedding, top_k])

                columns = [col[0] for col in cursor.description]
                results = [dict(zip(columns, row)) for row in cursor.fetchall()]

            logger.info(f"검색 완료: {len(results)}개 문서 발견")

            # 3. 결과 포매팅
            formatted_results = []
            for result in results:
                formatted_results.append({
                    'doc_id': result['doc_id'],
                    'application_number': result['application_number'],
                    'title_ko': result['title_ko'],
                    'title_en': result['title_en'],
                    'ipc': result['ipc'],
                    'text': result['text'][:1000],  # 텍스트는 1000자로 제한
                    'distance': float(result['distance']),
                    'similarity': 1 - float(result['distance'])  # 유사도 (1에 가까울수록 유사)
                })

            return formatted_results

        except Exception as e:
            logger.error(f"RAG 검색 실패: {e}")
            raise

    def search_by_patent(self, patent_text: str, top_k: int = 5, exclude_doc_id: Optional[str] = None) -> List[Dict]:
        """
        특허 텍스트를 기반으로 유사한 특허 검색

        Args:
            patent_text: 특허 전문 텍스트
            top_k: 반환할 상위 결과 개수
            exclude_doc_id: 제외할 문서 ID (자기 자신 제외)

        Returns:
            검색된 특허 문서 리스트
        """
        logger.info(f"특허 기반 검색 시작 (top_k={top_k})")

        try:
            # 1. 특허 텍스트를 벡터로 변환
            patent_embedding = self._get_embedding(patent_text[:2000])  # 2000자로 제한

            # 2. PostgreSQL에서 벡터 유사도 검색
            from django.db import connection

            with connection.cursor() as cursor:
                if exclude_doc_id:
                    cursor.execute("""
                        SELECT
                            doc_id,
                            application_number,
                            title_ko,
                            title_en,
                            ipc,
                            text,
                            (embedding <=> %s::vector) AS distance
                        FROM patent_rag_documents
                        WHERE doc_id != %s
                        ORDER BY distance
                        LIMIT %s
                    """, [patent_embedding, exclude_doc_id, top_k])
                else:
                    cursor.execute("""
                        SELECT
                            doc_id,
                            application_number,
                            title_ko,
                            title_en,
                            ipc,
                            text,
                            (embedding <=> %s::vector) AS distance
                        FROM patent_rag_documents
                        ORDER BY distance
                        LIMIT %s
                    """, [patent_embedding, top_k])

                columns = [col[0] for col in cursor.description]
                results = [dict(zip(columns, row)) for row in cursor.fetchall()]

            logger.info(f"검색 완료: {len(results)}개 유사 특허 발견")

            # 3. 결과 포매팅
            formatted_results = []
            for result in results:
                formatted_results.append({
                    'doc_id': result['doc_id'],
                    'application_number': result['application_number'],
                    'title_ko': result['title_ko'],
                    'title_en': result['title_en'],
                    'ipc': result['ipc'],
                    'text': result['text'][:1000],
                    'distance': float(result['distance']),
                    'similarity': 1 - float(result['distance'])
                })

            return formatted_results

        except Exception as e:
            logger.error(f"특허 기반 검색 실패: {e}")
            raise

    def classify_patents(self, patent_texts: List[str]) -> List[Dict]:
        """
        특허 분류 (Runpod 모델 서버 사용)

        Args:
            patent_texts: 분류할 특허 텍스트 리스트

        Returns:
            분류 결과 리스트
        """
        try:
            response = requests.post(
                f"{self.model_server_url}/classify",
                json={"texts": patent_texts},
                timeout=self.timeout
            )
            response.raise_for_status()
            data = response.json()
            return data['classifications']
        except requests.exceptions.RequestException as e:
            logger.error(f"특허 분류 실패: {e}")
            return []

    def health_check(self) -> bool:
        """
        Runpod 모델 서버 헬스 체크

        Returns:
            서버 정상 여부
        """
        try:
            response = requests.get(
                f"{self.model_server_url}/health",
                timeout=5
            )
            return response.status_code == 200
        except:
            return False
