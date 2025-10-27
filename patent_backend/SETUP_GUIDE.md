# 🚀 Patent Analysis System - 설정 가이드

## 📋 목차
1. [사전 준비](#1-사전-준비)
2. [데이터베이스 초기화 및 설정](#2-데이터베이스-초기화-및-설정)
3. [Django 프로젝트 설정](#3-django-프로젝트-설정)
4. [서버 실행 및 테스트](#4-서버-실행-및-테스트)
5. [프론트엔드 연결](#5-프론트엔드-연결)
6. [문제 해결](#6-문제-해결)

---

## 1. 사전 준비

### 필요한 것들
- ✅ PostgreSQL 12 이상 설치 및 실행
- ✅ Python 3.9 이상 환경
- ✅ pip (Python 패키지 관리자)

### 확인 방법
```bash
python --version
psql --version
pip --version
```

### 패키지 설치
```bash
cd /home/juhyeong/workspace/final_project/backend
pip install -r requirements.txt
```

**필수 패키지:**
- Django 5.2+
- djangorestframework
- djangorestframework-simplejwt
- psycopg2-binary
- dj-database-url
- django-cors-headers
- drf-spectacular

---

## 2. 데이터베이스 초기화 및 설정

### 2-1. PostgreSQL 접속
```bash
# WSL/Ubuntu
sudo -u postgres psql

# macOS (Homebrew)
psql postgres

# Windows
psql -U postgres
```

### 2-2. 데이터베이스 생성
```sql
-- patent_db 데이터베이스 생성
CREATE DATABASE patent_db;

-- 사용자 생성 (선택사항)
CREATE USER patent_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE patent_db TO patent_user;

-- 데이터베이스 전환
\c patent_db

-- 테이블 목록 확인
\dt
```

### 2-3. 기존 테이블 초기화
```bash
# patent_db에 접속한 상태에서
\c patent_db

# reset_database.sql 실행 (기존 테이블 모두 삭제)
\i /home/juhyeong/workspace/final_project/backend/reset_database.sql
```

**또는 psql 커맨드로 실행:**
```bash
psql -U postgres -d patent_db -f /home/juhyeong/workspace/final_project/backend/reset_database.sql
```

### 2-4. 새로운 테이블 생성
```bash
# create_new_tables.sql 실행
\i /home/juhyeong/workspace/final_project/backend/create_new_tables.sql
```

**또는 psql 커맨드로 실행:**
```bash
psql -U postgres -d patent_db -f /home/juhyeong/workspace/final_project/backend/create_new_tables.sql
```

**이 스크립트가 생성하는 테이블:**
- ✅ `company` (회사)
- ✅ `department` (부서)
- ✅ `user` (사용자) - UUID 기반
- ✅ `admin_request` (관리자 권한 요청)
- ✅ `password_reset_request` (비밀번호 초기화)

### 2-5. 테이블 생성 확인
```sql
-- 테이블 목록 확인
\dt

-- 각 테이블 구조 확인
\d company
\d department
\d "user"
\d admin_request
\d password_reset_request

-- 샘플 데이터 확인
SELECT * FROM company;
SELECT * FROM department;
```

**예상 출력:**
```
                List of relations
 Schema |         Name           | Type  |  Owner
--------+------------------------+-------+----------
 public | admin_request          | table | postgres
 public | company                | table | postgres
 public | department             | table | postgres
 public | password_reset_request | table | postgres
 public | user                   | table | postgres
```

---

## 3. Django 프로젝트 설정

### 3-1. 프로젝트 디렉토리로 이동
```bash
cd /home/juhyeong/workspace/final_project/backend
```

### 3-2. 가상환경 생성 및 활성화 (권장)
```bash
# 가상환경 생성
python -m venv venv

# 가상환경 활성화 (Linux/Mac)
source venv/bin/activate

# 가상환경 활성화 (Windows)
venv\Scripts\activate
```

### 3-3. 환경 변수 설정
```bash
# .env 파일 생성
cp .env.example .env

# .env 파일 편집
nano .env
```

**필수 환경 변수 (.env):**
```env
# Django
SECRET_KEY=your-secret-key-here-change-in-production
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Database
DATABASE_URL=postgresql://postgres:your_password@localhost:5432/patent_db

# JWT
ACCESS_TOKEN_LIFETIME=60
REFRESH_TOKEN_LIFETIME=7

# CORS
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000

# OpenAI (선택사항)
OPENAI_API_KEY=sk-your-openai-api-key-here
```

### 3-4. Django 설정 확인 및 연결 테스트
```bash
# settings.py에서 데이터베이스 연결 확인
python manage.py check

# 데이터베이스 연결 테스트
python manage.py dbshell
```

**Python shell에서 테스트:**
```bash
python manage.py shell
```

```python
from django.db import connection
connection.ensure_connection()
print("✅ PostgreSQL 연결 성공!")
exit()
```

### 3-5. Django 마이그레이션

**주의사항:**
- `accounts` 앱의 모델들은 `managed = False`로 설정되어 있습니다
- PostgreSQL에서 이미 테이블을 생성했으므로 Django 마이그레이션으로 재생성하지 않습니다
- Django의 auth, sessions, admin 등 기본 테이블만 마이그레이션됩니다

```bash
# Django 기본 앱들의 마이그레이션 적용
python manage.py migrate --run-syncdb

# 결과 확인
python manage.py showmigrations
```

### 3-6. Django Superuser 생성
```bash
python manage.py createsuperuser
```

**입력 예시:**
```
Username: admin
Email: admin@example.com
Password: ********
Password (again): ********
```

**주의:**
- 이 superuser는 Django admin 페이지 접속용입니다
- 실제 시스템의 super_admin 역할 사용자와는 별개입니다

---

## 4. 서버 실행 및 테스트

### 4-1. Django 개발 서버 실행
```bash
python manage.py runserver
```

**예상 출력:**
```
System check identified no issues (0 silenced).
October 21, 2025 - 10:00:00
Django version 5.2, using settings 'config.settings'
Starting development server at http://127.0.0.1:8000/
Quit the server with CONTROL-C.
```

### 4-2. 서버 동작 확인
```bash
curl http://127.0.0.1:8000/api/accounts/health/
```

**예상 응답:**
```json
{
  "status": "ok",
  "message": "API is running"
}
```

### 4-3. API 엔드포인트 테스트

#### 1️⃣ 회사 목록 조회
```bash
curl http://127.0.0.1:8000/api/accounts/companies/
```

**예상 응답:**
```json
[
  {
    "company_id": 1,
    "name": "테크 주식회사",
    "domain": "tech.com"
  },
  {
    "company_id": 2,
    "name": "이노베이션 코퍼레이션",
    "domain": "innovation.com"
  }
]
```

#### 2️⃣ 부서 목록 조회
```bash
curl http://127.0.0.1:8000/api/accounts/departments/
```

**예상 응답:**
```json
[
  {
    "department_id": 1,
    "company": 1,
    "company_name": "테크 주식회사",
    "name": "연구개발팀"
  },
  {
    "department_id": 2,
    "company": 1,
    "company_name": "테크 주식회사",
    "name": "특허팀"
  }
]
```

#### 3️⃣ 회원가입
```bash
curl -X POST http://127.0.0.1:8000/api/accounts/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "email": "testuser@example.com",
    "password": "SecurePass123!",
    "company": 1,
    "department": 1
  }'
```

**예상 응답:**
```json
{
  "message": "회원가입 성공. 관리자 승인 대기 중입니다.",
  "user": {
    "user_id": "123e4567-e89b-12d3-a456-426614174000",
    "username": "testuser",
    "email": "testuser@example.com",
    "status": "pending"
  }
}
```

#### 4️⃣ 로그인 (pending 상태)
```bash
curl -X POST http://127.0.0.1:8000/api/accounts/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "password": "SecurePass123!"
  }'
```

**예상 응답 (pending 상태):**
```json
{
  "error": "계정이 관리자 승인 대기 중입니다."
}
```

#### 5️⃣ 사용자 상태 변경 (super_admin이 승인)
```bash
# Django admin 또는 API를 통해 상태를 active로 변경
curl -X PATCH http://127.0.0.1:8000/api/accounts/users/USER_UUID/status/ \
  -H "Authorization: Bearer SUPER_ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "status": "active"
  }'
```

#### 6️⃣ 로그인 (active 상태)
```bash
curl -X POST http://127.0.0.1:8000/api/accounts/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "password": "SecurePass123!"
  }'
```

**예상 응답 (active 상태):**
```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "user": {
    "user_id": "123e4567-e89b-12d3-a456-426614174000",
    "username": "testuser",
    "email": "testuser@example.com",
    "role": "user",
    "status": "active"
  }
}
```

#### 7️⃣ 사용자 정보 조회 (인증 필요)
```bash
curl http://127.0.0.1:8000/api/accounts/me/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### 4-4. Django Admin 페이지

브라우저에서 접속:
```
http://127.0.0.1:8000/admin/
```

**로그인:** 앞서 생성한 superuser 계정 사용

**관리 가능한 항목:**
- **Company (회사)**: 회사 추가/수정/삭제
- **Department (부서)**: 부서 추가/수정/삭제
- **User (사용자)**: 사용자 조회/수정, 상태 변경, 역할 변경
- **Admin Request (관리자 권한 요청)**: 승인/거부
- **Password Reset Request (비밀번호 초기화)**: 초기화 요청 관리

---

## 5. 프론트엔드 연결

### 5-1. Next.js 로그인 페이지 수정

```tsx
// 로그인 핸들러 예시
const handleLogin = async (e: React.FormEvent) => {
  e.preventDefault()

  try {
    const response = await fetch('http://localhost:8000/api/accounts/login/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        username: username,  // username 필드 사용
        password: password
      })
    })

    const data = await response.json()

    if (response.ok) {
      // JWT 토큰 저장
      localStorage.setItem('access_token', data.access)
      localStorage.setItem('refresh_token', data.refresh)

      // 사용자 정보 저장
      localStorage.setItem('user', JSON.stringify(data.user))

      // 대시보드로 이동
      router.push('/dashboard')
    } else {
      // 오류 처리
      alert(data.error || '로그인 실패')
    }
  } catch (error) {
    console.error('로그인 오류:', error)
    alert('서버 연결 실패')
  }
}
```

### 5-2. 회원가입 페이지 예시

```tsx
// 회원가입 핸들러
const handleRegister = async (e: React.FormEvent) => {
  e.preventDefault()

  try {
    const response = await fetch('http://localhost:8000/api/accounts/register/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        username: username,
        email: email,
        password: password,
        company: selectedCompany,    // 회사 ID
        department: selectedDept     // 부서 ID
      })
    })

    const data = await response.json()

    if (response.ok) {
      alert('회원가입 성공! 관리자 승인 대기 중입니다.')
      router.push('/login')
    } else {
      alert(data.error || '회원가입 실패')
    }
  } catch (error) {
    console.error('회원가입 오류:', error)
    alert('서버 연결 실패')
  }
}
```

### 5-3. 인증이 필요한 API 요청 예시

```tsx
// 특허 검색 등 인증이 필요한 API 호출
const searchPatents = async (query: string) => {
  const token = localStorage.getItem('access_token')

  const response = await fetch('http://localhost:8000/api/patents/search/', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`  // JWT 토큰 포함
    },
    body: JSON.stringify({ query })
  })

  if (response.status === 401) {
    // 토큰 만료 → 로그인 페이지로
    alert('세션이 만료되었습니다. 다시 로그인해주세요.')
    router.push('/login')
    return
  }

  return await response.json()
}
```

### 5-4. 토큰 갱신 (Refresh Token)

```tsx
// Access Token 만료 시 Refresh Token으로 갱신
const refreshAccessToken = async () => {
  const refreshToken = localStorage.getItem('refresh_token')

  const response = await fetch('http://localhost:8000/api/accounts/token/refresh/', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      refresh: refreshToken
    })
  })

  if (response.ok) {
    const data = await response.json()
    localStorage.setItem('access_token', data.access)
    return data.access
  } else {
    // Refresh Token도 만료됨 → 재로그인 필요
    router.push('/login')
    return null
  }
}
```

---

## 6. 문제 해결

### ❌ "relation user does not exist" 오류
**원인**: `create_new_tables.sql` 실행 안 함

**해결**:
```bash
psql -U postgres -d patent_db -f /home/juhyeong/workspace/final_project/backend/create_new_tables.sql
```

### ❌ "could not connect to server" 오류
**원인**: PostgreSQL 서버가 실행되지 않음

**해결**:
```bash
# PostgreSQL 서비스 상태 확인 (Linux)
sudo systemctl status postgresql

# PostgreSQL 서비스 시작
sudo systemctl start postgresql

# WSL2의 경우
sudo service postgresql start
```

### ❌ "password authentication failed" 오류
**원인**: .env 파일의 데이터베이스 비밀번호가 틀림

**해결**:
```bash
# .env 파일 확인
cat .env | grep DATABASE_URL

# PostgreSQL 비밀번호 재설정
sudo -u postgres psql
ALTER USER postgres PASSWORD 'new_password';
```

### ❌ 로그인 시 "계정이 관리자 승인 대기 중입니다" 오류
**원인**: 사용자 status가 'pending' 상태

**해결 방법 1 - Django Admin 사용:**
```
1. http://127.0.0.1:8000/admin/ 접속
2. Users 메뉴 선택
3. 해당 사용자 클릭
4. Status를 'pending'에서 'active'로 변경
5. Save 클릭
```

**해결 방법 2 - SQL 직접 실행:**
```sql
psql -U postgres -d patent_db

UPDATE "user"
SET status = 'active'
WHERE username = 'testuser';
```

### ❌ "Given token not valid for any token type" 오류
**원인**: JWT 액세스 토큰 만료

**해결**:
```bash
# Refresh Token으로 새 Access Token 발급
curl -X POST http://127.0.0.1:8000/api/accounts/token/refresh/ \
  -H "Content-Type: application/json" \
  -d '{
    "refresh": "YOUR_REFRESH_TOKEN"
  }'
```

### ❌ CORS 오류 (프론트엔드에서)
**원인**: Django CORS 설정 누락

**해결**:
```bash
# .env 파일 확인
cat .env | grep CORS_ALLOWED_ORIGINS

# 프론트엔드 URL 추가
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
```

### ❌ "No migrations to apply" 메시지
**원인**: 정상 동작 (accounts 앱은 managed=False)

**참고**:
- accounts 앱의 테이블은 PostgreSQL에서 직접 생성했으므로 Django 마이그레이션이 불필요합니다
- 이 메시지는 문제가 아닙니다

---

## 🎉 완료!

모든 설정이 완료되었습니다. 이제 다음을 진행할 수 있습니다:

### ✅ 사용 가능한 기능
- 회원가입/로그인 (JWT 인증)
- 회사/부서 기반 사용자 관리
- 3단계 역할 시스템 (user, dept_admin, super_admin)
- 사용자 상태 관리 (pending, active, suspended)
- 부서 관리자 권한 요청 및 승인
- 비밀번호 초기화 기능
- Django Admin 페이지를 통한 관리

### 📊 시스템 구조 요약

#### 데이터베이스 구조
```
Company (회사)
  └── Department (부서)
        └── User (사용자)
              ├── AdminRequest (관리자 권한 요청)
              └── PasswordResetRequest (비밀번호 초기화)
```

#### 사용자 역할 (role)
- **user**: 일반 사용자
- **dept_admin**: 부서 관리자
- **super_admin**: 시스템 최고 관리자

#### 사용자 상태 (status)
- **pending**: 승인 대기
- **active**: 활성화 (로그인 가능)
- **suspended**: 정지 (로그인 불가)

---

## 📚 다음 단계

1. **특허 분석 API 개발** (`patents` 앱)
   - 특허 검색 기능
   - 특허 상세 정보 조회
   - 특허 분석 리포트 생성

2. **AI 챗봇 API 개발** (`chat` 앱)
   - OpenAI API 연동
   - 특허 관련 질의응답
   - 대화 히스토리 관리

3. **검색 히스토리 API** (`history` 앱)
   - 사용자별 검색 기록
   - 즐겨찾기 기능
   - 분석 결과 저장

4. **프론트엔드 완성** (Next.js)
   - 대시보드 페이지
   - 특허 검색 인터페이스
   - 분석 결과 시각화

---

## 📞 도움이 필요하면

- **Django 공식 문서**: https://docs.djangoproject.com/
- **DRF 공식 문서**: https://www.django-rest-framework.org/
- **PostgreSQL 공식 문서**: https://www.postgresql.org/docs/
- **JWT 공식 문서**: https://django-rest-framework-simplejwt.readthedocs.io/

**추가 도움이 필요하시면 언제든지 문의해주세요!**
