# Conda 가상환경 설정 가이드

## 📦 Conda 가상환경 정보

### 환경 이름
```
patent_backend
```

### Python 버전
```
Python 3.11
```

---

## 🚀 사용 방법

### 1. 가상환경 활성화

```bash
conda activate patent_backend
```

### 2. 패키지 확인

```bash
conda list
```

또는

```bash
pip list
```

### 3. Django 서버 실행

```bash
# 가상환경 활성화 후
cd /home/juhyeong/workspace/final_project/backend
python manage.py runserver
```

### 4. 가상환경 비활성화

```bash
conda deactivate
```

---

## 📋 설치된 주요 패키지

### Django 코어
- Django==5.0.1
- djangorestframework==3.14.0
- djangorestframework-simplejwt==5.3.1

### 데이터베이스
- psycopg2-binary==2.9.10
- dj-database-url==2.1.0

### CORS
- django-cors-headers==4.3.1

### 환경 변수
- python-decouple==3.8
- python-dotenv==1.0.1

### 데이터 처리
- pandas==2.2.3
- numpy==2.2.1

### AI/ML
- openai==1.58.1

### 파일 처리
- Pillow==10.4.0
- python-magic==0.4.27
- PyPDF2==3.0.1
- python-docx==1.1.2

### API 문서화
- drf-spectacular==0.27.1

### 비동기 & 백그라운드 작업
- celery==5.3.6
- redis==5.2.1
- django-celery-beat==2.6.0

### 유틸리티
- python-dateutil==2.9.0.post0
- pytz==2025.2
- requests==2.32.3

### 개발 도구
- django-debug-toolbar==4.2.0
- django-extensions==3.2.3

### 테스팅
- pytest==7.4.4
- pytest-django==4.7.0
- factory-boy==3.3.0

### 프로덕션
- gunicorn==21.2.0
- whitenoise==6.6.0

---

## 🔄 패키지 추가/업데이트

### 새 패키지 설치

```bash
conda activate patent_backend
pip install <package-name>

# 설치 후 requirements.txt 업데이트
pip freeze > requirements.txt
```

### requirements.txt에서 일괄 설치

```bash
conda activate patent_backend
pip install -r requirements.txt
```

---

## 🗑️ 가상환경 삭제 (필요 시)

```bash
conda deactivate
conda remove -n patent_backend --all
```

---

## 🆕 새로운 가상환경 재생성 (필요 시)

```bash
# 가상환경 생성
conda create -n patent_backend python=3.11 -y

# 가상환경 활성화
conda activate patent_backend

# 패키지 설치
cd /home/juhyeong/workspace/final_project/backend
pip install -r requirements.txt
```

---

## ✅ 환경 확인

```bash
# 가상환경 활성화 확인
conda info --envs

# 활성화된 환경 확인 (앞에 * 표시)
# * patent_backend

# Python 버전 확인
python --version
# Python 3.11.14

# Django 버전 확인
python -c "import django; print(django.get_version())"
# 5.0.1
```

---

## 🐛 문제 해결

### 1. 가상환경을 찾을 수 없음

```bash
# Conda 초기화
conda init bash
source ~/.bashrc

# 가상환경 목록 확인
conda env list
```

### 2. 패키지 설치 오류

```bash
# pip 업그레이드
pip install --upgrade pip

# 특정 패키지 재설치
pip install --force-reinstall <package-name>
```

### 3. PostgreSQL 연결 오류

```bash
# psycopg2 재설치
pip uninstall psycopg2-binary
pip install psycopg2-binary
```

---

## 📝 관련 문서

- [SETUP_GUIDE.md](SETUP_GUIDE.md) - 전체 백엔드 설정 가이드
- [ADMIN_REGISTER_GUIDE.md](ADMIN_REGISTER_GUIDE.md) - 관리자 회원가입 가이드

---

**작성일:** 2025-10-22
**버전:** 1.0
