# Django 백엔드 개발 가이드

## 🚀 시작하기

### 1. 프로젝트 구조

```
backend/
├── config/                 # Django 프로젝트 설정
│   ├── __init__.py
│   ├── settings.py        # 메인 설정
│   ├── urls.py            # 메인 URL 라우팅
│   ├── wsgi.py
│   └── asgi.py
├── accounts/              # 사용자 인증 앱
│   ├── models.py          # User 모델
│   ├── serializers.py     # DRF Serializers
│   ├── views.py           # API Views
│   └── urls.py            # URL 패턴
├── patents/               # 특허 검색 앱
│   ├── models.py          # Patent 모델
│   ├── serializers.py
│   ├── views.py
│   └── urls.py
├── chat/                  # AI 챗봇 앱
│   ├── models.py          # Conversation, Message 모델
│   ├── services/          # AI 로직
│   │   ├── similar.py     # 유사 특허 찾기
│   │   ├── qa.py          # Q&A
│   │   ├── editing.py     # 문서 첨삭
│   │   └── trend.py       # 트렌드 분석
│   ├── serializers.py
│   ├── views.py
│   └── urls.py
├── history/               # 히스토리 앱
│   ├── models.py          # SearchHistory 모델
│   ├── serializers.py
│   ├── views.py
│   └── urls.py
├── manage.py
├── requirements.txt
├── .env.example
└── README.md
```

---

## 📦 설치 및 초기 설정

### Step 1: 가상환경 활성화 및 패키지 설치

```bash
# conda 환경 활성화
conda activate final_project

# backend 폴더로 이동
cd backend

# 필수 패키지 설치
pip install -r requirements.txt
```

### Step 2: 환경 변수 설정

```bash
# .env 파일 생성
cp .env.example .env

# .env 파일 편집 (SECRET_KEY, DATABASE_URL 등)
nano .env
```

### Step 3: Django 설정 수정

`config/settings.py` 파일을 수정합니다:

```python
# config/settings.py
import os
from pathlib import Path
from decouple import config
from datetime import timedelta

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = config('SECRET_KEY')
DEBUG = config('DEBUG', default=False, cast=bool)
ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='localhost').split(',')

# 설치된 앱
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Third-party
    'rest_framework',
    'rest_framework_simplejwt',
    'corsheaders',
    'drf_spectacular',

    # Local apps
    'accounts',
    'patents',
    'chat',
    'history',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',  # CORS - 맨 위
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# CORS 설정
CORS_ALLOWED_ORIGINS = config('CORS_ALLOWED_ORIGINS').split(',')
CORS_ALLOW_CREDENTIALS = True

# REST Framework 설정
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
}

# JWT 설정
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=config('ACCESS_TOKEN_LIFETIME', default=60, cast=int)),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=config('REFRESH_TOKEN_LIFETIME', default=7, cast=int)),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'AUTH_HEADER_TYPES': ('Bearer',),
}

# 데이터베이스
DATABASES = {
    'default': dj_database_url.config(
        default=config('DATABASE_URL', default='sqlite:///db.sqlite3')
    )
}

# 커스텀 User 모델
AUTH_USER_MODEL = 'accounts.User'
```

---

## 🗄️ 데이터베이스 모델 작성

### accounts/models.py (사용자)

```python
from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    email = models.EmailField(unique=True)
    department = models.CharField(max_length=100, blank=True)
    role = models.CharField(
        max_length=20,
        choices=[
            ('researcher', '연구원'),
            ('planner', '기획자'),
            ('admin', '관리자'),
        ],
        default='researcher'
    )
    status = models.CharField(
        max_length=20,
        choices=[
            ('active', '활성'),
            ('inactive', '비활성'),
        ],
        default='active'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'users'
        verbose_name = '사용자'
        verbose_name_plural = '사용자들'

    def __str__(self):
        return self.username
```

### patents/models.py (특허)

```python
from django.db import models
from django.contrib.postgres.search import SearchVectorField
from django.contrib.postgres.indexes import GinIndex

class Patent(models.Model):
    title = models.TextField()
    application_number = models.CharField(max_length=50, unique=True)
    application_date = models.DateField()
    publication_number = models.CharField(max_length=50, blank=True)
    publication_date = models.DateField(null=True, blank=True)
    summary = models.TextField()
    claims = models.TextField(blank=True)
    description = models.TextField(blank=True)

    ipc_code = models.CharField(max_length=50, blank=True)
    cpc_code = models.CharField(max_length=50, blank=True)

    inventors = models.JSONField(default=list, blank=True)
    applicant = models.CharField(max_length=500, blank=True)

    status = models.CharField(max_length=50, default='registered')

    # Full-text search
    search_vector = SearchVectorField(null=True, blank=True)

    # Vector embeddings (for similarity search)
    title_embedding = models.JSONField(null=True, blank=True)
    summary_embedding = models.JSONField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'patents'
        verbose_name = '특허'
        verbose_name_plural = '특허들'
        indexes = [
            models.Index(fields=['application_number']),
            models.Index(fields=['application_date']),
            models.Index(fields=['ipc_code']),
            GinIndex(fields=['search_vector']),  # Full-text search index
        ]
        ordering = ['-application_date']

    def __str__(self):
        return f"{self.application_number}: {self.title[:50]}"
```

### chat/models.py (챗봇)

```python
from django.db import models
from accounts.models import User

class Conversation(models.Model):
    MODE_CHOICES = [
        ('similar', '유사 특허'),
        ('qa', '특허 Q&A'),
        ('editing', '문서 첨삭'),
        ('trend', '트렌드 분석'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='conversations')
    mode = models.CharField(max_length=20, choices=MODE_CHOICES)
    first_question = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'conversations'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} - {self.mode} - {self.created_at}"


class Message(models.Model):
    TYPE_CHOICES = [
        ('user', '사용자'),
        ('ai', 'AI'),
        ('system', '시스템'),
    ]

    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='messages')
    type = models.CharField(max_length=10, choices=TYPE_CHOICES)
    content = models.TextField()
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'messages'
        ordering = ['created_at']

    def __str__(self):
        return f"{self.type} - {self.created_at}"
```

### history/models.py (검색 이력)

```python
from django.db import models
from accounts.models import User

class SearchHistory(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='search_history')
    query = models.TextField()
    filters = models.JSONField(default=dict, blank=True)
    result_count = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'search_history'
        ordering = ['-created_at']
        verbose_name = '검색 이력'
        verbose_name_plural = '검색 이력들'

    def __str__(self):
        return f"{self.user.username} - {self.query} - {self.created_at}"
```

---

## 🔄 마이그레이션 실행

```bash
# 마이그레이션 파일 생성
python manage.py makemigrations

# 마이그레이션 실행
python manage.py migrate

# 관리자 계정 생성
python manage.py createsuperuser
```

---

## 🔑 API 개발 순서

### Phase 1: 인증 시스템 (accounts 앱)

1. **Serializers 작성** (`accounts/serializers.py`)
```python
from rest_framework import serializers
from .models import User

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'department', 'role', 'status']
        read_only_fields = ['id']

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'department']

    def create(self, validated_data):
        user = User.objects.create_user(**validated_data)
        return user
```

2. **Views 작성** (`accounts/views.py`)
```python
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.views import TokenObtainPairView
from .models import User
from .serializers import UserSerializer, RegisterSerializer

class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    permission_classes = [AllowAny]
    serializer_class = RegisterSerializer

class UserProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = UserSerializer

    def get_object(self):
        return self.request.user
```

3. **URLs 작성** (`accounts/urls.py`)
```python
from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from .views import RegisterView, UserProfileView

app_name = 'accounts'

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', TokenObtainPairView.as_view(), name='login'),
    path('refresh/', TokenRefreshView.as_view(), name='refresh'),
    path('me/', UserProfileView.as_view(), name='profile'),
]
```

4. **메인 URLs에 추가** (`config/urls.py`)
```python
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/auth/', include('accounts.urls')),
    path('api/patents/', include('patents.urls')),
    path('api/chat/', include('chat.urls')),
    path('api/history/', include('history.urls')),
]
```

---

### Phase 2: 특허 검색 (patents 앱)

1. **Serializers** (`patents/serializers.py`)
2. **Views** (`patents/views.py`)
   - `PatentSearchView`: 검색 API
   - `PatentDetailView`: 상세 조회
3. **URLs** (`patents/urls.py`)

---

### Phase 3: AI 챗봇 (chat 앱)

1. **Services 작성** (`chat/services/`)
   - `similar.py`: OpenAI Embeddings + Vector Search
   - `qa.py`: LangChain RAG
   - `editing.py`: GPT-4 분석
   - `trend.py`: 데이터 분석
2. **Views** (`chat/views.py`)
3. **URLs** (`chat/urls.py`)

---

## 🧪 테스트 실행

```bash
# 모든 테스트 실행
pytest

# 특정 앱만 테스트
pytest accounts/tests.py

# Coverage 포함
pytest --cov=. --cov-report=html
```

---

## 🚀 서버 실행

```bash
# 개발 서버
python manage.py runserver

# 특정 포트
python manage.py runserver 8000

# 외부 접속 허용
python manage.py runserver 0.0.0.0:8000
```

---

## 📝 다음 단계

1. ✅ Django 프로젝트 생성
2. ✅ 앱 구조 생성
3. ✅ 설정 파일 작성
4. ⬜ 데이터베이스 모델 작성
5. ⬜ 마이그레이션 실행
6. ⬜ 인증 API 개발
7. ⬜ 특허 검색 API 개발
8. ⬜ AI 챗봇 API 개발

---

## 🔗 유용한 명령어

```bash
# Django shell
python manage.py shell

# DB 초기화
python manage.py flush

# 새 앱 생성
python manage.py startapp app_name

# Static 파일 수집
python manage.py collectstatic

# 프로덕션 서버 (Gunicorn)
gunicorn config.wsgi:application --bind 0.0.0.0:8000
```

---

## 📚 참고 문서

- Django 공식 문서: https://docs.djangoproject.com/
- Django REST Framework: https://www.django-rest-framework.org/
- JWT 인증: https://django-rest-framework-simplejwt.readthedocs.io/
- PostgreSQL Full-text: https://docs.djangoproject.com/en/5.0/ref/contrib/postgres/search/
