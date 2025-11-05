#!/bin/bash

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  특허 데이터 적재 자동 실행"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "현재 시간: $(date '+%Y-%m-%d %H:%M:%S')"
echo ""
echo "📊 예상 소요 시간: 15-25분"
echo "📂 로그 파일: load_output.log"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# 기존 데이터 유지 (N 자동 입력)
# 실행 확인 (y 자동 입력)
echo -e "y\nN" | python3 load_patents_remote.py 2>&1 | tee load_output.log

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "완료 시간: $(date '+%Y-%m-%d %H:%M:%S')"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
