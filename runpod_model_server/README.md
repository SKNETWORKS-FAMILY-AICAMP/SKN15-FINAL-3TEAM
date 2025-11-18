# Runpod 모델 서버

**전체 RAG 파이프라인을 서빙하는 FastAPI 서버**

- BGE-M3 임베딩 모델
- Qwen2.5-7B 분류 모델 (LoRA)
- Qwen2.5-14B 챗봇 모델 (LoRA)

---

## 📋 배포 준비

### 1. 필요한 파일

- `classifiaction.zip` (36MB) - Qwen2.5-7B 분류 LoRA 어댑터
- `Qwen-14B-checkpoint-16-20251114T001419Z-1-001.zip` (43MB) - Qwen2.5-14B 챗봇 LoRA 어댑터

### 2. Runpod GPU Pod 생성

1. [Runpod](https://www.runpod.io/) 로그인
2. "Deploy" → "GPU Pods" 선택
3. **GPU 선택 (중요!):**
   - **권장: RTX A5000** (24GB VRAM, ~$0.34/hr)
   - 또는: **RTX A6000** (48GB VRAM, ~$0.79/hr)
   - 최소: **RTX 3090** (24GB VRAM, ~$0.34/hr)

   > **⚠️ 중요:** Qwen2.5-14B는 약 15-20GB VRAM 필요, 분류 모델은 약 7-10GB 필요
   > 총 VRAM: 최소 24GB 이상 (RTX 3090, A5000, A6000)

4. Template: **PyTorch 2.0+** 선택
5. Disk: **100GB** 이상
6. "Deploy" 클릭

---

## 🚀 Runpod 서버 배포

### Step 1: Pod 접속

Runpod 웹 터미널에서 실행:

```bash
# 저장소 클론
git clone https://github.com/your-repo/SKN15-FINAL-3TEAM.git
cd SKN15-FINAL-3TEAM/runpod_model_server
```

### Step 2: 모델 파일 업로드

```bash
# 로컬에서 Runpod로 모델 파일 전송
# 방법 1: SCP (Runpod SSH 사용)
scp -P <RUNPOD_SSH_PORT> \
  /path/to/classifiaction.zip \
  root@<RUNPOD_IP>:/workspace/

scp -P <RUNPOD_SSH_PORT> \
  "/path/to/Qwen-14B-checkpoint-16-20251114T001419Z-1-001.zip" \
  root@<RUNPOD_IP>:/workspace/

# 방법 2: 직접 다운로드 (Google Drive/Dropbox 링크)
cd /workspace
wget "YOUR_GOOGLE_DRIVE_LINK" -O classifiaction.zip
wget "YOUR_GOOGLE_DRIVE_LINK" -O qwen-14b.zip
```

### Step 3: 모델 압축 해제 및 배치

```bash
cd /workspace

# 분류 모델 압축 해제
mkdir -p models/classification
unzip classifiaction.zip -d models/classification

# 챗봇 모델 압축 해제
mkdir -p models/qwen-14b-temp
unzip "Qwen-14B-checkpoint-16-20251114T001419Z-1-001.zip" -d models/qwen-14b-temp
mv models/qwen-14b-temp/Qwen-14B-checkpoint-16/* models/qwen-14b/

# 확인
ls -lh models/classification/
ls -lh models/qwen-14b/
```

### Step 4: 패키지 설치

```bash
cd /workspace/SKN15-FINAL-3TEAM/runpod_model_server

# 패키지 설치
pip install -r requirements.txt
```

### Step 5: 서버 실행

```bash
# 백그라운드 실행
nohup python main.py > model_server.log 2>&1 &

# 로그 확인
tail -f model_server.log

# 또는 포그라운드 실행 (디버깅용)
python main.py
```

### Step 6: 공개 URL 확인

1. Runpod 대시보드에서 Pod 선택
2. "TCP Port Mappings" 섹션 확인
3. Port `8001`의 공개 URL 복사
   - 예: `https://abc123-8001.proxy.runpod.net`

---

## ✅ 테스트

### 1. 헬스 체크

```bash
curl https://abc123-8001.proxy.runpod.net/health
```

**예상 응답:**
```json
{
  "status": "healthy",
  "gpu_available": true,
  "device": "cuda",
  "models": {
    "embedding": true,
    "classification": true,
    "llm": true
  }
}
```

### 2. 임베딩 테스트

```bash
curl -X POST https://abc123-8001.proxy.runpod.net/embed \
  -H "Content-Type: application/json" \
  -d '{"text": "자동차 관련 특허"}'
```

### 3. 분류 테스트

```bash
curl -X POST https://abc123-8001.proxy.runpod.net/classify \
  -H "Content-Type: application/json" \
  -d '{
    "texts": ["자동차 자동 변속 장치에 관한 발명"],
    "top_k": 3
  }'
```

### 4. LLM 생성 테스트

```bash
curl -X POST https://abc123-8001.proxy.runpod.net/generate \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "자동차 특허에 대해 설명해주세요.",
    "max_length": 200
  }'
```

### 5. 전체 파이프라인 테스트

```bash
curl -X POST https://abc123-8001.proxy.runpod.net/rag/pipeline \
  -H "Content-Type: application/json" \
  -d '{
    "query": "자동차 관련 특허 찾아줘",
    "patents": [
      {
        "application_number": "1019830003182",
        "title_ko": "자동실방울가공장치",
        "ipc": "A63H 3/44",
        "text": "본문 내용..."
      }
    ],
    "use_classification": true,
    "max_length": 512
  }'
```

---

## 📊 성능 모니터링

### GPU 사용률

```bash
# Runpod 웹 터미널에서
nvidia-smi

# 실시간 모니터링
watch -n 1 nvidia-smi
```

### 메모리 사용량

```bash
# GPU 메모리
nvidia-smi --query-gpu=memory.used,memory.total --format=csv

# 시스템 메모리
free -h
```

### 서버 로그

```bash
tail -f /workspace/SKN15-FINAL-3TEAM/runpod_model_server/model_server.log
```

---

## 🔧 트러블슈팅

### 문제 1: CUDA Out of Memory

**증상:**
```
RuntimeError: CUDA out of memory
```

**해결:**
1. 더 큰 VRAM의 GPU 사용 (A6000 48GB)
2. 또는 8비트 양자화 사용:
   ```python
   # main.py 수정
   llm_base_model = AutoModelForCausalLM.from_pretrained(
       llm_base_model_name,
       load_in_8bit=True,  # 8비트 양자화
       device_map="auto"
   )
   ```

### 문제 2: 모델 로드 실패

**증상:**
```
⚠️ 분류 모델 로드 실패: [Errno 2] No such file or directory
```

**해결:**
모델 경로 확인:
```bash
ls -lh /workspace/models/classification/
ls -lh /workspace/models/qwen-14b/
```

### 문제 3: 서버 응답 느림

**원인:** GPU가 아닌 CPU에서 실행 중

**해결:**
```bash
# GPU 사용 가능 확인
python -c "import torch; print(torch.cuda.is_available())"
# True여야 함

# CUDA 버전 확인
nvidia-smi
```

---

## 💡 최적화 팁

### 1. 배치 추론

여러 특허를 한 번에 분류:
```python
# Django에서
patent_texts = [p['text'] for p in patents[:10]]  # 10개씩 배치
response = requests.post(
    f"{MODEL_SERVER_URL}/classify",
    json={"texts": patent_texts, "top_k": 1}
)
```

### 2. 캐싱

자주 검색되는 쿼리는 Redis에 캐싱:
```python
# Django에서
import redis
r = redis.Redis()

cache_key = f"rag:{query_hash}"
cached = r.get(cache_key)
if cached:
    return json.loads(cached)
```

### 3. 비용 절감

- **Spot Instance** 사용 (최대 70% 할인)
- 사용하지 않을 때 Pod 정지
- 자동 스케일링 설정

---

## 📝 API 엔드포인트

### GET /
서버 상태 확인

### POST /embed
단일 텍스트 임베딩

### POST /embed/batch
배치 임베딩

### POST /classify
특허 분류

### POST /generate
LLM 텍스트 생성

### POST /rag/pipeline
**전체 RAG 파이프라인 (메인 엔드포인트)**

**요청:**
```json
{
  "query": "사용자 질문",
  "patents": [검색된 특허 리스트],
  "use_classification": true,
  "max_length": 512
}
```

**응답:**
```json
{
  "query": "사용자 질문",
  "patents_used": 3,
  "classified": true,
  "response": "LLM이 생성한 답변",
  "metadata": {
    "prompt_length": 150,
    "generated_length": 300
  }
}
```

### GET /health
헬스 체크

---

**문의:** GitHub Issues 또는 Runpod 커뮤니티
