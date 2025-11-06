# AWS OpenSearch에서 Nori 플러그인 활성화 가이드

## 개요
현재 OpenSearch 인스턴스에는 Nori 플러그인이 설치되어 있지 않습니다.
Nori를 사용하려면 새로운 OpenSearch 도메인을 Nori 플러그인과 함께 생성해야 합니다.

---

## 1단계: 현재 도메인 플러그인 확인

현재 도메인:
- **도메인명**: vpc-my-patent-search-awh27u4ftg7cgcxwr347fma3cu.ap-northeast-2.es.amazonaws.com
- **버전**: OpenSearch 3.1.0
- **문제**: Nori 플러그인 미설치

확인 방법:
```bash
# EC2에서 실행
curl -u opensearch_admin:3-Bengio123 \
  https://vpc-my-patent-search-awh27u4ftg7cgcxwr347fma3cu.ap-northeast-2.es.amazonaws.com/_cat/plugins
```

---

## 2단계: 새 OpenSearch 도메인 생성 (Nori 포함)

### AWS Console에서 생성:

1. **AWS Console → OpenSearch Service → Domains → Create domain**

2. **도메인 설정**:
   - Domain name: `patent-search-with-nori`
   - Engine: OpenSearch 3.1

3. **플러그인 패키지 선택** (중요!):
   - ✅ **analysis-nori** 체크
   - ✅ **analysis-kuromoji** (일본어, 선택사항)
   - ✅ **analysis-icu** (다국어 지원, 선택사항)

4. **네트워크 설정**:
   - Deployment type: **VPC access**
   - VPC: 기존 VPC 선택
   - Subnet: 기존 subnet (10.0.1.0/24) 선택
   - Security group: opensearch-sg (포트 443 허용)

5. **액세스 정책**:
   - Fine-grained access control: **Enable**
   - Master user: `opensearch_admin`
   - Master password: `3-Bengio123`

6. **인스턴스 설정**:
   - Instance type: `t3.small.search` (또는 동일)
   - Number of nodes: 1
   - Storage: 20GB EBS

7. **생성 완료** (약 10-15분 소요)

---

## 3단계: 새 도메인 엔드포인트 확인

도메인 생성 후:
1. AWS Console에서 새 도메인의 **Endpoint** 확인
2. 예시: `vpc-patent-search-with-nori-xxxxx.ap-northeast-2.es.amazonaws.com`

---

## 4단계: .env 파일 업데이트

```bash
# /home/ubuntu/workspace/final_project/SKN15-FINAL-3TEAM/patent_backend/.env

# 새 OpenSearch 도메인으로 변경
OPENSEARCH_HOST=vpc-patent-search-with-nori-xxxxx.ap-northeast-2.es.amazonaws.com
OPENSEARCH_PORT=443
OPENSEARCH_USE_SSL=True
OPENSEARCH_VERIFY_CERTS=True
OPENSEARCH_USER=opensearch_admin
OPENSEARCH_PASSWORD=3-Bengio123
```

---

## 5단계: Nori 플러그인 확인

```bash
# EC2에서 실행
cd /home/ubuntu/workspace/final_project/SKN15-FINAL-3TEAM/patent_backend
source venv/bin/activate

python3 -c "
from patents.opensearch_client import get_opensearch_client

client = get_opensearch_client()

# 플러그인 목록 확인
plugins = client.cat.plugins(format='json')
print('설치된 플러그인:')
for plugin in plugins:
    print(f\"  - {plugin['component']}\")
"
```

**기대 결과**:
```
설치된 플러그인:
  - analysis-nori
  - opensearch-knn
  - ...
```

---

## 6단계: Nori Analyzer가 포함된 인덱스 생성

`patents/opensearch_client.py` 수정:

```python
def create_patents_index_with_nori(client, index_name='patents'):
    """
    특허 인덱스 생성 (Nori 형태소 분석 + 동의어 사전)
    """
    index_body = {
        'settings': {
            'index': {
                'number_of_shards': 2,
                'number_of_replicas': 1
            },
            'analysis': {
                'tokenizer': {
                    'nori_user_dict': {
                        'type': 'nori_tokenizer',
                        'decompound_mode': 'mixed',  # 복합어 분해 모드
                        'discard_punctuation': 'true',
                        'user_dictionary_rules': [
                            '인공지능',
                            '머신러닝',
                            '딥러닝',
                            '블록체인',
                            '자율주행'
                        ]
                    }
                },
                'filter': {
                    'nori_part_of_speech': {
                        'type': 'nori_part_of_speech',
                        'stoptags': [
                            'E',  # 어미
                            'IC', # 감탄사
                            'J',  # 조사
                            'MAG', 'MAJ',  # 부사
                            'MM',  # 관형사
                            'SP', 'SSC', 'SSO', 'SC', 'SE',  # 구두점
                            'XPN', 'XSA', 'XSN', 'XSV',  # 접미사
                            'UNA', 'NA', 'VSV'
                        ]
                    },
                    'synonym_filter': {
                        'type': 'synonym',
                        'synonyms': [
                            # AI/인공지능 관련
                            '인공지능, AI, artificial intelligence',
                            '머신러닝, machine learning, ML, 기계학습',
                            '딥러닝, deep learning, DL, 심층학습',
                            '신경망, neural network, NN',

                            # IoT/사물인터넷
                            'IoT, 사물인터넷, Internet of Things',

                            # 기타 기술 용어
                            '블록체인, blockchain',
                            '자율주행, autonomous driving, self-driving',
                            '빅데이터, big data',
                            '클라우드, cloud computing',
                            '로봇, robot, 로보틱스, robotics',
                            '드론, drone, UAV, 무인항공기',
                            'VR, 가상현실, virtual reality',
                            'AR, 증강현실, augmented reality',
                            '반도체, semiconductor',
                            '배터리, battery, 전지',
                            '5G, 5세대, 5세대 이동통신',
                            '6G, 6세대, 6세대 이동통신'
                        ]
                    }
                },
                'analyzer': {
                    'nori_korean_analyzer': {
                        'type': 'custom',
                        'tokenizer': 'nori_user_dict',
                        'filter': [
                            'nori_part_of_speech',
                            'lowercase',
                            'synonym_filter',
                            'nori_readingform'
                        ]
                    }
                }
            }
        },
        'mappings': {
            'properties': {
                'title': {
                    'type': 'text',
                    'analyzer': 'nori_korean_analyzer',
                    'fields': {
                        'keyword': {'type': 'keyword'}
                    }
                },
                'title_en': {
                    'type': 'text',
                    'analyzer': 'standard',
                    'fields': {
                        'keyword': {'type': 'keyword'}
                    }
                },
                'application_number': {'type': 'keyword'},
                'application_date': {'type': 'keyword'},
                'applicant': {
                    'type': 'text',
                    'analyzer': 'nori_korean_analyzer',
                    'fields': {
                        'keyword': {'type': 'keyword'}
                    }
                },
                'registration_number': {'type': 'keyword'},
                'registration_date': {'type': 'keyword'},
                'ipc_code': {'type': 'keyword'},
                'cpc_code': {'type': 'keyword'},
                'abstract': {
                    'type': 'text',
                    'analyzer': 'nori_korean_analyzer'
                },
                'claims': {
                    'type': 'text',
                    'analyzer': 'nori_korean_analyzer'
                },
                'legal_status': {'type': 'keyword'},
                'created_at': {'type': 'date'},
                'updated_at': {'type': 'date'}
            }
        }
    }

    # 인덱스 생성
    if client.indices.exists(index=index_name):
        print(f"인덱스 '{index_name}'가 이미 존재합니다.")
        return False

    response = client.indices.create(index=index_name, body=index_body)
    print(f"인덱스 '{index_name}' 생성 완료 (Nori 적용)")
    return True
```

---

## 7단계: 데이터 마이그레이션

```bash
cd /home/ubuntu/workspace/final_project/SKN15-FINAL-3TEAM/patent_backend
source venv/bin/activate

# 인덱스 생성
python3 -c "
from patents.opensearch_client import get_opensearch_client, create_patents_index_with_nori
client = get_opensearch_client()
create_patents_index_with_nori(client)
"

# 데이터 마이그레이션
python3 migrate_to_opensearch.py --type patents
python3 migrate_to_opensearch.py --type papers
```

---

## 8단계: Nori 검색 테스트

```bash
python3 -c "
from patents.opensearch_client import get_opensearch_client

client = get_opensearch_client()

# 테스트 쿼리
test_queries = ['인공지능', '인공', '지능', '머신러닝', '자율주행']

for keyword in test_queries:
    response = client.search(
        index='patents',
        body={
            'query': {
                'match': {
                    'title': keyword
                }
            },
            'size': 0
        }
    )
    count = response['hits']['total']['value']
    print(f\"'{keyword}' 검색: {count:,}건\")
"
```

**Nori 적용 후 기대 결과**:
```
'인공지능' 검색: 500건
'인공' 검색: 500건 (인공지능에서 '인공' 형태소 추출)
'지능' 검색: 500건 (인공지능에서 '지능' 형태소 추출)
'머신러닝' 검색: 300건
'자율주행' 검색: 200건
```

---

## 비용 고려사항

- **새 도메인 생성 비용**: 기존 도메인과 동일 (t3.small.search 기준 시간당 약 $0.036)
- **중복 실행 기간**: 마이그레이션 완료 후 기존 도메인 삭제 (1-2시간 중복)
- **총 추가 비용**: 약 $0.07 (2시간 중복 실행 가정)

---

## 대안: 비용 절감 방법

Nori가 꼭 필요하지 않다면 **현재 동의어 사전 방식**을 유지하는 것을 권장합니다:

### 현재 방식의 장점:
1. ✅ 추가 비용 없음
2. ✅ 주요 기술 용어 동의어 매칭 가능 (인공지능 ↔ AI)
3. ✅ Fuzzy matching으로 오타 허용
4. ✅ 이미 290건의 "인공지능" 검색 결과 확인

### Nori의 추가 이점:
1. ✅ "인공지능" → "인공", "지능" 자동 분리
2. ✅ 모든 한국어에 대한 형태소 분석
3. ✅ 동의어 사전에 없는 단어도 형태소 단위 검색

---

## 결론

**Nori를 사용하려면**: 새 OpenSearch 도메인 생성 필요 (약 15분 + 마이그레이션 5분)

**현재 상태 유지**: 동의어 사전 + Fuzzy matching으로 충분히 좋은 검색 품질 제공

선택은 검색 품질 향상의 필요성과 추가 작업 시간을 고려하여 결정하시면 됩니다.
