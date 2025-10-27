# 🎯 데이터베이스 빠른 시작 가이드

## 📋 테이블 구조 한눈에 보기

```
┌─────────────────────────────────────────────────┐
│          users (사용자)                          │
│  - id, userid, password, team                   │
│  - email, is_active, is_staff                   │
└──────────────────┬──────────────────────────────┘
                   │
                   ↓
┌─────────────────────────────────────────────────┐
│       userrolemap (사용자↔역할 연결)             │
│  - userid (FK → users.id)                       │
│  - roleid (FK → roles.roleid)                   │
└──────────────────┬──────────────────────────────┘
                   │
                   ↓
┌─────────────────────────────────────────────────┐
│          roles (역할)                            │
│  - roleid, rolename, description                │
│  예: admin, researcher, planner                 │
└──────────────────┬──────────────────────────────┘
                   │
                   ↓
┌─────────────────────────────────────────────────┐
│    rolepermissionmap (역할↔권한 연결)            │
│  - roleid (FK → roles.roleid)                   │
│  - permissionid (FK → permissions.permissionid) │
└──────────────────┬──────────────────────────────┘
                   │
                   ↓
┌─────────────────────────────────────────────────┐
│       permissions (권한)                         │
│  - permissionid, permissionname, description    │
│  예: view_patent, search_patent                 │
└─────────────────────────────────────────────────┘
```

---

## 🚀 가장 빠른 설정 방법 (3단계)

### 1️⃣ PostgreSQL 시작
```bash
sudo service postgresql start
```

### 2️⃣ 자동 설정 실행
```bash
bash backend/setup_database.sh
```

**입력값:**
- 데이터베이스: `patent_analysis` (엔터)
- 사용자: `patentuser` (엔터)
- 비밀번호: `원하는비밀번호` (입력)

### 3️⃣ Django 서버 시작
```bash
cd backend
python manage.py createsuperuser
python manage.py runserver
```

**완료!** 🎉

---

## 📊 생성되는 데이터

### 기본 역할 3개
| rolename | description |
|----------|-------------|
| researcher | 연구원 - 특허 검색 및 분석 |
| planner | 기획자 - 특허 분석 및 보고서 |
| admin | 관리자 - 모든 권한 |

### 기본 권한 6개
| permissionname | description |
|----------------|-------------|
| view_patent | 특허 조회 |
| search_patent | 특허 검색 |
| export_patent | 특허 내보내기 |
| use_ai_chat | AI 챗봇 사용 |
| manage_users | 사용자 관리 |
| view_history | 검색 히스토리 조회 |

### 역할별 권한 매핑
```
researcher → view_patent, search_patent, use_ai_chat, view_history
planner    → researcher 권한 + export_patent
admin      → 모든 권한
```

---

## 💻 Django 코드에서 사용

### 권한 확인
```python
# 역할 확인
if request.user.has_role('admin'):
    # 관리자 전용 기능

# 권한 확인
if request.user.has_permission('search_patent'):
    # 특허 검색 기능
```

### API 엔드포인트
```python
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def search_patents(request):
    if not request.user.has_permission('search_patent'):
        return Response({'error': '권한 없음'}, status=403)
    # ...
```

---

## 🔍 데이터 확인

```bash
# PostgreSQL 접속
sudo -u postgres psql -d patent_analysis

# 테이블 목록
\dt

# 역할 확인
SELECT * FROM roles;

# 역할별 권한
SELECT r.rolename, p.permissionname
FROM rolepermissionmap rpm
JOIN roles r ON rpm.roleid = r.roleid
JOIN permissions p ON rpm.permissionid = p.permissionid;

# 종료
\q
```

---

## 📁 관련 파일

- **[DATABASE_GUIDE.md](DATABASE_GUIDE.md)** - 상세한 설명 (역할, 예시 포함)
- **[create_tables.sql](create_tables.sql)** - 테이블 생성 SQL
- **[setup_database.sh](setup_database.sh)** - 자동 설정 스크립트
- **[START_HERE.md](START_HERE.md)** - 전체 실행 가이드

---

## ❓ 문제 해결

### "connection failed" 오류
```bash
sudo service postgresql start
```

### "database does not exist" 오류
```bash
bash backend/setup_database.sh
```

### "permission denied" 오류
```bash
sudo -u postgres psql
GRANT ALL PRIVILEGES ON DATABASE patent_analysis TO patentuser;
\q
```

---

## 🎓 더 알아보기

자세한 내용은 **[DATABASE_GUIDE.md](DATABASE_GUIDE.md)** 참고
