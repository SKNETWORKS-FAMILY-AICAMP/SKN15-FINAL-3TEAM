#!/bin/bash
# ======================================================
# 새로운 데이터베이스 구조로 마이그레이션 스크립트
# ======================================================
# 사용법: bash backend/migrate_to_new_structure.sh
# ======================================================

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}======================================"
echo "🔄 새로운 DB 구조로 마이그레이션"
echo "======================================"
echo -e "${NC}"

# ======================================================
# Step 1: PostgreSQL에 새 테이블 생성
# ======================================================
echo -e "${YELLOW}📌 Step 1: PostgreSQL에 새 테이블 생성${NC}"
echo "다음 명령어를 실행합니다:"
echo "  sudo -u postgres psql -d patentdb -f backend/create_new_tables_patentdb.sql"
echo ""

sudo -u postgres psql -d patentdb -f backend/create_new_tables_patentdb.sql

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ PostgreSQL 테이블 생성 완료${NC}"
else
    echo -e "${RED}❌ PostgreSQL 테이블 생성 실패${NC}"
    echo ""
    echo "다음 명령어를 직접 실행해보세요:"
    echo "  sudo -u postgres psql -d patentdb"
    echo "  \\i /home/juhyeong/workspace/final_project/backend/create_new_tables_patentdb.sql"
    echo "  \\q"
    exit 1
fi

echo ""

# ======================================================
# Step 2: 테이블 생성 확인
# ======================================================
echo -e "${YELLOW}📌 Step 2: 테이블 생성 확인${NC}"
sudo -u postgres psql -d patentdb -c "\dt" | grep -E "company|department|user |admin_request|password_reset"

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ 새 테이블 확인됨${NC}"
else
    echo -e "${RED}❌ 테이블이 보이지 않습니다${NC}"
fi

echo ""

# ======================================================
# Step 3: Conda 환경 활성화
# ======================================================
echo -e "${YELLOW}📌 Step 3: Conda 환경 활성화${NC}"
source ~/miniconda3/etc/profile.d/conda.sh
conda activate patent_backend

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Conda 환경 활성화 완료${NC}"
else
    echo -e "${RED}❌ Conda 환경 활성화 실패${NC}"
    exit 1
fi

echo ""

# ======================================================
# Step 4: Django 마이그레이션
# ======================================================
echo -e "${YELLOW}📌 Step 4: Django 마이그레이션${NC}"

cd backend

# 기존 마이그레이션 파일 삭제 (이미 삭제됨)
echo "마이그레이션 파일 상태 확인..."
ls -la accounts/migrations/

# 새 마이그레이션 생성
echo ""
echo "새 마이그레이션 생성 중..."
python manage.py makemigrations accounts

if [ $? -ne 0 ]; then
    echo -e "${RED}❌ 마이그레이션 생성 실패${NC}"
    exit 1
fi

# 마이그레이션 실행 (fake-initial: 테이블이 이미 있으므로)
echo ""
echo "마이그레이션 실행 중..."
python manage.py migrate accounts --fake-initial

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Django 마이그레이션 완료${NC}"
else
    echo -e "${RED}❌ 마이그레이션 실패${NC}"
    exit 1
fi

# 나머지 앱 마이그레이션
echo ""
echo "나머지 앱 마이그레이션..."
python manage.py migrate

echo ""

# ======================================================
# Step 5: 데이터 검증
# ======================================================
echo -e "${YELLOW}📌 Step 5: 데이터 검증${NC}"
echo "회사 및 부서 데이터 확인..."

python manage.py shell <<EOF
from accounts.models import Company, Department, User

print("\n=== 회사 목록 ===")
companies = Company.objects.all()
for c in companies:
    print(f"  {c.company_id}: {c.name}")

print("\n=== 부서 목록 ===")
departments = Department.objects.all()
for d in departments:
    print(f"  {d.department_id}: {d.company.name} - {d.name}")

print("\n=== 사용자 목록 ===")
users = User.objects.all()
if users.exists():
    for u in users:
        print(f"  {u.username} - {u.role} - {u.status}")
else:
    print("  (사용자 없음)")

print("\n✅ 데이터 검증 완료")
EOF

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ 데이터 검증 완료${NC}"
else
    echo -e "${RED}❌ 데이터 검증 실패${NC}"
fi

echo ""

# ======================================================
# 완료!
# ======================================================
echo -e "${GREEN}======================================"
echo "🎉 마이그레이션 완료!"
echo "======================================"
echo ""
echo "다음 단계:"
echo "  1. 슈퍼 관리자 생성:"
echo "     cd backend"
echo "     python manage.py createsuperuser"
echo ""
echo "  2. Django 서버 실행:"
echo "     python manage.py runserver"
echo ""
echo "  3. API 테스트:"
echo "     curl http://localhost:8000/api/accounts/companies/"
echo ""
echo -e "자세한 내용: ${BLUE}backend/MIGRATION_GUIDE.md${NC}"
echo -e "${NC}"
