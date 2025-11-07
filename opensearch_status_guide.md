# OpenSearch 전체 상태 확인 가이드

## 방법 1: EC2에서 Python 스크립트 실행 (추천)

### 1단계: EC2 접속
```bash
ssh ubuntu@3.37.175.204
cd /home/ubuntu/SKN15-FINAL-3TEAM
```

### 2단계: 최신 코드 pull
```bash
git pull origin main
```

### 3단계: OpenSearch 상태 확인 스크립트 실행
```bash
cd patent_backend
DJANGO_SETTINGS_MODULE=config.settings python3 opensearch_full_status.py
```

**출력 내용:**
- ✅ 모든 인덱스 목록과 문서 수
- 📋 papers 인덱스의 필드 구조 (어떤 필드들이 있는지)
- 📊 날짜 필드 통계 (published_date, created_at 몇 개 있는지)
- 🔍 실제 문서 3개 샘플 (어떻게 저장되어 있는지)
- 📄 JSON 형식으로 문서 1개 전체 내용
- 🎯 최종 진단 (재인덱싱 필요한지 여부)

---

## 방법 2: curl로 간단 확인

### 1. OpenSearch 터널 설정 (별도 터미널)
```bash
ssh ubuntu@3.37.175.204
cd /home/ubuntu/SKN15-FINAL-3TEAM
./start_opensearch_tunnel.sh
```

### 2. 인덱스 목록 확인
```bash
curl -X GET 'https://localhost:9200/_cat/indices?v' \
  -u 'opensearch_admin:3-Bengio123' -k
```

### 3. papers 인덱스 문서 수
```bash
curl -X GET 'https://localhost:9200/papers/_count?pretty' \
  -u 'opensearch_admin:3-Bengio123' -k
```

### 4. papers 인덱스 필드 구조 (매핑)
```bash
curl -X GET 'https://localhost:9200/papers/_mapping?pretty' \
  -u 'opensearch_admin:3-Bengio123' -k
```

### 5. 샘플 문서 1개 보기
```bash
curl -X GET 'https://localhost:9200/papers/_search?pretty&size=1' \
  -u 'opensearch_admin:3-Bengio123' -k
```

### 6. published_date 필드가 있는 문서 수
```bash
curl -X GET 'https://localhost:9200/papers/_count?pretty' \
  -u 'opensearch_admin:3-Bengio123' -k \
  -H 'Content-Type: application/json' \
  -d '{"query":{"exists":{"field":"published_date"}}}'
```

---

## 재인덱싱이 필요한 경우

만약 `published_date` 필드가 0개이거나 일부만 있다면:

```bash
cd /home/ubuntu/SKN15-FINAL-3TEAM/patent_backend

# 재인덱싱 실행
DJANGO_SETTINGS_MODULE=config.settings python3 manage.py reindex_papers

# 완료 후 서비스 재시작
sudo systemctl restart gunicorn
```

---

## 예상 출력 예시

### 정상 상태 (재인덱싱 완료)
```
📅 날짜 필드 통계:
  - published_date 있음: 196개 (100.0%)
  - created_at 있음: 196개 (100.0%)

✅ 모든 문서에 published_date 필드가 있습니다!
   → 날짜 필터와 정렬이 정상 작동합니다.
```

### 문제 상태 (재인덱싱 필요)
```
📅 날짜 필드 통계:
  - published_date 있음: 0개 (0.0%)
  - created_at 있음: 0개 (0.0%)

❌ 문제 발견: papers 인덱스에 published_date 필드가 없습니다!
   → 해결: DJANGO_SETTINGS_MODULE=config.settings python3 manage.py reindex_papers
```

---

## 문서 저장 형식 예시

OpenSearch에 저장된 논문 문서는 다음과 같은 JSON 형식입니다:

```json
{
  "id": 123,
  "title_kr": "잡음이 있는 경우 비균소 게임과 자기 테스트",
  "title_en": "Nonlocal Games and Self-Testing in the Presence of Noise",
  "authors": "Honghao Fu, Minglong Qin, Haochen Xu, Penghui Yao",
  "abstract_kr": "자기 테스트는 특정 비균소 게임의 핵심 특성으로...",
  "abstract_en": "Self-testing is a central feature of certain nonlocal games...",
  "pdf_link": "https://arxiv.org/pdf/...",
  "abstract_page_link": "https://arxiv.org/abs/...",
  "source_file": "arxiv_papers.json",
  "published_date": "2024-05-15",
  "created_at": "2025-01-15T12:30:45.123456",
  "updated_at": "2025-01-15T12:30:45.123456"
}
```

**핵심 필드:**
- `published_date`: 논문 발행일 (날짜 필터, 정렬에 사용)
- `created_at`: DB 저장 시각
- `title_kr`, `abstract_kr`: 한글 검색용
- `title_en`, `abstract_en`: 영문 검색용
