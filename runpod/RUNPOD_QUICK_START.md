# RunPod 모델 서버 빠른 설정 가이드

최신 멀티턴 대화 시스템이 적용된 LLaMA 모델 서버 설정 방법

---

## 1. RunPod Pod 생성

### 1-1. Pod 설정
https://www.runpod.io/ 접속 → **Pods** → **+ Deploy**

- **GPU**: RTX 3090/4090 (24GB) 권장
- **템플릿**: PyTorch 2.1+ (CUDA 12.1 포함)
- **스토리지**: 50GB 이상
- **포트**: HTTP Port `8000` 추가 ✅

### 1-2. 연결 정보 저장
Pod 시작 후 **Connect** 클릭

```
SSH: ssh root@xxx.proxy.runpod.net -p xxxxx
HTTP URL: https://xxxxx-8000.proxy.runpod.net  ← Django 연결에 필요
```

---

## 2. 모델 서버 설치

### 2-1. SSH 접속
```bash
ssh root@xxx.proxy.runpod.net -p xxxxx
```

### 2-2. 자동 설치 (권장)
```bash
cd /workspace
curl -O https://raw.githubusercontent.com/SKNETWORKS-FAMILY-AICAMP/SKN15-FINAL-3TEAM/main/runpod/runpod_setup.sh
bash runpod_setup.sh
```

### 2-3. Hugging Face 로그인
```bash
huggingface-cli login
# 토큰 입력: https://huggingface.co/settings/tokens
```

**LLaMA 3.2 사용 시**: https://huggingface.co/meta-llama/Llama-3.2-3B-Instruct 에서 접근 권한 요청 필요
**승인 대기 중**: `microsoft/Phi-3-mini-4k-instruct` 사용 (인증 불필요)

---

## 3. 서버 실행

### 3-1. 환경 변수 설정
```bash
# LLaMA 3.2 (승인 완료 시)
export MODEL_NAME="meta-llama/Llama-3.2-3B-Instruct"

# 또는 Phi-3 (승인 대기 시)
export MODEL_NAME="microsoft/Phi-3-mini-4k-instruct"

export MAX_TOKENS=512
export TEMPERATURE=0.7
```

### 3-2. 백그라운드 실행
```bash
cd /workspace/llama_server
nohup python runpod_llama_server.py > server.log 2>&1 &

# 로그 확인
tail -f server.log
```

### 3-3. 서버 확인
```bash
curl http://localhost:8000/health
```

응답 예시:
```json
{
  "status": "ok",
  "model_loaded": true,
  "model_name": "meta-llama/Llama-3.2-3B-Instruct",
  "device": "cuda"
}
```

---

## 4. Django 백엔드 연결

### 4-1. EC2 설정
```bash
ssh ubuntu@3.37.175.204
cd patent_backend
nano .env
```

### 4-2. 환경 변수 추가
```bash
# RunPod URL (1-2에서 저장한 HTTP URL)
MODEL_SERVER_URL=https://xxxxx-8000.proxy.runpod.net
CHATBOT_SERVICE=llama

# CORS (필요시)
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://3-bengio-veraclaim.com,https://3-bengio-veraclaim.com
```

저장: `Ctrl+O` → `Enter` → `Ctrl+X`

### 4-3. Django 재시작
```bash
pkill -f "python manage.py runserver"
DJANGO_SETTINGS_MODULE=config.settings python3 manage.py runserver 0.0.0.0:8000
```

---

## 5. 테스트

프론트엔드 챗봇 페이지에서:

1. "안녕하세요" → AI 응답 확인
2. "게임 특허 검색해줘" → 도메인 특화 응답 확인
3. "내가 뭐 검색한다고 했지?" → **멀티턴 기억 확인** ✅

---

## 🛠️ 문제 해결

### 최신 코드로 업데이트
```bash
# RunPod에서
pkill -f python
cd /workspace/llama_server
curl -H 'Cache-Control: no-cache' -o runpod_llama_server.py \
  "https://raw.githubusercontent.com/SKNETWORKS-FAMILY-AICAMP/SKN15-FINAL-3TEAM/main/runpod/runpod_llama_server.py?$(date +%s)"

export MODEL_NAME="meta-llama/Llama-3.2-3B-Instruct"
nohup python runpod_llama_server.py > server.log 2>&1 &
```

### LLaMA 접근 권한 에러
```bash
# Phi-3로 전환 (임시)
export MODEL_NAME="microsoft/Phi-3-mini-4k-instruct"
python runpod_llama_server.py
```

### 서버 연결 실패
```bash
# RunPod 서버 확인
ps aux | grep python

# RunPod URL 재확인
# Django .env 파일의 MODEL_SERVER_URL 확인
```

---

## 📊 모니터링

### 로그 확인
```bash
tail -f server.log
```

### GPU 사용률
```bash
nvidia-smi
```

### 서버 중지
```bash
pkill -f runpod_llama_server
```

---

## 🚀 최신 기능 (v2.0)

✅ **명시적 메모리 관리**: 10턴 이내 대화 완벽 기억
✅ **프로액티브 참조**: 질문하지 않아도 이전 대화 자동 연결
✅ **특허 도메인 특화**: 특허/논문 검색 최적화된 Few-Shot 예시
✅ **패턴 기반 사실 추출**: "특허 검색", "논문 찾" 등 자동 인식

**커밋**: 4573c20 (특허 도메인 Few-Shot 최적화)
**업데이트**: 2025-11-10
