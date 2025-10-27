#!/bin/bash
# ======================================================
# 자동 데이터베이스 설정 스크립트
# ======================================================
# 사용법: bash backend/setup_database.sh
# ======================================================

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}======================================"
echo "🚀 PostgreSQL 데이터베이스 자동 설정"
echo "======================================"
echo -e "${NC}"

# ======================================================
# Step 1: PostgreSQL 서버 확인
# ======================================================
echo -e "${YELLOW}📌 Step 1: PostgreSQL 서버 상태 확인${NC}"
if ! sudo service postgresql status > /dev/null 2>&1; then
    echo -e "${RED}❌ PostgreSQL 서버가 실행되지 않았습니다!${NC}"
    echo "다음 명령어로 시작하세요:"
    echo "  sudo service postgresql start"
    exit 1
fi
echo -e "${GREEN}✅ PostgreSQL 서버 실행 중${NC}"
echo ""

# ======================================================
# Step 2: 데이터베이스 이름 입력
# ======================================================
echo -e "${YELLOW}📌 Step 2: 데이터베이스 설정${NC}"
read -p "데이터베이스 이름 (기본: patent_analysis): " DB_NAME
DB_NAME=${DB_NAME:-patent_analysis}

read -p "PostgreSQL 사용자 이름 (기본: patentuser): " DB_USER
DB_USER=${DB_USER:-patentuser}

read -sp "PostgreSQL 비밀번호: " DB_PASSWORD
echo ""

if [ -z "$DB_PASSWORD" ]; then
    echo -e "${RED}❌ 비밀번호를 입력해주세요!${NC}"
    exit 1
fi

echo ""
echo -e "${BLUE}설정 정보:${NC}"
echo "  데이터베이스: $DB_NAME"
echo "  사용자: $DB_USER"
echo "  비밀번호: ******"
echo ""

read -p "계속 진행하시겠습니까? (y/n): " CONFIRM
if [ "$CONFIRM" != "y" ]; then
    echo "취소되었습니다."
    exit 0
fi

# ======================================================
# Step 3: 데이터베이스 및 사용자 생성
# ======================================================
echo ""
echo -e "${YELLOW}📌 Step 3: 데이터베이스 및 사용자 생성${NC}"

sudo -u postgres psql <<EOF
-- 기존 연결 종료 (필요시)
SELECT pg_terminate_backend(pg_stat_activity.pid)
FROM pg_stat_activity
WHERE pg_stat_activity.datname = '$DB_NAME'
  AND pid <> pg_backend_pid();

-- 데이터베이스 생성 (이미 있으면 무시)
SELECT 'CREATE DATABASE $DB_NAME'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = '$DB_NAME')\gexec

-- 사용자 생성 (이미 있으면 무시)
DO \$\$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_user WHERE usename = '$DB_USER') THEN
        CREATE USER $DB_USER WITH PASSWORD '$DB_PASSWORD';
    ELSE
        ALTER USER $DB_USER WITH PASSWORD '$DB_PASSWORD';
    END IF;
END
\$\$;

-- 권한 부여
GRANT ALL PRIVILEGES ON DATABASE $DB_NAME TO $DB_USER;

\c $DB_NAME

-- 스키마 권한 부여
GRANT ALL ON SCHEMA public TO $DB_USER;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO $DB_USER;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO $DB_USER;

-- 미래 테이블에도 권한 부여
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO $DB_USER;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO $DB_USER;
EOF

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ 데이터베이스 및 사용자 생성 완료${NC}"
else
    echo -e "${RED}❌ 데이터베이스 생성 실패${NC}"
    exit 1
fi

# ======================================================
# Step 4: 테이블 생성
# ======================================================
echo ""
echo -e "${YELLOW}📌 Step 4: 테이블 생성${NC}"

sudo -u postgres psql -d $DB_NAME -f backend/create_tables.sql

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ 테이블 생성 완료${NC}"
else
    echo -e "${RED}❌ 테이블 생성 실패${NC}"
    exit 1
fi

# ======================================================
# Step 5: .env 파일 업데이트
# ======================================================
echo ""
echo -e "${YELLOW}📌 Step 5: .env 파일 업데이트${NC}"

# DATABASE_URL 생성
DATABASE_URL="postgresql://$DB_USER:$DB_PASSWORD@localhost:5432/$DB_NAME"

# .env 파일에서 DATABASE_URL 업데이트
if [ -f "backend/.env" ]; then
    # 기존 DATABASE_URL 라인 제거
    sed -i '/^DATABASE_URL=/d' backend/.env
    # 새 DATABASE_URL 추가
    echo "DATABASE_URL=$DATABASE_URL" >> backend/.env
    echo -e "${GREEN}✅ .env 파일 업데이트 완료${NC}"
else
    echo -e "${RED}❌ backend/.env 파일이 없습니다!${NC}"
    echo "DATABASE_URL=$DATABASE_URL"
    echo "위 값을 .env 파일에 수동으로 추가하세요."
fi

# ======================================================
# Step 6: Django 마이그레이션
# ======================================================
echo ""
echo -e "${YELLOW}📌 Step 6: Django 마이그레이션${NC}"

cd backend

# Django 연결 테스트
echo "Django 연결 테스트..."
python manage.py check

if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Django 연결 실패!${NC}"
    echo ".env 파일을 확인해주세요."
    exit 1
fi

# 마이그레이션 실행
echo "마이그레이션 실행..."
python manage.py makemigrations
python manage.py migrate --fake-initial
python manage.py migrate

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Django 마이그레이션 완료${NC}"
else
    echo -e "${RED}❌ 마이그레이션 실패${NC}"
    exit 1
fi

# ======================================================
# 완료!
# ======================================================
echo ""
echo -e "${GREEN}======================================"
echo "🎉 데이터베이스 설정 완료!"
echo "======================================"
echo ""
echo "다음 단계:"
echo "  1. 관리자 계정 생성:"
echo "     cd backend"
echo "     python manage.py createsuperuser"
echo ""
echo "  2. Django 서버 실행:"
echo "     python manage.py runserver"
echo ""
echo "  3. API 테스트:"
echo "     curl http://localhost:8000/api/auth/health/"
echo ""
echo -e "DATABASE_URL: ${BLUE}$DATABASE_URL${NC}"
echo -e "${NC}"
