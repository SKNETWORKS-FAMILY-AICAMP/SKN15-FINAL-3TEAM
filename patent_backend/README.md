# Patent Analysis System - Django Backend

AI 기반 특허 분석 시스템의 Django REST API 백엔드입니다.

## 📁 프로젝트 구조

```
backend/
├── config/                  # Django 프로젝트 설정
│   ├── settings.py         # 메인 설정 파일 ✅
│   ├── urls.py             # URL 라우팅
│   ├── wsgi.py             # WSGI 엔트리포인트
│   └── asgi.py             # ASGI 엔트리포인트
├── accounts/                # 사용자 인증 앱 ✅
│   ├── models.py           # User 모델 ✅
│   ├── serializers.py      # DRF Serializers (작성 필요)
│   ├── views.py            # API Views (작성 필요)
│   └── urls.py             # URL 패턴 (작성 필요)
├── patents/                 # 특허 검색 앱
│   ├── models.py           # Patent 모델 (작성 필요)
│   ├── serializers.py
│   ├── views.py
│   └── urls.py
├── chat/                    # AI 챗봇 앱
│   ├── models.py           # Conversation, Message 모델 (작성 필요)
│   ├── services/           # AI 로직 (작성 필요)
│   ├── serializers.py
│   ├── views.py
│   └── urls.py
├── history/                 # 히스토리 앱
│   ├── models.py           # SearchHistory 모델 (작성 필요)
│   ├── serializers.py
│   ├── views.py
│   └── urls.py
├── manage.py               # Django CLI
├── requirements.txt        # 패키지 목록 ✅
├── .env.example            # 환경 변수 예시 ✅
├── DJANGO_SETUP_GUIDE.md  # 개발 가이드 ✅
└── README.md              # 이 파일
```

## ✅ 완료된 작업

1. **Django 프로젝트 초기화**
   - `django-admin startproject config .`
   - SQLite 데이터베이스로 시작 (나중에 PostgreSQL로 전환 가능)

2. **Django 앱 생성**
   - `accounts`: 사용자 인증 및 관리
   - `patents`: 특허 검색
   - `chat`: AI 챗봇
   - `history`: 검색/챗봇 히스토리

3. **설정 파일 구성** (`config/settings.py`)
   - Django REST Framework 설정
   - JWT 인증 (djangorestframework-simplejwt)
   - CORS 설정 (Next.js 프론트엔드 연동)
   - 커스텀 User 모델
   - API 문서화 (drf-spectacular)
   - 로깅 설정

4. **User 모델 작성** (`accounts/models.py`)
   - Django AbstractUser 확장
   - 필드: username, email, department, role, status
   - 역할: 연구원, 기획자, 관리자

5. **마이그레이션 실행**
   - 초기 데이터베이스 테이블 생성 완료
   - `users` 테이블 생성 완료

## 🚀 빠른 시작

### 1. conda 환경 활성화

```bash
conda activate final_project
cd backend
```

### 2. 추가 패키지 설치 (필요시)

```bash
pip install -r requirements.txt
```

### 3. 환경 변수 설정

```bash
# .env 파일 생성
cp .env.example .env

# 필요한 값 수정 (SECRET_KEY, DATABASE_URL 등)
nano .env
```

### 4. 관리자 계정 생성

```bash
python manage.py createsuperuser
# Username: admin
# Email: admin@example.com
# Password: (입력)
```

### 5. 서버 실행

```bash
# 개발 서버 시작
python manage.py runserver

# 또는 특정 포트로 실행
python manage.py runserver 8000
```

서버가 실행되면 다음 URL로 접속 가능:
- API Root: http://localhost:8000/api/
- Admin Panel: http://localhost:8000/admin/
- API 문서: http://localhost:8000/api/schema/ (설정 후)

## 📋 다음 단계 (개발 순서)

### Phase 1: 인증 API (accounts 앱)

1. **Serializers 작성** (`accounts/serializers.py`)
   ```python
   # UserSerializer, RegisterSerializer, LoginSerializer
   ```

2. **Views 작성** (`accounts/views.py`)
   ```python
   # RegisterView, LoginView, LogoutView, UserProfileView
   ```

3. **URLs 설정** (`accounts/urls.py`)
   ```python
   # POST /api/auth/register/
   # POST /api/auth/login/
   # POST /api/auth/logout/
   # GET  /api/auth/me/
   ```

4. **테스트**
   ```bash
   # 회원가입 테스트
   curl -X POST http://localhost:8000/api/auth/register/ \
     -H "Content-Type: application/json" \
     -d '{"username":"test","email":"test@example.com","password":"test1234","department":"개발팀"}'
   ```

### Phase 2: 특허 검색 API (patents 앱)

1. **Patent 모델 작성** (`patents/models.py`)
2. **Serializers 작성**
3. **Search API 구현**
4. **샘플 데이터 추가** (fixtures 또는 management command)

### Phase 3: AI 챗봇 API (chat 앱)

1. **Conversation, Message 모델 작성**
2. **OpenAI 통합** (`chat/services/`)
3. **4가지 챗봇 모드 구현**
   - 유사 특허 찾기
   - Q&A
   - 문서 첨삭
   - 트렌드 분석

### Phase 4: 히스토리 API (history 앱)

1. **SearchHistory 모델 작성**
2. **히스토리 저장/조회 API**

### Phase 5: 관리자 API

1. **통계 API** (`/api/admin/stats/`)
2. **사용자 관리 API** (`/api/admin/users/`)

## 🔧 유용한 명령어

```bash
# Django shell (DB 조작용)
python manage.py shell

# 새 마이그레이션 생성
python manage.py makemigrations

# 마이그레이션 적용
python manage.py migrate

# 슈퍼유저 생성
python manage.py createsuperuser

# 정적 파일 수집 (프로덕션용)
python manage.py collectstatic

# 테스트 실행 (pytest 사용)
pytest

# Django extensions 사용 (설치 후)
python manage.py show_urls  # 모든 URL 보기
python manage.py shell_plus  # 향상된 shell
```

## 📝 API 엔드포인트 (예정)

### 인증 (Auth)
```
POST   /api/auth/register/      # 회원가입
POST   /api/auth/login/         # 로그인 (JWT 토큰 발급)
POST   /api/auth/refresh/       # 토큰 갱신
GET    /api/auth/me/            # 현재 사용자 정보
```

### 특허 (Patents)
```
GET    /api/patents/search/     # 특허 검색
GET    /api/patents/{id}/       # 특허 상세
```

### 챗봇 (Chat)
```
POST   /api/chat/similar/       # 유사 특허 찾기
POST   /api/chat/qa/            # Q&A
POST   /api/chat/editing/       # 문서 첨삭
POST   /api/chat/trend/         # 트렌드 분석
GET    /api/chat/history/       # 대화 이력
```

### 히스토리 (History)
```
GET    /api/history/search/     # 검색 이력
GET    /api/history/chat/       # 챗봇 이력
```

### 관리자 (Admin)
```
GET    /api/admin/stats/        # 시스템 통계
GET    /api/admin/users/        # 사용자 목록
PUT    /api/admin/users/{id}/   # 사용자 수정
DELETE /api/admin/users/{id}/   # 사용자 삭제
```

## 🔐 인증 방식

JWT (JSON Web Token) 기반 인증

1. **로그인**: `POST /api/auth/login/`
   ```json
   {
     "username": "user",
     "password": "pass"
   }
   ```
   응답:
   ```json
   {
     "access": "eyJ0eXAiOi...",
     "refresh": "eyJ0eXAiOi..."
   }
   ```

2. **API 요청 시 헤더에 토큰 포함**:
   ```
   Authorization: Bearer eyJ0eXAiOi...
   ```

3. **토큰 갱신**: `POST /api/auth/refresh/`
   ```json
   {
     "refresh": "eyJ0eXAiOi..."
   }
   ```

## 📚 참고 문서

- **전체 요구사항**: [BACKEND_REQUIREMENTS.md](../BACKEND_REQUIREMENTS.md)
- **개발 가이드**: [DJANGO_SETUP_GUIDE.md](DJANGO_SETUP_GUIDE.md)
- **Django 공식 문서**: https://docs.djangoproject.com/
- **DRF 공식 문서**: https://www.django-rest-framework.org/
- **JWT 문서**: https://django-rest-framework-simplejwt.readthedocs.io/

## 🤝 개발 워크플로우

1. **기능 개발**
   - 모델 작성 → 마이그레이션 → Serializer → View → URL

2. **테스트**
   - Unit test 작성 (`tests.py`)
   - API 테스트 (Postman, curl, 또는 DRF browsable API)

3. **문서화**
   - Docstring 작성
   - API 스키마 자동 생성 (drf-spectacular)

4. **코드 리뷰 & 머지**

## 🐛 문제 해결

### ModuleNotFoundError
```bash
# 패키지 재설치
pip install -r requirements.txt
```

### 마이그레이션 충돌
```bash
# 마이그레이션 초기화 (개발 중에만)
find . -path "*/migrations/*.py" -not -name "__init__.py" -delete
find . -path "*/migrations/*.pyc" -delete
python manage.py makemigrations
python manage.py migrate
```

### CORS 에러
```python
# settings.py의 CORS_ALLOWED_ORIGINS 확인
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
]
```

## 📞 지원

문제가 발생하면 이슈를 등록하거나 팀원에게 문의하세요.

---

**작성일**: 2025-01-20
**버전**: 1.0
**상태**: 초기 설정 완료 ✅
