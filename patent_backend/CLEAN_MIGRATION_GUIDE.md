# 🔄 깨끗한 데이터베이스 마이그레이션 가이드

## 📋 현재 상황

- ❌ PostgreSQL에 **이전 역할 기반 테이블**이 존재 (users, roles, permissions 등)
- ❌ Owner가 postgres로 되어 있음
- ✅ Django 모델은 **새로운 Company-Department-User 구조**로 변경됨

## 🎯 목표

1. ✅ 이전 테이블 **완전 삭제**
2. ✅ 새 테이블 생성 (**Owner: final_play**)
3. ✅ Django 마이그레이션 완료
4. ✅ 초기 데이터 생성 (회사 2개, 부서 5개)

---

## 🚀 원클릭 마이그레이션 (권장)

### 실행 명령어

```bash
cd /home/juhyeong/workspace/final_project
bash backend/full_migration.sh
```

### 이 스크립트가 하는 일

1. **이전 테이블 삭제**
   - `users`, `roles`, `permissions`, `userrolemap`, `rolepermissionmap`
   - `usersessions`, `userqueries`, `chatbotlogs`, `adminpagelogs`, `keywordsearchlogs`

2. **새 테이블 생성** (Owner: final_play)
   - `company` (회사)
   - `department` (부서)
   - `user` (사용자)
   - `admin_request` (부서 관리자 승인 요청)
   - `password_reset_request` (비밀번호 초기화)

3. **Django 마이그레이션**
   - 기존 마이그레이션 파일 삭제
   - 새 마이그레이션 생성
   - `--fake-initial`로 실행

4. **데이터 검증**
   - 회사 2개, 부서 5개 샘플 데이터 확인

---

## 🔧 수동 마이그레이션 (단계별)

자동 스크립트가 실패하거나 단계별로 확인하고 싶을 때 사용하세요.

### Step 1: 이전 테이블 삭제

```bash
cd /home/juhyeong/workspace/final_project
sudo -u postgres psql -d patentdb -f backend/drop_old_tables.sql
```

**확인:**
```bash
sudo -u postgres psql -d patentdb -c "\dt"
```

### Step 2: 새 테이블 생성 (final_play 소유)

```bash
sudo -u postgres psql -d patentdb -f backend/create_new_tables_final_play.sql
```

**확인:**
```bash
sudo -u postgres psql -d patentdb -c "
SELECT tablename, tableowner
FROM pg_tables
WHERE schemaname = 'public'
  AND tablename IN ('company', 'department', 'user', 'admin_request', 'password_reset_request')
ORDER BY tablename;
"
```

**예상 결과:**
```
   tablename            | tableowner
------------------------+------------
 admin_request          | final_play
 company                | final_play
 department             | final_play
 password_reset_request | final_play
 user                   | final_play
```

### Step 3: Django 마이그레이션

```bash
cd backend
source ~/miniconda3/etc/profile.d/conda.sh
conda activate patent_backend

# 기존 마이그레이션 삭제
rm -f accounts/migrations/00*.py
rm -rf accounts/migrations/__pycache__

# 데이터베이스 연결 테스트
python manage.py check --database default

# 새 마이그레이션 생성
python manage.py makemigrations accounts

# 마이그레이션 실행 (fake-initial: 테이블이 이미 PostgreSQL에 있음)
python manage.py migrate accounts --fake-initial

# 나머지 앱 마이그레이션
python manage.py migrate
```

### Step 4: 데이터 검증

#### Python Shell에서 확인
```bash
python manage.py shell
```

```python
from accounts.models import Company, Department, User

# 회사 목록
print("=== 회사 ===")
for c in Company.objects.all():
    print(f"{c.company_id}: {c.name}")

# 부서 목록
print("\n=== 부서 ===")
for d in Department.objects.all():
    print(f"{d.department_id}: {d.company.name} - {d.name}")

# 사용자 확인
print("\n=== 사용자 ===")
print(f"총 {User.objects.count()}명")
```

**예상 출력:**
```
=== 회사 ===
1: Example Corp
2: Test Company

=== 부서 ===
1: Example Corp - 개발팀
2: Example Corp - 기획팀
3: Example Corp - 영업팀
4: Test Company - 연구소
5: Test Company - 관리부

=== 사용자 ===
총 0명
```

---

## 📊 새로운 테이블 구조

### Company (회사)
```sql
company_id    SERIAL PRIMARY KEY
name          VARCHAR(255) UNIQUE NOT NULL
domain        VARCHAR(255) UNIQUE
created_at    TIMESTAMP
updated_at    TIMESTAMP
```

### Department (부서)
```sql
department_id SERIAL PRIMARY KEY
company_id    INT → company(company_id)
name          VARCHAR(255) NOT NULL
created_at    TIMESTAMP
updated_at    TIMESTAMP
UNIQUE(company_id, name)
```

### User (사용자)
```sql
user_id       UUID PRIMARY KEY
username      VARCHAR(150) UNIQUE NOT NULL
email         VARCHAR(254) UNIQUE NOT NULL
password_hash VARCHAR(255) NOT NULL
company_id    INT → company(company_id)
department_id INT → department(department_id)
role          ENUM('user', 'dept_admin', 'super_admin')
status        ENUM('active', 'pending', 'suspended')
first_name    VARCHAR(150)
last_name     VARCHAR(150)
is_staff      BOOLEAN
is_active     BOOLEAN
is_superuser  BOOLEAN
...
```

---

## ✅ 마이그레이션 후 체크리스트

- [ ] 이전 테이블 삭제 확인 (`\dt`에서 users, roles 등이 사라짐)
- [ ] 새 테이블 생성 확인 (company, department, user 등)
- [ ] Owner가 `final_play`로 설정됨
- [ ] Django 마이그레이션 완료
- [ ] 회사 2개, 부서 5개 데이터 확인
- [ ] Django 데이터베이스 연결 성공

---

## 🎓 다음 단계

### 1. 슈퍼 관리자 생성

```bash
cd backend
python manage.py createsuperuser
```

**입력 예시:**
```
Username: admin
Email: admin@example.com
Password: ********
Password (again): ********
Company ID: 1
Department ID: 1
```

**중요:** Company ID와 Department ID는 반드시 존재하는 값을 입력하세요!

### 2. Django 서버 실행

```bash
python manage.py runserver
```

### 3. API 테스트

```bash
# 회사 목록
curl http://localhost:8000/api/accounts/companies/

# 부서 목록
curl http://localhost:8000/api/accounts/departments/

# 특정 회사의 부서 목록
curl http://localhost:8000/api/accounts/companies/1/departments/
```

### 4. 프론트엔드 테스트

```bash
cd ../test_app
npm run dev
```

브라우저에서 http://localhost:3000/login 접속 후:
- 회사 선택 드롭다운 확인
- 부서 선택 드롭다운 확인
- 일반 회원가입 테스트
- 관리자 회원가입 테스트 (http://localhost:3000/admin-register)

---

## 🔍 문제 해결

### 문제 1: "sudo password required"

**해결:**
```bash
# 수동으로 PostgreSQL 접속
sudo -u postgres psql -d patentdb

# SQL 파일 실행
\i /home/juhyeong/workspace/final_project/backend/drop_old_tables.sql
\i /home/juhyeong/workspace/final_project/backend/create_new_tables_final_play.sql

# 종료
\q
```

### 문제 2: "relation already exists"

**원인:** 테이블이 이미 존재

**해결:**
```bash
# 새 테이블만 삭제 후 재생성
sudo -u postgres psql -d patentdb -c "
DROP TABLE IF EXISTS password_reset_request CASCADE;
DROP TABLE IF EXISTS admin_request CASCADE;
DROP TABLE IF EXISTS \"user\" CASCADE;
DROP TABLE IF EXISTS department CASCADE;
DROP TABLE IF EXISTS company CASCADE;
"

# 다시 생성
sudo -u postgres psql -d patentdb -f backend/create_new_tables_final_play.sql
```

### 문제 3: "type already exists"

**원인:** ENUM 타입이 이미 존재

**해결:**
```bash
sudo -u postgres psql -d patentdb -c "
DROP TYPE IF EXISTS password_reset_status CASCADE;
DROP TYPE IF EXISTS admin_request_status CASCADE;
DROP TYPE IF EXISTS user_status CASCADE;
DROP TYPE IF EXISTS user_role CASCADE;
"

# 다시 생성
sudo -u postgres psql -d patentdb -f backend/create_new_tables_final_play.sql
```

### 문제 4: Django migration conflict

**해결:**
```bash
cd backend

# 모든 마이그레이션 히스토리 삭제
python manage.py migrate --fake accounts zero

# 마이그레이션 파일 삭제
rm -f accounts/migrations/00*.py

# 다시 생성
python manage.py makemigrations accounts
python manage.py migrate accounts --fake-initial
```

---

## 📚 관련 파일

### SQL 스크립트
- [drop_old_tables.sql](/home/juhyeong/workspace/final_project/backend/drop_old_tables.sql) - 이전 테이블 삭제
- [create_new_tables_final_play.sql](/home/juhyeong/workspace/final_project/backend/create_new_tables_final_play.sql) - 새 테이블 생성 (final_play 소유)

### 자동화 스크립트
- [full_migration.sh](/home/juhyeong/workspace/final_project/backend/full_migration.sh) - 완전 자동 마이그레이션

### Django 모델
- [accounts/models.py](/home/juhyeong/workspace/final_project/backend/accounts/models.py) - Company, Department, User 모델

### API
- [accounts/views.py](/home/juhyeong/workspace/final_project/backend/accounts/views.py) - 회원가입, 로그인 API
- [accounts/serializers.py](/home/juhyeong/workspace/final_project/backend/accounts/serializers.py) - Serializers

---

## 📞 요약

**한 줄 명령어로 모든 마이그레이션 실행:**

```bash
bash /home/juhyeong/workspace/final_project/backend/full_migration.sh
```

**이후 슈퍼 관리자 생성:**

```bash
cd /home/juhyeong/workspace/final_project/backend
python manage.py createsuperuser
python manage.py runserver
```

---

**작성일:** 2025-10-22
**데이터베이스:** patentdb
**Owner:** final_play
**Django 버전:** 5.2.7
