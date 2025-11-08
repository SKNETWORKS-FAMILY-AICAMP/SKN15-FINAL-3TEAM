"""
RunPod용 LLaMA 모델 서버
GPU 인스턴스에서 실행되며 FastAPI로 REST API 제공

RunPod 설정:
1. Template: PyTorch 2.1 + CUDA 12.1
2. GPU: RTX 4090 (24GB) 이상 권장
3. 포트: 8000 (HTTP)

환경 변수:
- MODEL_NAME: 사용할 모델 (기본: microsoft/Phi-3-mini-4k-instruct)
- MAX_TOKENS: 최대 생성 토큰 (기본: 512)
- TEMPERATURE: 생성 온도 (기본: 0.7)

지원 모델:
- microsoft/Phi-3-mini-4k-instruct (3.8B, 인증 불필요)
- meta-llama/Llama-3.2-3B-Instruct (인증 필요 - Hugging Face 로그인 & 승인)

실행:
python runpod_llama_server.py
"""

import os
import logging
from typing import List, Dict, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
import uvicorn

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# FastAPI 앱
app = FastAPI(
    title="RunPod LLaMA Model Server",
    description="특허 검색 및 분석을 위한 LLaMA 모델 서버",
    version="1.0.0"
)

# CORS 설정 (Django 백엔드에서 접근 허용)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 프로덕션에서는 특정 도메인만 허용
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 전역 변수
model = None
tokenizer = None
device = None

# 환경 변수로 설정 가능
MODEL_NAME = os.getenv("MODEL_NAME", "microsoft/Phi-3-mini-4k-instruct")
MAX_MODEL_TOKENS = int(os.getenv("MAX_TOKENS", "512"))
DEFAULT_TEMPERATURE = float(os.getenv("TEMPERATURE", "0.7"))


class GenerateRequest(BaseModel):
    """생성 요청 스키마"""
    message: str = Field(..., description="사용자 메시지", min_length=1)
    file_content: Optional[str] = Field(None, description="업로드된 파일 내용")
    conversation_history: Optional[List[Dict]] = Field(
        None,
        description="이전 대화 내역 [{'type': 'user'|'ai', 'content': '...'}]"
    )
    max_tokens: int = Field(
        MAX_MODEL_TOKENS,
        description="최대 생성 토큰 수",
        ge=1,
        le=2048
    )
    temperature: float = Field(
        DEFAULT_TEMPERATURE,
        description="생성 온도 (0.0~2.0)",
        ge=0.0,
        le=2.0
    )


class GenerateResponse(BaseModel):
    """생성 응답 스키마"""
    response: str = Field(..., description="AI 응답 텍스트")
    tokens_used: int = Field(..., description="사용된 토큰 수")
    model: str = Field(..., description="사용된 모델 이름")


class HealthResponse(BaseModel):
    """헬스체크 응답 스키마"""
    status: str
    model_loaded: bool
    model_name: str
    device: str
    gpu_available: bool
    gpu_name: Optional[str] = None


def load_model():
    """모델 초기화 (서버 시작 시 1회 실행)"""
    global model, tokenizer, device

    logger.info("=" * 60)
    logger.info("RunPod LLaMA 모델 서버 초기화 시작")
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

    # 모델 로딩
    logger.info(f"📥 모델 로딩 중: {MODEL_NAME}")

    try:
        # 토크나이저 로드
        logger.info("1/3: 토크나이저 로딩...")
        tokenizer = AutoTokenizer.from_pretrained(
            MODEL_NAME,
            trust_remote_code=True
        )

        # pad_token이 없으면 eos_token으로 설정
        if tokenizer.pad_token is None:
            tokenizer.pad_token = tokenizer.eos_token

        logger.info("✅ 토크나이저 로딩 완료")

        # 모델 로드
        logger.info("2/3: 모델 로딩... (시간이 걸릴 수 있습니다)")
        model = AutoModelForCausalLM.from_pretrained(
            MODEL_NAME,
            torch_dtype=torch.float16 if device == "cuda" else torch.float32,
            device_map="auto" if device == "cuda" else None,
            trust_remote_code=True,
            low_cpu_mem_usage=True
        )

        if device == "cpu":
            model = model.to(device)

        logger.info("✅ 모델 로딩 완료")

        # 모델 평가 모드
        logger.info("3/3: 모델 평가 모드 설정...")
        model.eval()

        logger.info("=" * 60)
        logger.info("✅ 모델 서버 초기화 완료!")
        logger.info(f"   - 모델: {MODEL_NAME}")
        logger.info(f"   - 디바이스: {device}")
        logger.info(f"   - 최대 토큰: {MAX_MODEL_TOKENS}")
        logger.info("=" * 60)

    except Exception as e:
        logger.error(f"❌ 모델 로딩 실패: {str(e)}")
        raise


def extract_conversation_context(conversation_history: Optional[List[Dict]]) -> str:
    """
    대화 히스토리에서 핵심 컨텍스트 추출 (RAG 개념 적용)

    멀티턴 성능 향상 전략:
    - 이전 대화에서 언급된 주요 엔티티(특허명, 키워드 등) 추출
    - 대화의 주제와 맥락 파악
    - 최근 3턴의 요약 생성
    """
    if not conversation_history or len(conversation_history) < 2:
        return ""

    # 최근 6개 메시지 분석 (3턴)
    recent_messages = conversation_history[-6:]

    # 키워드 추출 (간단한 방식)
    entities = []
    topics = []

    for msg in recent_messages:
        content = msg.get('content', '')

        # 특허/논문 관련 키워드
        if '특허' in content or '게임' in content or '골프' in content or '보드' in content:
            topics.append('특허')
        if '논문' in content or '연구' in content:
            topics.append('논문')

        # 구체적 엔티티 (예: "치킨", "게임 특허" 등)
        words = content.split()
        for word in words:
            if len(word) >= 2 and word not in ['이거', '저거', '그거', '뭐야', '어떻게']:
                entities.append(word)

    # 중복 제거 및 컨텍스트 구성
    unique_topics = list(set(topics))
    unique_entities = list(set(entities))[-5:]  # 최근 5개만

    context_parts = []
    if unique_topics:
        context_parts.append(f"대화 주제: {', '.join(unique_topics)}")
    if unique_entities:
        context_parts.append(f"언급된 내용: {', '.join(unique_entities)}")

    if context_parts:
        return "[대화 컨텍스트]\n" + "\n".join(context_parts) + "\n\n"
    return ""


def build_llama_prompt(
    message: str,
    file_content: Optional[str] = None,
    conversation_history: Optional[List[Dict]] = None
) -> str:
    """
    멀티턴 성능 향상을 위한 LLaMA 3.2 프롬프트 생성

    개선 사항:
    1. RAG 기반 컨텍스트 관리: 대화에서 핵심 정보 추출
    2. 명확한 지침: 역할과 응답 스타일 명시
    3. 대화 상태 관리: 이전 맥락 요약 제공

    Args:
        message: 현재 사용자 메시지
        file_content: 업로드된 파일 내용
        conversation_history: 이전 대화 내역

    Returns:
        LLaMA 형식의 프롬프트
    """
    prompt_parts = ["<|begin_of_text|>"]

    # 개선된 시스템 메시지 (명확한 지침)
    system_message = (
        "당신은 특허 및 논문 검색·분석 전문 AI 어시스턴트입니다.\n\n"
        "역할:\n"
        "- 특허 문서, 논문, 기술 분석에 대한 전문적이고 상세한 답변 제공\n"
        "- 이전 대화 맥락을 기억하고 연속성 있는 대화 진행\n"
        "- 사용자가 언급한 내용을 참조하여 답변\n\n"
        "응답 규칙:\n"
        "1. 이전 대화에서 언급된 내용은 반드시 기억하고 참조할 것\n"
        "2. 사용자 질문에 직접적으로 답변할 것\n"
        "3. 전문적이면서도 이해하기 쉽게 설명할 것\n"
        "4. 불확실한 경우 추측하지 말고 정직하게 답변할 것\n"
        "5. 한국어로 자연스럽게 응답할 것"
    )

    prompt_parts.append("<|start_header_id|>system<|end_header_id|>")
    prompt_parts.append(f"{system_message}<|eot_id|>")

    # 대화 컨텍스트 추출 및 요약
    conversation_context = extract_conversation_context(conversation_history)

    # 이전 대화 내역 추가 (최근 8개 = 4턴)
    # 컨텍스트가 있으면 더 적은 히스토리로도 충분
    max_history = 6 if conversation_context else 10

    if conversation_history:
        for hist in conversation_history[-max_history:]:
            role = "user" if hist['type'] == 'user' else "assistant"
            prompt_parts.append(f"<|start_header_id|>{role}<|end_header_id|>")
            prompt_parts.append(f"{hist['content']}<|eot_id|>")

    # 현재 사용자 메시지
    prompt_parts.append("<|start_header_id|>user<|end_header_id|>")

    # 컨텍스트 + 메시지 구성
    user_message_parts = []

    # 대화 컨텍스트 (RAG)
    if conversation_context:
        user_message_parts.append(conversation_context)

    # 파일 내용
    if file_content:
        user_message_parts.append(f"[첨부 파일]\n{file_content[:1000]}\n")

    # 실제 질문
    user_message_parts.append(f"[질문]\n{message}")

    prompt_parts.append("\n".join(user_message_parts) + "<|eot_id|>")

    # AI 응답 시작
    prompt_parts.append("<|start_header_id|>assistant<|end_header_id|>")

    return "\n".join(prompt_parts)


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
        model_loaded=model is not None,
        model_name=MODEL_NAME,
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
    멀티턴 대화를 지원하는 텍스트 생성

    특허 검색 및 분석 질문에 대해 LLaMA 모델을 사용하여 응답을 생성합니다.
    """
    if model is None or tokenizer is None:
        raise HTTPException(
            status_code=503,
            detail="모델이 로드되지 않았습니다. 서버를 재시작해주세요."
        )

    try:
        # 프롬프트 생성
        prompt = build_llama_prompt(
            message=request.message,
            file_content=request.file_content,
            conversation_history=request.conversation_history
        )

        logger.info(f"📝 생성 요청: {request.message[:100]}...")
        logger.info(f"   - max_tokens: {request.max_tokens}")
        logger.info(f"   - temperature: {request.temperature}")
        logger.info(f"   - 대화 히스토리: {len(request.conversation_history) if request.conversation_history else 0}개")

        # 토큰화
        inputs = tokenizer(
            prompt,
            return_tensors="pt",
            truncation=True,
            max_length=2048  # 입력 길이 제한
        ).to(device)

        # 응답 생성
        with torch.no_grad():
            outputs = model.generate(
                **inputs,
                max_new_tokens=request.max_tokens,
                min_new_tokens=50,  # 최소 50토큰 생성
                temperature=request.temperature,
                do_sample=True,
                top_p=0.9,
                top_k=50,
                repetition_penalty=1.2,  # 1.1 → 1.2 (반복 감소)
                pad_token_id=tokenizer.pad_token_id,
                eos_token_id=tokenizer.eos_token_id,
                no_repeat_ngram_size=3  # 3-gram 반복 방지
            )

        # 디코딩
        full_response = tokenizer.decode(outputs[0], skip_special_tokens=False)

        # 응답 부분만 추출
        # <|start_header_id|>assistant<|end_header_id|> 이후 마지막 부분만
        response_start = full_response.rfind("<|start_header_id|>assistant<|end_header_id|>")
        if response_start != -1:
            response_text = full_response[response_start + len("<|start_header_id|>assistant<|end_header_id|>"):]
            # <|eot_id|> 제거
            response_text = response_text.replace("<|eot_id|>", "").strip()
            response_text = response_text.replace("<|end_of_text|>", "").strip()
        else:
            response_text = full_response

        # 토큰 수 계산
        tokens_used = outputs[0].shape[0] - inputs['input_ids'].shape[1]

        logger.info(f"✅ 생성 완료: {len(response_text)} 글자, {tokens_used} 토큰")

        return GenerateResponse(
            response=response_text,
            tokens_used=tokens_used,
            model=MODEL_NAME
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
        "model_name": MODEL_NAME,
        "device": str(device),
        "max_tokens": MAX_MODEL_TOKENS,
        "default_temperature": DEFAULT_TEMPERATURE,
    }

    if torch.cuda.is_available():
        info["gpu_name"] = torch.cuda.get_device_name(0)
        info["gpu_memory_total"] = f"{torch.cuda.get_device_properties(0).total_memory / 1024**3:.1f} GB"
        info["gpu_memory_allocated"] = f"{torch.cuda.memory_allocated(0) / 1024**3:.1f} GB"
        info["gpu_memory_reserved"] = f"{torch.cuda.memory_reserved(0) / 1024**3:.1f} GB"

    return info


if __name__ == "__main__":
    # 서버 실행
    port = int(os.getenv("PORT", "8000"))
    host = os.getenv("HOST", "0.0.0.0")

    logger.info(f"🚀 서버 시작: http://{host}:{port}")
    logger.info(f"📖 API 문서: http://{host}:{port}/docs")

    uvicorn.run(
        app,
        host=host,
        port=port,
        log_level="info",
        access_log=True
    )
