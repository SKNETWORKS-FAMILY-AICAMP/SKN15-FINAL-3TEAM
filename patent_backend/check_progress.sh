#!/bin/bash

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  데이터 적재 진행 상황"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# RDS 데이터 수 확인
echo "🔍 RDS 데이터 확인 중..."
CURRENT=$(python3 -c "
import psycopg2
try:
    conn = psycopg2.connect(
        dbname='patent_db',
        user='postgres',
        password='3-bengio123',
        host='my-patent-db.c9iw88yiic4o.ap-northeast-2.rds.amazonaws.com',
        connect_timeout=5
    )
    cur = conn.cursor()
    cur.execute('SELECT COUNT(*) FROM patents')
    count = cur.fetchone()[0]
    print(count)
    cur.close()
    conn.close()
except Exception as e:
    print('0')
")

TOTAL=510328
REMAINING=$((TOTAL - CURRENT))
PERCENT=$(python3 -c "print(f'{($CURRENT / $TOTAL * 100):.1f}')")

echo ""
echo "📊 전체 진행 상황:"
echo "   총 데이터:    510,328건"
echo "   적재 완료:    $(printf "%'d" $CURRENT)건 (${PERCENT}%)"
echo "   남은 데이터:  $(printf "%'d" $REMAINING)건"
echo ""

if [ $CURRENT -eq $TOTAL ]; then
    echo "✅ 모든 데이터 적재 완료!"
elif [ $CURRENT -gt 0 ]; then
    # 예상 남은 시간 계산 (대략 1000건당 2.5초)
    EST_SECONDS=$(python3 -c "print(int($REMAINING / 1000 * 2.5))")
    EST_MINUTES=$((EST_SECONDS / 60))
    echo "⏱  예상 남은 시간: 약 ${EST_MINUTES}분"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "💡 자동 새로고침하려면:"
echo "   watch -n 10 ./check_progress.sh"
echo ""
