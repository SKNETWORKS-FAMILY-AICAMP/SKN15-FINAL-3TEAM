# Patent Backend - GitHub 업로드 가이드

## ✅ 업로드할 파일 목록

### 소스 코드 (필수)
```
patent_backend/
├── accounts/              # 사용자 인증/권한 관리
├── chat/                  # 채팅 기능
├── chatbot/               # 챗봇 API
├── config/                # Django 설정
├── history/               # 검색 히스토리
├── patents/               # 특허 관리
└── manage.py             # Django 관리 스크립트
```

### 설정 파일
```
├── .gitignore            # ⭐ Git 제외 파일 목록
├── .env.example          # ⭐ 환경 변수 예제
├── requirements.txt      # Python 패키지 목록
```

### 문서 (모두 포함)
```
├── README.md
├── START_HERE.md
├── SETUP_GUIDE.md
├── DATABASE_GUIDE.md
├── DJANGO_SETUP_GUIDE.md
├── ADMIN_REGISTER_GUIDE.md
├── MIGRATION_GUIDE.md
├── CLEAN_MIGRATION_GUIDE.md
├── CONDA_SETUP.md
└── README_DATABASE.md
```

### 유틸리티 스크립트 (일부)
```
├── QUICK_START.sh
├── setup_database.sh
├── full_migration.sh
├── migrate_to_new_structure.sh
└── test_login.sh
```

---

## ❌ 업로드하면 안 되는 파일 (자동 제외됨)

### 1. 환경 변수 및 민감 정보
```
❌ .env                          # DB 비밀번호 포함!
✅ .env.example                  # 예제만 업로드
```

**`.env` 파일 내용:**
- DATABASE_URL with password: `1q2w3e4r` 🚨
- SECRET_KEY
- OPENAI_API_KEY

### 2. 데이터베이스 파일
```
❌ db.sqlite3                    # SQLite 데이터베이스
❌ *.sql                         # SQL 스크립트들
   - create_tables.sql
   - create_new_tables.sql
   - create_new_tables_final_play.sql
   - create_new_tables_patentdb.sql
   - database_migration.sql
   - drop_old_tables.sql
   - reset_database.sql
```

### 3. Python 캐시 파일
```
❌ __pycache__/                  # Python 캐시
❌ *.pyc, *.pyo                  # 컴파일된 Python 파일
```

### 4. 로그 파일
```
❌ logs/                         # 로그 디렉토리
❌ *.log                         # 로그 파일
```

### 5. 민감한 스크립트
```
❌ reset_postgres_password.sh   # 비밀번호 리셋 스크립트
❌ create_superuser.sh           # 관리자 생성 스크립트
```

---

## 📋 .gitignore 설정 완료

다음 파일들이 자동으로 제외됩니다:

### 환경 및 설정
- `.env` (민감 정보)
- `local_settings.py`

### 데이터베이스
- `db.sqlite3`
- `*.sql` (초기 데이터 제외)

### Python
- `__pycache__/`
- `*.pyc`
- `venv/`, `.venv/`

### 로그
- `logs/`
- `*.log`

### 민감 스크립트
- `reset_postgres_password.sh`
- `create_superuser.sh`

---

## 🔍 업로드 전 최종 확인

```bash
# 1. .env 파일이 제외되었는지 확인
git status | grep .env
# 결과: .env.example만 나와야 함!

# 2. SQL 파일이 제외되었는지 확인
git status | grep .sql
# 결과: 아무것도 나오지 않아야 함!

# 3. DB 비밀번호가 코드에 없는지 확인
git grep -i "1q2w3e4r"
# 결과: 아무것도 나오지 않아야 함!

# 4. __pycache__ 제외 확인
git status | grep __pycache__
# 결과: 아무것도 나오지 않아야 함!
```

---

## 🚀 GitHub 업로드 방법

### 1단계: 현재 상태 확인
```bash
cd /home/juhyeong/workspace/final_project/SKN15-FINAL-3TEAM

# Git 상태 확인
git status
```

### 2단계: patent_backend 추가
```bash
# patent_backend 폴더 추가
git add patent_backend/

# 추가될 파일 확인 (민감 정보 제외됨)
git status
```

### 3단계: 커밋
```bash
git commit -m "Add patent backend

- Django REST API server
- User authentication & authorization
- Chatbot integration
- Search history management
- Admin management system"
```

### 4단계: 푸시
```bash
# GitHub에 푸시
git push origin main
```

---

## 📊 업로드 크기 비교

### Before (전체)
```
patent_backend/
├── 소스 코드         ~1.5MB
├── 문서              ~100KB
├── __pycache__       많음 ❌
├── db.sqlite3        164KB ❌
├── .env              민감 ❌
└── *.sql             ~50KB ❌
```

### After (업로드)
```
patent_backend/
├── 소스 코드         ~1.5MB  ✅
├── 문서              ~100KB  ✅
├── .env.example      1KB     ✅
└── requirements.txt  1KB     ✅
```

**총 업로드 크기: 약 1.6MB**

---

## ⚠️ 중요 주의사항

### 1. .env 파일 절대 업로드 금지!
`.env` 파일에는 다음 민감 정보가 포함되어 있습니다:
- PostgreSQL 비밀번호: `1q2w3e4r` 🚨
- Django SECRET_KEY
- OpenAI API KEY

### 2. SQL 파일 제외 이유
- 실제 데이터베이스 구조 노출 방지
- 민감한 초기 데이터 포함 가능성

### 3. 다른 개발자를 위한 설정
업로드 후 README에 다음 내용 추가 권장:

```markdown
## 환경 설정

1. `.env` 파일 생성:
\`\`\`bash
cp .env.example .env
\`\`\`

2. `.env` 파일 수정:
- DATABASE_URL: PostgreSQL 연결 정보 입력
- SECRET_KEY: 새로운 시크릿 키 생성
- OPENAI_API_KEY: OpenAI API 키 입력 (선택)
```

---

## ✅ 최종 체크리스트

업로드 전 확인:

- [x] `.gitignore` 파일 생성 완료
- [x] `.env` 파일 제외 확인
- [x] `db.sqlite3` 제외 확인
- [x] `*.sql` 파일 제외 확인
- [x] `__pycache__/` 제외 확인
- [x] `logs/` 제외 확인
- [x] 민감 스크립트 제외 확인
- [x] `.env.example` 포함 확인

모두 완료되었습니다! 안전하게 업로드할 수 있습니다. 🎉
