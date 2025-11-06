#!/bin/bash
# OpenSearch SSH 터널링 스크립트
# VPC 내부의 OpenSearch에 로컬에서 접근하기 위한 포트 포워딩

echo "======================================"
echo "  OpenSearch SSH 터널링 시작"
echo "======================================"
echo ""
echo "📡 OpenSearch 엔드포인트:"
echo "   vpc-my-patent-search-awh27u4ftg7cgcxwr347fma3cu.ap-northeast-2.es.amazonaws.com:443"
echo ""
echo "🔗 로컬 접근 주소:"
echo "   https://localhost:9200"
echo ""
echo "⚠️  주의사항:"
echo "   - 이 터미널 창은 열어두세요"
echo "   - 다른 터미널에서 개발 작업 진행"
echo "   - 종료: Ctrl+C"
echo ""
echo "======================================"
echo ""

# SSH 터널링 시작
# -N: 원격 명령 실행 안 함 (포트 포워딩만)
# -L: 로컬 포트 포워딩
# 9200:opensearch-endpoint:443 -> 로컬 9200 포트를 OpenSearch 443 포트로 연결
ssh -N -L 9200:vpc-my-patent-search-awh27u4ftg7cgcxwr347fma3cu.ap-northeast-2.es.amazonaws.com:443 ubuntu@3.37.175.204
