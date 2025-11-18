#!/bin/bash

# Runpod 모델 서버 시작 스크립트

# HF Transfer 비활성화 (hf_transfer 패키지가 없을 때)
unset HF_HUB_ENABLE_HF_TRANSFER

# 작업 디렉토리 이동
cd /workspace/runpod_model_server

# 서버 실행
echo "🚀 Starting Runpod Model Server..."
python main.py
