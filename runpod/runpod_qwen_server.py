"""
RunPod용 Qwen 2.5 14B QLoRA 모델 서버
특허 분석 특화 챗봇 서버

설치 필요:
pip install fastapi uvicorn transformers peft accelerate bitsandbytes

실행:
python runpod_qwen_server.py

환경 변수:
- MODEL_PATH: Qwen 체크포인트 경로 (기본: /workspace/Qwen-14B-checkpoint-16)
- PORT: 서버 포트 (기본: 8000)
"""

import os
import logging
from typing import List, Dict, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# FastAPI 앱
app = FastAPI(
    title="Qwen Patent Analysis Server",
    description="Qwen 2.5 14B + QLoRA 특허 분석 전문 서버",
    version="2.0.0"
)

# CORS 설정 (Django 백엔드 접근 허용)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 프로덕션: 특정 도메인만 허용
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 전역 변수
model = None
tokenizer = None
device = None

# 환경 변수
MODEL_PATH = os.getenv("MODEL_PATH", "/workspace/Qwen-14B-checkpoint-16")
PORT = int(os.getenv("PORT", "8000"))


class GenerateRequest(BaseModel):
    """생성 요청 스키마"""
    message: str = Field(..., description="사용자 메시지", min_length=1)
    file_content: Optional[str] = Field(None, description="업로드된 파일 내용")
    conversation_history: Optional[List[Dict]] = Field(
        None,
        description="이전 대화 내역 [{'type': 'user'|'ai', 'content': '...'}]"
    )
    max_tokens: int = Field(
        512,
        description="최대 생성 토큰 수",
        ge=1,
        le=2048
    )
    temperature: float = Field(
        0.7,
        description="생성 온도 (0.0~2.0)",
        ge=0.0,
        le=2.0
    )


class GenerateResponse(BaseModel):
    """생성 응답 스키마"""
    response: str = Field(..., description="AI 응답 텍스트")
    model: str = Field(..., description="사용된 모델 이름")


class HealthResponse(BaseModel):
    """헬스체크 응답 스키마"""
    status: str
    model: str
    model_loaded: bool
    device: str
    gpu_available: bool
    gpu_name: Optional[str] = None


def load_model():
    """Qwen 모델 + QLoRA 어댑터 초기화"""
    global model, tokenizer, device

    logger.info("=" * 60)
    logger.info("🔥 Qwen 2.5 14B QLoRA 모델 서버 초기화 시작")
    logger.info("=" * 60)

    # GPU 확인
    device = "cuda" if torch.cuda.is_available() else "cpu"
    logger.info(f"✅ 사용 디바이스: {device}")

    if device == "cuda":
        gpu_name = torch.cuda.get_device_name(0)
        gpu_memory = torch.cuda.get_device_properties(0).total_memory / 1024**3
        logger.info(f"✅ GPU: {gpu_name}")
        logger.info(f"✅ GPU 메모리: {gpu_memory:.1f} GB")
    else:
        logger.warning("⚠️  GPU를 사용할 수 없습니다. CPU 모드로 실행됩니다.")

    try:
        # 1. 베이스 모델 로드
        logger.info("📥 1/3: 베이스 모델 로딩 (Qwen 2.5 14B Instruct)...")
        base_model = AutoModelForCausalLM.from_pretrained(
            "Qwen/Qwen2.5-14B-Instruct",
            torch_dtype=torch.float16 if device == "cuda" else torch.float32,
            device_map="auto" if device == "cuda" else None,
            trust_remote_code=True,
            low_cpu_mem_usage=True,
            load_in_8bit=True if device == "cuda" else False  # 8비트 양자화
        )

        if device == "cpu":
            base_model = base_model.to(device)

        logger.info("✅ 베이스 모델 로딩 완료")

        # 2. QLoRA 어댑터 적용
        logger.info(f"📥 2/3: QLoRA 어댑터 로딩 ({MODEL_PATH})...")
        model = PeftModel.from_pretrained(
            base_model,
            MODEL_PATH
        )
        logger.info("✅ QLoRA 어댑터 로딩 완료")

        # 3. 토크나이저 로드
        logger.info("📥 3/3: 토크나이저 로딩...")
        tokenizer = AutoTokenizer.from_pretrained(
            MODEL_PATH,
            trust_remote_code=True
        )

        # pad_token 설정
        if tokenizer.pad_token is None:
            tokenizer.pad_token = tokenizer.eos_token

        logger.info("✅ 토크나이저 로딩 완료")

        # 모델 평가 모드
        model.eval()

        logger.info("=" * 60)
        logger.info("✅ 모델 서버 초기화 완료!")
        logger.info(f"   - 모델: Qwen 2.5 14B + QLoRA")
        logger.info(f"   - 디바이스: {device}")
        logger.info(f"   - 체크포인트: {MODEL_PATH}")
        logger.info("=" * 60)

    except Exception as e:
        logger.error(f"❌ 모델 로딩 실패: {str(e)}")
        raise


def build_qwen_prompt(
    message: str,
    file_content: Optional[str] = None,
    conversation_history: Optional[List[Dict]] = None
) -> str:
    """
    Qwen ChatML 형식으로 프롬프트 생성

    Args:
        message: 현재 사용자 메시지
        file_content: 업로드된 파일 내용
        conversation_history: 이전 대화 내역

    Returns:
        Qwen ChatML 형식 프롬프트
    """
    # 메시지 리스트 구성
    messages = [
        {
            "role": "system",
            "content": (
                "당신은 특허 분석 전문 AI 어시스턴트입니다.\n\n"
                "**주요 역할:**\n"
                "1. 특허 청구항 분석 및 신규성/진보성 평가\n"
                "2. 유사 특허 비교 분석\n"
                "3. 특허 등록 가능성 판단 및 개선 제안\n"
                "4. 일반적인 대화 및 질의응답\n\n"
                "**응답 원칙:**\n"
                "- 특허 질문: 전문적이고 상세한 분석 제공\n"
                "- 일반 대화: 친절하고 간단한 답변\n"
                "- 불확실한 내용: 솔직하게 모른다고 말하기\n"
                "- 항상 한국어로 응답"
            )
        }
    ]

    # 대화 히스토리 추가 (최근 10턴)
    if conversation_history:
        for hist in conversation_history[-10:]:
            role = "user" if hist.get('type') == 'user' else "assistant"
            content = hist.get('content', '')
            if content:
                messages.append({"role": role, "content": content})

    # 현재 사용자 메시지 구성
    user_message_parts = []

    if file_content:
        user_message_parts.append(f"[첨부 파일]\n{file_content[:1000]}\n")

    user_message_parts.append(message)

    messages.append({
        "role": "user",
        "content": "\n".join(user_message_parts)
    })

    # Qwen ChatML 형식으로 자동 변환
    prompt = tokenizer.apply_chat_template(
        messages,
        tokenize=False,
        add_generation_prompt=True
    )

    return prompt


@app.on_event("startup")
async def startup_event():
    """서버 시작 시 모델 로드"""
    load_model()


@app.get("/", response_model=HealthResponse)
async def root():
    """루트 엔드포인트 - 헬스체크"""
    gpu_name = None
    if torch.cuda.is_available():
        gpu_name = torch.cuda.get_device_name(0)

    return HealthResponse(
        status="ok",
        model="Qwen 2.5 14B + QLoRA (Patent Analysis)",
        model_loaded=model is not None,
        device=str(device),
        gpu_available=torch.cuda.is_available(),
        gpu_name=gpu_name
    )


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """헬스 체크 엔드포인트"""
    return await root()


@app.post("/generate", response_model=GenerateResponse)
async def generate(request: GenerateRequest):
    """
    Qwen 모델로 응답 생성

    멀티턴 대화를 지원하며, 특허 분석에 최적화되어 있습니다.
    """
    if model is None or tokenizer is None:
        raise HTTPException(
            status_code=503,
            detail="모델이 로드되지 않았습니다. 서버를 재시작해주세요."
        )

    try:
        # 1. 프롬프트 생성
        prompt = build_qwen_prompt(
            message=request.message,
            file_content=request.file_content,
            conversation_history=request.conversation_history
        )

        logger.info(f"📝 생성 요청: {request.message[:100]}...")
        logger.info(f"   - max_tokens: {request.max_tokens}")
        logger.info(f"   - temperature: {request.temperature}")
        logger.info(f"   - 대화 히스토리: {len(request.conversation_history) if request.conversation_history else 0}턴")

        # 2. 토큰화
        inputs = tokenizer(
            prompt,
            return_tensors="pt",
            truncation=True,
            max_length=4096  # Qwen 최대 길이
        ).to(device)

        # 3. 응답 생성
        with torch.no_grad():
            outputs = model.generate(
                **inputs,
                max_new_tokens=request.max_tokens,
                min_new_tokens=20,
                temperature=request.temperature,
                do_sample=True,
                top_p=0.9,
                top_k=50,
                repetition_penalty=1.3,
                pad_token_id=tokenizer.pad_token_id,
                eos_token_id=tokenizer.eos_token_id,
                no_repeat_ngram_size=3
            )

        # 4. 디코딩
        full_response = tokenizer.decode(outputs[0], skip_special_tokens=True)

        # 5. assistant 응답만 추출
        # Qwen ChatML 형식: <|im_start|>assistant\n응답<|im_end|>
        if "<|im_start|>assistant" in full_response:
            response_text = full_response.split("<|im_start|>assistant")[-1]
            response_text = response_text.replace("<|im_end|>", "").strip()
        else:
            # 폴백: 프롬프트 제거
            prompt_length = len(tokenizer.decode(inputs['input_ids'][0], skip_special_tokens=True))
            response_text = full_response[prompt_length:].strip()

        # 빈 응답 방지
        if not response_text:
            response_text = "죄송합니다. 응답을 생성하지 못했습니다. 다시 시도해주세요."

        logger.info(f"✅ 생성 완료 - 응답 길이: {len(response_text)} 글자")

        return GenerateResponse(
            response=response_text,
            model="Qwen 2.5 14B + QLoRA"
        )

    except torch.cuda.OutOfMemoryError:
        logger.error("❌ GPU 메모리 부족")
        raise HTTPException(
            status_code=507,
            detail="GPU 메모리가 부족합니다. max_tokens를 줄이거나 서버를 재시작해주세요."
        )
    except Exception as e:
        logger.error(f"❌ 응답 생성 오류: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"응답 생성 중 오류가 발생했습니다: {str(e)}"
        )


@app.get("/model-info")
async def model_info():
    """모델 정보 조회"""
    if model is None:
        raise HTTPException(status_code=503, detail="모델이 로드되지 않았습니다")

    info = {
        "model_name": "Qwen 2.5 14B Instruct + QLoRA",
        "checkpoint_path": MODEL_PATH,
        "device": str(device),
        "specialization": "특허 분석 (Patent Analysis)",
        "supported_languages": ["Korean", "English"],
    }

    if torch.cuda.is_available():
        info["gpu_name"] = torch.cuda.get_device_name(0)
        info["gpu_memory_total"] = f"{torch.cuda.get_device_properties(0).total_memory / 1024**3:.1f} GB"
        info["gpu_memory_allocated"] = f"{torch.cuda.memory_allocated(0) / 1024**3:.1f} GB"
        info["gpu_memory_reserved"] = f"{torch.cuda.memory_reserved(0) / 1024**3:.1f} GB"

    return info


if __name__ == "__main__":
    import uvicorn

    logger.info(f"🚀 서버 시작 준비")
    logger.info(f"   - 호스트: 0.0.0.0")
    logger.info(f"   - 포트: {PORT}")
    logger.info(f"   - 모델 경로: {MODEL_PATH}")
    logger.info(f"📖 API 문서: http://0.0.0.0:{PORT}/docs")

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=PORT,
        log_level="info",
        access_log=True
    )
