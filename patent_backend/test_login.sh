#!/bin/bash
# 로그인 API 테스트 스크립트

echo "=== Django 서버 재시작 ==="
pkill -f "python manage.py runserver"
sleep 1

cd /home/juhyeong/workspace/final_project/backend
source ~/miniconda3/etc/profile.d/conda.sh
conda activate patent_backend

echo "서버 시작 중..."
python manage.py runserver &
SERVER_PID=$!

sleep 3

echo ""
echo "=== API 테스트 ==="
echo ""
echo "1. Health Check:"
curl -s http://localhost:8000/api/accounts/health/
echo ""
echo ""

echo "2. Companies:"
curl -s http://localhost:8000/api/accounts/companies/ | python3 -m json.tool 2>/dev/null | head -20
echo ""
echo ""

echo "3. Login Test (잘못된 계정):"
curl -s -X POST http://localhost:8000/api/accounts/login/ \
  -H "Content-Type: application/json" \
  -d '{"username":"test","password":"test"}' | python3 -m json.tool 2>/dev/null
echo ""
echo ""

echo "4. 사용자 목록 확인:"
echo "현재 등록된 사용자:"
python manage.py shell <<EOF
from accounts.models import User
for u in User.objects.all():
    print(f"  - {u.username} (role: {u.role}, status: {u.status})")
EOF

echo ""
echo "=== 테스트 완료 ==="
echo ""
echo "서버가 백그라운드에서 실행 중입니다 (PID: $SERVER_PID)"
echo "중지하려면: kill $SERVER_PID"
