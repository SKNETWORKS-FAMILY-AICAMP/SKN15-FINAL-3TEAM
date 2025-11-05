"""
LLaMA 모델 서버 예시
멀티턴 대화를 지원하는 FastAPI 서버

설치 필요:
pip install fastapi uvicorn transformers torch accelerate

실행:
python llama_model_server_example.py

주의: GPU가 없으면 매우 느림 (CPU 모드)
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Optional
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="LLaMA Model Server")

# 전역 변수로 모델 관리
model = None
tokenizer = None

class GenerateRequest(BaseModel):
    message: str
    file_content: Optional[str] = None
    conversation_history: Optional[List[Dict]] = None
    max_tokens: int = 512
    temperature: float = 0.7

class GenerateResponse(BaseModel):
    response: str

def load_model():
    """모델 초기화 (서버 시작 시 1회 실행)"""
    global model, tokenizer

    # LLaMA 3.2 3B 모델 (가장 작은 모델)
    # 더 작은 모델이 필요하면 "meta-llama/Llama-3.2-1B" 사용
    model_name = "meta-llama/Llama-3.2-3B-Instruct"

    logger.info(f"모델 로딩 중: {model_name}")

    try:
        # GPU 사용 가능 여부 확인
        device = "cuda" if torch.cuda.is_available() else "cpu"
        logger.info(f"사용 디바이스: {device}")

        # 토크나이저 로드
        tokenizer = AutoTokenizer.from_pretrained(model_name)

        # 모델 로드
        model = AutoModelForCausalLM.from_pretrained(
            model_name,
            torch_dtype=torch.float16 if device == "cuda" else torch.float32,
            device_map="auto" if device == "cuda" else None,
            low_cpu_mem_usage=True
        )

        if device == "cpu":
            model = model.to(device)

        logger.info("모델 로딩 완료!")

    except Exception as e:
        logger.error(f"모델 로딩 실패: {str(e)}")
        raise

def build_prompt_from_history(message: str, conversation_history: Optional[List[Dict]] = None) -> str:
    """대화 히스토리를 LLaMA 프롬프트 형식으로 변환"""

    # LLaMA 3.2 Instruct 프롬프트 형식
    prompt_parts = ["<|begin_of_text|>"]

    # 시스템 메시지
    prompt_parts.append("<|start_header_id|>system<|end_header_id|>")
    prompt_parts.append("당신은 특허 검색 및 분석을 도와주는 AI 어시스턴트입니다. 친절하고 정확하게 답변해주세요.<|eot_id|>")

    # 이전 대화 내역 추가
    if conversation_history:
        for hist in conversation_history[-10:]:  # 최근 10개만
            if hist['type'] == 'user':
                prompt_parts.append("<|start_header_id|>user<|end_header_id|>")
                prompt_parts.append(f"{hist['content']}<|eot_id|>")
            else:
                prompt_parts.append("<|start_header_id|>assistant<|end_header_id|>")
                prompt_parts.append(f"{hist['content']}<|eot_id|>")

    # 현재 사용자 메시지
    prompt_parts.append("<|start_header_id|>user<|end_header_id|>")
    prompt_parts.append(f"{message}<|eot_id|>")

    # AI 응답 시작
    prompt_parts.append("<|start_header_id|>assistant<|end_header_id|>")

    return "\n".join(prompt_parts)

@app.on_event("startup")
async def startup_event():
    """서버 시작 시 모델 로드"""
    load_model()

@app.get("/")
def health_check():
    """헬스 체크"""
    return {
        "status": "ok",
        "model_loaded": model is not None,
        "device": "cuda" if torch.cuda.is_available() else "cpu"
    }

@app.post("/generate", response_model=GenerateResponse)
def generate(request: GenerateRequest):
    """멀티턴 대화를 고려한 응답 생성"""

    if model is None or tokenizer is None:
        raise HTTPException(status_code=503, detail="모델이 로드되지 않았습니다")

    try:
        # 멀티턴 프롬프트 생성
        prompt = build_prompt_from_history(
            request.message,
            request.conversation_history
        )

        logger.info(f"생성 시작 - 메시지: {request.message[:50]}...")

        # 토큰화
        inputs = tokenizer(prompt, return_tensors="pt").to(model.device)

        # 응답 생성
        with torch.no_grad():
            outputs = model.generate(
                **inputs,
                max_new_tokens=request.max_tokens,
                temperature=request.temperature,
                do_sample=True,
                top_p=0.9,
                pad_token_id=tokenizer.eos_token_id
            )

        # 디코딩
        full_response = tokenizer.decode(outputs[0], skip_special_tokens=False)

        # 응답 부분만 추출 (프롬프트 제거)
        # <|start_header_id|>assistant<|end_header_id|> 이후 텍스트만 추출
        response_start = full_response.rfind("<|start_header_id|>assistant<|end_header_id|>")
        if response_start != -1:
            response_text = full_response[response_start + len("<|start_header_id|>assistant<|end_header_id|>"):]
            # <|eot_id|> 제거
            response_text = response_text.replace("<|eot_id|>", "").strip()
        else:
            response_text = full_response

        logger.info(f"생성 완료 - 응답 길이: {len(response_text)}")

        return GenerateResponse(response=response_text)

    except Exception as e:
        logger.error(f"응답 생성 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn

    # 서버 실행
    # GPU 서버라면 workers=1로 설정 (GPU 메모리 공유 이슈)
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8001,
        log_level="info"
    )
