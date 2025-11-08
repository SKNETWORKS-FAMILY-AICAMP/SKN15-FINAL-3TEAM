# RunPod LLaMA 모델 서버 완벽 설정 가이드

새로운 RunPod Pod을 생성하고 Django 백엔드와 연결하는 전체 과정

---

## 📋 목차

1. [RunPod Pod 생성](#1-runpod-pod-생성)
2. [Hugging Face 인증](#2-hugging-face-인증)
3. [모델 서버 설치](#3-모델-서버-설치)
4. [서버 실행 및 테스트](#4-서버-실행-및-테스트)
5. [Django 백엔드 연결](#5-django-백엔드-연결)
6. [문제 해결](#6-문제-해결)

---

## 1. RunPod Pod 생성

### 1-1. RunPod 웹사이트 접속
- https://www.runpod.io/ 로그인

### 1-2. Pod 생성
**Pods** → **+ Deploy** 클릭

**GPU 선택:**
- RTX 3090 (24GB) 또는 RTX 4090 (24GB) 권장
- 최소: GPU 8GB VRAM

**템플릿 선택:**
- `PyTorch 2.1` 또는 `PyTorch 2.2+` 선택
- CUDA 12.1 포함된 템플릿

**스토리지:**
- 최소 50GB 권장

**포트 설정:**
- HTTP Port: `8000` 추가 (중요!)

**Deploy** 클릭

### 1-3. Pod 연결 정보 확인
Pod이 시작되면 **Connect** 버튼 클릭

중요 정보:
- **SSH 명령어**: `ssh root@xxx.proxy.runpod.net -p xxxxx`
- **HTTP Service URL**: `https://xxxxxxx-8000.proxy.runpod.net`

> 💡 **HTTP Service URL을 메모장에 복사해두세요!** (나중에 Django 설정에 필요)

---

## 2. Hugging Face 인증

### 2-1. Hugging Face 토큰 생성
1. https://huggingface.co/settings/tokens 접속
2. **New token** 클릭
3. Token 이름: `runpod_llama`
4. Type: **Read** 선택
5. **Generate** 클릭
6. 토큰 복사 (예: `hf_xxxxxxxxxxxx`)

### 2-2. LLaMA 3.2 모델 접근 권한 요청
1. https://huggingface.co/meta-llama/Llama-3.2-3B-Instruct 접속
2. **Request access** 클릭
3. Meta 라이선스 동의
4. 승인 대기 (몇 분~몇 시간)

> ⏳ **승인 대기 중**: Phi-3 모델을 임시로 사용 가능 (인증 불필요)

---

## 3. 모델 서버 설치

### 3-1. RunPod SSH 접속

로컬 터미널에서:
```bash
ssh root@xxx.proxy.runpod.net -p xxxxx
```

### 3-2. 작업 디렉토리 생성
```bash
cd /workspace
mkdir -p llama_server
cd llama_server
```

### 3-3. 필요한 파일 다운로드

**방법 1: 자동 설치 스크립트 (권장)**
```bash
curl -O https://raw.githubusercontent.com/SKNETWORKS-FAMILY-AICAMP/SKN15-FINAL-3TEAM/main/runpod/runpod_setup.sh
bash runpod_setup.sh
```

**방법 2: 수동 설치**
```bash
# 서버 파일 다운로드
curl -O https://raw.githubusercontent.com/SKNETWORKS-FAMILY-AICAMP/SKN15-FINAL-3TEAM/main/runpod/runpod_llama_server.py

# requirements 다운로드
curl -O https://raw.githubusercontent.com/SKNETWORKS-FAMILY-AICAMP/SKN15-FINAL-3TEAM/main/runpod/runpod_requirements.txt

# 의존성 설치
pip install -r runpod_requirements.txt
```

### 3-4. Hugging Face 로그인

```bash
pip install huggingface_hub
huggingface-cli login
```

프롬프트가 나오면:
1. 토큰 입력 (2-1에서 생성한 토큰)
2. `Add token as git credential? (Y/n)` → `Y` 입력

---

## 4. 서버 실행 및 테스트

### 4-1. 환경 변수 설정

**LLaMA 3.2 사용 (승인 받은 경우):**
```bash
export MODEL_NAME="meta-llama/Llama-3.2-3B-Instruct"
export MAX_TOKENS=512
export TEMPERATURE=0.7
```

**Phi-3 사용 (승인 대기 중):**
```bash
export MODEL_NAME="microsoft/Phi-3-mini-4k-instruct"
export MAX_TOKENS=512
export TEMPERATURE=0.7
```

### 4-2. 서버 실행

**포그라운드 실행 (테스트용):**
```bash
python runpod_llama_server.py
```

다음 메시지가 나오면 성공:
```
✅ 모델 서버 초기화 완료!
   - 모델: meta-llama/Llama-3.2-3B-Instruct
   - 디바이스: cuda
   - 최대 토큰: 512
INFO:     Uvicorn running on http://0.0.0.0:8000
```

### 4-3. 서버 테스트 (새 터미널)

새 SSH 세션을 열어서:
```bash
curl http://localhost:8000/health
```

응답 예시:
```json
{
  "status": "ok",
  "model_loaded": true,
  "model_name": "meta-llama/Llama-3.2-3B-Instruct",
  "device": "cuda",
  "gpu_available": true,
  "gpu_name": "NVIDIA GeForce RTX 3090"
}
```

### 4-4. 백그라운드 실행 (프로덕션)

테스트 성공 후:
```bash
# 기존 프로세스 종료
pkill -f python

# 백그라운드 실행
nohup python runpod_llama_server.py > server.log 2>&1 &

# 로그 확인
tail -f server.log
```

서버 중지:
```bash
pkill -f runpod_llama_server
```

---

## 5. Django 백엔드 연결

### 5-1. RunPod URL 확인

RunPod 대시보드에서:
1. **Pods** → 실행 중인 Pod 선택
2. **Connect** → **HTTP Services** → **Port 8000**
3. URL 복사 (예: `https://hrb45hj7po3w8b-8000.proxy.runpod.net`)

### 5-2. EC2 서버 설정

EC2에 SSH 접속:
```bash
ssh ubuntu@3.37.175.204
```

**환경 변수 설정:**
```bash
cd patent_backend
nano .env
```

`.env` 파일에 추가:
```bash
# RunPod 모델 서버 설정
MODEL_SERVER_URL=https://hrb45hj7po3w8b-8000.proxy.runpod.net
CHATBOT_SERVICE=llama

# CORS 설정 (이미 있으면 수정)
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000,http://3-bengio-veraclaim.com,https://3-bengio-veraclaim.com,http://52.79.153.131
```

저장: `Ctrl+O` → `Enter` → `Ctrl+X`

### 5-3. 최신 코드 가져오기

```bash
cd patent_backend

# 로컬 변경사항 백업
git stash

# 최신 코드 가져오기
git pull origin main

# 변경사항 확인
git diff HEAD~1 config/settings.py
```

### 5-4. Django 서버 재시작

```bash
# 기존 서버 종료
pkill -f "python manage.py runserver"

# 서버 재시작
DJANGO_SETTINGS_MODULE=config.settings python3 manage.py runserver 0.0.0.0:8000
```

또는 gunicorn 사용 시:
```bash
sudo systemctl restart gunicorn
```

### 5-5. 연결 테스트

프론트엔드에서 챗봇 페이지 접속 후 메시지 전송:
- "안녕하세요"
- "게임 특허에 대해 알려주세요"

---

## 6. 문제 해결

### ❌ 문제 1: PyTorch 버전 에러
```
ERROR: Could not find a version that satisfies the requirement torch==2.1.2
```

**해결:**
```bash
# torch는 RunPod에 이미 설치되어 있음
# requirements.txt에서 torch 줄이 주석 처리되어 있는지 확인
grep torch runpod_requirements.txt

# 출력 예시:
# # torch>=2.1.0  # RunPod 템플릿에 이미 설치되어 있음
```

---

### ❌ 문제 2: LLaMA 모델 접근 권한 에러
```
OSError: You are trying to access a gated repo.
401 Client Error: Unauthorized
```

**원인:** Hugging Face 인증 또는 LLaMA 승인 미완료

**해결 방법 1: Hugging Face 재로그인**
```bash
huggingface-cli login
# 토큰 다시 입력
```

**해결 방법 2: Phi-3 임시 사용**
```bash
export MODEL_NAME="microsoft/Phi-3-mini-4k-instruct"
python runpod_llama_server.py
```

**해결 방법 3: 승인 상태 확인**
- https://huggingface.co/meta-llama/Llama-3.2-3B-Instruct 접속
- "Request access" 버튼이 보이면 아직 미승인
- "Files and versions" 탭이 보이면 승인 완료

---

### ❌ 문제 3: hf_transfer 에러
```
ValueError: Fast download using 'hf_transfer' is enabled but 'hf_transfer' package is not available
```

**해결:**
```bash
# 옵션 1: hf_transfer 설치
pip install hf_transfer

# 옵션 2: 환경 변수로 비활성화
export HF_HUB_ENABLE_HF_TRANSFER=0
python runpod_llama_server.py
```

---

### ❌ 문제 4: CORS 에러 (프론트엔드)
```
Access to fetch at 'http://52.79.153.131/api/chatbot/send/' from origin 'http://3-bengio-veraclaim.com' has been blocked by CORS policy
```

**해결:** EC2 설정 확인
```bash
# EC2에서
cd patent_backend
cat config/settings.py | grep CORS_ALLOWED_ORIGINS

# 다음 도메인들이 포함되어 있어야 함:
# http://3-bengio-veraclaim.com
# https://3-bengio-veraclaim.com
```

없으면 .env 파일 수정:
```bash
nano .env
# CORS_ALLOWED_ORIGINS에 도메인 추가
```

---

### ❌ 문제 5: 모델 서버 연결 실패
```
모델 서버에 연결할 수 없습니다. 서버가 실행 중인지 확인해주세요.
```

**체크리스트:**
1. **RunPod 서버 실행 중?**
   ```bash
   # RunPod에서
   ps aux | grep python
   ```

2. **RunPod URL이 정확한가?**
   - RunPod 대시보드에서 URL 재확인
   - `.env` 파일의 MODEL_SERVER_URL과 비교

3. **Django가 재시작되었는가?**
   ```bash
   # EC2에서
   pkill -f "python manage.py runserver"
   python3 manage.py runserver 0.0.0.0:8000
   ```

4. **RunPod에서 직접 테스트:**
   ```bash
   curl https://hrb45hj7po3w8b-8000.proxy.runpod.net/health
   ```

---

### ❌ 문제 6: 응답이 너무 짧거나 이상함

**증상:**
- "치킨이 ngon한 거예요!" 같은 이상한 응답
- 15~28 토큰만 생성

**원인:** 이전 버전의 서버 코드 사용 중

**해결:**
```bash
# RunPod에서 서버 중지
pkill -f python

# 최신 파일 다운로드
cd /workspace/llama_server
curl -H 'Cache-Control: no-cache' -o runpod_llama_server.py \
  "https://raw.githubusercontent.com/SKNETWORKS-FAMILY-AICAMP/SKN15-FINAL-3TEAM/main/runpod/runpod_llama_server.py?$(date +%s)"

# 서버 재시작
export MODEL_NAME="meta-llama/Llama-3.2-3B-Instruct"
python runpod_llama_server.py
```

**최신 버전 특징:**
- `min_new_tokens=50`: 최소 50토큰 생성
- `repetition_penalty=1.2`: 반복 감소
- RAG 기반 컨텍스트 추출
- 개선된 시스템 프롬프트

---

## 📊 서버 모니터링

### 로그 실시간 확인
```bash
# RunPod에서
tail -f server.log
```

로그 예시:
```
2025-11-07 17:09:06 - INFO - 📝 생성 요청: 안녕하세요...
2025-11-07 17:09:06 - INFO -    - max_tokens: 512
2025-11-07 17:09:06 - INFO -    - temperature: 0.7
2025-11-07 17:09:06 - INFO -    - 대화 히스토리: 9개
2025-11-07 17:09:07 - INFO - ✅ 생성 완료: 156 글자, 87 토큰
```

### GPU 사용량 확인
```bash
# RunPod에서
nvidia-smi
```

### 프로세스 확인
```bash
ps aux | grep python
```

---

## 🚀 완료!

축하합니다! 이제 다음 구성이 완료되었습니다:

```
프론트엔드 (Vercel)
    ↓
Django API (EC2)
    ↓
RunPod LLaMA 서버 (GPU)
```

**테스트:**
1. 프론트엔드에서 챗봇 접속
2. "안녕하세요" 입력
3. AI 응답 확인
4. "내가 뭐라고 인사했어?" 입력 (멀티턴 테스트)
5. 이전 내용을 기억하는 응답 확인

---

## 📚 참고 문서

- [전체 배포 가이드](./RUNPOD_DEPLOYMENT_GUIDE.md)
- [RunPod 공식 문서](https://docs.runpod.io/)
- [LLaMA 3.2 모델 페이지](https://huggingface.co/meta-llama/Llama-3.2-3B-Instruct)
- [Phi-3 모델 페이지](https://huggingface.co/microsoft/Phi-3-mini-4k-instruct)

---

## 💡 팁

### Pod 비용 절약
- 사용하지 않을 때 Pod **Stop** (비용 절감)
- 필요할 때만 **Start**
- 데이터는 유지됨

### 안정적인 운영
- 백그라운드 실행 사용 (`nohup`)
- 로그 정기 확인 (`tail -f server.log`)
- GPU 메모리 모니터링 (`nvidia-smi`)

### 성능 최적화
- `temperature`: 0.7 (기본값, 균형)
  - 낮추면 (0.3~0.5): 일관적, 보수적 응답
  - 높이면 (0.9~1.2): 창의적, 다양한 응답
- `max_tokens`: 512 (기본값)
  - 더 긴 응답 필요 시: 1024
- `min_new_tokens`: 50 (짧은 응답 방지)

---

**마지막 업데이트:** 2025-11-07
**커밋:** e29cc2e (멀티턴 성능 향상 버전)
