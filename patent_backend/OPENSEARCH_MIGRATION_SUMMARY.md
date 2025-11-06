# OpenSearch Migration Summary

## 개요

Django 백엔드의 특허/논문 검색 시스템을 PostgreSQL Full-Text Search에서 AWS OpenSearch + Nori 한국어 형태소 분석기로 마이그레이션한 내역입니다.

---

## 1. 시스템 구성

### OpenSearch 인프라
- **서비스**: AWS OpenSearch Service
- **엔드포인트**: `vpc-my-patent-search-awh27u4ftg7cgcxwr347fma3cu.ap-northeast-2.es.amazonaws.com`
- **포트**: 443 (HTTPS)
- **인증**: Basic Auth (opensearch_admin / 3-Bengio123)
- **플러그인**: analysis-nori (AWS Console에서 Associate Package로 연결)

### 인덱스 구조
1. **patents**: 특허 데이터 (61,499건)
2. **papers**: 논문 데이터 (196건)
3. **reject_documents**: 거절결정서 데이터 (1,090건)

---

## 2. Nori 한국어 분석기 설정

### Nori 컴포넌트
```json
{
  "analysis": {
    "tokenizer": {
      "nori_mixed": {
        "type": "nori_tokenizer",
        "decompound_mode": "mixed"
      }
    },
    "filter": {
      "nori_posfilter": {
        "type": "nori_part_of_speech",
        "stoptags": ["E", "IC", "J", "MAG", "MM", "SP", "SSC", "SSO", "SC", "SE", "XPN", "XSA", "XSN", "XSV", "UNA", "NA", "VSV"]
      },
      "nori_readingform": {
        "type": "nori_readingform"
      }
    },
    "analyzer": {
      "nori_analyzer": {
        "type": "custom",
        "tokenizer": "nori_mixed",
        "filter": ["nori_posfilter", "nori_readingform", "lowercase"]
      }
    }
  }
}
```

### 적용 필드
- **특허**: title, abstract, claims, applicant
- **논문**: title_kr, abstract_kr, authors
- **거절결정서**: invention_name, processed_text, applicant

---

## 3. 핵심 파일 및 변경사항

### 3.1 reindex_with_nori.py
**목적**: PostgreSQL → OpenSearch 전체 데이터 재인덱싱

**주요 함수**:
- `reindex_patents()` - 특허 데이터 재인덱싱
- `reindex_papers()` - 논문 데이터 재인덱싱 (새로 추가)
- `reindex_reject_documents()` - 거절결정서 데이터 재인덱싱

**처리 흐름**:
```python
def reindex_patents(client):
    # 1. 기존 인덱스 삭제
    delete_index(client, 'patents')

    # 2. Nori 기반 새 인덱스 생성
    create_patents_index(client)

    # 3. PostgreSQL에서 전체 데이터 읽기
    patents = Patent.objects.all()

    # 4. Bulk 인덱싱 (배치 사이즈: 500)
    for patent in patents:
        doc = {
            '_index': 'patents',
            '_id': str(patent.id),
            '_source': { ... }
        }
        actions.append(doc)

        if len(actions) >= 500:
            helpers.bulk(client, actions)
```

**중요**: 이 스크립트는 **전체 재인덱싱**을 수행합니다. 증분 업데이트가 아니므로:
- 기존 인덱스를 완전히 삭제
- 새 인덱스 생성
- PostgreSQL에서 모든 데이터 다시 읽어서 인덱싱
- 중간에 실패 시 처음부터 다시 실행 필요

### 3.2 patents/opensearch_client.py
**목적**: OpenSearch 클라이언트 및 인덱스 생성 관리

**주요 함수**:
- `get_opensearch_client()` - OpenSearch 클라이언트 인스턴스 생성
- `create_patents_index()` - Nori 기반 특허 인덱스 생성
- `create_papers_index()` - Nori 기반 논문 인덱스 생성
- `create_reject_documents_index()` - 거절결정서 인덱스 생성
- `delete_index()` - 인덱스 삭제

**연결 설정**:
```python
client = OpenSearch(
    hosts=[{
        'host': 'vpc-my-patent-search-awh27u4ftg7cgcxwr347fma3cu.ap-northeast-2.es.amazonaws.com',
        'port': 443
    }],
    http_auth=('opensearch_admin', '3-Bengio123'),
    use_ssl=True,
    verify_certs=True,
    ssl_show_warn=False
)
```

### 3.3 patents/opensearch_service.py
**목적**: OpenSearch 검색 로직 구현

**주요 함수**:
- `search_patents()` - 특허 검색 (키워드, 필터, 정렬, 페이징)
- `search_papers()` - 논문 검색
- `get_patent_by_id()` - 특허 상세 조회
- `get_paper_by_id()` - 논문 상세 조회

**검색 쿼리 구조**:
```python
# 키워드 검색 (multi_match with fuzziness)
must_queries = [{
    'multi_match': {
        'query': keyword,
        'fields': ['title', 'abstract', 'claims'],
        'type': 'best_fields',
        'operator': 'or',
        'fuzziness': 'AUTO'  # 오타 허용
    }
}]

# 필터 조건
filter_queries = []

# 법적상태 필터 (정확한 일치)
if legal_status:
    filter_queries.append({
        'term': {
            'legal_status': legal_status
        }
    })

# IPC 코드 필터 (부분 일치)
if ipc_code:
    filter_queries.append({
        'wildcard': {
            'ipc_code': f"*{ipc_code}*"
        }
    })

# 날짜 범위 필터
if application_start_date or application_end_date:
    filter_queries.append({
        'range': {
            'application_date': {
                'gte': application_start_date,
                'lte': application_end_date
            }
        }
    })

# 정렬 (관련도 우선, 그 다음 날짜)
sort_order = [
    {'_score': {'order': 'desc'}},  # 관련도순
    {'application_date': {'order': 'desc'}}  # 최신순/오래된순
]
```

### 3.4 patents/views.py
**목적**: REST API 엔드포인트

**주요 변경사항**:
- PostgreSQL SearchQuery/SearchVector 제거
- OpenSearchService로 전환

**변경 전 (PostgreSQL)**:
```python
from django.contrib.postgres.search import SearchQuery, SearchRank, SearchVector

patents = Patent.objects.annotate(
    search=SearchVector('title', 'abstract', 'claims')
).filter(
    search=SearchQuery(keyword, search_type='websearch')
).annotate(
    rank=SearchRank('search', SearchQuery(keyword))
).order_by('-rank')
```

**변경 후 (OpenSearch)**:
```python
from .opensearch_service import OpenSearchService

opensearch_service = OpenSearchService()

filters = {
    'ipc_code': ipc_code,
    'application_start_date': application_start_date.replace('-', '.'),
    'application_end_date': application_end_date.replace('-', '.'),
    'registration_start_date': registration_start_date.replace('-', '.'),
    'registration_end_date': registration_end_date.replace('-', '.'),
    'legal_status': legal_status
}

search_result = opensearch_service.search_patents(
    keyword=keyword,
    search_fields=['title', 'abstract', 'claims'],
    filters=filters,
    page=page,
    page_size=page_size,
    sort_by=sort_by
)
```

### 3.5 config/settings.py
**OpenSearch 관련 설정**:
```python
# Django REST Framework
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',  # 인증 필요
    ],
    ...
}
```

**주의**: 401 Unauthorized 에러는 만료된 로그인 세션 때문이며, 설정 문제가 아닙니다.

---

## 4. 데이터 모델

### 4.1 Patent (특허)
```python
class Patent(models.Model):
    title = models.TextField()  # 한글 제목
    title_en = models.TextField()  # 영문 제목
    application_number = models.CharField(max_length=50)
    application_date = models.CharField(max_length=20)  # YYYY.MM.DD
    applicant = models.TextField()
    registration_number = models.CharField(max_length=50)
    registration_date = models.CharField(max_length=20)
    ipc_code = models.TextField()
    cpc_code = models.TextField()
    abstract = models.TextField()
    claims = models.TextField()
    legal_status = models.CharField(max_length=20)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
```

### 4.2 Paper (논문)
```python
class Paper(models.Model):
    title_en = models.TextField()  # 영문 제목
    title_kr = models.TextField()  # 한글 제목
    authors = models.TextField()
    abstract_en = models.TextField()
    abstract_kr = models.TextField()
    abstract_page_link = models.URLField(max_length=500)
    pdf_link = models.URLField(max_length=500)
    source_file = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
```

### 4.3 RejectDocument (거절결정서)
```python
class RejectDocument(models.Model):
    doc_id = models.CharField(max_length=100)
    send_number = models.CharField(max_length=100)
    send_date = models.CharField(max_length=20)
    applicant_code = models.CharField(max_length=50)
    applicant = models.TextField()
    agent = models.TextField()
    application_number = models.CharField(max_length=50)
    invention_name = models.TextField()
    examination_office = models.CharField(max_length=100)
    examiner = models.CharField(max_length=100)
    tables_raw = models.TextField()
    processed_text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
```

---

## 5. 검색 기능

### 5.1 특허 검색 (search_patents)
**검색 가능 필드**:
- title (제목)
- title_en (영문 제목)
- abstract (초록)
- claims (청구항)
- applicant (출원인)

**필터 옵션**:
- ipc_code: IPC 코드 (부분 일치)
- application_date: 출원일 범위 (시작일/종료일)
- registration_date: 등록일 범위 (시작일/종료일)
- legal_status: 법적상태 (정확히 일치)

**정렬 옵션**:
- date_desc: 관련도 + 최신순 (기본값)
- date_asc: 관련도 + 오래된순

**페이징**:
- page: 페이지 번호 (1부터 시작)
- page_size: 페이지당 결과 수 (기본값: 10)

### 5.2 논문 검색 (search_papers)
**검색 가능 필드**:
- title_kr (한글 제목)
- title_en (영문 제목)
- abstract_kr (한글 초록)
- abstract_en (영문 초록)
- authors (저자)

**정렬**:
- 관련도순 (_score) + 생성일 최신순 (created_at)

---

## 6. 발생한 문제 및 해결

### 문제 1: 논문 재인덱싱 누락
**증상**: reindex_with_nori.py에 특허와 거절결정서만 있고 논문이 없었음

**원인**: 초기 작성 시 논문 모델 누락

**해결**:
- Paper 모델 import 추가
- reindex_papers() 함수 생성 (특허와 동일한 패턴)
- main() 함수에 논문 재인덱싱 호출 추가
- 최종 통계에 papers 인덱스 카운트 추가

**커밋**: `feat: 논문 재인덱싱 기능 추가`

### 문제 2: 401 Unauthorized 에러
**증상**: 브라우저 콘솔에 401 에러 발생

**초기 진단**: DEFAULT_PERMISSION_CLASSES 설정 문제로 판단

**실제 원인**: 만료된 로그인 세션

**해결**:
- AllowAny로 변경했다가 다시 IsAuthenticated로 복구
- 사용자가 재로그인하면 해결됨

**커밋**: `revert: API 인증 설정 원래대로 복구`

### 문제 3: 검색 필터/정렬 미작동 (중요!)
**증상**:
- 법적상태 필터에서 "등록"을 선택하면 "소멸" 결과가 나옴
- 최신순/오래된순 정렬이 작동하지 않음

**원인**: views.py가 여전히 PostgreSQL Full-Text Search를 사용하고 있었음
- OpenSearch 인프라는 모두 구축되었고 데이터도 인덱싱되었지만
- API 엔드포인트는 여전히 PostgreSQL을 호출하고 있었음

**해결**:
1. PostgreSQL 관련 import 제거:
   - `from django.contrib.postgres.search import SearchQuery, SearchRank, SearchVector`

2. OpenSearchService import 추가:
   - `from .opensearch_service import OpenSearchService`

3. search() 함수 전체 재작성:
   - PostgreSQL 쿼리 → OpenSearchService.search_patents() 호출
   - 필터 파라미터 정확히 전달 (IPC, 날짜, 법적상태, sort_by)
   - 동일한 응답 포맷 유지 (프론트엔드 호환성)

**결과**:
- 법적상태 필터: term query로 정확히 일치하는 결과만 반환
- 날짜 정렬: OpenSearch sort로 _score + application_date 정렬

**커밋**: `feat: 특허 검색을 OpenSearch로 전환`

---

## 7. 재인덱싱 실행 방법

### 사전 준비
1. AWS Console → OpenSearch 도메인 선택
2. Packages 탭 → Associate package
3. analysis-nori 패키지 선택 및 연결
4. 도메인 상태가 Active가 될 때까지 대기 (10-15분 소요)

### 실행
```bash
cd /home/juhyeong/workspace/final_project/SKN15-FINAL-3TEAM/patent_backend
python3 reindex_with_nori.py
```

### 예상 출력
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
   클러스터: vpc-my-patent-search-awh27u4ftg7cgcxwr347fma3cu
   버전: 2.x.x

============================================================
특허 데이터 재인덱싱 시작
============================================================

1️⃣  기존 patents 인덱스 삭제...
✅ 인덱스 'patents' 삭제 완료

2️⃣  Nori 기반 patents 인덱스 생성...
✅ 인덱스 'patents' 생성 완료

3️⃣  PostgreSQL에서 특허 데이터 읽기...
총 61,499건의 특허 데이터 발견

4️⃣  OpenSearch에 데이터 인덱싱 중...
  진행률: 500/61499 (0.8%)
  진행률: 1000/61499 (1.6%)
  ...
  진행률: 61499/61499 (100.0%)

✅ 특허 인덱싱 완료!
   성공: 61,499건

============================================================
논문 데이터 재인덱싱 시작
============================================================
...
✅ 논문 인덱싱 완료!
   성공: 196건

============================================================
거절결정서 데이터 재인덱싱 시작
============================================================
...
✅ 거절결정서 인덱싱 완료!
   성공: 1,090건

============================================================
✅ 전체 재인덱싱 완료!
============================================================

📊 최종 인덱스 통계:
   patents: 61,499건
   papers: 196건
   reject_documents: 1,090건
```

---

## 8. 테스트 방법

### 8.1 OpenSearch 연결 테스트
```python
from patents.opensearch_client import get_opensearch_client

client = get_opensearch_client()
info = client.info()
print(f"클러스터: {info['cluster_name']}")
print(f"버전: {info['version']['number']}")
```

### 8.2 인덱스 확인
```python
# 인덱스 존재 여부
print(client.indices.exists(index='patents'))

# 문서 개수
stats = client.cat.count(index='patents', format='json')
print(f"특허 문서 수: {stats[0]['count']}")
```

### 8.3 검색 테스트
```python
from patents.opensearch_service import OpenSearchService

service = OpenSearchService()

# 키워드 검색
result = service.search_patents(
    keyword='인공지능',
    search_fields=['title', 'abstract'],
    page=1,
    page_size=10
)

print(f"검색 결과: {result['total_count']}건")
for patent in result['results']:
    print(f"- {patent['title']} (관련도: {patent['score']})")
```

### 8.4 필터 테스트
```python
# 법적상태 필터
result = service.search_patents(
    keyword='',
    filters={'legal_status': '등록'},
    page=1,
    page_size=10
)

# 날짜 범위 필터
result = service.search_patents(
    keyword='반도체',
    filters={
        'application_start_date': '2020.01.01',
        'application_end_date': '2023.12.31'
    },
    page=1,
    page_size=10
)

# IPC 코드 필터
result = service.search_patents(
    keyword='배터리',
    filters={'ipc_code': 'H01M'},
    page=1,
    page_size=10
)
```

---

## 9. 현재 시스템 상태

### 인덱싱 완료
- ✅ patents: 61,499건
- ✅ papers: 196건
- ✅ reject_documents: 1,090건

### 기능 정상 작동
- ✅ Nori 한국어 형태소 분석
- ✅ 다중 필드 검색 (title, abstract, claims)
- ✅ 퍼지 매칭 (오타 허용)
- ✅ IPC/CPC 코드 필터링 (wildcard)
- ✅ 날짜 범위 필터링 (application_date, registration_date)
- ✅ 법적상태 필터링 (term 정확 일치)
- ✅ 정렬 (관련도 + 최신순/오래된순)
- ✅ 페이징
- ✅ JWT 인증

### 데이터 흐름
```
프론트엔드 (Next.js)
    ↓ HTTP Request (JWT Token)
Django REST API (views.py)
    ↓ OpenSearchService.search_patents()
OpenSearchService (opensearch_service.py)
    ↓ OpenSearch Query (DSL)
AWS OpenSearch + Nori Analyzer
    ↓ Search Results
Django REST API
    ↓ JSON Response
프론트엔드 (검색 결과 표시)
```

---

## 10. 향후 고려사항

### 10.1 성능 최적화
- 검색 결과 캐싱 (Redis)
- 인덱스 샤드 수 조정
- 리플리카 설정 (고가용성)

### 10.2 증분 업데이트
현재는 전체 재인덱싱만 지원. 향후 개선 방안:
```python
def index_single_patent(patent):
    """단일 특허 문서 인덱싱/업데이트"""
    client = get_opensearch_client()

    doc = {
        'title': patent.title,
        'abstract': patent.abstract,
        # ...
    }

    client.index(
        index='patents',
        id=str(patent.id),
        body=doc
    )
```

Django 시그널로 자동 동기화:
```python
from django.db.models.signals import post_save, post_delete

@receiver(post_save, sender=Patent)
def update_opensearch_on_save(sender, instance, **kwargs):
    index_single_patent(instance)

@receiver(post_delete, sender=Patent)
def delete_opensearch_on_delete(sender, instance, **kwargs):
    client = get_opensearch_client()
    client.delete(index='patents', id=str(instance.id))
```

### 10.3 검색 품질 개선
- 동의어 사전 추가 (예: AI ↔ 인공지능)
- 불용어 사전 커스터마이징
- 검색어 자동완성 (Completion Suggester)
- 검색 결과 하이라이팅

### 10.4 모니터링
- OpenSearch 쿼리 성능 모니터링
- 검색 키워드 통계
- 느린 쿼리 로깅

---

## 11. 참고 자료

### OpenSearch 공식 문서
- [OpenSearch Documentation](https://opensearch.org/docs/latest/)
- [Nori Analysis Plugin](https://opensearch.org/docs/latest/analyzers/language-analyzers/#korean-nori)

### AWS OpenSearch
- [AWS OpenSearch Service](https://docs.aws.amazon.com/opensearch-service/)
- [AWS OpenSearch Packages](https://docs.aws.amazon.com/opensearch-service/latest/developerguide/custom-packages.html)

### Python 클라이언트
- [opensearch-py](https://github.com/opensearch-project/opensearch-py)
- [opensearch-dsl-py](https://github.com/opensearch-project/opensearch-dsl-py)

---

## 12. 작성 정보

- **작성일**: 2025-01-XX
- **작성자**: Claude (Anthropic)
- **프로젝트**: SKN15-FINAL-3TEAM / PatentAI
- **백엔드 경로**: /home/juhyeong/workspace/final_project/SKN15-FINAL-3TEAM/patent_backend

---

## 13. 변경 이력

| 날짜 | 내용 | 커밋 메시지 |
|------|------|------------|
| 2025-01-XX | 논문 재인덱싱 기능 추가 | feat: 논문 재인덱싱 기능 추가 |
| 2025-01-XX | API 인증 설정 복구 | revert: API 인증 설정 원래대로 복구 |
| 2025-01-XX | PostgreSQL → OpenSearch 전환 | feat: 특허 검색을 OpenSearch로 전환 |
