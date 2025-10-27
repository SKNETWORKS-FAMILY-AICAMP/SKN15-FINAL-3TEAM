#!/bin/bash
# 빠른 시작 스크립트 (한 번에 실행)
# 사용법: bash backend/QUICK_START.sh

echo "🚀 Django 백엔드 빠른 시작 스크립트"
echo "======================================"
echo ""

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Step 1: PostgreSQL 서버 시작
echo -e "${YELLOW}📌 Step 1: PostgreSQL 서버 시작${NC}"
echo "다음 명령어를 실행하세요:"
echo "  sudo service postgresql start"
echo ""
read -p "PostgreSQL 서버를 시작했나요? (y/n): " pg_started

if [ "$pg_started" != "y" ]; then
    echo -e "${RED}❌ PostgreSQL을 먼저 시작해주세요!${NC}"
    exit 1
fi

# Step 2: 데이터베이스 존재 확인
echo ""
echo -e "${YELLOW}📌 Step 2: 데이터베이스 확인${NC}"
echo "다음 중 하나를 선택하세요:"
echo "  1) 이미 데이터베이스가 있음 (patent_analysis)"
echo "  2) 새로 데이터베이스를 만들어야 함"
read -p "선택 (1 or 2): " db_choice

if [ "$db_choice" == "2" ]; then
    echo ""
    echo "다음 명령어를 실행하세요:"
    echo ""
    echo "  sudo -u postgres psql"
    echo ""
    echo "PostgreSQL shell에서:"
    echo "  CREATE DATABASE patent_analysis;"
    echo "  CREATE USER patentuser WITH PASSWORD 'yourpassword';"
    echo "  GRANT ALL PRIVILEGES ON DATABASE patent_analysis TO patentuser;"
    echo "  \\q"
    echo ""
    read -p "데이터베이스를 만들었나요? (y/n): " db_created

    if [ "$db_created" != "y" ]; then
        echo -e "${RED}❌ 데이터베이스를 먼저 만들어주세요!${NC}"
        exit 1
    fi
fi

# Step 3: 테이블 확인
echo ""
echo -e "${YELLOW}📌 Step 3: 테이블 확인${NC}"
echo "다음 명령어로 테이블을 확인하세요:"
echo "  sudo -u postgres psql -d patent_analysis -c '\\dt'"
echo ""
read -p "users, roles, permissions 테이블이 있나요? (y/n): " tables_exist

if [ "$tables_exist" != "y" ]; then
    echo ""
    echo "START_HERE.md의 Step 3을 참고하여 테이블을 만들어주세요!"
    exit 1
fi

# Step 4: SQL 마이그레이션 실행
echo ""
echo -e "${YELLOW}📌 Step 4: Django 필수 컬럼 추가 (SQL 실행)${NC}"
echo "다음 명령어를 실행하세요:"
echo "  sudo -u postgres psql -d patent_analysis -f backend/database_migration.sql"
echo ""
read -p "SQL 마이그레이션을 실행했나요? (y/n): " sql_done

if [ "$sql_done" != "y" ]; then
    echo -e "${RED}❌ SQL 마이그레이션을 먼저 실행해주세요!${NC}"
    exit 1
fi

# Step 5: .env 파일 확인
echo ""
echo -e "${YELLOW}📌 Step 5: .env 파일 확인${NC}"
if [ ! -f "backend/.env" ]; then
    echo -e "${RED}❌ backend/.env 파일이 없습니다!${NC}"
    exit 1
fi

echo "DATABASE_URL이 올바른지 확인:"
grep "DATABASE_URL" backend/.env
echo ""
read -p ".env 파일의 DATABASE_URL이 올바른가요? (y/n): " env_ok

if [ "$env_ok" != "y" ]; then
    echo "backend/.env 파일을 수정해주세요!"
    echo "형식: DATABASE_URL=postgresql://사용자명:비밀번호@localhost:5432/patent_analysis"
    exit 1
fi

# Step 6: Django 체크
echo ""
echo -e "${YELLOW}📌 Step 6: Django 연결 테스트${NC}"
cd backend
python manage.py check

if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Django 체크 실패!${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Django 체크 성공!${NC}"

# Step 7: 마이그레이션
echo ""
echo -e "${YELLOW}📌 Step 7: Django 마이그레이션 실행${NC}"
python manage.py makemigrations
python manage.py migrate --fake-initial
python manage.py migrate

if [ $? -ne 0 ]; then
    echo -e "${RED}❌ 마이그레이션 실패!${NC}"
    exit 1
fi

echo -e "${GREEN}✅ 마이그레이션 성공!${NC}"

# Step 8: Superuser 생성
echo ""
echo -e "${YELLOW}📌 Step 8: 관리자 계정 생성${NC}"
read -p "관리자 계정을 만들었나요? (y/n): " superuser_created

if [ "$superuser_created" != "y" ]; then
    echo "다음 명령어를 실행하세요:"
    echo "  python manage.py createsuperuser"
    echo ""
    read -p "관리자 계정을 만들었나요? (y/n): " superuser_created
fi

# 완료!
echo ""
echo -e "${GREEN}======================================"
echo "🎉 모든 설정 완료!"
echo "======================================"
echo ""
echo "이제 Django 서버를 실행하세요:"
echo "  cd backend"
echo "  python manage.py runserver"
echo ""
echo "API 테스트:"
echo "  curl http://localhost:8000/api/auth/health/"
echo ""
echo "Django Admin:"
echo "  http://localhost:8000/admin/"
echo -e "${NC}"
