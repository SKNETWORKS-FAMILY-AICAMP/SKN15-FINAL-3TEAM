# 커스텀 모델 연동 가이드

## 개요

챗봇 시스템에 자신만의 AI 모델을 쉽게 연동할 수 있습니다. 멀티턴 대화를 자동으로 지원하며, 모델 서버만 구현하면 됩니다.

## 사용 방법

### 1. 환경 변수 설정

`.env` 파일 또는 환경 변수에 다음을 추가:

```bash
# 커스텀 모델 사용 설정
CHATBOT_SERVICE=custom

# 모델 서버 URL 설정
CUSTOM_MODEL_SERVER_URL=http://localhost:8002
```

### 2. 모델 서버 구현

#### 필수 엔드포인트: `POST /generate`

**요청 형식 (JSON):**
```json
{
  "prompt": "이전 대화 내역:\n사용자: 안녕\nAI: 안녕하세요!\n\n현재 질문:\n사용자: 특허 검색해줘\n\nAI:",
  "message": "특허 검색해줘",
  "file_content": null,
  "conversation_history": [
    {"type": "user", "content": "안녕"},
    {"type": "ai", "content": "안녕하세요!"}
  ],
  "max_tokens": 512,
  "temperature": 0.7
}
```

**응답 형식 (JSON):**
```json
{
  "response": "특허 검색을 도와드리겠습니다. 어떤 키워드로 검색하시겠습니까?"
}
```

### 3. 모델 서버 예시 (FastAPI)

```python
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Optional
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

app = FastAPI()

# 모델 로드 (예: GPT-2 기반)
model_name = "your-custom-model"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForCausalLM.from_pretrained(model_name)

class GenerateRequest(BaseModel):
    prompt: str
    message: str
    file_content: Optional[str] = None
    conversation_history: Optional[List[Dict]] = None
    max_tokens: int = 512
    temperature: float = 0.7

class GenerateResponse(BaseModel):
    response: str

@app.post("/generate", response_model=GenerateResponse)
def generate(request: GenerateRequest):
    """멀티턴 대화를 고려한 응답 생성"""
    try:
        # 프롬프트에 이미 멀티턴 컨텍스트가 포함되어 있음
        inputs = tokenizer(request.prompt, return_tensors="pt")

        # 응답 생성
        outputs = model.generate(
            **inputs,
            max_new_tokens=request.max_tokens,
            temperature=request.temperature,
            do_sample=True,
            top_p=0.9
        )

        # 디코딩
        response_text = tokenizer.decode(outputs[0], skip_special_tokens=True)

        # 프롬프트 제거하고 응답만 추출
        response_text = response_text.replace(request.prompt, "").strip()

        return GenerateResponse(response=response_text)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)
```

### 4. 서버 실행

```bash
# 모델 서버 실행
python model_server.py

# Django 백엔드 재시작 (환경 변수 적용)
python manage.py runserver
```

## 멀티턴 대화 작동 원리

### 자동 처리되는 부분

1. **대화 히스토리 수집**: Django가 자동으로 DB에서 이전 대화 내역을 가져옴
2. **프롬프트 생성**: `CustomModelChatService`가 자동으로 멀티턴 컨텍스트를 포함한 프롬프트 생성
3. **최근 10개 대화만 사용**: 토큰 제한을 고려하여 최근 10턴만 포함

### 프롬프트 형식

```
이전 대화 내역:
사용자: 인공지능 특허 검색해줘
AI: AI 관련 특허를 검색하겠습니다. 총 45건의 특허가 검색되었습니다.
사용자: 그 중에서 이미지 인식 관련된 것만 보여줘

현재 질문:
사용자: 가장 최신 거부터 보여줘

AI:
```

### 사용자가 할 일

모델 서버는 단순히:
1. 받은 `prompt`를 모델에 입력
2. 생성된 텍스트를 반환

멀티턴 대화 관리는 Django 백엔드가 자동으로 처리합니다.

## 테스트

### 헬스 체크

```bash
curl http://localhost:8000/api/chatbot/health/
```

**응답:**
```json
{
  "status": "ok",
  "service": "CustomModelChatService",
  "message": "챗봇 서비스가 정상 작동 중입니다."
}
```

### 대화 테스트

```bash
# 첫 번째 메시지
curl -X POST http://localhost:8000/api/chatbot/send/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "안녕하세요"
  }'

# 두 번째 메시지 (멀티턴)
curl -X POST http://localhost:8000/api/chatbot/send/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "아까 내가 뭐라고 했지?",
    "conversation_id": "CONVERSATION_ID_FROM_FIRST_RESPONSE"
  }'
```

## 모델 전환

### KoSBERT로 전환
```bash
CHATBOT_SERVICE=kosbert
```

### LLaMA로 전환
```bash
CHATBOT_SERVICE=llama
MODEL_SERVER_URL=http://localhost:8001
```

### 커스텀 모델로 전환
```bash
CHATBOT_SERVICE=custom
CUSTOM_MODEL_SERVER_URL=http://localhost:8002
```

## 주의사항

1. **토큰 제한**: 최근 10개 대화만 포함하므로, 매우 긴 대화는 이전 내용이 잘릴 수 있음
2. **서버 가용성**: 모델 서버가 응답하지 않으면 에러 메시지 반환
3. **타임아웃**: 60초 이상 응답이 없으면 타임아웃 처리

## 추가 커스터마이징

### 대화 히스토리 개수 조정

[chatbot/services.py:276](chatbot/services.py#L276)에서 수정:

```python
for hist in conversation_history[-10:]:  # 10을 원하는 숫자로 변경
```

### 프롬프트 형식 변경

`_build_prompt_with_history` 메서드를 수정하여 원하는 형식으로 커스터마이징 가능
