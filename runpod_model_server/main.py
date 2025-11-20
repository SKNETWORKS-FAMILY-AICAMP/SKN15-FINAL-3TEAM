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

# 3. Qwen2.5-14B 베이스 모델 (등록건용 - 튜닝 안 된 원본)
logger.info("📦 Qwen2.5-14B 베이스 모델 로딩 (등록건용)...")
base_model_name = "Qwen/Qwen2.5-14B-Instruct"

try:
    # 베이스 모델 토크나이저
    base_tokenizer = AutoTokenizer.from_pretrained(
        base_model_name,
        trust_remote_code=True
    )

    # 베이스 모델 (등록건용 - LoRA 없음)
    base_model = AutoModelForCausalLM.from_pretrained(
        base_model_name,
        trust_remote_code=True,
        torch_dtype=torch.float16 if device == "cuda" else torch.float32,
        low_cpu_mem_usage=True
    ).to(device)
    base_model.eval()
    logger.info("✅ Qwen2.5-14B 베이스 모델 로드 완료 (등록건용)")

    BASE_MODEL_AVAILABLE = True
except Exception as e:
    logger.warning(f"⚠️ 베이스 모델 로드 실패: {e}. 등록건 분석 기능 비활성화")
    BASE_MODEL_AVAILABLE = False

# 4. SLLM (Qwen2.5-14B + qwen-14b LoRA) - 거절 이유 분석 전문 모델
logger.info("📦 SLLM (거절 이유 분석) 모델 로딩...")
sllm_adapter_path = "/workspace/models/qwen-14b"  # checkpoint-16 LoRA 어댑터

try:
    # SLLM 토크나이저 (베이스 모델과 동일)
    sllm_tokenizer = base_tokenizer  # 재사용

    # SLLM용 베이스 모델 별도 로드
    sllm_base_model = AutoModelForCausalLM.from_pretrained(
        base_model_name,  # "Qwen/Qwen2.5-14B-Instruct"
        trust_remote_code=True,
        torch_dtype=torch.float16 if device == "cuda" else torch.float32,
        low_cpu_mem_usage=True
    ).to(device)

    # qwen-14b (checkpoint-16) LoRA 어댑터 로드
    sllm_model = PeftModel.from_pretrained(
        sllm_base_model,
        sllm_adapter_path
    )
    sllm_model.eval()
    logger.info("✅ SLLM (거절 분석) 모델 로드 완료")

    SLLM_AVAILABLE = True
except Exception as e:
    logger.warning(f"⚠️ SLLM 모델 로드 실패: {e}. SLLM 기능 비활성화")
    SLLM_AVAILABLE = False

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
            "base_model": f"Qwen2.5-14B Base ({'available' if BASE_MODEL_AVAILABLE else 'unavailable'})",
            "sllm": f"Qwen2.5-14B + SLLM LoRA ({'available' if SLLM_AVAILABLE else 'unavailable'})"
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
                class_id = int(idx)
                predictions.append({
                    "class_id": class_id,
                    "label": f"label_{class_id}",  # label_0 (등록) 또는 label_1 (거절)
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
    """베이스 모델을 사용한 답변 생성 (등록건용)"""
    if not BASE_MODEL_AVAILABLE:
        raise HTTPException(status_code=503, detail="베이스 모델을 사용할 수 없습니다")

    try:
        # 토큰화
        inputs = base_tokenizer(
            request.prompt,
            return_tensors="pt",
            truncation=True,
            max_length=2048
        ).to(device)

        # 생성
        with torch.no_grad():
            outputs = base_model.generate(
                **inputs,
                max_new_tokens=request.max_length,
                temperature=request.temperature,
                top_p=request.top_p,
                do_sample=True,
                pad_token_id=base_tokenizer.pad_token_id,
                eos_token_id=base_tokenizer.eos_token_id
            )

        # 디코딩
        response = base_tokenizer.decode(
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
        is_rejection = False  # 거절 여부 플래그

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

            # 첫 번째 특허의 분류 결과로 거절 여부 판단
            # 분류 결과: label_0 = 등록, label_1 = 거절 (모델에 따라 다를 수 있음)
            first_classification = classification_result['classifications'][0]['predictions'][0]
            is_rejection = first_classification['label'] == 'label_1'
            logger.info(f"분류 결과: {'거절' if is_rejection else '등록'} (label: {first_classification['label']})")
        else:
            classified_patents = request.patents

        # 2. 유사 특허 목록 생성 (공통)
        similar_claims_text = ""
        mappings = []
        for i, p in enumerate(classified_patents, 1):
            app_no = p.get('application_number', 'N/A')
            title = p.get('title_ko', 'N/A')
            text = p.get('text', '')[:300]
            similar_claims_text += f"{i}) [출원번호: {app_no}]\n제목: {title}\n내용: {text}...\n\n"
            mappings.append(f"- 인용발명{i}: 출원번호 {app_no}")

        # 3. 거절건이면 SLLM 사용, 등록건이면 LLM 사용
        if is_rejection and SLLM_AVAILABLE:
            logger.info("🔴 거절 건 감지 → SLLM (checkpoint-16) 사용")

            # SLLM 프롬프트 구성 (거절 이유 분석 특화)
            system_msg = (
                "You are Qwen, a helpful patent analysis assistant.\n"
                "규칙:\n"
                "1) 반드시 한국어만 사용하고 중국어, 일본어 등 외국어(한자 포함)를 절대 사용하지 마십시오.\n"
                "2) 출력은 줄바꿈 없이 한 단락의 한국어 공식 문장으로만 작성하십시오.\n"
                "3) 본문에서 인용발명을 언급할 때는 반드시 '인용발명N(출원번호 XXXXX)' 형식으로 표기하십시오.\n"
            )

            # 선행문헌 정보 추출 (첫 번째 특허를 주 선행문헌으로)
            prior_art_no = classified_patents[0].get('application_number', 'N/A') if classified_patents else 'N/A'

            user_msg = (
                f"다음 (선행문헌/유사문서의 청구항 목록과 대상 청구항)을 바탕으로, "
                f"거절 사유(신규성, 진보성, 명확성 등)를 판별하고 핵심 근거를 3줄 이내로 간결히 설명해줘. "
                f"유사점과 차이점을 명확히 지적해.\n\n"
                f"[선행문헌/인용 번호]\n{prior_art_no}\n\n"
                f"[대상 청구항 / 사용자 질문]\n{request.query}\n\n"
                f"[유사 문서의 청구항 목록 (상위 {len(classified_patents)}개)]\n{similar_claims_text}"
                f"[인용발명 라벨-출원번호 매핑]\n" + "\n".join(mappings) + "\n\n"
                "주의: 본문에서 인용발명을 언급할 때는 반드시 '인용발명N(출원번호 XXXXX)' 형식으로 표기하고, "
                "한국어만 사용하며 한 단락으로 작성하라."
            )

            prompt = f"<|im_start|>system\n{system_msg}<|im_end|>\n<|im_start|>user\n{user_msg}<|im_end|>\n<|im_start|>assistant"

            # SLLM 생성 (checkpoint-16 파라미터 사용)
            inputs = sllm_tokenizer([prompt], return_tensors="pt", truncation=True, max_length=1792).to(device)

            with torch.inference_mode():
                outputs = sllm_model.generate(
                    **inputs,
                    max_new_tokens=256,
                    do_sample=False,
                    num_beams=3,
                    no_repeat_ngram_size=3,
                    length_penalty=0.9,
                    repetition_penalty=1.1,
                    pad_token_id=sllm_tokenizer.pad_token_id,
                    eos_token_id=sllm_tokenizer.eos_token_id
                )

            response_text = sllm_tokenizer.decode(
                outputs[0][inputs['input_ids'].shape[1]:],
                skip_special_tokens=True
            ).strip()

            # 후처리: 중국어 제거, 줄바꿈 제거
            import re
            response_text = re.sub(r'[\u4E00-\u9FFF]+', '', response_text)
            response_text = re.sub(r'\s*\n\s*', ' ', response_text).strip()

            # 마지막 문구 추가 (거절 결론)
            if not response_text.endswith("따라서 특허를 받을 수 없습니다."):
                if not response_text.endswith("."):
                    response_text += "."
                response_text += " 따라서 특허를 받을 수 없습니다."

            return {
                "query": request.query,
                "patents_used": len(classified_patents),
                "classified": True,
                "classification": "rejection",
                "model_used": "SLLM (checkpoint-16)",
                "response": response_text,
                "metadata": {
                    "prompt_length": inputs['input_ids'].shape[1],
                    "generated_length": outputs.shape[1] - inputs['input_ids'].shape[1]
                }
            }

        # 4. 등록건 → 베이스 모델 사용
        else:
            logger.info("🟢 등록 건 감지 → 베이스 모델 사용")

            # 등록건 프롬프트 구성
            system_msg = (
                "You are Qwen, a helpful patent analysis assistant.\n"
                "규칙:\n"
                "1) 반드시 한국어만 사용하고 중국어, 일본어 등 외국어(한자 포함)를 절대 사용하지 마십시오.\n"
                "2) 출력은 한 단락의 한국어 공식 문장으로만 작성하십시오.\n"
                "3) 유사 특허와 비교하여 등록 가능성이 있는 이유를 설명하십시오.\n"
            )

            user_msg = (
                f"다음 유사 특허 정보를 바탕으로 사용자의 청구항이 등록된 특허임을 분석해주세요.\n\n"
                f"[사용자 청구항]\n{request.query}\n\n"
                f"[유사 특허 목록 (상위 {len(classified_patents)}개)]\n{similar_claims_text}\n\n"
                "위 유사 특허들과 비교했을 때, 제출된 청구항은 등록된 특허입니다. "
                "유사 특허와의 차별점을 간단히 설명하고, 등록 가능한 이유를 한국어로 한 단락으로 작성해주세요."
            )

            prompt = f"<|im_start|>system\n{system_msg}<|im_end|>\n<|im_start|>user\n{user_msg}<|im_end|>\n<|im_start|>assistant"

            if BASE_MODEL_AVAILABLE:
                base_response = generate_response(
                    LLMRequest(
                        prompt=prompt,
                        max_length=request.max_length
                    )
                )

                return {
                    "query": request.query,
                    "patents_used": len(classified_patents),
                    "classified": request.use_classification and CLASSIFICATION_AVAILABLE,
                    "classification": "registration",
                    "model_used": "Base Model (Qwen2.5-14B)",
                    "response": base_response['response'],
                    "metadata": {
                        "prompt_length": base_response['prompt_length'],
                        "generated_length": base_response['generated_length']
                    }
                }
            else:
                # 베이스 모델 사용 불가 시 단순 메시지 반환
                return {
                    "query": request.query,
                    "patents_used": len(classified_patents),
                    "classified": request.use_classification and CLASSIFICATION_AVAILABLE,
                    "classification": "registration",
                    "model_used": "None",
                    "response": f"제출하신 청구항은 등록된 특허로 분류되었습니다. 관련 유사 특허 {len(classified_patents)}개를 찾았습니다.",
                    "metadata": {"base_model_available": False}
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
            "base_model": BASE_MODEL_AVAILABLE,
            "sllm": SLLM_AVAILABLE
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
