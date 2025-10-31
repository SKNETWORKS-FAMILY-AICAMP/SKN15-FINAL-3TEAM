# RDS 슈퍼 관리자 생성 가이드

RDS 또는 새로운 데이터베이스에서 슈퍼 관리자를 생성하는 3가지 방법을 제공합니다.

---

## 방법 1: 환경 변수 사용 (권장 - CI/CD)

### 사용 시나리오
- AWS ECS, Lambda, EC2 등에서 배포할 때
- GitHub Actions, GitLab CI 등 CI/CD 파이프라인
- 환경 변수로 비밀번호를 안전하게 관리

### 사용 방법

```bash
# 1. 환경 변수 설정
export SUPER_USERNAME=admin
export SUPER_EMAIL=admin@company.com
export SUPER_PASSWORD=your_secure_password
export SUPER_COMPANY_NAME=회사명
export SUPER_COMPANY_DOMAIN=company.com       # 선택사항
export SUPER_DEPARTMENT_NAME=개발팀            # 선택사항
export SUPER_FIRST_NAME=관리자                 # 선택사항
export SUPER_LAST_NAME=시스템                  # 선택사항

# 2. 스크립트 실행
python create_rds_superuser.py
```

### AWS Secrets Manager와 함께 사용

```bash
# AWS Secrets Manager에서 비밀번호 가져오기
export SUPER_PASSWORD=$(aws secretsmanager get-secret-value \
  --secret-id rds/superuser/password \
  --query SecretString \
  --output text)

# 다른 환경 변수 설정
export SUPER_USERNAME=admin
export SUPER_EMAIL=admin@company.com
export SUPER_COMPANY_NAME=회사명

# 스크립트 실행
python create_rds_superuser.py
```

---

## 방법 2: JSON 설정 파일 사용 (권장 - 로컬/개발)

### 사용 시나리오
- 로컬 개발 환경
- 여러 관리자를 한 번에 생성
- 설정을 파일로 관리하고 싶을 때

### 사용 방법

```bash
# 1. 예제 파일 복사
cp superuser_config.json.example superuser_config.json

# 2. 설정 파일 수정
vim superuser_config.json
```

**superuser_config.json 예시**:
```json
{
  "username": "admin",
  "email": "admin@example.com",
  "password": "your_secure_password_here",
  "company": {
    "name": "회사명",
    "domain": "example.com"
  },
  "department": {
    "name": "개발팀"
  },
  "first_name": "관리자",
  "last_name": "시스템"
}
```

```bash
# 3. 스크립트 실행
python create_superuser_from_json.py

# 또는 커스텀 설정 파일 사용
python create_superuser_from_json.py --config my_config.json
```

**⚠️ 주의**: `superuser_config.json`은 비밀번호가 포함되어 있으므로 **절대 git에 커밋하지 마세요**! (이미 .gitignore에 추가됨)

---

## 방법 3: Django Shell 사용 (기본)

### 사용 시나리오
- 빠르게 테스트할 때
- 한 번만 실행하면 될 때
- 대화형으로 작업하고 싶을 때

### 사용 방법

```bash
# Django Shell 실행
python manage.py shell
```

```python
from accounts.models import User, Company, Department

# 회사 생성
company, _ = Company.objects.get_or_create(
    name="회사명",
    defaults={'domain': 'company.com'}
)

# 부서 생성 (선택사항)
dept, _ = Department.objects.get_or_create(
    company=company,
    name="개발팀"
)

# 슈퍼 관리자 생성
user = User.objects.create_superuser(
    username='admin',
    email='admin@company.com',
    password='your_secure_password',
    company=company,
    department=dept,
    first_name='관리자',
    last_name='시스템'
)

print(f"✅ 슈퍼 관리자 생성: {user.username}")
```

---

## 방법 4: Django Management Command (대화형)

### 사용 방법

```bash
# 기존에 있는 대화형 명령어 사용
python manage.py createsuperuser_with_company

# 또는 완전 초기 설정
python manage.py setup_initial_admin
```

이 방법은 대화형으로 입력을 받으므로 자동화에는 적합하지 않습니다.

---

## RDS 배포 전체 시나리오

### AWS RDS 초기 설정 + 슈퍼 관리자 생성

```bash
# 1. RDS 엔드포인트 정보 설정
export RDS_ENDPOINT=your-rds-endpoint.amazonaws.com
export RDS_USER=final_play
export RDS_PASSWORD=your_rds_password
export RDS_DATABASE=patentdb

# 2. 데이터베이스 스키마 적용
PGPASSWORD=$RDS_PASSWORD psql \
  -h $RDS_ENDPOINT \
  -U $RDS_USER \
  -d $RDS_DATABASE \
  -f initial_schema.sql

# 3. Django 마이그레이션 실행
python manage.py migrate

# 4. 슈퍼 관리자 생성 (환경 변수 방식)
export SUPER_USERNAME=admin
export SUPER_EMAIL=admin@company.com
export SUPER_PASSWORD=secure_password
export SUPER_COMPANY_NAME=회사명
python create_rds_superuser.py
```

---

## CI/CD 파이프라인 예시

### GitHub Actions

```yaml
name: Deploy to RDS

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Apply Database Schema
        run: |
          PGPASSWORD=${{ secrets.RDS_PASSWORD }} psql \
            -h ${{ secrets.RDS_ENDPOINT }} \
            -U ${{ secrets.RDS_USER }} \
            -d ${{ secrets.RDS_DATABASE }} \
            -f initial_schema.sql

      - name: Run Migrations
        run: python manage.py migrate
        env:
          DB_HOST: ${{ secrets.RDS_ENDPOINT }}
          DB_USER: ${{ secrets.RDS_USER }}
          DB_PASSWORD: ${{ secrets.RDS_PASSWORD }}
          DB_NAME: ${{ secrets.RDS_DATABASE }}

      - name: Create Superuser
        run: python create_rds_superuser.py
        env:
          SUPER_USERNAME: ${{ secrets.SUPER_USERNAME }}
          SUPER_EMAIL: ${{ secrets.SUPER_EMAIL }}
          SUPER_PASSWORD: ${{ secrets.SUPER_PASSWORD }}
          SUPER_COMPANY_NAME: ${{ secrets.SUPER_COMPANY_NAME }}
          DB_HOST: ${{ secrets.RDS_ENDPOINT }}
          DB_USER: ${{ secrets.RDS_USER }}
          DB_PASSWORD: ${{ secrets.RDS_PASSWORD }}
          DB_NAME: ${{ secrets.RDS_DATABASE }}
```

---

## 보안 주의사항

### ✅ DO (해야 할 것)

1. **환경 변수 사용**
   - 비밀번호는 환경 변수나 비밀 관리 서비스 사용
   - AWS Secrets Manager, HashiCorp Vault 등 활용

2. **강력한 비밀번호**
   - 최소 12자 이상
   - 대소문자, 숫자, 특수문자 조합

3. **설정 파일 보호**
   - `superuser_config.json`은 절대 git에 커밋하지 않기
   - `.gitignore`에 추가 확인

4. **로그 주의**
   - CI/CD 로그에 비밀번호가 노출되지 않도록 주의

### ❌ DON'T (하지 말아야 할 것)

1. ❌ 비밀번호를 코드에 직접 하드코딩
2. ❌ `superuser_config.json`을 git에 커밋
3. ❌ 프로덕션에서 약한 비밀번호 사용 (admin, 1234 등)
4. ❌ 로그에 비밀번호 출력

---

## 트러블슈팅

### 문제: "사용자명이 이미 존재합니다"

**해결**:
```bash
# Django Shell에서 기존 사용자 삭제
python manage.py shell
```

```python
from accounts.models import User
User.objects.filter(username='admin').delete()
```

또는 `create_superuser_from_json.py`를 사용하면 대화형으로 삭제 여부를 물어봅니다.

### 문제: "Company matching query does not exist"

**원인**: `initial_schema.sql`이 실행되지 않음

**해결**:
```bash
PGPASSWORD=$RDS_PASSWORD psql \
  -h $RDS_ENDPOINT \
  -U $RDS_USER \
  -d $RDS_DATABASE \
  -f initial_schema.sql
```

### 문제: "DJANGO_SETTINGS_MODULE is not set"

**해결**:
```bash
export DJANGO_SETTINGS_MODULE=config.settings
python create_rds_superuser.py
```

---

## 파일 설명

| 파일 | 용도 | Git 추적 |
|------|------|---------|
| `create_rds_superuser.py` | 환경 변수 기반 생성 스크립트 | ✅ |
| `create_superuser_from_json.py` | JSON 파일 기반 생성 스크립트 | ✅ |
| `superuser_config.json.example` | JSON 설정 예제 | ✅ |
| `superuser_config.json` | 실제 설정 파일 (비밀번호 포함) | ❌ (.gitignore) |
| `initial_schema.sql` | DB 초기 스키마 | ✅ |
| `RDS_SUPERUSER_GUIDE.md` | 이 문서 | ✅ |

---

## 요약

**로컬 개발**: 방법 2 (JSON 파일) 또는 방법 3 (Django Shell)
**RDS 배포**: 방법 1 (환경 변수)
**CI/CD**: 방법 1 (환경 변수) + GitHub Secrets
**테스트**: 방법 3 (Django Shell) 또는 방법 4 (Management Command)
