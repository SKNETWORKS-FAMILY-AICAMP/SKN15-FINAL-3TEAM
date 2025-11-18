# RAG 시스템 배포 가이드

PostgreSQL pgvector + Runpod 모델 서버 기반 특허 RAG 시스템 배포 가이드

---

## 📋 목차

1. [아키텍처 개요](#아키텍처-개요)
2. [사전 준비](#사전-준비)
3. [Runpod 모델 서버 배포](#runpod-모델-서버-배포)
4. [AWS 백엔드 서버 설정](#aws-백엔드-서버-설정)
5. [데이터 마이그레이션](#데이터-마이그레이션)
6. [테스트 및 검증](#테스트-및-검증)
7. [트러블슈팅](#트러블슈팅)

---

## 🏗️ 아키텍처 개요

```
┌─────────────────┐
│  Next.js 프론트  │
│  (AWS EC2)      │
└────────┬────────┘
         │
         ▼
┌─────────────────┐      ┌──────────────────┐
│  Django 백엔드   │─────→│  PostgreSQL RDS  │
│  (AWS EC2)      │      │  + pgvector      │
│  - RAG 클라이언트│      │  61,000 특허     │
└────────┬────────┘      └──────────────────┘
         │
         ▼
┌─────────────────┐
│  Runpod 모델서버│
│  (GPU)          │
│  - BGE-M3       │
│  - 분류 모델     │
│  - LLM          │
└─────────────────┘
```

---

## 🔧 사전 준비

### 1. 필요한 파일

- `rag.zip` (1GB) - FAISS 인덱스 + 코퍼스
- Runpod 계정 (GPU Pod 생성용)
- AWS RDS PostgreSQL 16 (pgvector 지원)

### 2. 로컬에서 코드 커밋

```bash
cd /home/juhyeong/workspace/final_project/SKN15-FINAL-3TEAM

# 변경사항 확인
git status

# 추가
git add .

# 커밋
git commit -m "Add RAG system with Runpod integration

- Add PatentRAGDocument model with pgvector support
- Add Runpod FastAPI model server
- Add RAG service client in Django
- Integrate RAG with chatbot
- Add FAISS to PostgreSQL migration script"

# 푸시
git push origin main
```

---

## 🚀 Runpod 모델 서버 배포

### Step 1: Runpod Pod 생성

1. [Runpod](https://www.runpod.io/) 로그인
2. "Deploy" → "GPU Pods" 클릭
3. GPU 선택:
   - 권장: **RTX 3090** (24GB VRAM, ~$0.34/hr)
   - 또는: **RTX A4000** (16GB VRAM, ~$0.29/hr)
4. Template: **PyTorch 2.0+** 선택
5. Disk: **50GB** 이상
6. "Deploy" 클릭

### Step 2: Pod 접속 및 코드 배포

```bash
# Runpod 웹 터미널에서

# 저장소 클론
git clone https://github.com/your-repo/SKN15-FINAL-3TEAM.git
cd SKN15-FINAL-3TEAM/runpod_model_server

# 패키지 설치
pip install -r requirements.txt

# 서버 실행 (백그라운드)
nohup python main.py > model_server.log 2>&1 &

# 로그 확인
tail -f model_server.log
```

### Step 3: 공개 URL 확인

1. Runpod 대시보드에서 Pod 선택
2. "TCP Port Mappings" 섹션 확인
3. Port `8001`의 공개 URL 복사
   - 예: `https://abc123-8001.proxy.runpod.net`

### Step 4: 서버 테스트

```bash
# 헬스 체크
curl https://abc123-8001.proxy.runpod.net/health

# 임베딩 테스트
curl -X POST https://abc123-8001.proxy.runpod.net/embed \
  -H "Content-Type: application/json" \
  -d '{"text": "자동차 관련 특허"}'
```

---

## ⚙️ AWS 백엔드 서버 설정

### Step 1: 코드 업데이트

```bash
# SSH로 AWS 백엔드 서버 접속
ssh -i your-key.pem ec2-user@52.79.153.131

# 코드 업데이트
cd /path/to/SKN15-FINAL-3TEAM
git pull origin main

# conda 환경 활성화
conda activate patent_backend

# 새 패키지 설치
pip install pgvector sentence-transformers faiss-cpu
```

### Step 2: .env 설정

```bash
cd patent_backend
nano .env
```

다음 내용 추가/수정:

```bash
# Chatbot Model Settings
CHATBOT_SERVICE=rag

# Runpod 모델 서버 URL (위에서 복사한 URL)
MODEL_SERVER_URL=https://abc123-8001.proxy.runpod.net
```

### Step 3: RDS에 pgvector 확장 설치

```bash
# RDS에 연결
PGPASSWORD=3-bengio123 psql \
  -h my-patent-db.c9iw88yiic4o.ap-northeast-2.rds.amazonaws.com \
  -U postgres \
  -d patent_db

# pgvector 확장 설치
CREATE EXTENSION IF NOT EXISTS vector;

# 확인
\dx vector

# 종료
\q
```

### Step 4: Django 마이그레이션

```bash
cd /path/to/SKN15-FINAL-3TEAM/patent_backend

# 마이그레이션 적용
python manage.py migrate patents

# 테이블 확인
PGPASSWORD=3-bengio123 psql \
  -h my-patent-db.c9iw88yiic4o.ap-northeast-2.rds.amazonaws.com \
  -U postgres \
  -d patent_db \
  -c "\d patent_rag_documents"
```

---

## 💾 데이터 마이그레이션

### Step 1: rag.zip 업로드

```bash
# 로컬에서 AWS 서버로 파일 전송 (약 1GB, 시간 소요)
scp -i your-key.pem \
  /home/juhyeong/workspace/final_project/rag.zip \
  ec2-user@52.79.153.131:/home/ec2-user/
```

### Step 2: 압축 해제

```bash
# AWS 서버에서
cd /home/ec2-user
unzip rag.zip -d rag_extracted

# 파일 확인
ls -lh rag_extracted/
# corpus.csv (317MB)
# index_ip_bgem3_v2.faiss (766MB)
# doc_ids_bgem3_v2.npy (1.6MB)
```

### Step 3: 마이그레이션 스크립트 수정

```bash
cd /path/to/SKN15-FINAL-3TEAM/patent_backend
nano migrate_rag_to_postgres.py
```

RAG_DIR 경로를 다음과 같이 수정:

```python
# 수정 전
RAG_DIR = '/home/juhyeong/workspace/final_project/rag_extracted'

# 수정 후
RAG_DIR = '/home/ec2-user/rag_extracted'
```

### Step 4: 마이그레이션 실행

```bash
# 백엔드 디렉토리에서
cd /path/to/SKN15-FINAL-3TEAM/patent_backend

# 마이그레이션 실행 (약 30-60분 소요)
conda activate patent_backend
python migrate_rag_to_postgres.py

# 진행 상황 확인
# - 총 61,492개 문서 처리
# - 1000개씩 배치로 저장
# - 벡터 인덱스 자동 생성
```

### Step 5: 마이그레이션 검증

```bash
# PostgreSQL에서 확인
PGPASSWORD=3-bengio123 psql \
  -h my-patent-db.c9iw88yiic4o.ap-northeast-2.rds.amazonaws.com \
  -U postgres \
  -d patent_db

-- 총 문서 수 확인
SELECT COUNT(*) FROM patent_rag_documents;
-- 예상 결과: 61492

-- 샘플 데이터 확인
SELECT doc_id, title_ko, array_length(embedding, 1) as dim
FROM patent_rag_documents
LIMIT 5;

-- 인덱스 확인
\d patent_rag_documents
```

---

## ✅ 테스트 및 검증

### 1. Runpod 모델 서버 테스트

```bash
curl https://abc123-8001.proxy.runpod.net/health
```

**예상 응답:**
```json
{
  "status": "healthy",
  "gpu_available": true,
  "device": "cuda"
}
```

### 2. Django RAG 서비스 테스트

```python
# Django shell에서
python manage.py shell

from chatbot.rag_service import RAGService

rag = RAGService()

# 헬스 체크
print(rag.health_check())  # True

# 검색 테스트
results = rag.search("자동차 관련 특허", top_k=3)
for r in results:
    print(f"{r['application_number']}: {r['title_ko']} (유사도: {r['similarity']:.2%})")
```

### 3. 챗봇 API 테스트

```bash
# 챗봇 API 테스트
curl -X POST http://52.79.153.131:8000/api/chatbot/send/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "message": "자동차 관련 특허를 찾아줘",
    "conversation_id": null
  }'
```

### 4. 프론트엔드 테스트

1. http://3-bengio-veraclaim.com 접속
2. 로그인
3. 챗봇에 "특허 검색" 입력
4. RAG 검색 결과 확인

---

## 🔧 트러블슈팅

### 문제 1: pgvector 확장 설치 실패

**증상:**
```
permission denied to create extension "vector"
```

**해결:**
```bash
# postgres 슈퍼유저로 실행
PGPASSWORD=3-bengio123 psql \
  -h my-patent-db.c9iw88yiic4o.ap-northeast-2.rds.amazonaws.com \
  -U postgres \
  -d patent_db \
  -c "CREATE EXTENSION IF NOT EXISTS vector;"
```

### 문제 2: Runpod 모델 서버 연결 실패

**증상:**
```
모델 서버 연결 실패: Connection refused
```

**해결:**
1. Runpod Pod 상태 확인 (Running인지)
2. `MODEL_SERVER_URL`이 올바른지 확인
3. Runpod 웹 터미널에서 서버 로그 확인:
   ```bash
   tail -f model_server.log
   ```

### 문제 3: 마이그레이션 중 메모리 부족

**증상:**
```
MemoryError: Unable to allocate array
```

**해결:**
마이그레이션 스크립트의 `BATCH_SIZE`를 줄임:
```python
# migrate_rag_to_postgres.py
BATCH_SIZE = 500  # 1000 → 500으로 변경
```

### 문제 4: 벡터 검색 결과가 없음

**증상:**
```
죄송합니다. 관련된 특허를 찾지 못했습니다.
```

**원인 및 해결:**
1. 데이터가 제대로 로드되었는지 확인:
   ```sql
   SELECT COUNT(*) FROM patent_rag_documents;
   ```

2. 벡터 인덱스가 생성되었는지 확인:
   ```sql
   \d patent_rag_documents
   ```

3. Runpod 모델 서버가 응답하는지 확인:
   ```bash
   curl https://abc123-8001.proxy.runpod.net/health
   ```

---

## 📊 성능 모니터링

### Runpod GPU 사용률

```bash
# Runpod 웹 터미널에서
nvidia-smi

# 실시간 모니터링
watch -n 1 nvidia-smi
```

### PostgreSQL 쿼리 성능

```sql
-- 벡터 검색 성능 확인
EXPLAIN ANALYZE
SELECT *
FROM patent_rag_documents
ORDER BY embedding <=> '[0.1, 0.2, ...]'::vector
LIMIT 5;
```

### Django 로그

```bash
# 백엔드 서버에서
tail -f /path/to/patent_backend/logs/django.log
```

---

## 💡 팁

1. **Runpod 비용 절감:**
   - 사용하지 않을 때 Pod 정지
   - Spot Instance 사용 (더 저렴)

2. **검색 속도 향상:**
   - `ivfflat` 인덱스 리스트 수 조정 (100 → 200)
   - 배치 임베딩 사용

3. **모니터링:**
   - Runpod 대시보드에서 GPU 사용률 확인
   - CloudWatch로 RDS 성능 모니터링

---

## 📝 다음 단계

- [ ] 분류 모델 추가 (Runpod 서버에)
- [ ] 캐싱 시스템 구축 (Redis)
- [ ] 검색 결과 하이라이팅
- [ ] 특허 유사도 시각화

---

**문의:** 문제 발생 시 GitHub Issues에 등록해주세요.
