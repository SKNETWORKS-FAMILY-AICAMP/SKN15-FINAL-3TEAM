# 🔄 새로운 데이터베이스 구조로 마이그레이션 가이드

## 현재 상황

- ✅ Django 모델은 새로운 Company-Department-User 구조로 변경됨
- ❌ PostgreSQL에는 아직 이전 역할 기반 테이블만 존재
- ❌ Django 마이그레이션 파일이 이전 구조로 되어 있음

## 📋 마이그레이션 단계

### 1단계: PostgreSQL에 새 테이블 생성

#### 방법 1: psql 명령어로 직접 실행 (권장)

```bash
# PostgreSQL postgres 사용자로 실행
sudo -u postgres psql -d patentdb -f /home/juhyeong/workspace/final_project/backend/create_new_tables_patentdb.sql
```

#### 방법 2: 일반 사용자로 실행 (비밀번호 필요)

```bash
# 비밀번호 입력이 필요한 경우
psql -U final_play -d patentdb -h localhost -f /home/juhyeong/workspace/final_project/backend/create_new_tables_patentdb.sql
```

비밀번호를 모르는 경우, PostgreSQL 관리자로 재설정:
```bash
sudo -u postgres psql
ALTER USER final_play WITH PASSWORD 'new_password';
\q

# .env 파일 업데이트
sed -i 's/yourpassword/new_password/' /home/juhyeong/workspace/final_project/backend/.env
```

---

### 2단계: 테이블 생성 확인

```bash
sudo -u postgres psql -d patentdb -c "\dt"
```

**예상 결과:**
```
 Schema |        Name              | Type  |   Owner
--------+--------------------------+-------+------------
 public | admin_request            | table | final_play
 public | company                  | table | final_play  ← 새 테이블
 public | department               | table | final_play  ← 새 테이블
 public | password_reset_request   | table | final_play  ← 새 테이블
 public | user                     | table | final_play  ← 새 테이블
 public | users (이전)              | table | final_play
 public | roles (이전)              | table | final_play
 ... (기존 테이블들)
```

---

### 3단계: Django 마이그레이션 생성 및 실행

```bash
cd /home/juhyeong/workspace/final_project/backend

# Conda 환경 활성화
source ~/miniconda3/etc/profile.d/conda.sh
conda activate patent_backend

# 마이그레이션 생성
python manage.py makemigrations accounts

# 마이그레이션 실행 (fake-initial: 이미 테이블이 있으므로)
python manage.py migrate accounts --fake-initial

# 나머지 앱 마이그레이션
python manage.py migrate
```

---

### 4단계: 슈퍼 관리자 계정 생성

```bash
python manage.py createsuperuser
```

**입력 예시:**
```
Username: admin
Email: admin@example.com
Password: ********
Password (again): ********
Company ID: 1
Department ID (선택): 1
```

---

### 5단계: 데이터 검증

#### Django Shell에서 확인
```bash
python manage.py shell
```

```python
from accounts.models import Company, Department, User

# 회사 목록
companies = Company.objects.all()
for c in companies:
    print(f"{c.company_id}: {c.name}")

# 부서 목록
departments = Department.objects.all()
for d in departments:
    print(f"{d.department_id}: {d.company.name} - {d.name}")

# 사용자 목록
users = User.objects.all()
for u in users:
    print(f"{u.username} - {u.role} - {u.status}")
```

#### PostgreSQL에서 확인
```bash
sudo -u postgres psql -d patentdb
```

```sql
-- 회사 목록
SELECT * FROM company;

-- 회사별 부서 및 사용자 수
SELECT
    c.name as company_name,
    COUNT(DISTINCT d.department_id) as dept_count,
    COUNT(DISTINCT u.user_id) as user_count
FROM company c
LEFT JOIN department d ON c.company_id = d.company_id
LEFT JOIN "user" u ON c.company_id = u.company_id
GROUP BY c.company_id, c.name;

-- 전체 사용자 및 역할
SELECT username, email, role, status, c.name as company
FROM "user" u
JOIN company c ON u.company_id = c.company_id;
```

---

### 6단계: Django 서버 실행 및 테스트

```bash
# 서버 실행
python manage.py runserver

# 다른 터미널에서 API 테스트
curl http://localhost:8000/api/accounts/companies/
curl http://localhost:8000/api/accounts/departments/
```

---

## 🔧 문제 해결

### 문제 1: "relation does not exist" 오류

**원인:** PostgreSQL에 테이블이 생성되지 않음

**해결:**
```bash
sudo -u postgres psql -d patentdb -f /home/juhyeong/workspace/final_project/backend/create_new_tables_patentdb.sql
```

---

### 문제 2: "type already exists" 오류

**원인:** ENUM 타입이 이미 존재

**해결:** SQL 스크립트가 이미 `IF NOT EXISTS` 처리되어 있으므로 무시 가능

---

### 문제 3: "password authentication failed" 오류

**원인:** PostgreSQL 비밀번호가 .env 파일과 다름

**해결:**
```bash
# 비밀번호 재설정
sudo -u postgres psql
ALTER USER final_play WITH PASSWORD 'new_password';
\q

# .env 파일 업데이트
nano /home/juhyeong/workspace/final_project/backend/.env
# DATABASE_URL 수정
```

---

### 문제 4: Django 마이그레이션 충돌

**원인:** 이전 마이그레이션과 충돌

**해결:**
```bash
# 마이그레이션 완전 초기화
cd /home/juhyeong/workspace/final_project/backend
rm -rf accounts/migrations/00*.py
python manage.py makemigrations accounts
python manage.py migrate accounts --fake-initial
```

---

## 📊 새 구조 vs 이전 구조

### 이전 구조 (Role-Based)
```
users → userrolemap → roles → rolepermissionmap → permissions
```

### 새 구조 (Company-Department-Based)
```
company → department → user
                       ├─ role (user/dept_admin/super_admin)
                       └─ status (active/pending/suspended)
```

**주요 차이점:**
- ✅ 회사/부서 계층 구조 추가
- ✅ 역할이 ENUM으로 단순화 (user, dept_admin, super_admin)
- ✅ 상태 관리 추가 (active, pending, suspended)
- ✅ UUID 기반 사용자 ID
- ✅ 부서 관리자 승인 워크플로우 추가

---

## ✅ 완료 체크리스트

- [ ] PostgreSQL에 새 테이블 생성 (company, department, user, admin_request, password_reset_request)
- [ ] Django 마이그레이션 파일 삭제 및 재생성
- [ ] Django 마이그레이션 실행 (--fake-initial)
- [ ] 슈퍼 관리자 계정 생성
- [ ] 회사/부서 데이터 확인
- [ ] Django 서버 실행 테스트
- [ ] API 엔드포인트 테스트
- [ ] 프론트엔드 연동 테스트

---

## 📞 다음 단계

마이그레이션이 완료되면:
1. Frontend 회원가입 페이지에서 회사/부서 선택 기능 테스트
2. 관리자 회원가입 페이지 테스트
3. 로그인 및 JWT 토큰 발급 테스트
4. 역할별 권한 확인

---

**작성일:** 2025-10-22
**Django 버전:** 5.2.7
**PostgreSQL 데이터베이스:** patentdb
