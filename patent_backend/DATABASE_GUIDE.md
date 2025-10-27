# 📊 데이터베이스 구조 및 역할 완벽 가이드

## 🎯 목차
1. [테이블 구조 이해하기](#1-테이블-구조-이해하기)
2. [데이터 흐름 예시](#2-데이터-흐름-예시)
3. [자동 설정 방법](#3-자동-설정-방법)
4. [수동 설정 방법](#4-수동-설정-방법)

---

## 1. 테이블 구조 이해하기

### 📋 전체 구조 (5개 테이블)

```
users (사용자 정보)
  ↓
userrolemap (사용자 ↔ 역할 연결)
  ↓
roles (역할 정의)
  ↓
rolepermissionmap (역할 ↔ 권한 연결)
  ↓
permissions (권한 정의)
```

---

### 1️⃣ users 테이블 (사용자 기본 정보)

**역할**: 회원가입한 사용자의 정보 저장

| 컬럼 | 타입 | 필수 | 설명 | 예시 값 |
|------|------|------|------|---------|
| `id` | SERIAL | ✅ | 사용자 고유 번호 (자동 생성) | 1, 2, 3... |
| `userid` | VARCHAR(50) | ✅ | 로그인 ID (중복 불가) | "testuser", "admin" |
| `password` | VARCHAR(255) | ✅ | 비밀번호 (해시 저장) | "pbkdf2_sha256$..." |
| `team` | VARCHAR(50) | ❌ | 소속 팀/부서 | "개발팀", "기획팀" |
| `email` | VARCHAR(254) | ❌ | 이메일 주소 | "test@example.com" |
| `first_name` | VARCHAR(150) | ❌ | 이름 | "길동" |
| `last_name` | VARCHAR(150) | ❌ | 성 | "홍" |
| `is_staff` | BOOLEAN | ✅ | 관리자 페이지 접근 가능 여부 | true, false |
| `is_active` | BOOLEAN | ✅ | 계정 활성화 여부 | true, false |
| `is_superuser` | BOOLEAN | ✅ | 최고 관리자 여부 (모든 권한) | true, false |
| `last_login` | TIMESTAMP | ❌ | 마지막 로그인 시간 | 2025-10-21 10:30:00 |
| `createdat` | TIMESTAMP | ✅ | 계정 생성일 | 2025-10-21 10:00:00 |
| `updatedat` | TIMESTAMP | ✅ | 정보 수정일 | 2025-10-21 11:00:00 |
| `date_joined` | TIMESTAMP | ✅ | 가입일 (Django 용) | 2025-10-21 10:00:00 |

**샘플 데이터:**
```sql
INSERT INTO users (userid, password, email, team, is_active) VALUES
('testuser', 'hashed_password_here', 'test@example.com', '개발팀', true);
```

---

### 2️⃣ roles 테이블 (역할 정의)

**역할**: 시스템에서 사용할 역할 종류 정의 (예: 관리자, 연구원, 기획자)

| 컬럼 | 타입 | 필수 | 설명 | 예시 값 |
|------|------|------|------|---------|
| `roleid` | SERIAL | ✅ | 역할 고유 번호 (자동 생성) | 1, 2, 3 |
| `rolename` | VARCHAR(50) | ✅ | 역할 이름 (중복 불가) | "admin", "researcher" |
| `description` | TEXT | ❌ | 역할 설명 | "관리자 - 모든 권한 보유" |
| `createdat` | TIMESTAMP | ✅ | 역할 생성일 | 2025-10-21 10:00:00 |

**기본 역할 3개:**
```sql
INSERT INTO roles (rolename, description) VALUES
('researcher', '연구원 - 특허 검색 및 분석'),
('planner', '기획자 - 특허 분석 및 보고서 작성'),
('admin', '관리자 - 모든 권한 및 사용자 관리');
```

---

### 3️⃣ permissions 테이블 (권한 정의)

**역할**: 시스템에서 수행 가능한 작업 정의 (예: 특허 조회, 사용자 삭제)

| 컬럼 | 타입 | 필수 | 설명 | 예시 값 |
|------|------|------|------|---------|
| `permissionid` | SERIAL | ✅ | 권한 고유 번호 (자동 생성) | 1, 2, 3 |
| `permissionname` | VARCHAR(100) | ✅ | 권한 이름 (중복 불가) | "view_patent", "delete_user" |
| `description` | TEXT | ❌ | 권한 설명 | "특허 조회 권한" |
| `createdat` | TIMESTAMP | ✅ | 권한 생성일 | 2025-10-21 10:00:00 |

**기본 권한 6개:**
```sql
INSERT INTO permissions (permissionname, description) VALUES
('view_patent', '특허 조회'),
('search_patent', '특허 검색'),
('export_patent', '특허 내보내기'),
('use_ai_chat', 'AI 챗봇 사용'),
('manage_users', '사용자 관리 (관리자 전용)'),
('view_history', '검색 히스토리 조회');
```

---

### 4️⃣ userrolemap 테이블 (사용자 ↔ 역할 연결)

**역할**: "누가 어떤 역할을 가지는가?" 연결

| 컬럼 | 타입 | 필수 | 설명 | 예시 값 |
|------|------|------|------|---------|
| `userid` | INT | ✅ | 사용자 ID (users.id 참조) | 1 |
| `roleid` | INT | ✅ | 역할 ID (roles.roleid 참조) | 2 |
| **복합 기본키** | (userid, roleid) | - | 중복 방지 | (1, 2) 한 번만 가능 |

**예시:**
- 사용자 ID 1번이 역할 "researcher" (roleid=1) 보유
- 사용자 ID 2번이 역할 "admin" (roleid=3) 보유

```sql
-- testuser에게 researcher 역할 부여
INSERT INTO userrolemap (userid, roleid) VALUES
(1, 1);  -- userid=1(testuser), roleid=1(researcher)
```

---

### 5️⃣ rolepermissionmap 테이블 (역할 ↔ 권한 연결)

**역할**: "어떤 역할이 어떤 권한을 가지는가?" 연결

| 컬럼 | 타입 | 필수 | 설명 | 예시 값 |
|------|------|------|------|---------|
| `roleid` | INT | ✅ | 역할 ID (roles.roleid 참조) | 1 |
| `permissionid` | INT | ✅ | 권한 ID (permissions.permissionid 참조) | 3 |
| **복합 기본키** | (roleid, permissionid) | - | 중복 방지 | (1, 3) 한 번만 가능 |

**예시:**
- 역할 "researcher"가 권한 "view_patent", "search_patent" 보유
- 역할 "admin"이 모든 권한 보유

```sql
-- researcher 역할에 view_patent 권한 부여
INSERT INTO rolepermissionmap (roleid, permissionid) VALUES
(1, 1);  -- roleid=1(researcher), permissionid=1(view_patent)
```

---

## 2. 데이터 흐름 예시

### 시나리오: "testuser가 특허를 검색할 수 있나?"

**데이터 흐름:**
```
1. users 테이블에서 testuser 조회
   → id = 1

2. userrolemap 테이블에서 userid=1의 역할 조회
   → roleid = 2 (researcher)

3. rolepermissionmap 테이블에서 roleid=2의 권한 조회
   → permissionid = 2 (search_patent)

4. permissions 테이블에서 permissionid=2 조회
   → permissionname = "search_patent" ✅

결론: testuser는 특허를 검색할 수 있다!
```

**SQL 쿼리:**
```sql
-- testuser가 보유한 모든 권한 조회
SELECT
    u.userid,
    r.rolename,
    p.permissionname,
    p.description
FROM users u
JOIN userrolemap urm ON u.id = urm.userid
JOIN roles r ON urm.roleid = r.roleid
JOIN rolepermissionmap rpm ON r.roleid = rpm.roleid
JOIN permissions p ON rpm.permissionid = p.permissionid
WHERE u.userid = 'testuser';
```

**결과:**
```
 userid   | rolename   | permissionname  | description
----------|------------|-----------------|------------------
testuser  | researcher | view_patent     | 특허 조회
testuser  | researcher | search_patent   | 특허 검색
testuser  | researcher | use_ai_chat     | AI 챗봇 사용
testuser  | researcher | view_history    | 검색 히스토리 조회
```

---

## 3. 자동 설정 방법 (추천!)

### 🚀 한 번에 모든 설정 완료

```bash
# PostgreSQL 서버 시작
sudo service postgresql start

# 자동 설정 스크립트 실행
bash backend/setup_database.sh

# 입력 사항:
# - 데이터베이스 이름: patent_analysis (기본값)
# - 사용자 이름: patentuser (기본값)
# - 비밀번호: 원하는 비밀번호 입력
```

**이 스크립트가 자동으로 처리:**
1. ✅ PostgreSQL 데이터베이스 생성
2. ✅ PostgreSQL 사용자 생성 및 권한 부여
3. ✅ 5개 테이블 생성 (users, roles 등)
4. ✅ 초기 데이터 삽입 (3개 역할, 6개 권한)
5. ✅ 역할-권한 매핑 자동 설정
6. ✅ .env 파일 자동 업데이트
7. ✅ Django 마이그레이션 실행

**완료 후:**
```bash
cd backend
python manage.py createsuperuser
python manage.py runserver
```

---

## 4. 수동 설정 방법

### 방법 1: SQL 파일 사용

```bash
# PostgreSQL 서버 시작
sudo service postgresql start

# PostgreSQL 접속
sudo -u postgres psql

# 데이터베이스 및 사용자 생성
CREATE DATABASE patent_analysis;
CREATE USER patentuser WITH PASSWORD 'yourpassword';
GRANT ALL PRIVILEGES ON DATABASE patent_analysis TO patentuser;
\q

# 테이블 생성 (SQL 파일 실행)
sudo -u postgres psql -d patent_analysis -f backend/create_tables.sql

# .env 파일 수정
nano backend/.env
# DATABASE_URL=postgresql://patentuser:yourpassword@localhost:5432/patent_analysis

# Django 마이그레이션
cd backend
python manage.py migrate --fake-initial
python manage.py migrate
```

### 방법 2: 테이블별 직접 생성

`START_HERE.md` 파일의 Step 3 참고

---

## 5. 데이터 확인 방법

### PostgreSQL에서 직접 확인

```bash
# PostgreSQL 접속
sudo -u postgres psql -d patent_analysis
```

```sql
-- 테이블 목록 확인
\dt

-- 각 테이블 구조 확인
\d users
\d roles
\d permissions

-- 데이터 확인
SELECT * FROM roles;
SELECT * FROM permissions;

-- 역할별 권한 조회
SELECT
    r.rolename,
    p.permissionname
FROM rolepermissionmap rpm
JOIN roles r ON rpm.roleid = r.roleid
JOIN permissions p ON rpm.permissionid = p.permissionid
ORDER BY r.rolename;

-- 종료
\q
```

---

## 6. Django에서 사용 방법

### 사용자 권한 확인

```python
# accounts/models.py에 이미 구현됨!

# 역할 확인
user.has_role('admin')  # True or False

# 권한 확인
user.has_permission('view_patent')  # True or False

# 관리자 여부
user.is_admin_user  # True or False
```

### API에서 권한 확인

```python
# accounts/views.py 예시

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def search_patents(request):
    # 권한 확인
    if not request.user.has_permission('search_patent'):
        return Response({'error': '권한이 없습니다.'}, status=403)

    # 검색 로직...
    return Response({'results': [...]})
```

---

## 7. 자주 묻는 질문 (FAQ)

### Q1. 역할과 권한의 차이는?
**A:**
- **역할 (Role)**: 사용자의 직책/역할 (예: 관리자, 연구원)
- **권한 (Permission)**: 수행 가능한 작업 (예: 특허 조회, 사용자 삭제)
- 하나의 역할은 여러 권한을 가질 수 있음

### Q2. 한 사용자가 여러 역할을 가질 수 있나?
**A:** 네! `userrolemap` 테이블로 N:M 관계 지원
```sql
-- testuser에게 researcher와 planner 역할 동시 부여
INSERT INTO userrolemap (userid, roleid) VALUES
(1, 1),  -- researcher
(1, 2);  -- planner
```

### Q3. 새로운 권한을 추가하려면?
**A:**
```sql
-- 1. 권한 정의 추가
INSERT INTO permissions (permissionname, description) VALUES
('delete_patent', '특허 삭제 권한');

-- 2. admin 역할에 이 권한 부여
INSERT INTO rolepermissionmap (roleid, permissionid)
SELECT r.roleid, p.permissionid
FROM roles r, permissions p
WHERE r.rolename = 'admin'
  AND p.permissionname = 'delete_patent';
```

### Q4. 테이블을 완전히 삭제하고 다시 만들려면?
**A:**
```bash
# create_tables.sql 파일이 자동으로 DROP 후 재생성
sudo -u postgres psql -d patent_analysis -f backend/create_tables.sql
```

---

## 8. 트러블슈팅

### 문제: "relation does not exist"
```bash
# 테이블이 생성되지 않음
sudo -u postgres psql -d patent_analysis -f backend/create_tables.sql
```

### 문제: "permission denied"
```bash
# 사용자 권한 부여
sudo -u postgres psql
GRANT ALL PRIVILEGES ON DATABASE patent_analysis TO patentuser;
GRANT ALL ON SCHEMA public TO patentuser;
\q
```

### 문제: Django에서 권한 확인 안 됨
```python
# 사용자에게 역할 할당 확인
python manage.py shell

from accounts.models import User, Role, UserRoleMap
user = User.objects.get(userid='testuser')
print(user.roles.all())  # 역할 목록 출력
```

---

## 🎉 요약

1. **5개 테이블**: users, roles, permissions, userrolemap, rolepermissionmap
2. **자동 설정**: `bash backend/setup_database.sh`
3. **수동 설정**: `sudo -u postgres psql -d patent_analysis -f backend/create_tables.sql`
4. **Django 사용**: `user.has_role()`, `user.has_permission()`

**다음 단계:**
```bash
cd backend
python manage.py createsuperuser
python manage.py runserver
curl http://localhost:8000/api/auth/health/
```
