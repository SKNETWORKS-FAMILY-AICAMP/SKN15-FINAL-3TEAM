#!/bin/bash
# RunPod 서버 빠른 설치 스크립트

set -e  # 에러 발생 시 중단

echo "================================"
echo "RunPod LLaMA 서버 설치 시작"
echo "================================"

# 작업 디렉토리 생성
cd /workspace
mkdir -p llama_server
cd llama_server

# GitHub에서 필요한 파일만 다운로드
echo "1/4: 서버 파일 다운로드 중..."
REPO_URL="https://raw.githubusercontent.com/SKNETWORKS-FAMILY-AICAMP/SKN15-FINAL-3TEAM/main"

curl -sS -o runpod_llama_server.py "${REPO_URL}/runpod_llama_server.py"
curl -sS -o runpod_requirements.txt "${REPO_URL}/runpod_requirements.txt"

echo "✅ 파일 다운로드 완료"

# 의존성 설치
echo "2/4: 의존성 패키지 설치 중..."
pip install -q -r runpod_requirements.txt

echo "✅ 패키지 설치 완료"

# 환경 변수 설정 (선택)
echo "3/4: 환경 변수 설정..."
export MODEL_NAME="meta-llama/Llama-3.2-3B-Instruct"
export MAX_TOKENS=512
export TEMPERATURE=0.7
export PORT=8000

echo "✅ 환경 변수 설정 완료"

# GPU 확인
echo "4/4: GPU 확인..."
python -c "import torch; print(f'GPU 사용 가능: {torch.cuda.is_available()}'); print(f'GPU 이름: {torch.cuda.get_device_name(0) if torch.cuda.is_available() else \"없음\"}')"

echo ""
echo "================================"
echo "✅ 설치 완료!"
echo "================================"
echo ""
echo "서버 실행:"
echo "  python runpod_llama_server.py"
echo ""
echo "백그라운드 실행:"
echo "  nohup python runpod_llama_server.py > server.log 2>&1 &"
echo ""
echo "로그 확인:"
echo "  tail -f server.log"
echo ""
