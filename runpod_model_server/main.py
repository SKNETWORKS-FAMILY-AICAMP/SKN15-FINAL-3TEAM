"""
Runpod 모델 서버 - FastAPI
BGE-M3 임베딩, Qwen2.5 분류 모델, Qwen2.5-14B 챗봇
"""
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import torch
from sentence_transformers import SentenceTransformer
from transformers import AutoTokenizer, AutoModelForSequenceClassification, AutoModelForCausalLM
from peft import PeftModel
import logging

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Patent RAG Model Server with Classification and LLM")

# GPU 사용 가능 여부 확인
device = "cuda" if torch.cuda.is_available() else "cpu"
logger.info(f"💻 Device: {device}")

# 모델 로딩 (서버 시작 시 한 번만)
logger.info("🚀 모델 로딩 중...")

# 1. BGE-M3 임베딩 모델
logger.info("📦 BGE-M3 임베딩 모델 로딩...")
embedding_model = SentenceTransformer('BAAI/bge-m3', device=device)
logger.info("✅ BGE-M3 모델 로드 완료")

# 2. Qwen2.5-7B 분류 모델 (LoRA 어댑터)
logger.info("📦 Qwen2.5-7B 분류 모델 로딩...")
classification_base_model_name = "Qwen/Qwen2.5-7B-Instruct"
classification_adapter_path = "/workspace/models/classification"  # Runpod에서 모델 경로

try:
    # 분류 모델 토크나이저
    classification_tokenizer = AutoTokenizer.from_pretrained(
        classification_base_model_name,
        trust_remote_code=True
    )

    # 분류 베이스 모델
    classification_base_model = AutoModelForSequenceClassification.from_pretrained(
        classification_base_model_name,
        num_labels=2,  # 실제 모델이 2-class로 학습됨
        trust_remote_code=True,
        torch_dtype=torch.float16 if device == "cuda" else torch.float32
    )

    # LoRA 어댑터 로드
    classification_model = PeftModel.from_pretrained(
        classification_base_model,
        classification_adapter_path
    )
    classification_model = classification_model.to(device)
    classification_model.eval()
    logger.info("✅ Qwen2.5-7B 분류 모델 로드 완료")

    CLASSIFICATION_AVAILABLE = True
except Exception as e:
    logger.warning(f"⚠️ 분류 모델 로드 실패: {e}. 분류 기능 비활성화")
    CLASSIFICATION_AVAILABLE = False

# 3. Qwen2.5-14B 챗봇 모델 (LoRA 어댑터)
logger.info("📦 Qwen2.5-14B 챗봇 모델 로딩...")
llm_base_model_name = "Qwen/Qwen2.5-14B-Instruct"
llm_adapter_path = "/workspace/models/qwen-14b"  # Runpod에서 모델 경로

try:
    # LLM 토크나이저
    llm_tokenizer = AutoTokenizer.from_pretrained(
        llm_base_model_name,
        trust_remote_code=True
    )

    # LLM 베이스 모델
    llm_base_model = AutoModelForCausalLM.from_pretrained(
        llm_base_model_name,
        trust_remote_code=True,
        torch_dtype=torch.float16 if device == "cuda" else torch.float32,
        device_map="auto"
    )

    # LoRA 어댑터 로드
    llm_model = PeftModel.from_pretrained(
        llm_base_model,
        llm_adapter_path
    )
    llm_model.eval()
    logger.info("✅ Qwen2.5-14B 챗봇 모델 로드 완료")

    LLM_AVAILABLE = True
except Exception as e:
    logger.warning(f"⚠️ LLM 모델 로드 실패: {e}. LLM 기능 비활성화")
    LLM_AVAILABLE = False

logger.info("🎉 모든 모델 로딩 완료!")


# API 모델
class EmbedRequest(BaseModel):
    text: str
    normalize: bool = True


class EmbedBatchRequest(BaseModel):
    texts: List[str]
    normalize: bool = True


class ClassifyRequest(BaseModel):
    texts: List[str]
    top_k: int = 3  # 상위 K개 클래스 반환


class LLMRequest(BaseModel):
    prompt: str
    max_length: int = 512
    temperature: float = 0.7
    top_p: float = 0.9


class RAGPipelineRequest(BaseModel):
    """전체 RAG 파이프라인 요청"""
    query: str
    patents: List[dict]  # RAG 검색 결과
    use_classification: bool = True
    max_length: int = 512


# API 엔드포인트
@app.get("/")
def root():
    """서버 상태 확인"""
    return {
        "status": "running",
        "device": device,
        "models": {
            "embedding": "BAAI/bge-m3",
            "classification": f"Qwen2.5-7B + LoRA ({'available' if CLASSIFICATION_AVAILABLE else 'unavailable'})",
            "llm": f"Qwen2.5-14B + LoRA ({'available' if LLM_AVAILABLE else 'unavailable'})"
        }
    }


@app.post("/embed")
def embed_text(request: EmbedRequest):
    """단일 텍스트를 벡터로 변환"""
    try:
        embedding = embedding_model.encode(
            request.text,
            normalize_embeddings=request.normalize,
            show_progress_bar=False
        )
        return {
            "embedding": embedding.tolist(),
            "dimension": len(embedding)
        }
    except Exception as e:
        logger.error(f"임베딩 생성 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/embed/batch")
def embed_batch(request: EmbedBatchRequest):
    """여러 텍스트를 배치로 벡터화"""
    try:
        embeddings = embedding_model.encode(
            request.texts,
            normalize_embeddings=request.normalize,
            show_progress_bar=False,
            batch_size=32
        )
        return {
            "embeddings": embeddings.tolist(),
            "count": len(embeddings),
            "dimension": embeddings.shape[1]
        }
    except Exception as e:
        logger.error(f"배치 임베딩 생성 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/classify")
def classify_patents(request: ClassifyRequest):
    """특허 IPC 분류"""
    if not CLASSIFICATION_AVAILABLE:
        raise HTTPException(status_code=503, detail="분류 모델을 사용할 수 없습니다")

    try:
        results = []

        for text in request.texts:
            # 토큰화
            inputs = classification_tokenizer(
                text[:512],  # 최대 512 토큰
                return_tensors="pt",
                truncation=True,
                max_length=512
            ).to(device)

            # 추론
            with torch.no_grad():
                outputs = classification_model(**inputs)
                logits = outputs.logits

            # 상위 K개 클래스
            probs = torch.softmax(logits, dim=-1)[0]
            top_k_probs, top_k_indices = torch.topk(probs, request.top_k)

            predictions = []
            for prob, idx in zip(top_k_probs.cpu(), top_k_indices.cpu()):
                predictions.append({
                    "class_id": int(idx),
                    "confidence": float(prob)
                })

            results.append({
                "text": text[:100] + "..." if len(text) > 100 else text,
                "predictions": predictions
            })

        return {"classifications": results}

    except Exception as e:
        logger.error(f"분류 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/generate")
def generate_response(request: LLMRequest):
    """LLM을 사용한 답변 생성"""
    if not LLM_AVAILABLE:
        raise HTTPException(status_code=503, detail="LLM 모델을 사용할 수 없습니다")

    try:
        # 토큰화
        inputs = llm_tokenizer(
            request.prompt,
            return_tensors="pt",
            truncation=True,
            max_length=2048
        ).to(device)

        # 생성
        with torch.no_grad():
            outputs = llm_model.generate(
                **inputs,
                max_new_tokens=request.max_length,
                temperature=request.temperature,
                top_p=request.top_p,
                do_sample=True,
                pad_token_id=llm_tokenizer.pad_token_id,
                eos_token_id=llm_tokenizer.eos_token_id
            )

        # 디코딩
        response = llm_tokenizer.decode(
            outputs[0][inputs['input_ids'].shape[1]:],
            skip_special_tokens=True
        )

        return {
            "response": response.strip(),
            "prompt_length": inputs['input_ids'].shape[1],
            "generated_length": outputs.shape[1] - inputs['input_ids'].shape[1]
        }

    except Exception as e:
        logger.error(f"생성 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/rag/pipeline")
def rag_pipeline(request: RAGPipelineRequest):
    """
    전체 RAG 파이프라인: 검색 → 분류 → LLM 답변
    """
    try:
        # 1. 분류 (선택사항)
        classified_patents = []
        if request.use_classification and CLASSIFICATION_AVAILABLE:
            logger.info("특허 분류 수행 중...")

            patent_texts = [p.get('text', '')[:512] for p in request.patents]
            classification_result = classify_patents(
                ClassifyRequest(texts=patent_texts, top_k=1)
            )

            for i, patent in enumerate(request.patents):
                patent_with_class = patent.copy()
                patent_with_class['classification'] = classification_result['classifications'][i]
                classified_patents.append(patent_with_class)
        else:
            classified_patents = request.patents

        # 2. LLM 프롬프트 구성
        context = "\n\n".join([
            f"[특허 {i+1}] {p['application_number']}\n"
            f"제목: {p.get('title_ko', 'N/A')}\n"
            f"IPC: {p.get('ipc', 'N/A')}\n"
            + (f"분류 결과: {p.get('classification', {}).get('predictions', [{}])[0].get('class_id', 'N/A')}\n"
               if request.use_classification else "")
            + f"내용: {p.get('text', '')[:300]}..."
            for i, p in enumerate(classified_patents)
        ])

        prompt = f"""다음은 검색된 관련 특허 정보입니다:

{context}

사용자 질문: {request.query}

위 특허 정보를 참고하여 사용자의 질문에 답변해주세요.
특허 번호와 제목을 언급하면서 명확하게 설명해주세요."""

        # 3. LLM 답변 생성
        if LLM_AVAILABLE:
            logger.info("LLM 답변 생성 중...")
            llm_response = generate_response(
                LLMRequest(
                    prompt=prompt,
                    max_length=request.max_length
                )
            )

            return {
                "query": request.query,
                "patents_used": len(classified_patents),
                "classified": request.use_classification and CLASSIFICATION_AVAILABLE,
                "response": llm_response['response'],
                "metadata": {
                    "prompt_length": llm_response['prompt_length'],
                    "generated_length": llm_response['generated_length']
                }
            }
        else:
            # LLM 사용 불가 시 검색 결과만 반환
            return {
                "query": request.query,
                "patents_used": len(classified_patents),
                "classified": request.use_classification and CLASSIFICATION_AVAILABLE,
                "response": f"관련 특허 {len(classified_patents)}개를 찾았습니다:\n\n{context}",
                "metadata": {"llm_available": False}
            }

    except Exception as e:
        logger.error(f"RAG 파이프라인 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
def health_check():
    """헬스 체크"""
    return {
        "status": "healthy",
        "gpu_available": torch.cuda.is_available(),
        "device": device,
        "models": {
            "embedding": True,
            "classification": CLASSIFICATION_AVAILABLE,
            "llm": LLM_AVAILABLE
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
