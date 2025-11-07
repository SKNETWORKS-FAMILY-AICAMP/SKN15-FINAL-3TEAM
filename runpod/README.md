# RunPod LLaMA 모델 서버

RunPod GPU 인스턴스에서 실행되는 LLaMA 3.2 모델 서버입니다.

## 파일 구조

- `runpod_llama_server.py` - FastAPI 기반 LLaMA 모델 서버
- `runpod_requirements.txt` - 의존성 패키지
- `runpod_setup.sh` - 자동 설치 스크립트
- `RUNPOD_DEPLOYMENT_GUIDE.md` - 상세 배포 가이드

## 빠른 시작

### 1. RunPod Pod 생성
- GPU: RTX 4090 (24GB) 권장
- Template: PyTorch 2.1
- HTTP Port: 8000

### 2. 서버 설치 (RunPod Pod 내부)

**자동 설치:**
```bash
cd /workspace
curl -O https://raw.githubusercontent.com/SKNETWORKS-FAMILY-AICAMP/SKN15-FINAL-3TEAM/main/runpod/runpod_setup.sh
bash runpod_setup.sh
```

**수동 설치:**
```bash
cd /workspace
curl -O https://raw.githubusercontent.com/SKNETWORKS-FAMILY-AICAMP/SKN15-FINAL-3TEAM/main/runpod/runpod_llama_server.py
curl -O https://raw.githubusercontent.com/SKNETWORKS-FAMILY-AICAMP/SKN15-FINAL-3TEAM/main/runpod/runpod_requirements.txt

pip install -r runpod_requirements.txt
python runpod_llama_server.py
```

### 3. Django 백엔드 연결

`patent_backend/config/settings.py`:
```python
MODEL_SERVER_URL = 'https://<POD_ID>-8000.proxy.runpod.net'
```

## 상세 문서

전체 배포 가이드는 [RUNPOD_DEPLOYMENT_GUIDE.md](RUNPOD_DEPLOYMENT_GUIDE.md)를 참조하세요.

## 권장 사양

- **최소**: GPU 8GB VRAM
- **권장**: RTX 4090 (24GB)
- **용량**: 50GB 이상
