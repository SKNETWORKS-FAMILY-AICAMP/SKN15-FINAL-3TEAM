#!/bin/bash

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  특허 데이터 적재 (백그라운드 실행)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "시작 시간: $(date '+%Y-%m-%d %H:%M:%S')"
echo ""

# 백그라운드로 실행
nohup bash -c 'echo -e "y\nN" | python3 load_patents_remote.py' > load_output.log 2>&1 &

PID=$!

echo "✅ 백그라운드로 실행 시작"
echo "📊 프로세스 ID: $PID"
echo "📂 로그 파일: load_output.log"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "진행 상황 확인 방법:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "1. 로그 실시간 보기:"
echo "   tail -f load_output.log"
echo ""
echo "2. 프로세스 확인:"
echo "   ps aux | grep load_patents_remote"
echo ""
echo "3. 현재까지 적재된 건수 확인 (RDS):"
echo "   python3 -c \"import psycopg2; conn = psycopg2.connect(dbname='patent_db', user='postgres', password='3-bengio123', host='my-patent-db.c9iw88yiic4o.ap-northeast-2.rds.amazonaws.com'); cur = conn.cursor(); cur.execute('SELECT COUNT(*) FROM patents'); print(f'{cur.fetchone()[0]:,}건'); cur.close(); conn.close()\""
echo ""
echo "4. 중지 (필요시):"
echo "   kill $PID"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
