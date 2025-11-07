# RunPod LLaMA 모델 서버 배포 가이드

## 목차
1. [RunPod 계정 설정](#1-runpod-계정-설정)
2. [Pod 생성](#2-pod-생성)
3. [모델 서버 배포](#3-모델-서버-배포)
4. [Django 백엔드 연결](#4-django-백엔드-연결)
5. [테스트](#5-테스트)
6. [문제 해결](#6-문제-해결)

---

## 1. RunPod 계정 설정

### 1.1 RunPod 가입
1. [RunPod.io](https://www.runpod.io/) 접속
2. 계정 생성 및 로그인
3. 결제 수단 등록 (크레딧 카드 또는 암호화폐)

### 1.2 크레딧 충전
- 최소 $10 충전 권장
- RTX 4090: 약 $0.69/시간
- RTX A6000: 약 $0.79/시간

---

## 2. Pod 생성

### 2.1 GPU Pod 선택
1. RunPod 대시보드 → **GPU Pods** 클릭
2. **+ Deploy** 버튼 클릭

### 2.2 템플릿 선택
**방법 A: PyTorch 템플릿 사용 (권장)**
- Template: `RunPod PyTorch 2.1`
- CUDA: 12.1
- Python: 3.10

**방법 B: 커스텀 Docker 이미지**
```dockerfile
FROM runpod/pytorch:2.1.0-py3.10-cuda12.1.0-devel-ubuntu22.04
```

### 2.3 GPU 선택
**권장 GPU (LLaMA 3.2 3B 기준)**:
- RTX 4090 (24GB VRAM) - **최적**
- RTX A6000 (48GB VRAM) - 여유있음
- RTX 3090 (24GB VRAM) - 가능

**최소 요구사항**:
- VRAM: 8GB 이상
- 권장: 24GB 이상

### 2.4 설정
- **Volume**: 50GB 이상
- **Expose HTTP Ports**: `8000` 체크
- **Start Jupyter**: 선택 (디버깅용)

### 2.5 배포
- **Deploy On-Demand Pod** 또는 **Deploy Spot Pod** 선택
  - On-Demand: 안정적, 비용 높음
  - Spot: 저렴, 중단 가능

---

## 3. 모델 서버 배포

### 3.1 Pod 접속
Pod가 생성되면 **Connect** 버튼 클릭:

**옵션 1: SSH 접속**
```bash
ssh root@<POD_ID>-<PORT>.proxy.runpod.net -p <SSH_PORT> -i ~/.ssh/id_ed25519
```

**옵션 2: Web Terminal**
- RunPod 대시보드에서 **Web Terminal** 클릭

### 3.2 파일 업로드
**방법 A: git clone (권장)**
```bash
cd /workspace
git clone https://github.com/yourusername/SKN15-FINAL-3TEAM.git
cd SKN15-FINAL-3TEAM
```

**방법 B: 직접 복사**
```bash
# 로컬에서 실행
scp -P <SSH_PORT> -i ~/.ssh/id_ed25519 \
  runpod_llama_server.py \
  runpod_requirements.txt \
  root@<POD_ID>-<PORT>.proxy.runpod.net:/workspace/
```

### 3.3 환경 설정
```bash
cd /workspace

# 의존성 설치
pip install -r runpod_requirements.txt

# Hugging Face 로그인 (선택 - private 모델 사용 시)
pip install huggingface_hub
huggingface-cli login
# Token 입력: hf_xxxxxxxxxxxxx
```

### 3.4 환경 변수 설정 (선택)
```bash
# 모델 변경 시
export MODEL_NAME="meta-llama/Llama-3.2-3B-Instruct"

# 성능 조정
export MAX_TOKENS=512
export TEMPERATURE=0.7
export PORT=8000
```

### 3.5 서버 실행

**방법 A: 직접 실행 (테스트용)**
```bash
python runpod_llama_server.py
```

**방법 B: nohup으로 백그라운드 실행 (권장)**
```bash
nohup python runpod_llama_server.py > server.log 2>&1 &

# 로그 확인
tail -f server.log
```

**방법 C: tmux/screen 사용**
```bash
# tmux 설치 (없는 경우)
apt-get update && apt-get install -y tmux

# tmux 세션 시작
tmux new -s llama_server

# 서버 실행
python runpod_llama_server.py

# Detach: Ctrl+B → D
# Reattach: tmux attach -t llama_server
```

### 3.6 서버 확인
```bash
# 헬스체크
curl http://localhost:8000/health

# 모델 정보
curl http://localhost:8000/model-info
```

**예상 출력**:
```json
{
  "status": "ok",
  "model_loaded": true,
  "model_name": "meta-llama/Llama-3.2-3B-Instruct",
  "device": "cuda",
  "gpu_available": true,
  "gpu_name": "NVIDIA GeForce RTX 4090"
}
```

---

## 4. Django 백엔드 연결

### 4.1 RunPod 외부 URL 확인
RunPod 대시보드에서 **Connect** 버튼 클릭:
- HTTP Service: `https://<POD_ID>-8000.proxy.runpod.net`

### 4.2 Django settings.py 수정
```python
# patent_backend/config/settings.py

# 챗봇 서비스 설정
CHATBOT_SERVICE = 'llama'  # 또는 'custom'

# RunPod 모델 서버 URL
MODEL_SERVER_URL = 'https://<POD_ID>-8000.proxy.runpod.net'

# 예시:
# MODEL_SERVER_URL = 'https://abc123xyz-8000.proxy.runpod.net'
```

### 4.3 로컬 테스트 (선택)
SSH 터널링으로 로컬에서 테스트:
```bash
# 로컬에서 실행
ssh -L 8001:localhost:8000 \
  -p <SSH_PORT> \
  -i ~/.ssh/id_ed25519 \
  root@<POD_ID>-<PORT>.proxy.runpod.net

# Django settings.py
MODEL_SERVER_URL = 'http://localhost:8001'
```

### 4.4 Django 서버 재시작
```bash
# 로컬 개발 서버
python manage.py runserver

# EC2 프로덕션 서버
sudo systemctl restart gunicorn
```

---

## 5. 테스트

### 5.1 직접 API 테스트
```bash
# 간단한 테스트
curl -X POST https://<POD_ID>-8000.proxy.runpod.net/generate \
  -H "Content-Type: application/json" \
  -d '{
    "message": "특허 검색이 뭔가요?",
    "max_tokens": 256,
    "temperature": 0.7
  }'
```

### 5.2 Python 스크립트 테스트
```python
import requests

url = "https://<POD_ID>-8000.proxy.runpod.net/generate"

response = requests.post(url, json={
    "message": "특허 검색에 대해 설명해주세요.",
    "conversation_history": [],
    "max_tokens": 256,
    "temperature": 0.7
})

print(response.json())
```

### 5.3 Django 챗봇 테스트
1. 프론트엔드 로그인
2. 검색 페이지 → 챗봇 탭
3. 메시지 입력: "특허 검색이 뭔가요?"
4. 응답 확인

---

## 6. 문제 해결

### 6.1 모델 로딩 실패

**증상**: "모델이 로드되지 않았습니다" 오류

**해결**:
```bash
# 서버 로그 확인
tail -f server.log

# GPU 메모리 확인
nvidia-smi

# 프로세스 재시작
pkill -f runpod_llama_server.py
python runpod_llama_server.py
```

### 6.2 GPU 메모리 부족

**증상**: `torch.cuda.OutOfMemoryError`

**해결**:
```bash
# 더 작은 모델 사용
export MODEL_NAME="meta-llama/Llama-3.2-1B-Instruct"

# max_tokens 줄이기
export MAX_TOKENS=256

# 서버 재시작
```

### 6.3 연결 타임아웃

**증상**: Django에서 "모델 서버에 연결할 수 없습니다"

**해결 1: RunPod 포트 확인**
- RunPod 대시보드 → Pod 설정
- **Expose HTTP Ports**: 8000 포트 열려있는지 확인

**해결 2: 서버 상태 확인**
```bash
# Pod 내부에서
curl http://localhost:8000/health

# 외부에서
curl https://<POD_ID>-8000.proxy.runpod.net/health
```

**해결 3: 방화벽/CORS 확인**
- `runpod_llama_server.py`의 CORS 설정 확인
- Django settings의 `MODEL_SERVER_URL` 확인

### 6.4 느린 응답 속도

**원인**:
- CPU 모드로 실행 중
- 작은 GPU 사용
- max_tokens가 너무 큼

**해결**:
```bash
# GPU 사용 확인
nvidia-smi

# 서버 로그에서 디바이스 확인
tail -f server.log | grep "디바이스"
# 출력: "✅ 사용 디바이스: cuda" 여야 함

# max_tokens 줄이기
export MAX_TOKENS=256
```

### 6.5 Pod 중단 (Spot Pod)

**증상**: Spot Pod가 갑자기 종료됨

**해결**:
1. On-Demand Pod로 변경 (안정적, 비용 증가)
2. Auto-restart 스크립트 작성:

```bash
#!/bin/bash
# auto_restart.sh

while true; do
  if ! pgrep -f "runpod_llama_server.py" > /dev/null; then
    echo "서버 다운 감지, 재시작 중..."
    cd /workspace/SKN15-FINAL-3TEAM
    nohup python runpod_llama_server.py > server.log 2>&1 &
  fi
  sleep 60
done
```

---

## 7. 비용 최적화

### 7.1 Spot Pod 사용
- 비용: On-Demand 대비 50-70% 저렴
- 단점: 언제든 중단 가능
- 권장: 개발/테스트 환경

### 7.2 자동 중지 설정
```bash
# 30분 미사용 시 자동 중지 스크립트
# auto_stop.sh

IDLE_TIME=1800  # 30분 (초)
LOG_FILE="/workspace/server.log"

while true; do
  LAST_MODIFIED=$(stat -c %Y $LOG_FILE)
  CURRENT_TIME=$(date +%s)
  IDLE=$((CURRENT_TIME - LAST_MODIFIED))

  if [ $IDLE -gt $IDLE_TIME ]; then
    echo "30분 미사용, Pod 중지..."
    # RunPod API로 Pod 중지 (별도 구현 필요)
    break
  fi

  sleep 300  # 5분마다 체크
done
```

### 7.3 모델 최적화
- 더 작은 모델 사용: LLaMA 3.2 1B
- Quantization: 4-bit 또는 8-bit
- Batch processing: 여러 요청 동시 처리

---

## 8. 프로덕션 체크리스트

배포 전 확인사항:

- [ ] GPU Pod 생성 완료
- [ ] 모델 서버 정상 작동 (`/health` 응답 확인)
- [ ] Django `settings.py`에 `MODEL_SERVER_URL` 설정
- [ ] 프론트엔드에서 챗봇 테스트 완료
- [ ] 응답 시간 확인 (30초 이내)
- [ ] 에러 핸들링 테스트 (서버 중단 시)
- [ ] 로그 모니터링 설정
- [ ] 비용 알림 설정 (RunPod 대시보드)

---

## 9. 참고 자료

### RunPod 공식 문서
- [RunPod Docs](https://docs.runpod.io/)
- [RunPod Python SDK](https://github.com/runpod/runpod-python)

### LLaMA 모델
- [Hugging Face - LLaMA 3.2](https://huggingface.co/meta-llama/Llama-3.2-3B-Instruct)
- [LLaMA 3.2 Release Notes](https://ai.meta.com/blog/llama-3-2/)

### FastAPI
- [FastAPI 공식 문서](https://fastapi.tiangolo.com/)

---

## 10. 작성 정보

- **작성일**: 2025-01-07
- **프로젝트**: SKN15-FINAL-3TEAM / PatentAI
- **서버 파일**: `runpod_llama_server.py`
- **Django 연동**: `patent_backend/chatbot/services.py`
