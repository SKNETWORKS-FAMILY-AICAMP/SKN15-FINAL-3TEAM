"""
KoSBERT 모델 로더 - Hugging Face에서 모델 자동 다운로드 및 캐싱
"""

import os
import logging
from typing import Optional, List
from sentence_transformers import SentenceTransformer
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

logger = logging.getLogger(__name__)


class KoSBERTModelLoader:
    """KoSBERT 모델 로더 및 임베딩 생성기"""

    # 기본 모델명 (Hugging Face에서 자동 다운로드)
    DEFAULT_MODEL_NAME = "BM-K/KoSimCSE-roberta"

    def __init__(self, model_name: Optional[str] = None, cache_dir: Optional[str] = None):
        """
        KoSBERT 모델 초기화

        Args:
            model_name: Hugging Face 모델 이름 (기본값: BM-K/KoSimCSE-roberta)
            cache_dir: 모델 캐시 디렉토리 (기본값: ~/.cache/huggingface)
        """
        self.model_name = model_name or self.DEFAULT_MODEL_NAME
        self.cache_dir = cache_dir
        self.model: Optional[SentenceTransformer] = None

    def load_model(self) -> SentenceTransformer:
        """
        모델을 로드합니다 (처음 실행 시 Hugging Face에서 다운로드)

        Returns:
            SentenceTransformer 모델 인스턴스
        """
        if self.model is not None:
            return self.model

        try:
            logger.info(f"KoSBERT 모델 로딩 중: {self.model_name}")

            # Hugging Face에서 모델 다운로드 및 로드
            # 최초 실행 시에만 다운로드, 이후에는 캐시 사용
            self.model = SentenceTransformer(
                self.model_name,
                cache_folder=self.cache_dir
            )

            logger.info(f"KoSBERT 모델 로딩 완료: {self.model_name}")
            return self.model

        except Exception as e:
            logger.error(f"모델 로딩 실패: {str(e)}")
            raise RuntimeError(f"KoSBERT 모델을 로드할 수 없습니다: {str(e)}")

    def encode(self, texts: List[str]) -> np.ndarray:
        """
        텍스트를 임베딩 벡터로 변환

        Args:
            texts: 임베딩할 텍스트 리스트

        Returns:
            임베딩 벡터 배열 (shape: [num_texts, embedding_dim])
        """
        if self.model is None:
            self.load_model()

        try:
            embeddings = self.model.encode(texts, convert_to_numpy=True)
            return embeddings
        except Exception as e:
            logger.error(f"임베딩 생성 실패: {str(e)}")
            raise RuntimeError(f"텍스트 임베딩 생성에 실패했습니다: {str(e)}")

    def compute_similarity(self, text1: str, text2: str) -> float:
        """
        두 텍스트 간의 코사인 유사도 계산

        Args:
            text1: 첫 번째 텍스트
            text2: 두 번째 텍스트

        Returns:
            코사인 유사도 (0~1 사이의 값)
        """
        embeddings = self.encode([text1, text2])
        similarity = cosine_similarity([embeddings[0]], [embeddings[1]])[0][0]
        return float(similarity)

    def find_most_similar(self, query: str, candidates: List[str], top_k: int = 5) -> List[tuple]:
        """
        쿼리와 가장 유사한 텍스트들을 찾습니다

        Args:
            query: 쿼리 텍스트
            candidates: 후보 텍스트 리스트
            top_k: 반환할 상위 결과 개수

        Returns:
            (인덱스, 유사도) 튜플 리스트 (유사도 내림차순)
        """
        if not candidates:
            return []

        # 쿼리와 모든 후보의 임베딩 생성
        query_embedding = self.encode([query])
        candidate_embeddings = self.encode(candidates)

        # 코사인 유사도 계산
        similarities = cosine_similarity(query_embedding, candidate_embeddings)[0]

        # 상위 k개 결과 반환
        top_indices = np.argsort(similarities)[::-1][:top_k]
        results = [(int(idx), float(similarities[idx])) for idx in top_indices]

        return results


# 싱글톤 인스턴스
_model_loader_instance: Optional[KoSBERTModelLoader] = None


def get_kosbert_loader() -> KoSBERTModelLoader:
    """
    KoSBERT 모델 로더 인스턴스를 반환 (싱글톤)

    Returns:
        KoSBERTModelLoader 인스턴스
    """
    global _model_loader_instance
    if _model_loader_instance is None:
        _model_loader_instance = KoSBERTModelLoader()
        # 애플리케이션 시작 시 모델 미리 로드 (선택사항)
        # _model_loader_instance.load_model()
    return _model_loader_instance
