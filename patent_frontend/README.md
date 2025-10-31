# Patent Analysis System - Frontend

AI 기반 특허 분석 시스템의 프론트엔드 - Next.js 15 + React 19 기반 웹 애플리케이션

## 🚀 빠른 시작

### 필수 요구사항

- **Node.js**: 18.x 이상
- **npm**: 9.x 이상

### 설치 및 실행

```bash
# 의존성 설치
npm install

# 개발 서버 실행
npm run dev
```

브라우저에서 [http://localhost:3000](http://localhost:3000)을 열어 확인하세요.

### 환경 변수 설정

`.env.local` 파일 생성:

```bash
# API 서버 주소
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## 📁 프로젝트 구조

```
patent_frontend/
├── app/                    # Next.js App Router
│   ├── admin/             # 관리자 페이지
│   ├── history/           # 분석 히스토리
│   ├── login/             # 로그인
│   ├── search/            # 특허 검색 (메인 기능)
│   ├── layout.tsx         # 루트 레이아웃
│   └── globals.css        # 전역 스타일
├── components/            # React 컴포넌트
│   ├── ui/               # UI 컴포넌트 (shadcn/ui)
│   └── main-layout.tsx   # 메인 레이아웃
├── lib/                  # 유틸리티 함수
│   ├── config.ts         # 설정
│   └── utils.ts          # 헬퍼 함수
├── public/               # 정적 파일
│   └── *.jpg            # 이미지 파일
└── package.json         # 패키지 설정
```

## 🎨 주요 기능

### 1. 통합 검색 (Integrated Search)
- AI 기반 특허 문서 검색
- 고급 필터링 (제목, 요약 검색)
- 실시간 검색 결과
- 페이지네이션

### 2. AI 챗봇
- 특허 관련 질문/답변
- 대화 히스토리 관리
- 파일 업로드 지원
- 자동 스크롤

### 3. 분석 히스토리
- 과거 분석 결과 조회
- 결과 필터링 및 검색

### 4. 관리자 대시보드
- 시스템 통계
- 사용자 관리
- 승인 대기 목록

### 5. 반응형 디자인
- 모바일/태블릿/데스크톱 지원
- 글래스모피즘 UI
- 다크/라이트 테마

## 🛠 기술 스택

### Core
- **Next.js 15.2.4** - React 프레임워크
- **React 19** - UI 라이브러리
- **TypeScript** - 타입 안정성

### Styling
- **Tailwind CSS 4** - 유틸리티 우선 CSS
- **shadcn/ui** - 재사용 가능한 UI 컴포넌트
- **Radix UI** - 접근성 높은 기본 컴포넌트

### State & Data
- **React Hooks** - 상태 관리
- **localStorage** - 클라이언트 저장소

### Icons & Assets
- **Lucide React** - 아이콘
- **Next/Image** - 이미지 최적화

## 📝 스크립트

```bash
# 개발 서버 시작
npm run dev

# 프로덕션 빌드
npm run build

# 프로덕션 서버 실행
npm start

# 린트 검사
npm run lint
```

## 🔧 설정 파일

### next.config.mjs
```javascript
const nextConfig = {
  typescript: {
    ignoreBuildErrors: true,  // 개발 편의성
  },
  images: {
    unoptimized: true,       // 이미지 최적화 비활성화
  },
  output: 'standalone',      // 독립 실행형 출력
}
```

### tailwind.config.ts
- Tailwind CSS v4 설정
- 커스텀 색상 및 테마
- 애니메이션 설정

## 🚨 문제 해결

### npm install 실패

```bash
# node_modules 삭제 후 재설치
rm -rf node_modules package-lock.json
npm install
```

### 포트 3000 사용 중

```bash
# 포트 사용 프로세스 확인
lsof -i :3000

# 프로세스 종료
kill -9 <PID>

# 또는 다른 포트 사용
PORT=3001 npm run dev
```

### 환경 변수 적용 안 됨

```bash
# 서버 재시작 필요
# .env.local 수정 후 반드시 재시작
npm run dev
```

## 🐳 Docker로 실행

```bash
# 이미지 빌드
docker build -t patent-frontend .

# 컨테이너 실행
docker run -p 3000:3000 patent-frontend
```

## 📦 배포

### Vercel (권장)
```bash
# Vercel CLI 설치
npm i -g vercel

# 배포
vercel
```

### 수동 배포
```bash
# 빌드
npm run build

# standalone 폴더 사용
cd .next/standalone
node server.js
```

## 🔗 관련 링크

- **백엔드 저장소**: [patent_backend](../patent_backend)
- **API 문서**: http://localhost:8000/docs
- **Next.js 문서**: https://nextjs.org/docs
- **Tailwind CSS**: https://tailwindcss.com/docs

## 📄 라이선스

이 프로젝트는 팀 프로젝트입니다.

## 👥 기여

프로젝트 팀원들만 기여 가능합니다.
