# Patent Analysis System

AI 기반 특허 분석 시스템 - Next.js 15 + React 19 기반의 웹 애플리케이션입니다.

## 목차

- [필수 요구사항](#필수-요구사항)
- [Conda 환경 설정](#conda-환경-설정)
- [로컬 개발 환경 실행](#로컬-개발-환경-실행)
- [Docker로 실행](#docker로-실행)
- [프로젝트 구조](#프로젝트-구조)
- [주요 기능](#주요-기능)
- [사용 기술](#사용-기술)

## 필수 요구사항

- **Conda**: Miniconda 또는 Anaconda
- **Node.js**: 20.x (conda 환경에 포함됨)
- **Python**: 3.11 (conda 환경에 포함됨)
- **Docker** (선택사항): Docker를 사용하여 실행하는 경우

## Conda 환경 설정

### 1. Conda 환경 생성 및 활성화

```bash
# final_project 이름의 conda 환경 생성
conda create -n final_project python=3.11 nodejs=20 -y

# 환경 활성화
conda activate final_project
```

### 2. 패키지 설치

#### Node.js 패키지 설치

```bash
# test_app 디렉토리로 이동
cd test_app

# npm 패키지 설치
npm install --legacy-peer-deps
```

> **참고**: `--legacy-peer-deps` 플래그는 React 19와 일부 패키지 간의 peer dependency 충돌을 해결하기 위해 필요합니다.

#### Python 패키지 설치 (백엔드용)

```bash
# conda 환경이 활성화된 상태에서
pip install -r requirements.txt
```

설치되는 주요 패키지:
- **FastAPI**: 백엔드 API 프레임워크
- **Uvicorn**: ASGI 서버
- **SQLAlchemy**: ORM
- **Pandas & NumPy**: 데이터 처리
- **Pydantic**: 데이터 검증

## 로컬 개발 환경 실행

### Frontend (Next.js) 실행

```bash
# conda 환경 활성화 (아직 활성화하지 않은 경우)
conda activate final_project

# test_app 디렉토리로 이동
cd test_app

# 개발 서버 시작
npm run dev
```

브라우저에서 [http://localhost:3000](http://localhost:3000)을 열어 애플리케이션을 확인하세요.

### Backend (FastAPI) 실행 (선택사항)

백엔드 API가 필요한 경우:

```bash
# conda 환경 활성화
conda activate final_project

# FastAPI 서버 실행 (backend 디렉토리가 있는 경우)
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 프로덕션 빌드

```bash
# 프로덕션 빌드
npm run build

# 프로덕션 서버 시작
npm start
```

### 린트 실행

```bash
npm run lint
```

## Docker로 실행

### 1. Docker 이미지 빌드

```bash
# test_app 디렉토리에서 실행
docker build -t patent-analysis-system .
```

### 2. Docker 컨테이너 실행

```bash
docker run -p 3000:3000 patent-analysis-system
```

브라우저에서 [http://localhost:3000](http://localhost:3000)을 열어 애플리케이션을 확인하세요.

### Docker Compose 사용 (권장)

`docker-compose.yml` 파일을 생성하여 사용할 수 있습니다:

```yaml
version: '3.8'
services:
  frontend:
    build: .
    ports:
      - "3000:3000"
    environment:
      - NODE_ENV=production
      - NEXT_PUBLIC_API_URL=http://backend:8000
    depends_on:
      - backend

  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://user:password@db:5432/patents
    depends_on:
      - db

  db:
    image: postgres:15-alpine
    environment:
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=password
      - POSTGRES_DB=patents
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  postgres_data:
```

실행:

```bash
docker-compose up -d
```

## 프로젝트 구조

```
test_app/
├── app/                       # Next.js App Router
│   ├── admin/                # 관리자 페이지
│   │   └── page.tsx         # 관리자 대시보드
│   ├── history/             # 히스토리 페이지
│   │   ├── page.tsx        # 분석 히스토리
│   │   └── loading.tsx     # 로딩 UI
│   ├── login/              # 로그인 페이지
│   │   └── page.tsx       # 로그인 폼
│   ├── search/            # 검색 페이지
│   │   ├── page.tsx      # 특허 검색 인터페이스
│   │   └── loading.tsx   # 로딩 UI
│   ├── layout.tsx        # 루트 레이아웃
│   ├── page.tsx          # 홈 페이지
│   ├── loading.tsx       # 전역 로딩 UI
│   └── globals.css       # 전역 스타일
├── components/           # React 컴포넌트
│   ├── ui/              # UI 컴포넌트 (shadcn/ui)
│   ├── main-layout.tsx  # 메인 레이아웃 컴포넌트
│   └── theme-provider.tsx # 다크모드 테마 프로바이더
├── hooks/               # Custom React Hooks
│   ├── use-mobile.ts    # 모바일 감지 훅
│   └── use-toast.ts     # Toast 알림 훅
├── lib/                 # 유틸리티 함수
│   └── utils.ts         # 공통 유틸리티
├── public/              # 정적 파일
│   ├── placeholder-logo.png
│   ├── placeholder-logo.svg
│   ├── placeholder-user.jpg
│   └── *.jpg            # 기타 이미지 파일
├── styles/              # 스타일 파일
│   └── globals.css      # 전역 CSS
├── .dockerignore        # Docker 빌드 제외 파일
├── .gitignore          # Git 제외 파일
├── Dockerfile          # Docker 설정
├── next.config.mjs     # Next.js 설정
├── package.json        # npm 패키지 설정
├── requirements.txt    # Python 패키지 설정
└── tsconfig.json       # TypeScript 설정
```

## 주요 기능

### 1. 특허 검색 및 분석
- AI 기반 특허 문서 분석
- 고급 검색 필터링
- 실시간 검색 결과

### 2. 관리자 대시보드
- 시스템 통계 및 모니터링
- 사용자 관리
- 데이터 분석 리포트

### 3. 분석 히스토리
- 과거 분석 결과 조회
- 분석 데이터 내보내기
- 결과 비교 및 트렌드 분석

### 4. 사용자 인증
- 로그인/로그아웃
- 세션 관리
- 권한 기반 접근 제어

### 5. 반응형 디자인
- 모바일/태블릿/데스크톱 지원
- 다크모드 지원
- 접근성 준수

## 사용 기술

### Frontend
- **Next.js 15.2.4**: React 프레임워크 (App Router)
- **React 19**: UI 라이브러리
- **TypeScript 5**: 타입 안정성
- **Tailwind CSS 4**: 유틸리티 우선 CSS 프레임워크

### Backend (Optional)
- **FastAPI 0.115.5**: 고성능 Python 웹 프레임워크
- **Uvicorn 0.34.0**: ASGI 서버
- **SQLAlchemy 2.0.36**: ORM
- **Pydantic 2.10.5**: 데이터 검증

### UI 컴포넌트
- **Radix UI**: 접근성 높은 UI 컴포넌트
- **shadcn/ui**: 재사용 가능한 UI 컴포넌트
- **Lucide React**: 아이콘 라이브러리
- **Next Themes**: 다크모드 지원

### 폼 & 유효성 검사
- **React Hook Form**: 폼 관리
- **Zod**: 스키마 유효성 검사

### 차트 & 시각화
- **Recharts**: 데이터 시각화

### 데이터 처리
- **Pandas 2.2.3**: 데이터 분석
- **NumPy 2.2.1**: 수치 계산

### 스타일링
- **class-variance-authority**: 컴포넌트 변형 관리
- **tailwind-merge**: Tailwind 클래스 병합
- **tailwindcss-animate**: 애니메이션 유틸리티

## 환경 변수

`.env.local` 파일을 생성하여 환경 변수를 설정하세요:

```bash
# Frontend
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_APP_NAME=Patent Analysis System

# Backend (필요시)
DATABASE_URL=postgresql://user:password@localhost:5432/patents
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# AI/ML API Keys (필요시)
# OPENAI_API_KEY=sk-...
# ANTHROPIC_API_KEY=...
```

## 문제 해결

### npm install 실패

의존성 충돌이 발생하는 경우:

```bash
# 기존 node_modules 및 lock 파일 삭제
rm -rf node_modules package-lock.json

# 재설치
npm install --legacy-peer-deps
```

또는 강제 설치:

```bash
npm install --force
```

### conda 환경이 활성화되지 않음

```bash
# conda 초기화
conda init bash

# 터미널 재시작 후
conda activate final_project
```

### Python 패키지 설치 실패

```bash
# conda 환경이 활성화된 상태에서
pip install --upgrade pip
pip install -r requirements.txt
```

### Docker 빌드 실패

캐시를 무시하고 다시 빌드:

```bash
docker build --no-cache -t patent-analysis-system .
```

### 포트가 이미 사용 중인 경우

```bash
# 3000번 포트 사용 프로세스 확인
lsof -i :3000

# 프로세스 종료
kill -9 <PID>
```

## 성능 최적화

### 프로덕션 빌드 최적화
- Standalone output 모드 활성화
- 이미지 최적화 (unoptimized: true 설정 제거 권장)
- TypeScript 빌드 오류 확인 (ignoreBuildErrors 제거 권장)

### 권장 설정

`next.config.mjs` 프로덕션 설정:

```javascript
const nextConfig = {
  output: 'standalone',
  // typescript: {
  //   ignoreBuildErrors: false, // 프로덕션에서는 false 권장
  // },
  images: {
    unoptimized: false, // 프로덕션에서는 최적화 활성화
    domains: ['yourdomain.com'], // 외부 이미지 도메인
  },
  compress: true,
  poweredByHeader: false,
}
```

## 개발 팁

### Hot Reload
개발 모드에서 파일 변경 시 자동으로 새로고침됩니다.

### TypeScript 타입 체크
```bash
# 타입 체크만 실행
npx tsc --noEmit
```

### 컴포넌트 추가
```bash
# shadcn/ui 컴포넌트 추가
npx shadcn@latest add <component-name>
```

## 배포

### Vercel 배포 (권장)
```bash
# Vercel CLI 설치
npm i -g vercel

# 배포
vercel
```

### 기타 플랫폼
- **AWS**: Amplify, ECS, EC2
- **Google Cloud**: App Engine, Cloud Run
- **Azure**: App Service
- **Netlify**: Next.js 지원

## 추가 정보

- [Next.js 문서](https://nextjs.org/docs)
- [React 문서](https://react.dev)
- [Tailwind CSS 문서](https://tailwindcss.com/docs)
- [shadcn/ui 문서](https://ui.shadcn.com)
- [FastAPI 문서](https://fastapi.tiangolo.com)

## 라이선스

이 프로젝트는 private 프로젝트입니다.

## 지원

문제가 발생하거나 질문이 있으신 경우 이슈를 등록해주세요.
