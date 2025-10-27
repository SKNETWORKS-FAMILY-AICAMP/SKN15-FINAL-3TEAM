#!/bin/bash
# ======================================================
# 완전한 데이터베이스 마이그레이션 스크립트
# - 이전 테이블 삭제
# - 새 테이블 생성 (final_play 소유)
# - Django 마이그레이션
# ======================================================
# 사용법: bash backend/full_migration.sh
# ======================================================

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo -e "${BLUE}======================================"
echo "🔄 완전한 DB 마이그레이션"
echo "======================================"
echo -e "${NC}"

# ======================================================
# 경고 메시지
# ======================================================
echo -e "${RED}⚠️  경고: 이 스크립트는 다음 작업을 수행합니다:${NC}"
echo "   1. 이전 역할 기반 테이블 삭제 (users, roles, permissions 등)"
echo "   2. 로그 테이블 삭제 (usersessions, chatbotlogs 등)"
echo "   3. 새로운 테이블 생성 (company, department, user 등)"
echo ""
echo -e "${YELLOW}❗ 기존 데이터가 모두 삭제됩니다!${NC}"
echo ""
read -p "계속 진행하시겠습니까? (yes/no): " CONFIRM

if [ "$CONFIRM" != "yes" ]; then
    echo "취소되었습니다."
    exit 0
fi

echo ""

# ======================================================
# Step 1: 이전 테이블 삭제
# ======================================================
echo -e "${YELLOW}📌 Step 1: 이전 테이블 삭제${NC}"
echo "다음 명령어를 실행합니다:"
echo "  sudo -u postgres psql -d patentdb -f backend/drop_old_tables.sql"
echo ""

sudo -u postgres psql -d patentdb -f backend/drop_old_tables.sql

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ 이전 테이블 삭제 완료${NC}"
else
    echo -e "${RED}❌ 이전 테이블 삭제 실패${NC}"
    exit 1
fi

echo ""
sleep 2

# ======================================================
# Step 2: 새 테이블 생성 (final_play 소유)
# ======================================================
echo -e "${YELLOW}📌 Step 2: 새 테이블 생성 (final_play 소유)${NC}"
echo "다음 명령어를 실행합니다:"
echo "  sudo -u postgres psql -d patentdb -f backend/create_new_tables_final_play.sql"
echo ""

sudo -u postgres psql -d patentdb -f backend/create_new_tables_final_play.sql

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ 새 테이블 생성 완료${NC}"
else
    echo -e "${RED}❌ 새 테이블 생성 실패${NC}"
    exit 1
fi

echo ""
sleep 2

# ======================================================
# Step 3: 테이블 및 소유자 확인
# ======================================================
echo -e "${YELLOW}📌 Step 3: 테이블 및 소유자 확인${NC}"
sudo -u postgres psql -d patentdb -c "
SELECT tablename, tableowner
FROM pg_tables
WHERE schemaname = 'public'
  AND tableowner = 'final_play'
ORDER BY tablename;
"

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ 테이블 확인 완료 (Owner: final_play)${NC}"
else
    echo -e "${RED}❌ 테이블 확인 실패${NC}"
fi

echo ""
sleep 2

# ======================================================
# Step 4: Conda 환경 활성화
# ======================================================
echo -e "${YELLOW}📌 Step 4: Conda 환경 활성화${NC}"
source ~/miniconda3/etc/profile.d/conda.sh
conda activate patent_backend

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Conda 환경 활성화 완료 (patent_backend)${NC}"
else
    echo -e "${RED}❌ Conda 환경 활성화 실패${NC}"
    exit 1
fi

echo ""

# ======================================================
# Step 5: Django 마이그레이션 파일 정리
# ======================================================
echo -e "${YELLOW}📌 Step 5: Django 마이그레이션 파일 정리${NC}"

cd backend

# 기존 마이그레이션 파일 삭제 (00*.py)
if ls accounts/migrations/00*.py 1> /dev/null 2>&1; then
    echo "기존 마이그레이션 파일 삭제 중..."
    rm -f accounts/migrations/00*.py
    echo -e "${GREEN}✅ 기존 마이그레이션 파일 삭제 완료${NC}"
else
    echo "삭제할 마이그레이션 파일이 없습니다."
fi

# __pycache__ 정리
if [ -d "accounts/migrations/__pycache__" ]; then
    rm -rf accounts/migrations/__pycache__
    echo -e "${GREEN}✅ __pycache__ 정리 완료${NC}"
fi

echo ""

# ======================================================
# Step 6: Django 데이터베이스 연결 테스트
# ======================================================
echo -e "${YELLOW}📌 Step 6: Django 데이터베이스 연결 테스트${NC}"
python manage.py check --database default

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ 데이터베이스 연결 성공${NC}"
else
    echo -e "${RED}❌ 데이터베이스 연결 실패${NC}"
    echo "   .env 파일의 DATABASE_URL을 확인하세요."
    exit 1
fi

echo ""

# ======================================================
# Step 7: Django 마이그레이션 생성
# ======================================================
echo -e "${YELLOW}📌 Step 7: Django 마이그레이션 생성${NC}"
python manage.py makemigrations accounts

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ 마이그레이션 파일 생성 완료${NC}"
else
    echo -e "${RED}❌ 마이그레이션 파일 생성 실패${NC}"
    exit 1
fi

echo ""

# ======================================================
# Step 8: Django 마이그레이션 실행
# ======================================================
echo -e "${YELLOW}📌 Step 8: Django 마이그레이션 실행${NC}"

# accounts 앱 마이그레이션 (fake-initial: 테이블이 이미 있음)
echo "accounts 앱 마이그레이션 실행 중..."
python manage.py migrate accounts --fake-initial

if [ $? -ne 0 ]; then
    echo -e "${RED}❌ accounts 마이그레이션 실패${NC}"
    exit 1
fi

# 나머지 앱 마이그레이션
echo "나머지 앱 마이그레이션 실행 중..."
python manage.py migrate

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Django 마이그레이션 완료${NC}"
else
    echo -e "${RED}❌ 마이그레이션 실패${NC}"
    exit 1
fi

echo ""

# ======================================================
# Step 9: 데이터 검증
# ======================================================
echo -e "${YELLOW}📌 Step 9: 데이터 검증${NC}"

python manage.py shell <<EOF
from accounts.models import Company, Department, User

print("\n${CYAN}=== 회사 목록 ===${NC}")
companies = Company.objects.all()
for c in companies:
    print(f"  ID: {c.company_id}, 이름: {c.name}, 도메인: {c.domain or 'N/A'}")

print("\n${CYAN}=== 부서 목록 ===${NC}")
departments = Department.objects.all()
for d in departments:
    print(f"  ID: {d.department_id}, 회사: {d.company.name}, 부서: {d.name}")

print("\n${CYAN}=== 사용자 목록 ===${NC}")
users = User.objects.all()
if users.exists():
    for u in users:
        print(f"  {u.username} - {u.role} - {u.status}")
else:
    print("  (사용자 없음 - createsuperuser로 생성하세요)")

print("\n✅ 데이터 검증 완료\n")
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
echo -e "${CYAN}📊 마이그레이션 결과:${NC}"
echo "  ✅ 이전 테이블 삭제 완료"
echo "  ✅ 새 테이블 생성 완료 (Owner: final_play)"
echo "  ✅ Django 마이그레이션 완료"
echo "  ✅ 초기 데이터 생성 완료"
echo "     - 회사 2개: Example Corp, Test Company"
echo "     - 부서 5개: 개발팀, 기획팀, 영업팀, 연구소, 관리부"
echo ""
echo -e "${YELLOW}📋 다음 단계:${NC}"
echo ""
echo "  ${CYAN}1. 슈퍼 관리자 생성:${NC}"
echo "     cd backend"
echo "     python manage.py createsuperuser"
echo ""
echo "  ${CYAN}2. Django 서버 실행:${NC}"
echo "     python manage.py runserver"
echo ""
echo "  ${CYAN}3. API 테스트:${NC}"
echo "     curl http://localhost:8000/api/accounts/companies/"
echo "     curl http://localhost:8000/api/accounts/departments/"
echo ""
echo "  ${CYAN}4. 프론트엔드 테스트:${NC}"
echo "     cd ../test_app"
echo "     npm run dev"
echo "     브라우저: http://localhost:3000/login"
echo ""
echo -e "자세한 내용: ${BLUE}backend/MIGRATION_GUIDE.md${NC}"
echo -e "${NC}"
