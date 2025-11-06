#!/bin/bash
# OpenSearch SSH 터널링 스크립트

echo "🔌 SSH 터널링 시작..."
echo "OpenSearch 엔드포인트: vpc-my-patent-search-awh27u4ftg7cgcxwr347fma3cu.ap-northeast-2.es.amazonaws.com:443"
echo "로컬 포트: localhost:9200"
echo ""
echo "이 터미널은 열어두고, 다른 터미널에서 작업하세요."
echo "중지: Ctrl+C"
echo ""

ssh -N -L 9200:vpc-my-patent-search-awh27u4ftg7cgcxwr347fma3cu.ap-northeast-2.es.amazonaws.com:443 ubuntu@3.37.175.204
