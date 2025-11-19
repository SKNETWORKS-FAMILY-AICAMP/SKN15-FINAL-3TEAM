"""
OpenAI API를 사용한 RAG 검색 서비스
임베딩, 분류, LLM을 모두 OpenAI로 처리
"""
import os
import logging
from typing import List, Dict, Optional
from openai import OpenAI

logger = logging.getLogger(__name__)


class OpenAIRAGService:
    """OpenAI API 기반 RAG 서비스"""

    def __init__(self):
        self.api_key = os.getenv('OPENAI_API_KEY')
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY 환경 변수가 설정되지 않았습니다")

        self.client = OpenAI(api_key=self.api_key)
        self.embedding_model = "text-embedding-3-large"  # 3072 차원
        self.chat_model = "gpt-4o-mini"  # 비용 절약용, gpt-4도 가능

        logger.info("✅ OpenAI RAG 서비스 초기화 완료")

    def _get_embedding(self, text: str) -> List[float]:
        """
        OpenAI 임베딩 API로 벡터 생성
        """
        try:
            response = self.client.embeddings.create(
                model=self.embedding_model,
                input=text[:8000],  # OpenAI 최대 토큰 제한
                encoding_format="float"
            )
            return response.data[0].embedding
        except Exception as e:
            logger.error(f"OpenAI 임베딩 생성 실패: {e}")
            raise Exception(f"임베딩 생성 실패: {e}")

    def search(self, query: str, top_k: int = 5) -> List[Dict]:
        """
        PostgreSQL pgvector를 사용한 검색
        (OpenAI 임베딩 사용)
        """
        logger.info(f"OpenAI RAG 검색 시작: '{query}' (top_k={top_k})")

        try:
            # 1. 쿼리를 벡터로 변환 (OpenAI)
            query_embedding = self._get_embedding(query)
            logger.info(f"OpenAI 임베딩 생성 완료 (차원: {len(query_embedding)})")

            # 2. PostgreSQL에서 벡터 유사도 검색
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
                    'text': result['text'][:1000],
                    'distance': float(result['distance']),
                    'similarity': 1 - float(result['distance'])
                })

            return formatted_results

        except Exception as e:
            logger.error(f"RAG 검색 실패: {e}")
            raise

    def classify_patent(self, patent_text: str) -> Dict:
        """
        GPT를 사용한 특허 분류 (거절 vs 등록)
        """
        try:
            response = self.client.chat.completions.create(
                model=self.chat_model,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "당신은 특허 분류 전문가입니다. "
                            "주어진 특허 텍스트를 분석하여 '거절' 또는 '등록'으로 분류하세요. "
                            "응답은 반드시 JSON 형식으로: {\"classification\": \"거절\" 또는 \"등록\", \"confidence\": 0.0~1.0}"
                        )
                    },
                    {
                        "role": "user",
                        "content": f"다음 특허를 분류하세요:\n\n{patent_text[:2000]}"
                    }
                ],
                temperature=0.3,
                response_format={"type": "json_object"}
            )

            import json
            result = json.loads(response.choices[0].message.content)

            return {
                "label": "label_1" if result["classification"] == "거절" else "label_0",
                "confidence": result.get("confidence", 0.5)
            }

        except Exception as e:
            logger.error(f"특허 분류 실패: {e}")
            # 기본값 반환 (거절로 가정)
            return {"label": "label_1", "confidence": 0.5}

    def generate_response(
        self,
        query: str,
        patents: List[Dict],
        is_rejection: bool = False
    ) -> str:
        """
        GPT를 사용한 답변 생성
        거절건과 등록건을 다르게 처리
        """
        try:
            # 유사 특허 정보 구성
            similar_patents_text = ""
            for i, p in enumerate(patents, 1):
                app_no = p.get('application_number', 'N/A')
                title = p.get('title_ko', 'N/A')
                text = p.get('text', '')[:300]
                similar_patents_text += (
                    f"{i}) [출원번호: {app_no}]\n"
                    f"제목: {title}\n"
                    f"내용: {text}...\n\n"
                )

            # 시스템 프롬프트 (거절/등록에 따라 다름)
            if is_rejection:
                system_prompt = (
                    "당신은 특허 거절 이유 분석 전문가입니다. "
                    "거절 사유(신규성, 진보성, 명확성 등)를 판별하고 핵심 근거를 간결히 설명하세요. "
                    "유사점과 차이점을 명확히 지적하세요. "
                    "반드시 한국어로만 작성하고, 마지막에 '따라서 특허를 받을 수 없습니다.'로 끝내세요."
                )
            else:
                system_prompt = (
                    "당신은 특허 분석 전문가입니다. "
                    "유사 특허 정보를 바탕으로 사용자 질문에 답변하세요. "
                    "반드시 한국어로만 작성하고, 간결하게 답변하세요."
                )

            user_prompt = (
                f"[사용자 질문]\n{query}\n\n"
                f"[유사 특허 목록 (상위 {len(patents)}개)]\n{similar_patents_text}\n\n"
                "위 정보를 바탕으로 답변해주세요."
            )

            response = self.client.chat.completions.create(
                model=self.chat_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.7,
                max_tokens=512
            )

            answer = response.choices[0].message.content.strip()

            # 거절건이면 마지막 문구 확인
            if is_rejection and not answer.endswith("따라서 특허를 받을 수 없습니다."):
                if not answer.endswith("."):
                    answer += "."
                answer += " 따라서 특허를 받을 수 없습니다."

            return answer

        except Exception as e:
            logger.error(f"답변 생성 실패: {e}")
            return f"죄송합니다. 답변 생성 중 오류가 발생했습니다: {str(e)}"

    def rag_pipeline(
        self,
        query: str,
        use_classification: bool = True,
        top_k: int = 3
    ) -> str:
        """
        전체 RAG 파이프라인: 검색 → 분류 → 답변 생성
        """
        logger.info(f"OpenAI RAG 파이프라인 시작: '{query}'")

        try:
            # 1. RAG 검색
            patents = self.search(query, top_k=top_k)

            if not patents:
                return "죄송합니다. 관련된 특허를 찾지 못했습니다."

            # 2. 분류 (선택적)
            is_rejection = False
            if use_classification and patents:
                # 첫 번째 특허로 분류
                classification = self.classify_patent(patents[0]['text'])
                is_rejection = classification['label'] == 'label_1'
                logger.info(f"분류 결과: {'거절' if is_rejection else '등록'}")

            # 3. 답변 생성
            response = self.generate_response(
                query=query,
                patents=patents,
                is_rejection=is_rejection
            )

            return response

        except Exception as e:
            logger.error(f"RAG 파이프라인 실패: {e}")
            return f"죄송합니다. 처리 중 오류가 발생했습니다: {str(e)}"

    def health_check(self) -> bool:
        """OpenAI API 연결 확인"""
        try:
            # 간단한 임베딩 테스트
            self._get_embedding("test")
            return True
        except:
            return False
