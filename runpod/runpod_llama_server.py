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
import re
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


def clean_non_korean_text(text: str) -> str:
    """
    한국어가 아닌 문자를 제거하고 한국어만 남김

    허용:
    - 한글 (가-힣, ㄱ-ㅎ, ㅏ-ㅣ)
    - 영문 (A-Z, a-z) - 기술 용어용
    - 숫자 (0-9)
    - 기본 문장부호 (.,!?()[]{}'" 등)
    - 공백

    제거:
    - 베트남어, 중국어, 일본어, 태국어 등 다른 언어의 문자
    """
    # 한글, 영문, 숫자, 기본 문장부호만 허용
    allowed_pattern = r'[가-힣ㄱ-ㅎㅏ-ㅣa-zA-Z0-9\s.,!?()[\]{}\'"·※→←↑↓√×÷±≤≥≠∞∑∫-]'

    # 문자 단위로 필터링
    cleaned = ''.join(char for char in text if re.match(allowed_pattern, char))

    # 연속된 공백 정리
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()

    return cleaned


def extract_explicit_memory(conversation_history: Optional[List[Dict]]) -> Dict[str, any]:
    """
    명시적 메모리 추출: 중요 정보를 Key-Value 형태로 저장

    멀티턴 성능을 극대화하기 위한 확실한 기억 관리
    """
    memory = {
        'facts': [],  # 사용자가 말한 사실들
        'preferences': [],  # 사용자의 선호/계획
        'topics': set(),  # 대화 주제
        'last_mentioned': {}  # 각 사실이 몇 턴 전에 언급되었는지
    }

    if not conversation_history:
        return memory

    total_turns = len(conversation_history)

    for idx, msg in enumerate(conversation_history):
        if msg.get('type') != 'user':
            continue

        content = msg.get('content', '')
        turns_ago = total_turns - idx

        # 패턴 기반 사실 추출 (특허/논문 도메인 특화)
        # "나는 X다" / "나 X 할거야" / "X 검색하고 싶어"
        patterns = [
            # 특허 관련 패턴
            ('특허 검색', 'patent_search'),
            ('특허 찾', 'patent_search'),
            ('특허 분석', 'patent_analysis'),
            ('특허를', 'patent_interest'),
            # 논문 관련 패턴
            ('논문 검색', 'paper_search'),
            ('논문 찾', 'paper_search'),
            ('논문을', 'paper_interest'),
            ('연구 찾', 'research_interest'),
            # 일반 선호도
            ('좋아해', 'preference'),
            ('싫어해', 'dislike'),
            ('관심있', 'interest'),
        ]

        for pattern, fact_type in patterns:
            if pattern in content:
                # 핵심 단어 추출 (패턴 앞의 명사)
                words = content.split()
                for i, word in enumerate(words):
                    if pattern in word and i > 0:
                        key_info = ' '.join(words[max(0, i-3):i])
                        memory['facts'].append({
                            'type': fact_type,
                            'content': key_info + ' ' + pattern,
                            'turns_ago': turns_ago
                        })
                        memory['last_mentioned'][fact_type] = turns_ago

        # 주제 추출
        if '특허' in content or '게임' in content:
            memory['topics'].add('특허')
        if '논문' in content or '연구' in content:
            memory['topics'].add('논문')

    return memory


def build_structured_summary(memory: Dict, conversation_history: Optional[List[Dict]]) -> str:
    """
    구조화된 대화 요약 생성

    명확한 형식으로 중요 정보를 정리하여 모델이 확실하게 이해하도록 함
    """
    if not memory['facts'] and not memory['topics']:
        return ""

    summary_parts = ["[대화 메모리]"]

    # 주제
    if memory['topics']:
        summary_parts.append(f"주제: {', '.join(memory['topics'])}")

    # 사용자가 언급한 사실들 (최근 5개)
    if memory['facts']:
        summary_parts.append("\n핵심 사실:")
        for fact in memory['facts'][-5:]:
            summary_parts.append(
                f"  • {fact['content']} ({fact['turns_ago']}턴 전)"
            )

    # 최근 관련 대화 (컨텍스트용)
    if conversation_history and len(conversation_history) >= 2:
        recent = conversation_history[-2:]
        summary_parts.append("\n최근 대화:")
        for msg in recent:
            role = "사용자" if msg['type'] == 'user' else "AI"
            content = msg['content'][:50] + "..." if len(msg['content']) > 50 else msg['content']
            summary_parts.append(f"  {role}: {content}")

    return "\n".join(summary_parts) + "\n\n"


def build_llama_prompt(
    message: str,
    file_content: Optional[str] = None,
    conversation_history: Optional[List[Dict]] = None
) -> str:
    """
    10턴 내 확실한 기억을 위한 개선된 프롬프트 생성

    전략:
    1. 명시적 메모리: 중요 사실을 Key-Value로 추출
    2. 구조화된 요약: 명확한 형식으로 정보 정리
    3. Few-Shot 예시: 올바른 기억 방법 시범

    Args:
        message: 현재 사용자 메시지
        file_content: 업로드된 파일 내용
        conversation_history: 이전 대화 내역

    Returns:
        LLaMA 형식의 프롬프트
    """
    prompt_parts = ["<|begin_of_text|>"]

    # Few-Shot 예시가 포함된 시스템 메시지 (특허 도메인 특화 + 프로액티브 기능)
    system_message = (
        "당신은 특허 및 논문 검색·분석 전문 AI 어시스턴트입니다.\n\n"
        "**IMPORTANT: You MUST respond ONLY in Korean language. Never use English, Vietnamese, Chinese, or any other language.**\n"
        "**중요: 반드시 한국어로만 답변하세요. 영어, 베트남어, 중국어 등 다른 언어를 절대 사용하지 마세요.**\n\n"
        "**중요: 대화 내용을 정확히 기억하는 방법**\n\n"
        "예시 1 - 특허 검색 기억:\n"
        "사용자: 게임 특허 검색하고 싶어\n"
        "AI: 게임 관련 특허를 검색해드리겠습니다. 어떤 종류의 게임인가요?\n"
        "사용자: 내가 무슨 특허 찾는다고 했지?\n"
        "✓ 정답: '게임 특허를 검색하신다고 하셨습니다 (2턴 전)'\n"
        "✗ 오답: '기억이 안 나요' / '뭔가 특허를...'\n\n"
        "예시 2 - 논문 주제 기억:\n"
        "사용자: 딥러닝 논문 찾아보는 중이야\n"
        "AI: 딥러닝 분야 논문을 찾고 계시는군요. 어떤 세부 주제에 관심이 있으신가요?\n"
        "사용자: 내가 찾는 논문 주제가 뭐였지?\n"
        "✓ 정답: '딥러닝 논문을 찾고 계셨습니다 (2턴 전)'\n\n"
        "예시 3 - 프로액티브 특허 분석:\n"
        "사용자: 골프 게임 특허 검색 중이야\n"
        "AI: 골프 게임 특허를 찾고 계시는군요! 검색해드리겠습니다.\n"
        "사용자: 좋은 검색 방법 있어?\n"
        "✓ 정답: '골프 게임 특허는 IPC 분류 A63B나 G06T를 활용하면 좋습니다. 키워드로는 \"golf simulation\", \"swing analysis\" 등을 추천드립니다.'\n"
        "✗ 오답: '일반적으로 키워드 검색이 좋습니다' (골프 게임 맥락 무시)\n\n"
        "예시 4 - 프로액티브 유사 특허:\n"
        "사용자: 보드게임 특허 분석해줘\n"
        "AI: 보드게임 특허 분석해드리겠습니다.\n"
        "사용자: 유사한 특허도 있어?\n"
        "✓ 정답: '네! 보드게임과 유사한 특허로는 카드게임, 퍼즐게임 관련 특허들이 있습니다. 검색해드릴까요?'\n"
        "✗ 오답: '유사 특허가 있을 수 있습니다' (보드게임 맥락 무시)\n\n"
        "예시 5 - 프로액티브 논문 연계:\n"
        "사용자: 자연어처리 논문 검색해줘\n"
        "AI: 자연어처리 논문을 찾아드리겠습니다.\n"
        "사용자: 최신 연구 동향도 알려줘\n"
        "✓ 정답: '자연어처리 분야에서는 최근 LLM(대규모 언어모델), RAG, 프롬프트 엔지니어링 연구가 활발합니다. 관련 논문을 검색해드릴까요?'\n"
        "✗ 오답: 'AI 연구가 활발합니다' (자연어처리 맥락 무시)\n\n"
        "**응답 규칙:**\n"
        "1. [대화 메모리] 섹션의 정보를 반드시 참조하세요\n"
        "2. 특허/논문 관련 이전 언급을 자연스럽게 연결하세요 (물어보지 않아도!)\n"
        "3. 몇 턴 전에 언급되었는지 알려주면 더 좋습니다\n"
        "4. 정확한 정보만 답변하고, 불확실하면 솔직히 말하세요\n"
        "5. 한국어로 자연스럽게 응답하세요"
    )

    prompt_parts.append("<|start_header_id|>system<|end_header_id|>")
    prompt_parts.append(f"{system_message}<|eot_id|>")

    # 명시적 메모리 추출 + 구조화된 요약 생성
    memory = extract_explicit_memory(conversation_history)
    structured_summary = build_structured_summary(memory, conversation_history)

    # 대화 히스토리 추가 (메모리가 있으면 최소화)
    max_history = 4 if structured_summary else 8

    if conversation_history:
        for hist in conversation_history[-max_history:]:
            role = "user" if hist['type'] == 'user' else "assistant"
            prompt_parts.append(f"<|start_header_id|>{role}<|end_header_id|>")
            prompt_parts.append(f"{hist['content']}<|eot_id|>")

    # 현재 사용자 메시지
    prompt_parts.append("<|start_header_id|>user<|end_header_id|>")

    # 메시지 구성
    user_message_parts = []

    # 구조화된 메모리 (가장 중요!)
    if structured_summary:
        user_message_parts.append(structured_summary)

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

        # 응답 생성 (한국어 강제 유지)
        with torch.no_grad():
            outputs = model.generate(
                **inputs,
                max_new_tokens=request.max_tokens,
                min_new_tokens=20,  # 최소 20토큰 (50→20으로 감소)
                temperature=request.temperature,
                do_sample=True,
                top_p=0.9,
                top_k=50,
                repetition_penalty=1.5,  # 1.2→1.5 (반복 억제 강화)
                pad_token_id=tokenizer.pad_token_id,
                eos_token_id=tokenizer.eos_token_id,
                no_repeat_ngram_size=3,
                use_cache=False,
                # 한국어 강제 설정
                forced_bos_token_id=None,  # 시작 토큰 자유롭게
                exponential_decay_length_penalty=(1, 1.05)  # 짧은 답변 선호
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

        # 한국어가 아닌 언어 제거 (베트남어, 중국어 등)
        original_length = len(response_text)
        response_text = clean_non_korean_text(response_text)
        if len(response_text) < original_length:
            logger.warning(f"⚠️ 비한국어 문자 제거: {original_length} → {len(response_text)} 글자")

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
