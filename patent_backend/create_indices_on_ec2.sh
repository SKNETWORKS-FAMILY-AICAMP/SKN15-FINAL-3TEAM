#!/bin/bash
# OpenSearch 인덱스 생성 스크립트 (EC2에서 실행)

echo "=========================================="
echo " OpenSearch 인덱스 생성"
echo "=========================================="
echo ""

# 환경 변수 설정
export OPENSEARCH_HOST='vpc-my-patent-search-awh27u4ftg7cgcxwr347fma3cu.ap-northeast-2.es.amazonaws.com'
export OPENSEARCH_PORT=443
export OPENSEARCH_USE_SSL=True
export OPENSEARCH_VERIFY_CERTS=True
export OPENSEARCH_USER='opensearch_admin'
export OPENSEARCH_PASSWORD='3-Bengio123'

echo "OpenSearch 연결 정보:"
echo "  Host: $OPENSEARCH_HOST"
echo "  Port: $OPENSEARCH_PORT"
echo "  SSL: $OPENSEARCH_USE_SSL"
echo ""

# Python 스크립트 실행
echo "인덱스 생성 스크립트 실행 중..."
python3 patents/opensearch_client.py

echo ""
echo "완료!"
