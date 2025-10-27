# GitHub 업로드 파일 목록

## ✅ 업로드할 파일 (필수)

```
test_app/
├── app/                    # 모든 페이지 코드
├── components/             # UI 컴포넌트
├── lib/                    # 유틸리티 함수
├── hooks/                  # React 커스텀 훅
├── styles/                 # CSS 스타일
├── public/                 # 이미지 파일 (선택적)
├── .gitignore
├── package.json
├── package-lock.json
├── tsconfig.json
├── next.config.mjs
├── postcss.config.mjs
├── components.json
├── .dockerignore
├── .env.example            # ⭐ 생성 필요!
└── README.md
```

**총 용량: 약 2~3.5MB**

---

## ❌ 업로드하면 안 되는 파일

```
test_app/
├── node_modules/           # 643MB - npm install로 복원 가능
├── .next/                  # 77MB - 빌드 결과물
├── .env.local              # 보안 - API URL 포함
├── patent_analysis_db/     # 28KB - ⚠️ DB 비밀번호 포함!
├── pnpm-lock.yaml          # package-lock.json 있으면 불필요
├── requirements.txt        # Python 파일 (프론트엔드에 불필요)
└── next-env.d.ts           # 자동 생성 파일
```

---

## 🔧 업로드 전 필수 작업

### 1. .env.example 파일 생성
```bash
cat > .env.example << 'EOF'
# API Configuration
NEXT_PUBLIC_API_URL=http://localhost:8000
EOF
```

### 2. .gitignore에 추가
```bash
# .gitignore 파일 끝에 추가
echo "patent_analysis_db/" >> .gitignore
```

### 3. 파일 확인
```bash
# Git이 추적할 파일 확인
git status

# .env 파일이 포함되지 않았는지 확인
git status | grep .env
# 결과: .env.example만 있어야 함!
```

---

## 📋 요약

### 올릴 것 ✅
- 소스 코드 (app, components, lib, hooks, styles)
- 설정 파일 (package.json, tsconfig.json 등)
- .gitignore, .env.example

### 안 올릴 것 ❌
- node_modules/
- .next/
- .env.local
- patent_analysis_db/
