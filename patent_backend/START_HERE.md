# 🚀 처음부터 끝까지 완벽 실행 가이드

**이 파일을 순서대로 따라하면 됩니다!** ✅ 체크하면서 진행하세요.

---

## ✅ 체크리스트

- [ ] Step 1: PostgreSQL 서버 시작
- [ ] Step 2: 데이터베이스 생성
- [ ] Step 3: 기존 테이블 생성 (또는 확인)
- [ ] Step 4: Django 필수 컬럼 추가 (SQL 실행)
- [ ] Step 5: .env 파일 수정
- [ ] Step 6: Django 마이그레이션
- [ ] Step 7: 관리자 계정 생성
- [ ] Step 8: Django 서버 실행
- [ ] Step 9: API 테스트

---

## 📌 Step 1: PostgreSQL 서버 시작 (필수!)

### WSL Ubuntu에서 실행:

```bash
# PostgreSQL 서버 시작
sudo service postgresql start

# 상태 확인
sudo service postgresql status
# ✅ "online" 또는 "active (running)" 표시되어야 함

# 만약 에러가 나면 재시작
sudo service postgresql restart
```

**중요!** WSL을 재부팅하면 PostgreSQL이 자동으로 꺼지므로, 매번 시작해야 합니다.

---

## 📌 Step 2: 데이터베이스 생성

### Option A: 이미 만든 DB가 있는 경우

```bash
# PostgreSQL 접속 (postgres 사용자로)
sudo -u postgres psql

# DB 목록 확인
\l

# 당신의 DB 이름 확인 (예: patent_analysis, patent_db 등)
# 있으면 Step 3으로, 없으면 Option B로
```

### Option B: DB가 없는 경우 (새로 생성)

```bash
# PostgreSQL 접속
sudo -u postgres psql

# 아래 명령어를 PostgreSQL shell에서 실행:
```

```sql
-- 데이터베이스 생성
CREATE DATABASE patent_analysis;

-- 사용자 생성
CREATE USER patentuser WITH PASSWORD 'yourpassword';

-- 권한 부여
GRANT ALL PRIVILEGES ON DATABASE patent_analysis TO patentuser;

-- 종료
\q
```

**메모!** 비밀번호는 나중에 .env 파일에 똑같이 입력해야 합니다!

---

## 📌 Step 3: 기존 테이블 확인 또는 생성

### 이미 테이블이 있는지 확인

```bash
# 당신의 DB에 접속
sudo -u postgres psql -d patent_analysis

# 테이블 목록 확인
\dt

# 결과 확인:
# - users, roles, permissions, userrolemap, rolepermissionmap 테이블이 있으면 ✅
# - 없으면 아래로 계속
```

### 테이블이 없으면 생성

```sql
-- PostgreSQL shell에서 실행

CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    userid VARCHAR(50) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    team VARCHAR(50),
    createdat TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updatedat TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE roles (
    roleid SERIAL PRIMARY KEY,
    rolename VARCHAR(50) UNIQUE NOT NULL,
    description TEXT,
    createdat TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE permissions (
    permissionid SERIAL PRIMARY KEY,
    permissionname VARCHAR(100) UNIQUE NOT NULL,
    description TEXT,
    createdat TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE userrolemap (
    userid INT REFERENCES users(id) ON DELETE CASCADE,
    roleid INT REFERENCES roles(roleid) ON DELETE CASCADE,
    PRIMARY KEY (userid, roleid)
);

CREATE TABLE rolepermissionmap (
    roleid INT REFERENCES roles(roleid) ON DELETE CASCADE,
    permissionid INT REFERENCES permissions(permissionid) ON DELETE CASCADE,
    PRIMARY KEY (roleid, permissionid)
);

-- 확인
\dt

-- 종료
\q
```

---

## 📌 Step 4: Django 필수 컬럼 추가 (중요!)

**이 단계가 가장 중요합니다!** Django가 요구하는 컬럼을 추가해야 합니다.

```bash
# 현재 위치 확인
pwd
# /home/juhyeong/workspace/final_project 이어야 함

# SQL 파일 실행
sudo -u postgres psql -d patent_analysis -f backend/database_migration.sql

# 또는 비밀번호를 입력할 수 있다면:
psql -U patentuser -d patent_analysis -f backend/database_migration.sql
```

**성공하면 다음과 같은 메시지가 출력됩니다:**
```
ALTER TABLE
UPDATE 0
CREATE INDEX
INSERT 0 3
INSERT 0 6
...
```

**확인:**
```bash
# PostgreSQL 접속
sudo -u postgres psql -d patent_analysis

# users 테이블 구조 확인
\d users

# ✅ 다음 컬럼들이 보여야 함:
# - id, userid, password, team, createdat, updatedat
# - email, first_name, last_name (새로 추가됨)
# - is_staff, is_active, is_superuser (새로 추가됨)
# - last_login, date_joined (새로 추가됨)
```

---

## 📌 Step 5: .env 파일 수정

```bash
# .env 파일 열기
nano backend/.env

# 또는
code backend/.env
```

**수정할 내용:**
```env
# DATABASE_URL을 당신의 정보로 수정
# 형식: postgresql://사용자명:비밀번호@호스트:포트/DB명

DATABASE_URL=postgresql://patentuser:yourpassword@localhost:5432/patent_analysis

# 예시 (Step 2에서 설정한 비밀번호 사용):
# DATABASE_URL=postgresql://patentuser:mypassword123@localhost:5432/patent_analysis
```

**저장 후 확인:**
```bash
cat backend/.env | grep DATABASE_URL
```

---

## 📌 Step 6: Django 마이그레이션

```bash
# backend 폴더로 이동
cd /home/juhyeong/workspace/final_project/backend

# 가상환경 활성화 (conda 사용 중이라면)
conda activate final_project

# Django 연결 테스트
python manage.py check

# ✅ "System check identified no issues" 메시지 나와야 함

# 마이그레이션 생성
python manage.py makemigrations

# 마이그레이션 실행 (fake-initial: 테이블은 이미 있으므로)
python manage.py migrate --fake-initial

# Django 시스템 테이블 생성
python manage.py migrate

# ✅ 성공 메시지 확인
```

**에러가 나면:**
```bash
# 에러 메시지를 잘 읽고, 주로 다음 문제:
# 1. PostgreSQL 서버 꺼짐 → sudo service postgresql start
# 2. .env 파일 비밀번호 틀림 → 다시 확인
# 3. database_migration.sql 실행 안 함 → Step 4로 돌아가기
```

---

## 📌 Step 7: 관리자 계정 생성

```bash
python manage.py createsuperuser

# 입력 예시:
# Userid: admin
# Email address: admin@example.com
# Password: admin1234
# Password (again): admin1234

# ✅ "Superuser created successfully." 메시지 확인
```

---

## 📌 Step 8: Django 서버 실행

```bash
# 서버 시작
python manage.py runserver

# ✅ 출력 확인:
# Starting development server at http://127.0.0.1:8000/
# Quit the server with CONTROL-C.
```

**서버가 실행 중인 상태로 새 터미널을 열어서 테스트하세요!**

---

## 📌 Step 9: API 테스트

### 새 터미널 열기 (서버는 계속 실행 중)

#### 9-1. 헬스체크 (가장 기본)

```bash
curl http://localhost:8000/api/auth/health/

# ✅ 예상 결과:
# {"status":"ok","message":"Patent Analysis API is running"}
```

#### 9-2. 회원가입

```bash
curl -X POST http://localhost:8000/api/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "userid": "testuser",
    "password": "test1234",
    "password_confirm": "test1234",
    "email": "test@example.com",
    "first_name": "길동",
    "last_name": "홍",
    "team": "개발팀",
    "role": "researcher"
  }'

# ✅ 예상 결과:
# {
#   "message": "회원가입이 완료되었습니다.",
#   "user": {...},
#   "tokens": {
#     "refresh": "eyJ0eXAiOiJKV1Qi...",
#     "access": "eyJ0eXAiOiJKV1Qi..."
#   }
# }
```

#### 9-3. 로그인

```bash
curl -X POST http://localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "userid": "testuser",
    "password": "test1234"
  }'

# ✅ 예상 결과:
# {
#   "message": "로그인 성공",
#   "user": {
#     "userid": "testuser",
#     "email": "test@example.com",
#     "roles": [{"rolename": "researcher"}],
#     "permissions": ["view_patent", "search_patent", ...]
#   },
#   "tokens": {...}
# }
```

#### 9-4. 사용자 정보 조회 (토큰 필요)

```bash
# 위 로그인에서 받은 access token을 복사해서 사용
export TOKEN="여기에_access_token_붙여넣기"

curl http://localhost:8000/api/auth/me/ \
  -H "Authorization: Bearer $TOKEN"

# ✅ 예상 결과: 사용자 정보 JSON
```

#### 9-5. Django Admin 페이지 (브라우저)

```
http://localhost:8000/admin/

로그인:
- Username: admin
- Password: admin1234
```

---

## 🎯 모든 단계 완료 후 확인사항

### ✅ 체크리스트

- [ ] PostgreSQL 서버가 실행 중 (`sudo service postgresql status`)
- [ ] 데이터베이스 `patent_analysis` 존재
- [ ] `users` 테이블에 Django 필수 컬럼 존재 (`\d users`로 확인)
- [ ] `.env` 파일에 올바른 DB 연결 정보
- [ ] `python manage.py check` 성공
- [ ] `python manage.py migrate` 성공
- [ ] `python manage.py createsuperuser` 성공
- [ ] `python manage.py runserver` 실행 중
- [ ] `curl http://localhost:8000/api/auth/health/` 성공
- [ ] 회원가입/로그인 API 작동
- [ ] Django Admin 페이지 접속 가능

---

## ❌ 자주 발생하는 문제 해결

### 문제 1: "connection to server on socket failed"
```bash
# PostgreSQL 서버가 꺼져있음
sudo service postgresql start
```

### 문제 2: "database does not exist"
```bash
# DB 생성 안 됨 → Step 2로
sudo -u postgres psql
CREATE DATABASE patent_analysis;
\q
```

### 문제 3: "column email does not exist"
```bash
# database_migration.sql 실행 안 됨 → Step 4로
sudo -u postgres psql -d patent_analysis -f backend/database_migration.sql
```

### 문제 4: "role 'patentuser' does not exist"
```bash
# 사용자 생성 안 됨 → Step 2로
sudo -u postgres psql
CREATE USER patentuser WITH PASSWORD 'yourpassword';
GRANT ALL PRIVILEGES ON DATABASE patent_analysis TO patentuser;
\q
```

### 문제 5: "password authentication failed"
```bash
# .env 파일의 비밀번호가 틀림 → Step 5로
nano backend/.env
# DATABASE_URL의 비밀번호를 Step 2에서 설정한 것과 동일하게 수정
```

---

## 🎉 완료 후 다음 단계

모든 API 테스트가 성공하면:

1. **프론트엔드 연결** (login/page.tsx 수정)
2. **특허 검색 API 개발** (patents 앱)
3. **AI 챗봇 API 개발** (chat 앱)

---

## 📞 도움말

각 단계에서 에러가 나면:
1. 에러 메시지를 정확히 복사
2. 어느 단계에서 발생했는지 확인
3. 위 "자주 발생하는 문제 해결" 참고

**핵심 명령어:**
- PostgreSQL 시작: `sudo service postgresql start`
- PostgreSQL 접속: `sudo -u postgres psql`
- Django 체크: `python manage.py check`
- Django 서버: `python manage.py runserver`
