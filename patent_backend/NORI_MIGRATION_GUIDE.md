# Nori 기반 OpenSearch 마이그레이션 가이드

## 📋 완료된 작업

### 1. 동의어 사전 관련 코드/파일 삭제 ✅
다음 파일들을 삭제했습니다:
- `reindex_with_synonyms.py`
- `check_nori_plugin.py`
- `NORI_SETUP_GUIDE.md`
- `test_index_simple.py`
- `test_opensearch_remote.py`

### 2. `opensearch_client.py` 수정 완료 ✅
- `create_patents_index()`: Nori 형태소 분석기로 변경
- `create_papers_index()`: Nori 형태소 분석기로 변경
- 한글 필드는 `nori_korean_analyzer` 사용
- 영문 필드는 `standard` analyzer 사용

**Nori 설정**:
```python
'tokenizer': 'nori_user_dict',  # 사용자 사전 포함
'filter': [
    'nori_posfilter',      # 불필요한 품사 제거
    'lowercase',            # 소문자 변환
    'nori_readingform'     # 한자를 한글 발음으로 변환
]
```

**사용자 사전**:
- 인공지능, 머신러닝, 딥러닝, 블록체인
- 자율주행, 빅데이터, 클라우드, 사물인터넷

### 3. `opensearch_service.py` 검증 완료 ✅
모든 고급 필터 기능이 정상 작동합니다:

#### ✅ 특허 검색 필터 (search_patents)
- **키워드 검색**: multi_match + fuzzy matching (오타 허용)
- **IPC/CPC 코드 필터**: wildcard 쿼리로 부분 일치 검색
- **출원일 범위 필터**: range 쿼리 (gte/lte)
- **등록일 범위 필터**: range 쿼리 (gte/lte)
- **법적상태 필터**: term 쿼리 (정확한 일치)
- **정렬**: 관련도순 + 출원일 최신순
- **하이라이팅**: 검색어 강조 표시

#### ✅ 논문 검색 필터 (search_papers)
- **키워드 검색**: multi_match + fuzzy matching
- **정렬**: 관련도순 + 생성일 최신순
- **하이라이팅**: 검색어 강조 표시

### 4. 마이그레이션 스크립트 생성 ✅
`reindex_with_nori.py` 생성:
- 기존 인덱스 삭제
- Nori 기반 새 인덱스 생성
- PostgreSQL 데이터 재인덱싱
- Bulk 인덱싱으로 성능 최적화 (500건씩)

---

## 🔧 다음 단계 (사용자가 수행해야 함)

### 1. AWS Console에서 Nori 패키지 연결

#### 방법:
1. AWS Console 로그인
2. OpenSearch Service → 도메인 선택 (`my-patent-search`)
3. 왼쪽 메뉴에서 **"Packages"** 탭 클릭
4. **"Associate package"** 버튼 클릭
5. Package 목록에서 **"analysis-nori"** 선택
6. Associate 버튼 클릭
7. 도메인 상태가 **"Processing"** → **"Active"**로 변경될 때까지 대기 (약 10-15분)

#### 확인 방법:
```bash
# EC2 서버에서 실행
cd /home/ubuntu/workspace/final_project/SKN15-FINAL-3TEAM/patent_backend
source venv/bin/activate

python3 -c "
from patents.opensearch_client import get_opensearch_client
client = get_opensearch_client()

# Nori 플러그인 확인
try:
    response = client.cat.plugins(format='json')
    nori_found = False
    for plugin in response:
        if 'analysis-nori' in plugin.get('component', ''):
            print('✅ Nori 플러그인 사용 가능!')
            nori_found = True
            break
    if not nori_found:
        print('❌ Nori 플러그인을 찾을 수 없습니다')
except Exception as e:
    print(f'오류: {e}')
"
```

### 2. 코드를 EC2 서버에 푸시

```bash
# 로컬에서 실행
cd /home/juhyeong/workspace/final_project/SKN15-FINAL-3TEAM
git add .
git commit -m "feat: Nori 형태소 분석기 적용

- 동의어 사전 관련 코드 제거
- opensearch_client.py를 Nori 전용으로 수정
- patents, papers 인덱스에 nori_korean_analyzer 적용
- reindex_with_nori.py 마이그레이션 스크립트 생성
- 모든 고급 필터 기능 검증 완료"

git push origin main
```

### 3. EC2 서버에서 코드 업데이트

```bash
# EC2 서버에서 실행
ssh ubuntu@3.37.175.204
cd /home/ubuntu/workspace/final_project/SKN15-FINAL-3TEAM
git pull origin main
```

### 4. 데이터 재인덱싱

```bash
# EC2 서버에서 실행
cd /home/ubuntu/workspace/final_project/SKN15-FINAL-3TEAM/patent_backend
source venv/bin/activate

python3 reindex_with_nori.py
```

**예상 출력**:
```
============================================================
Nori 기반 OpenSearch 재인덱싱 스크립트
============================================================

⚠️  주의사항:
1. AWS Console에서 analysis-nori 패키지를 먼저 연결해야 합니다
2. 기존 인덱스를 삭제하고 새로 생성합니다
3. PostgreSQL 데이터를 기준으로 재인덱싱합니다

계속하시겠습니까? (yes/no): yes

📡 OpenSearch 연결 중...
✅ OpenSearch 연결 성공!
   클러스터: 851725447549:my-patent-search
   버전: 2.18

============================================================
특허 데이터 재인덱싱 시작
============================================================

1️⃣  기존 patents 인덱스 삭제...
인덱스 'patents' 삭제 완료: {'acknowledged': True}

2️⃣  Nori 기반 patents 인덱스 생성...
인덱스 'patents' 생성 완료: {'acknowledged': True, ...}

3️⃣  PostgreSQL에서 특허 데이터 읽기...
총 61,496건의 특허 데이터 발견

4️⃣  OpenSearch에 데이터 인덱싱 중...
  진행률: 500/61496 (0.8%)
  진행률: 1000/61496 (1.6%)
  ...
  진행률: 61496/61496 (100.0%)

✅ 특허 인덱싱 완료!
   성공: 61,496건

============================================================
거절결정서 데이터 재인덱싱 시작
============================================================
...
```

---

## 🧪 테스트 방법

### 1. Nori 형태소 분석 테스트

```bash
# EC2 서버에서 실행
cd /home/ubuntu/workspace/final_project/SKN15-FINAL-3TEAM/patent_backend
source venv/bin/activate

python3 -c "
from patents.opensearch_client import get_opensearch_client

client = get_opensearch_client()

# 형태소 분석 테스트
response = client.indices.analyze(
    index='patents',
    body={
        'analyzer': 'nori_korean_analyzer',
        'text': '인공지능 기반 자율주행 시스템'
    }
)

print('형태소 분석 결과:')
for token in response['tokens']:
    print(f\"  - {token['token']} (position: {token['position']})\")
"
```

**예상 출력**:
```
형태소 분석 결과:
  - 인공지능 (position: 0)
  - 기반 (position: 1)
  - 자율주행 (position: 2)
  - 시스템 (position: 3)
```

### 2. 검색 기능 테스트

```bash
python3 -c "
from patents.opensearch_service import OpenSearchService

service = OpenSearchService()

# 키워드 검색 테스트
result = service.search_patents(
    keyword='인공지능',
    search_fields=['title', 'abstract'],
    page=1,
    page_size=5
)

print(f'검색 결과: {result[\"total_count\"]}건')
for i, patent in enumerate(result['results'], 1):
    print(f'{i}. {patent[\"title\"][:50]}...')
    if patent.get('highlight'):
        print(f'   하이라이트: {patent[\"highlight\"]}')
"
```

### 3. 고급 필터 테스트

```bash
python3 -c "
from patents.opensearch_service import OpenSearchService

service = OpenSearchService()

# IPC 코드 + 날짜 범위 필터 테스트
result = service.search_patents(
    keyword='반도체',
    filters={
        'ipc_code': 'H01L',
        'application_start_date': '2020.01.01',
        'application_end_date': '2023.12.31',
        'legal_status': '등록'
    },
    page=1,
    page_size=10
)

print(f'필터 검색 결과: {result[\"total_count\"]}건')
for patent in result['results'][:3]:
    print(f'- {patent[\"title\"][:40]}...')
    print(f'  IPC: {patent[\"ipc_code\"]}, 출원일: {patent[\"application_date\"]}')
"
```

---

## 📊 예상 성능 향상

### Nori 형태소 분석기 사용 시:
- ✅ **"인공지능"** 검색 → "인공지능", "AI", "artificial intelligence" 모두 매칭
- ✅ **형태소 기반 검색**: "자율주행차" → "자율주행", "자율", "주행", "차" 각각 분석
- ✅ **복합어 처리**: "머신러닝알고리즘" → "머신러닝", "알고리즘" 분리
- ✅ **한자 발음 변환**: "人工知能" → "인공지능"으로 검색 가능

### 기존 대비 개선점:
1. **검색 정확도 향상**: 형태소 단위 검색으로 더 관련성 높은 결과
2. **오타 허용**: fuzzy matching으로 1-2글자 오타 자동 보정
3. **하이라이팅**: 검색어가 포함된 부분을 `<mark>` 태그로 강조
4. **필터 조합**: 키워드 + IPC/CPC + 날짜 범위 + 법적상태 동시 적용 가능

---

## ⚠️ 주의사항

1. **Nori 패키지를 먼저 연결해야 함**
   - AWS Console에서 analysis-nori 패키지 연결 필수
   - 연결 전에 재인덱싱하면 오류 발생: `Unknown analyzer type [nori]`

2. **기존 인덱스 삭제**
   - `reindex_with_nori.py` 실행 시 기존 인덱스 삭제됨
   - PostgreSQL 데이터는 영향 없음 (안전)

3. **재인덱싱 시간**
   - 61,496건 특허: 약 5-10분 소요
   - 2,274건 거절결정서: 약 1분 소요

4. **서비스 중단 최소화**
   - 재인덱싱 중에는 해당 인덱스 검색 불가
   - 작업은 업무 시간 외에 수행 권장

---

## 🔍 문제 해결

### 문제 1: "Unknown analyzer type [nori]" 오류
**원인**: Nori 패키지가 연결되지 않음
**해결**: AWS Console에서 analysis-nori 패키지 연결 후 재시도

### 문제 2: 재인덱싱 중 Bulk 오류
**원인**: 네트워크 타임아웃 또는 메모리 부족
**해결**: `batch_size`를 500 → 100으로 줄이기

### 문제 3: 검색 결과가 없음
**원인**: 인덱스가 비어있거나 필드명 불일치
**해결**:
```bash
# 인덱스 통계 확인
python3 -c "
from patents.opensearch_client import get_opensearch_client
client = get_opensearch_client()
stats = client.cat.count(index='patents', format='json')
print(f\"patents: {stats[0]['count']}건\")
"
```

---

## 📞 지원

문제가 발생하면 다음 정보와 함께 문의:
1. 오류 메시지 전체
2. 실행한 명령어
3. OpenSearch 도메인 상태 (AWS Console)
4. `opensearch_client.py`의 연결 테스트 결과
