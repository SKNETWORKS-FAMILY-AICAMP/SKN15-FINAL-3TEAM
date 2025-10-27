# 관리자 회원가입 가이드

## 📋 개요

이 문서는 부서 관리자(dept_admin)와 슈퍼 관리자(super_admin) 회원가입 방법을 설명합니다.

---

## 🔐 관리자 승인 코드

### 코드 종류

| 코드 | 역할 | 상태 | 설명 |
|------|------|------|------|
| `DEPT_ADMIN_2025` | 부서 관리자 | pending | 슈퍼 관리자 승인 필요 |
| `SUPER_ADMIN_2025` | 슈퍼 관리자 | active | 즉시 활성화 |

**⚠️ 주의:** 이 코드는 보안을 위해 주기적으로 변경해야 합니다.

---

## 🎯 관리자 회원가입 프로세스

### 1. 부서 관리자 (dept_admin)

#### 회원가입 절차
1. http://localhost:3000/admin-register 접속
2. 필수 정보 입력:
   - 아이디
   - 이메일
   - 비밀번호
   - 성/이름 (선택)
   - 연락처 (선택)
   - 직책/직급 (선택)
   - 회사
   - 부서
   - **관리자 승인 코드: `DEPT_ADMIN_2025`**

3. "관리자로 회원가입" 버튼 클릭
4. **상태: pending** (슈퍼 관리자 승인 대기)

#### 승인 절차
1. 슈퍼 관리자가 Django Admin 또는 API를 통해 승인
2. 상태를 `pending` → `active`로 변경
3. 이후 로그인 가능

### 2. 슈퍼 관리자 (super_admin)

#### 회원가입 절차
1. http://localhost:3000/admin-register 접속
2. 필수 정보 입력 (부서 관리자와 동일)
3. **관리자 승인 코드: `SUPER_ADMIN_2025`**
4. "관리자로 회원가입" 버튼 클릭
5. **상태: active** (즉시 활성화)
6. JWT 토큰 자동 발급
7. 대시보드로 자동 리다이렉트

---

## 📝 입력 필드 상세

### 필수 필드

| 필드 | 타입 | 설명 | DB 컬럼 |
|------|------|------|---------|
| 아이디 | text | 고유한 사용자명 | `username` |
| 이메일 | email | 고유한 이메일 | `email` |
| 비밀번호 | password | 최소 8자 이상 | `password_hash` |
| 비밀번호 확인 | password | 비밀번호와 일치 | - |
| 회사 | select | Company 테이블 참조 | `company_id` (FK) |
| 부서 | select | Department 테이블 참조 | `department_id` (FK) |
| 관리자 승인 코드 | password | 관리자 코드 | - |

### 선택 필드

| 필드 | 타입 | 설명 | DB 컬럼 |
|------|------|------|---------|
| 성 | text | 예: 홍 | `last_name` |
| 이름 | text | 예: 길동 | `first_name` |
| 연락처 | tel | 예: 010-1234-5678 | - (미저장) |
| 직책/직급 | text | 예: 부서장, 팀장 | - (미저장) |

**참고:** 연락처와 직책은 현재 DB에 저장되지 않습니다. 필요 시 UserProfile 모델 추가 가능.

---

## 🔌 API 엔드포인트

### 요청

**URL:** `POST /api/accounts/admin/register/`

**Headers:**
```
Content-Type: application/json
```

**Body:**
```json
{
  "username": "admin1",
  "email": "admin1@tech.com",
  "password": "Admin1234!",
  "password_confirm": "Admin1234!",
  "first_name": "길동",
  "last_name": "홍",
  "phone": "010-1234-5678",
  "position": "부서장",
  "admin_code": "DEPT_ADMIN_2025",
  "company": 1,
  "department": 1
}
```

### 응답 (부서 관리자)

**성공 (201 Created):**
```json
{
  "message": "부서 관리자로 회원가입이 완료되었습니다. 슈퍼 관리자의 승인 후 사용 가능합니다.",
  "user": {
    "user_id": "123e4567-e89b-12d3-a456-426614174000",
    "username": "admin1",
    "email": "admin1@tech.com",
    "first_name": "길동",
    "last_name": "홍",
    "full_name": "홍길동",
    "company": 1,
    "company_name": "테크 주식회사",
    "department": 1,
    "department_name": "연구개발팀",
    "role": "dept_admin",
    "status": "pending"
  },
  "tokens": null
}
```

### 응답 (슈퍼 관리자)

**성공 (201 Created):**
```json
{
  "message": "슈퍼 관리자로 회원가입이 완료되었습니다. 즉시 로그인 가능합니다.",
  "user": {
    "user_id": "234e5678-f89b-12d3-a456-426614174111",
    "username": "superadmin1",
    "email": "superadmin1@tech.com",
    "role": "super_admin",
    "status": "active"
  },
  "tokens": {
    "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc...",
    "access": "eyJ0eXAiOiJKV1QiLCJhbGc..."
  }
}
```

### 오류 응답

**잘못된 관리자 코드 (400 Bad Request):**
```json
{
  "admin_code": ["유효하지 않은 관리자 승인 코드입니다."]
}
```

**중복 아이디 (400 Bad Request):**
```json
{
  "username": ["이미 존재하는 사용자명입니다."]
}
```

**비밀번호 불일치 (400 Bad Request):**
```json
{
  "password_confirm": ["비밀번호가 일치하지 않습니다."]
}
```

---

## ✅ 테스트 시나리오

### 시나리오 1: 부서 관리자 회원가입

```bash
# 1. 부서 관리자로 회원가입
curl -X POST http://localhost:8000/api/accounts/admin/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "deptadmin1",
    "email": "deptadmin1@tech.com",
    "password": "Dept1234!",
    "password_confirm": "Dept1234!",
    "first_name": "길동",
    "last_name": "홍",
    "phone": "010-1234-5678",
    "position": "부서장",
    "admin_code": "DEPT_ADMIN_2025",
    "company": 1,
    "department": 1
  }'

# 2. DB 확인
psql -U postgres -d patent_db
SELECT username, email, role, status FROM "user" WHERE username = 'deptadmin1';

# 예상 결과:
#  username    |        email         |    role    | status
#  deptadmin1  | deptadmin1@tech.com  | dept_admin | pending

# 3. 슈퍼 관리자가 승인
UPDATE "user"
SET status = 'active'
WHERE username = 'deptadmin1';

# 4. 로그인 테스트
curl -X POST http://localhost:8000/api/accounts/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "deptadmin1",
    "password": "Dept1234!"
  }'
```

### 시나리오 2: 슈퍼 관리자 회원가입

```bash
# 1. 슈퍼 관리자로 회원가입
curl -X POST http://localhost:8000/api/accounts/admin/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "superadmin1",
    "email": "superadmin1@tech.com",
    "password": "Super1234!",
    "password_confirm": "Super1234!",
    "first_name": "관리자",
    "last_name": "최고",
    "admin_code": "SUPER_ADMIN_2025",
    "company": 1,
    "department": 1
  }'

# 2. 응답에 토큰 포함됨 (즉시 로그인 가능)
# {
#   "message": "슈퍼 관리자로 회원가입이 완료되었습니다...",
#   "tokens": {
#     "access": "...",
#     "refresh": "..."
#   }
# }

# 3. DB 확인
psql -U postgres -d patent_db
SELECT username, email, role, status FROM "user" WHERE username = 'superadmin1';

# 예상 결과:
#  username     |         email          |     role     | status
#  superadmin1  | superadmin1@tech.com   | super_admin  | active
```

### 시나리오 3: 잘못된 관리자 코드

```bash
curl -X POST http://localhost:8000/api/accounts/admin/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testadmin",
    "email": "testadmin@tech.com",
    "password": "Test1234!",
    "password_confirm": "Test1234!",
    "admin_code": "WRONG_CODE",
    "company": 1,
    "department": 1
  }'

# 예상 응답 (400 Bad Request):
# {
#   "admin_code": ["유효하지 않은 관리자 승인 코드입니다."]
# }
```

---

## 🔒 보안 고려사항

### 1. 관리자 코드 관리

**현재 방식:**
- 하드코딩: `DEPT_ADMIN_2025`, `SUPER_ADMIN_2025`

**권장 방식:**
```python
# settings.py 또는 .env 파일에서 관리
DEPT_ADMIN_CODE = os.getenv('DEPT_ADMIN_CODE', 'DEPT_ADMIN_2025')
SUPER_ADMIN_CODE = os.getenv('SUPER_ADMIN_CODE', 'SUPER_ADMIN_2025')
```

### 2. 코드 변경 주기

- 월별 또는 분기별로 코드 변경 권장
- 변경 시 기존 관리자에게 공지

### 3. 로깅

- 관리자 회원가입 시도 로그 기록
- 실패한 코드 입력 시도 모니터링

---

## 📊 관리자 역할 비교

| 구분 | user | dept_admin | super_admin |
|------|------|------------|-------------|
| 회원가입 방법 | 일반 회원가입 | 관리자 코드 필요 | 관리자 코드 필요 |
| 초기 상태 | pending | pending | **active** |
| 승인 필요 | ✅ 필요 | ✅ 필요 | ❌ 불필요 |
| 부서 내 사용자 관리 | ❌ | ✅ | ✅ |
| 전체 사용자 관리 | ❌ | ❌ | ✅ |
| 사용자 승인 | ❌ | ❌ | ✅ |
| 역할 변경 | ❌ | ❌ | ✅ |
| 비밀번호 초기화 | ❌ | ❌ | ✅ |

---

## 🛠️ 커스터마이징

### 1. 추가 정보 필드 저장

연락처와 직책을 DB에 저장하려면 UserProfile 모델 추가:

```python
# models.py
class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    phone = models.CharField('연락처', max_length=20, blank=True)
    position = models.CharField('직책/직급', max_length=100, blank=True)
    # 기타 추가 필드...
```

### 2. 이메일 인증 추가

관리자 회원가입 시 이메일 인증 단계 추가 가능.

### 3. 2단계 인증 (2FA)

슈퍼 관리자에게는 2FA 필수 적용 권장.

---

## 📚 관련 문서

- [SETUP_GUIDE.md](SETUP_GUIDE.md) - 전체 설정 가이드
- [CONDA_SETUP.md](CONDA_SETUP.md) - Conda 가상환경 가이드
- [test_app/FRONTEND_GUIDE.md](../test_app/FRONTEND_GUIDE.md) - 프론트엔드 가이드

---

**작성일:** 2025-10-22
**버전:** 1.0
**관리자 코드 갱신일:** 2025-10-22
