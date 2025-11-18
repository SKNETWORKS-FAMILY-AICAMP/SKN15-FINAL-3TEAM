"""
FAISS 기반 RAG 검색 서비스
로컬 FAISS 인덱스를 사용한 특허 검색
"""
import os
import logging
from typing import List, Dict, Optional
import numpy as np
import pandas as pd
import faiss
from django.conf import settings

logger = logging.getLogger(__name__)


class FAISSRAGService:
    """FAISS 기반 특허 검색 서비스"""

    def __init__(self):
        # 경로 설정 (Django settings에서 가져오거나 기본값 사용)
        base_dir = getattr(settings, 'FAISS_BASE_DIR', '/home/ubuntu/rag_data')
        self.index_path = os.path.join(base_dir, "artifacts", "index_ip_bgem3_v2.faiss")
        self.doc_ids_path = os.path.join(base_dir, "artifacts", "doc_ids_bgem3_v2.npy")
        self.corpus_path = os.path.join(base_dir, "corpus.csv")

        self.initialized = False
        self.index = None
        self.doc_ids = None
        self.doc_map = {}

        # Lazy loading - 실제 사용할 때 로드
        self._try_initialize()

    def _try_initialize(self):
        """FAISS 인덱스 초기화 시도"""
        try:
            # 파일 존재 확인
            if not os.path.exists(self.index_path):
                logger.warning(f"FAISS 인덱스 파일 없음: {self.index_path}")
                return False

            if not os.path.exists(self.doc_ids_path):
                logger.warning(f"Doc IDs 파일 없음: {self.doc_ids_path}")
                return False

            if not os.path.exists(self.corpus_path):
                logger.warning(f"Corpus 파일 없음: {self.corpus_path}")
                return False

            # Corpus 로드
            logger.info("Corpus 로딩 중...")
            corpus_df = self._load_corpus(self.corpus_path)
            self.doc_map = {
                str(r["doc_id"]): {
                    "title": str(r["title"]) if isinstance(r["title"], str) else "",
                    "text": str(r["text"]) if isinstance(r["text"], str) else "",
                }
                for _, r in corpus_df.iterrows()
            }
            logger.info(f"Corpus 로드 완료: {len(self.doc_map)}개 문서")

            # FAISS 인덱스 로드
            logger.info("FAISS 인덱스 로딩 중...")
            self.index = faiss.read_index(self.index_path)
            logger.info(f"FAISS 인덱스 로드 완료: {self.index.ntotal}개 벡터")

            # Doc IDs 로드
            raw_doc_ids = np.load(self.doc_ids_path, allow_pickle=True)
            self.doc_ids = np.array(raw_doc_ids).astype(str)
            logger.info(f"Doc IDs 로드 완료: {len(self.doc_ids)}개")

            self.initialized = True
            logger.info("✅ FAISS RAG 서비스 초기화 완료")
            return True

        except Exception as e:
            logger.error(f"FAISS 초기화 실패: {e}")
            return False

    def _load_corpus(self, corpus_path: str) -> pd.DataFrame:
        """Corpus CSV 로드"""
        df = pd.read_csv(corpus_path)

        if "doc_id" not in df.columns:
            raise KeyError(f"corpus에 doc_id 컬럼 없음: {list(df.columns)}")

        # title 컬럼 찾기
        title_col = None
        for cand in ["title_ko", "title", "title_en"]:
            if cand in df.columns:
                title_col = cand
                break
        if title_col is None:
            df["__title"] = ""
            title_col = "__title"

        # text 컬럼 찾기
        text_col = None
        for cand in ["full_text", "text", "body", "contents"]:
            if cand in df.columns:
                text_col = cand
                break
        if text_col is None:
            raise KeyError("본문 텍스트 컬럼 없음(full_text/text/body/contents)")

        df["doc_id"] = df["doc_id"].astype(str)
        out = df[["doc_id", title_col, text_col]].copy()
        out = out.rename(columns={title_col: "title", text_col: "text"})

        return out

    def search(self, query: str, top_k: int = 5) -> List[Dict]:
        """
        FAISS로 유사한 특허 검색 (Runpod 임베딩 사용)

        Args:
            query: 검색 쿼리
            top_k: 반환할 상위 결과 개수

        Returns:
            검색된 특허 문서 리스트
        """
        if not self.initialized:
            logger.warning("FAISS가 초기화되지 않았습니다. PostgreSQL로 fallback...")
            return []

        try:
            # Runpod 모델 서버로 임베딩 생성
            import requests
            model_server_url = os.getenv('MODEL_SERVER_URL', 'http://localhost:8001')

            response = requests.post(
                f"{model_server_url}/embed",
                json={"text": query, "normalize": True},
                timeout=30
            )
            response.raise_for_status()
            query_embedding = response.json()['embedding']

            # numpy array로 변환 및 정규화
            q_emb = np.array([query_embedding], dtype='float32')
            q_emb = q_emb / np.linalg.norm(q_emb, axis=1, keepdims=True)

            # FAISS 검색
            distances, indices = self.index.search(q_emb, top_k)

            # 결과 포매팅
            results = []
            for rank, (idx, dist) in enumerate(zip(indices[0], distances[0]), start=1):
                if idx < 0:
                    continue

                doc_id = self.doc_ids[idx]
                info = self.doc_map.get(doc_id, {"title": "", "text": ""})

                results.append({
                    'doc_id': doc_id,
                    'application_number': doc_id,  # doc_id를 application_number로 사용
                    'title_ko': info['title'],
                    'title_en': '',
                    'ipc': '',  # FAISS에는 IPC 정보 없음
                    'text': info['text'][:1000],  # 1000자로 제한
                    'distance': float(dist),
                    'similarity': 1 - float(dist)  # L2 거리를 유사도로 변환
                })

            logger.info(f"FAISS 검색 완료: {len(results)}개 문서 발견")
            return results

        except Exception as e:
            logger.error(f"FAISS 검색 실패: {e}")
            return []

    def is_available(self) -> bool:
        """FAISS 서비스 사용 가능 여부"""
        return self.initialized
