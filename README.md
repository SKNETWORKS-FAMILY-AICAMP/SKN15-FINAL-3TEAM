## 👨‍👩‍👧‍👦 조원 명단

<div align="center">
<table>
  <tr>
    <td align="center" width="200">
      <img src="" width="120" height="120">
      <h3>조솔찬</h3>
    </td>
    <td align="center" width="200">
      <img src="" width="120" height="120">
      <h3>노건우</h3>
    </td>
    <td align="center" width="200">
      <img src="" width="120" height="120">
      <h3>김주형</h3>
    </td>
    <td align="center" width="200">
      <img src="" width="120" height="120">
      <h3>이소정</h3>
    </td>
    <td align="center" width="200">
      <img src="" width="120" height="120">
      <h3>미정</h3>
    </td>
  </tr>
</table>
</div>


## 🔍 프로젝트 개요

<div align="center">
  <table>
    <tr>
      <td align="center">
        <h3>🎯 목표</h3>
        <p>특허 청구항, 거절결정서, 법령·심사기준을 통합하여<br/>특허 등록 가능성을 자동으로 분석하는 사내 AI 허브 구축</p>
      </td>
      <td align="center">
        <h3>💡 해결 과제</h3>
        <p>흩어진 특허/법령 데이터를 한 곳에 모으고,<br/>전문가가 아니면 이해하기 어려운 거절 사유와 법적 근거를<br/>AI가 대신 판별·요약</p>
      </td>
      <td align="center">
        <h3>🚀 혁신</h3>
        <p>RAG + 자체 LLM(분류/근거생성)을 결합하여<br/>“등록/거절 예측 + 이유 설명 + 개선 인사이트”를<br/>원샷으로 제공하는 특허 특화 AI 어시스턴트</p>
      </td>
    </tr>
  </table>
</div>



## 🎯 프로젝트 목표

<div align="center">
  <h3>특허 검토 전 과정을 돕는 ‘TtalKkak AI’ 구축</h3>
</div>

<div align="center">
<table>
  <tr>
    <td align="center">
      <h3>1️⃣</h3>
      <b>등록 가능성 자동 분류</b><br/>
      사용자 청구항 입력만으로 등록/거절 예측 및 신뢰도 반환
    </td>
    <td align="center">
      <h3>2️⃣</h3>
      <b>유사·선행 문헌 자동 검색</b><br/>
      FAISS 기반 유사 청구항·거절 사례 탐색으로 근거 확보
    </td>
    <td align="center">
      <h3>3️⃣</h3>
      <b>거절 사유·개선안 리포트 생성</b><br/>
      거절 이유, 관련 조문, 개선 방향을 자연어 리포트로 제공
    </td>
  </tr>
</table>
</div>

## ✨ 핵심 기능

### 1️⃣ 입력 청구항 기반 유사 특허 판별

사용자가 **직접 작성한 특허 청구항**을 입력하면,  
유사 특허를 찾아주고 LLM이 **얼마나 유사한지**를 함께 판정합니다.

**동작 방식**

1. **후보 특허 검색**
   - 입력 청구항 → 임베딩 벡터로 변환 (예: multilingual-e5-base)
   - FAISS Vector DB에서 코사인 유사도 기준 Top-K 특허 검색
   - 출원번호, 발명의 명칭, 대표 청구항, 요약 정보까지 함께 조회

2. **LLM 유사성 판정**
   - 입력 청구항 vs 후보 청구항들을 Qwen 기반 LLM으로 비교
   - “매우 유사 / 부분 유사 / 비유사” 또는 **0~1 사이 점수** 형태로 표현
   - 어떤 구성 요소가 겹치는지, 기술적 차이는 무엇인지 **설명 텍스트**로 제공

3. **리포트 출력**
   - 상위 유사 특허 목록 + 유사도 점수 표 형태 정렬
   - 유사도가 높은(위험도 높은) 특허를 상단에 노출
   - “등록 가능성 관점에서 주의할 점”을 짧은 요약으로 제공


---

### 2️⃣ 키워드 · 문장 기반 유사 특허 검색

**키워드 한두 개**부터 **자연어 문장**까지 자유롭게 입력하면,  
그 의미에 가장 가까운 특허들을 **유사도 순으로 검색**할 수 있습니다.

**검색 입력 예시**

- 키워드: `게임 보상 시스템`, `칩 계측 장치`, `파친코`
- 문장: `AI를 활용해서 오프라인 매장에서 고객 행동을 분석하고 보상을 주는 시스템`

**동작 방식**

1. **자연어 질의 처리**
   - 질의를 그대로 임베딩(문장 단위)으로 변환
   - 단순 키워드 매칭이 아닌, **문장 의미 기반** 유사도 계산

2. **벡터 기반 의미 검색**
   - 특허 전체 코퍼스를 벡터 공간에서 비교
   - IPC/CPC 코드가 달라도, **기능·구성 관점에서 유사한 특허**를 찾아냄
   - (옵션) 법적 상태(등록/거절), 출원일, 분야 필터와 함께 사용 가능

3. **결과 표시**
   - 발명의 명칭, 출원번호, 요약, 대표 청구항을 리스트/카드 형태로 노출
   - 유사도 점수와 함께 상위 N개 결과를 정렬
   - 선택 시 상세 페이지에서 **전문·거절 이유·관련 조문**까지 연동 가능


## 🛠️ 기술 스택

<table align="center">
  <tr>
    <th>Category</th>
    <th>Technologies</th>
  </tr>

  <!-- Languages -->
  <tr>
    <td><b>Programming Languages</b></td>
    <td>
      <img src="https://img.shields.io/badge/Python-3776AB?logo=python&logoColor=white&style=flat-square" />
      <img src="https://img.shields.io/badge/JavaScript-F7DF1E?logo=javascript&logoColor=black&style=flat-square" />
    </td>
  </tr>

  <!-- Frameworks & Libraries -->
  <tr>
    <td><b>Frameworks & Libraries</b></td>
    <td>
      <img src="https://img.shields.io/badge/Django%20REST-092E20?logo=django&logoColor=white&style=flat-square" />
      <img src="https://img.shields.io/badge/React-61DAFB?logo=react&logoColor=black&style=flat-square" />
      <img src="https://img.shields.io/badge/FastAPI-009688?logo=fastapi&logoColor=white&style=flat-square" />
      <img src="https://img.shields.io/badge/sentence--transformers-000000?style=flat-square" />
      <img src="https://img.shields.io/badge/FAISS-005571?style=flat-square" />
    </td>
  </tr>

  <!-- AI / Models -->
  <tr>
    <td><b>AI / Models</b></td>
    <td>
      <img src="https://img.shields.io/badge/Qwen2.5-7B%2F14B-512BD4?style=flat-square" />
      <img src="https://img.shields.io/badge/QLoRA-FF6F00?style=flat-square" />
      <img src="https://img.shields.io/badge/PyTorch-EE4C2C?logo=pytorch&logoColor=white&style=flat-square" />
      <img src="https://img.shields.io/badge/Transformers-FFD54F?style=flat-square" />
      <img src="https://img.shields.io/badge/PEFT-2962FF?style=flat-square" />
      <img src="https://img.shields.io/badge/multilingual--e5--base-00897B?style=flat-square" />
    </td>
  </tr>

  <!-- DB & Storage -->
  <tr>
    <td><b>Databases & Storage</b></td>
    <td>
      <img src="https://img.shields.io/badge/MySQL-4479A1?logo=mysql&logoColor=white&style=flat-square" />
      <img src="https://img.shields.io/badge/CSV-0277BD?style=flat-square" />
      <img src="https://img.shields.io/badge/JSONL-795548?style=flat-square" />
      <img src="https://img.shields.io/badge/FAISS%20Vector%20Index-005571?style=flat-square" />
    </td>
  </tr>

  <!-- Infra & Tools -->
  <tr>
    <td><b>Infra & Tools</b></td>
    <td>
      <img src="https://img.shields.io/badge/RunPod-4A148C?style=flat-square" />
      <img src="https://img.shields.io/badge/GitHub-181717?logo=github&logoColor=white&style=flat-square" />
      <img src="https://img.shields.io/badge/Docker-2496ED?logo=docker&logoColor=white&style=flat-square" />
      <img src="https://img.shields.io/badge/dotenv-556B2F?style=flat-square" />
    </td>
  </tr>
</table>


## 📊 데이터

### 📚 1) 수집 대상 & 규모

<table align="center">
  <tr>
    <th>데이터셋</th>
    <th>규모</th>
    <th>특징</th>
  </tr>
  <tr>
    <td><b>특허 데이터 (patents.csv)</b></td>
    <td>약 61,000건</td>
    <td>출원번호 기준 중복 제거, 청구항·요약·법적 상태 등 메타데이터 포함</td>
  </tr>
  <tr>
    <td><b>거절결정서/의견제출통지서 (reject.jsonl 등)</b></td>
    <td>약 8,500건</td>
    <td>PDF → 텍스트 추출, 페이지 단위 JSONL 저장, 거절 사유 패턴 분석에 활용</td>
  </tr>
  <tr>
    <td><b>법령·심사기준·논문</b></td>
    <td>법령 9건, 심사기준 21건, 논문 약 210건</td>
    <td>특허법·심사기준 조문 및 관련 논문 텍스트로 법적 근거 및 배경지식 제공</td>
  </tr>
</table>


### 🔧 2) 전처리/정합성

- **형식 통일**
  - PDF/CSV → JSON/JSONL/CSV 스키마 통합

- **중복 제거**
  - 출원번호 · `doc_id` 기준 중복 레코드 제거

- **결측 처리**
  - 핵심 필드(청구항 텍스트, 거절 사유)가 없는 경우 행 제거  
  - 선택 필드는 `"결측"` 플래그 또는 별도 컬럼으로 관리

- **이상치 탐지**
  - 잘못된 날짜(미래 시점, 역전된 일자) 제거  
  - 존재하지 않는 출원번호 제거  
  - 비정상 길이 텍스트 제거

- **품질 점검**
  - 특허 / 거절이력 / 법령 간 교차 검증  
  - 샘플링 기반 수작업 점검 및 룰셋 보강


### 💾 3) 저장

- **Raw 데이터**
  - `/data/raw/…` 경로에 원본 CSV/PDF/JSONL 보관

- **정제 데이터**
  - 학습용: `train.jsonl`, `val.jsonl`, `test.jsonl`  
  - RAG용: `claim_text.csv`, `reject.jsonl`, `law.csv` 등

- **Vector Index**
  - `rag/index/faiss.index`  
  - `rag/index/id_map.npy`


### 📜 4) 라이선스/출처

- **특허/거절 데이터**
  - KIPRIS 공개 특허 데이터, 비상업·연구·교육 목적 활용
- **법령 데이터**
  - AI Hub 및 공공 데이터 포털
- **논문 데이터**
  - arXiv 공개 논문 메타/전문 활용
- 상기 데이터는 서비스 외부 배포가 아닌 **내부 PoC/교육용**으로만 사용


### 🔄 데이터처리 파이프라인

1. 외부 데이터 수집 (API 호출/크롤링/파일 업로드)
2. 스키마 정규화 및 타입 변환 (날짜/텍스트/정수)
3. 결측/이상치 처리 및 중복 제거
4. 학습/검증/테스트 세트 분리
5. 임베딩 생성 및 FAISS 인덱싱
6. LLM 학습/평가에 투입 및 서비스에 연동


## 🤖 모델 구성

<div align="center">
  <table>
    <tr>
      <th>분류 LLM (등록/거절)</th>
      <th>근거 생성 LLM</th>
      <th>RAG · 서비스 LLM</th>
    </tr>
    <tr>
      <td>
        • Base Model: Qwen/Qwen2.5-7B-Instruct<br/>
        • 언어: 한국어 중심(멀티링구얼 지원)<br/>
        • Fine-tuning: LoRA (q_proj, v_proj)<br/>
        • Task: 특허 청구항 등록/거절 이진 분류<br/>
        • 지표: Accuracy 0.86, F1 0.87
      </td>
      <td>
        • Base Model: Qwen/Qwen2.5-14B-Instruct<br/>
        • Fine-tuning: QLoRA (4bit, NF4)<br/>
        • Task: 거절 사유·근거 설명문 생성<br/>
        • 평가: GPTScore 4.35 수준의 자연스러운 설명 품질
      </td>
      <td>
        • Models: Qwen 14B (분류결과+RAG 컨텍스트 기반 리포트 생성)<br/>
        • Fine-tuning: LoRA 어댑터 + 프롬프트 최적화<br/>
        • Quantization: 4-bit (QLoRA)로 추론 비용 절감<br/>
        • 컨텍스트: 최대 8K 토큰 (청구항 + 유사문헌 요약 포함)
      </td>
    </tr>
  </table>
</div>


## 📐 ERD

### 서비스의 데이터베이스 구조

- **주요 엔터티**
  - `users`, `roles`, `permissions`, `user_role_map`
  - `patents`, `rejection_decisions`, `rejection_reasons`
  - `patent_laws`, `examination_criteria`
  - `user_sessions`, `user_queries`
  - `keyword_search_logs`, `chatbot_logs`, `admin_page_logs`

- ERD 예시는 `docs/erd.png` (또는 ERD 이미지 파일)로 관리


## 🏗️ 시스템 아키텍처

### TtalKkak AI 프로젝트 관리 시스템의 전체 아키텍처

<div align="center">
  <p>React Frontend – Django REST API – RAG 모듈 – LLM 서버(Qwen) – DB(MySQL/FAISS)의 계층적 구조</p>
</div>


### 📋 주요 구성 요소

- **클라이언트 레이어**
  - React 기반 SPA  
  - 청구항 입력, 분석 결과 리포트, 로그 조회 UI 제공

- **백엔드 API 레이어**
  - Django REST Framework  
  - `/chatbot/send-message` 등 API 엔드포인트 제공  
  - 요청 타입(일반 대화 vs 특허 분석) 분기 처리

- **AI 처리 엔진**
  - RAG 모듈 (임베딩 + FAISS 검색)  
  - 분류 LLM, 근거 생성 LLM 호출  
  - 프롬프트 구성 및 응답 포맷팅

- **데이터 레이어**
  - MySQL (사용자/특허/거절/법령/로그 테이블)  
  - 파일 스토리지 및 Vector Index(FAISS)

- **비즈니스 서비스**
  - 특허 등록 가능성 스코어링  
  - 거절 사유 추론 및 조문 매칭  
  - 검색/상담 이력 기반 인사이트 도출

- **외부 서비스 연동**
  - KIPRIS, AI Hub, arXiv 등에서 초기 데이터 수집  
  - RunPod/HuggingFace Hub를 통한 LLM 서빙


## 🔄 시퀀스 다이어그램

### 1️⃣ 사용자 청구항 입력

1. 사용자가 웹 UI에서 특허 청구항 텍스트 입력  
2. (선택) 관련 키워드/분야(CPC, IPC 등) 같이 입력  
3. Django REST API에 `/chatbot/send-message` 요청 전송

### 2️⃣ 벡터 검색 & 분류 모델 처리

1. 백엔드에서 입력 텍스트를 임베딩 모델(`multilingual-e5-base`)로 벡터화  
2. FAISS Vector DB에서 유사 청구항 Top-K 검색  
3. 검색 결과를 바탕으로 분류 LLM(Qwen 7B)에게 등록/거절 예측 요청  
4. 분류 결과(예: “거절”)와 신뢰도(score)를 반환

### 3️⃣ 근거 생성 LLM 호출

1. 백엔드는 분류 결과 + 유사 청구항 요약 + 메타데이터(출원번호 등)를 묶어 프롬프트 구성  
2. 근거 생성 LLM(Qwen 14B QLoRA)에 호출  
3. 신규성/진보성/명세서 기재 불비 등 위반 항목과 주요 근거를 한 단락으로 생성

#### 주요 처리 단계 (요약)

text
[React] 사용자 입력
  → [Django API] 요청 수신 및 타입 분류
    → [RAG 모듈] 임베딩 + FAISS 검색
      → [분류 LLM] 등록/거절 예측
        → [근거 LLM] 거절 사유·개선안 생성
          → [Django API] 응답 포맷팅
            → [React] 리포트 UI 렌더링 및 히스토리 저장

### 4️⃣ 결과 저장 & 통합

- 질의/응답, 분류 결과, 사용된 선행문헌 목록을  
  `user_sessions`, `user_queries`, `chatbot_logs` 등에 저장  
- 추후 모델 재학습 및 성능 분석, 사용 행태 분석에 활용


### 5️⃣ 시스템 성능 지표

<div align="center">
  <table>
    <tr>
      <td align="center">
        <h3>⏱️</h3>
        <b>평균 처리 시간</b><br/>
        (요청 → 응답)
      </td>
      <td align="center">
        <h3>🎙️</h3>
        <b>STT 지연 시간</b><br/>
        (향후 음성 입력 확장 시 기준)
      </td>
      <td align="center">
        <h3>🤖</h3>
        <b>LLM 처리</b><br/>
        (분류 + 근거 생성)
      </td>
      <td align="center">
        <h3>📋</h3>
        <b>Task 분석 지연</b><br/>
        (RAG + 전처리)
      </td>
    </tr>
    <tr>
      <td align="center">
        <h3>📝</h3>
        평균 3~5초/요청
      </td>
      <td align="center">
        <h3>🚀</h3>
        <b>동시 처리</b><br/>
        10개 세션 기준 실험
      </td>
      <td align="center">
        <h3>📊</h3>
        <b>정확도</b><br/>
        분류 Accuracy 약 86~90%
      </td>
      <td align="center">
        <h3>💾</h3>
        <b>처리 용량</b><br/>
        세션당 약 100MB 이내
      </td>
    </tr>
  </table>
</div>

## 📱 실행 화면

### 🏠 랜딩페이지

- 서비스 소개, 주요 기능, 사용 플로우 안내 섹션 구성   

### 📊 대시보드

- 최근 질의 목록, 분류 결과 통계(등록/거절 비율) 표시  
- 데이터 소스 별(특허/거절/법령) 사용 현황 및 로그 요약  

### 🎬 시연영상



