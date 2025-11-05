# 시스템 업데이트 요약 (2025-10-30)

## 🎯 주요 변경사항

### 1. 관리자 회원가입 기능 제거 ✅

**변경 이유:**
- 시스템 단순화
- 중앙화된 권한 관리
- 보안 강화

**변경 내용:**
- ❌ 관리자 회원가입 페이지 (`/admin-register`) 삭제
- ❌ 관리자 회원가입 API (`POST /api/accounts/admin/register/`) 제거
- ✅ 모든 사용자는 일반 회원가입 사용
- ✅ 슈퍼 관리자가 필요 시 부서 관리자로 승격

---

## 🔐 새로운 회원가입 및 권한 관리 프로세스

### 회원가입 절차

1. **회원가입** (`POST /api/accounts/register/`)
   - 모든 사용자는 `role='user'`, `status='pending'`으로 가입
   - 즉시 토큰 발급되지만 `is_active=False`로 로그인 불가

2. **관리자 승인** (`PATCH /api/accounts/users/{id}/status/`)
   - 부서 관리자 또는 슈퍼 관리자가 `status='active'`로 변경
   - `is_active=True`가 되어 로그인 가능

3. **부서 관리자 승격** (선택 사항, `PATCH /api/accounts/users/{id}/role/`)
   - 슈퍼 관리자만 가능
   - `role='user'` → `role='dept_admin'`
   - `is_staff`가 자동으로 `True`로 변경

### 권한 체계

```
일반 사용자 (user)
  ↓ (관리자 승인)
활성화된 일반 사용자 (user, status=active)
  ↓ (슈퍼 관리자 승격)
부서 관리자 (dept_admin, is_staff=True)
```

---

## 📋 권한별 가능한 작업

### 일반 사용자 (`role='user'`)
- ✅ 자신의 정보 수정
- ✅ 자신의 비밀번호 변경
- ✅ 비밀번호 재설정 요청 (→ 부서 관리자)
- ✅ 부서 관리자 권한 요청
- ❌ 다른 사용자 관리 불가

### 부서 관리자 (`role='dept_admin'`)
- ✅ 일반 사용자의 모든 권한
- ✅ 같은 부서 일반 사용자 승인/정지
- ✅ 같은 부서 일반 사용자 비밀번호 재설정
- ✅ 비밀번호 재설정 요청 (→ 슈퍼 관리자)
- ❌ 사용자 역할 변경 불가
- ❌ 다른 부서 관리자 관리 불가

### 슈퍼 관리자 (`role='super_admin'`)
- ✅ 부서 관리자의 모든 권한
- ✅ 같은 회사 모든 사용자 승인/정지
- ✅ 사용자를 부서 관리자로 승격
- ✅ 같은 회사 모든 사용자 비밀번호 재설정 (부서 관리자 포함)
- ✅ 부서 관리자 권한 요청 승인/거부
- ❌ 비밀번호 재설정 요청 불가 (최상위 권한)

---

## 🔧 주요 API 엔드포인트

### 인증
```
POST   /api/accounts/register/              # 회원가입 (모든 사용자)
POST   /api/accounts/login/                 # 로그인
POST   /api/accounts/logout/                # 로그아웃
```

### 사용자 관리 (관리자)
```
GET    /api/accounts/users/                 # 사용자 목록
PATCH  /api/accounts/users/{id}/status/     # 상태 변경 (승인/정지)
PATCH  /api/accounts/users/{id}/role/       # 역할 변경 (슈퍼 관리자만)
POST   /api/accounts/users/{id}/reset-password/  # 비밀번호 재설정
DELETE /api/accounts/users/{id}/            # 사용자 삭제
```

### 비밀번호 재설정
```
POST   /api/accounts/password-resets/request/           # 요청 (로그인 상태)
POST   /api/accounts/password-resets/request-anonymous/ # 요청 (비로그인)
GET    /api/accounts/password-resets/                   # 요청 목록 (관리자)
```

### 부서 관리자 권한 요청
```
POST   /api/accounts/admin-requests/create/         # 요청 생성
GET    /api/accounts/admin-requests/                # 요청 목록
POST   /api/accounts/admin-requests/{id}/handle/   # 승인/거부
```

---

## 📁 변경된 파일

### 백엔드
```
SKN15-FINAL-3TEAM/patent_backend/
├── accounts/
│   ├── serializers.py    (AdminRegisterSerializer 제거)
│   ├── views.py          (admin_register 뷰 제거)
│   └── urls.py           (admin/register/ URL 제거)
└── ADMIN_REGISTRATION_REMOVAL_GUIDE.md  (신규 생성)
```

### 프론트엔드
```
test_app/
├── app/
│   ├── admin-register/   (폴더 삭제)
│   └── login/
│       └── page.tsx      (관리자 회원가입 버튼 제거)
```

---

## ✅ 검증 결과

### 백엔드
```bash
$ python manage.py check
System check identified no issues (0 silenced).
```

### API 테스트
- ✅ 일반 회원가입: 정상 작동
- ✅ 사용자 승인: 정상 작동
- ✅ 부서 관리자 승격: 정상 작동
- ✅ 비밀번호 재설정: 정상 작동
- ❌ 관리자 회원가입: 404 Not Found (의도된 동작)

### 프론트엔드
- ✅ 로그인 페이지: 관리자 회원가입 버튼 제거 확인
- ❌ `/admin-register` 접근: 404 Not Found (의도된 동작)

---

## 📚 관련 문서

### 상세 가이드
- [ADMIN_REGISTRATION_REMOVAL_GUIDE.md](SKN15-FINAL-3TEAM/patent_backend/ADMIN_REGISTRATION_REMOVAL_GUIDE.md)
  - 변경 사항 상세 설명
  - API 사용 예시
  - 권한 매트릭스
  - 시퀀스 다이어그램
  - 테스트 체크리스트

### 기타 문서
- [PASSWORD_MANAGEMENT_IMPLEMENTATION.md](SKN15-FINAL-3TEAM/patent_backend/PASSWORD_MANAGEMENT_IMPLEMENTATION.md)
- [TABLE_MODIFICATIONS_IMPLEMENTED.md](SKN15-FINAL-3TEAM/patent_backend/TABLE_MODIFICATIONS_IMPLEMENTED.md)
- [CODE_CHANGES_SUMMARY.md](SKN15-FINAL-3TEAM/patent_backend/CODE_CHANGES_SUMMARY.md)

---

## 🎉 완료 항목

### 백엔드 ✅
1. `AdminRegisterSerializer` 클래스 제거
2. `admin_register` 뷰 함수 제거
3. `admin/register/` URL 패턴 제거
4. Import 문 정리
5. Django 검증 통과

### 프론트엔드 ✅
1. `/admin-register` 페이지 폴더 삭제
2. 로그인 페이지에서 관리자 회원가입 링크 제거

### 문서화 ✅
1. 상세 가이드 작성 (ADMIN_REGISTRATION_REMOVAL_GUIDE.md)
2. 시스템 업데이트 요약 작성 (SYSTEM_UPDATES_2025-10-30.md)
3. API 사용 예시 및 시퀀스 다이어그램 포함

---

## 🔄 배포 방법

### 백엔드
```bash
cd SKN15-FINAL-3TEAM/patent_backend

# Django 검증
conda run -n patent_backend python manage.py check

# 서버 재시작
pkill -f "python manage.py runserver"
conda run -n patent_backend python manage.py runserver
```

### 프론트엔드
```bash
cd test_app

# 빌드 및 재시작
npm run build
npm run start
```

---

## 📞 문의

시스템 관련 문의 사항은 프로젝트 관리자에게 연락해주세요.

**업데이트 날짜:** 2025-10-30
**문서 버전:** 1.0
