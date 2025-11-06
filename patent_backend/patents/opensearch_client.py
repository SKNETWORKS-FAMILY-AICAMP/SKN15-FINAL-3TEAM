"""
OpenSearch 클라이언트 유틸리티
특허 검색을 위한 OpenSearch 연결 및 인덱스 관리
"""
import os
from pathlib import Path
from opensearchpy import OpenSearch, RequestsHttpConnection
from requests_aws4auth import AWS4Auth

# .env 파일 로드
try:
    from dotenv import load_dotenv
    BASE_DIR = Path(__file__).resolve().parent.parent
    load_dotenv(BASE_DIR / '.env')
except ImportError:
    # dotenv가 없으면 Django settings 사용
    try:
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
        import django
        django.setup()
    except ImportError:
        pass


def get_opensearch_client():
    """
    OpenSearch 클라이언트 생성 및 반환
    """
    host = os.getenv('OPENSEARCH_HOST', 'localhost')
    port = int(os.getenv('OPENSEARCH_PORT', 9200))
    use_ssl = os.getenv('OPENSEARCH_USE_SSL', 'False') == 'True'
    verify_certs = os.getenv('OPENSEARCH_VERIFY_CERTS', 'False') == 'True'

    # 사용자 인증 정보 (마스터 사용자)
    opensearch_user = os.getenv('OPENSEARCH_USER')
    opensearch_password = os.getenv('OPENSEARCH_PASSWORD')

    # AWS 자격증명 설정 (AWS OpenSearch 사용 시)
    aws_access_key = os.getenv('AWS_ACCESS_KEY_ID')
    aws_secret_key = os.getenv('AWS_SECRET_ACCESS_KEY')
    region = os.getenv('AWS_REGION', 'ap-northeast-2')

    if opensearch_user and opensearch_password:
        # 사용자 이름/비밀번호 인증 (VPC 내부 또는 퍼블릭 액세스)
        client = OpenSearch(
            hosts=[{'host': host, 'port': port}],
            http_auth=(opensearch_user, opensearch_password),
            use_ssl=use_ssl,
            verify_certs=verify_certs,
            connection_class=RequestsHttpConnection,
            timeout=30
        )
    elif aws_access_key and aws_secret_key:
        # AWS IAM 인증
        awsauth = AWS4Auth(
            aws_access_key,
            aws_secret_key,
            region,
            'es'  # 서비스 이름
        )

        client = OpenSearch(
            hosts=[{'host': host, 'port': port}],
            http_auth=awsauth,
            use_ssl=use_ssl,
            verify_certs=verify_certs,
            connection_class=RequestsHttpConnection,
            timeout=30
        )
    else:
        # 로컬 OpenSearch 사용 (인증 없음)
        client = OpenSearch(
            hosts=[{'host': host, 'port': port}],
            use_ssl=use_ssl,
            verify_certs=verify_certs,
            timeout=30
        )

    return client


def create_patents_index(client, index_name='patents'):
    """
    특허 인덱스 생성 (한글 검색 최적화)
    """
    index_body = {
        'settings': {
            'index': {
                'number_of_shards': 2,
                'number_of_replicas': 1
            }
        },
        'mappings': {
            'properties': {
                'title': {
                    'type': 'text',
                    'analyzer': 'standard',
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
                'application_number': {
                    'type': 'keyword'
                },
                'application_date': {
                    'type': 'keyword'
                },
                'applicant': {
                    'type': 'text',
                    'analyzer': 'standard',
                    'fields': {
                        'keyword': {'type': 'keyword'}
                    }
                },
                'registration_number': {
                    'type': 'keyword'
                },
                'registration_date': {
                    'type': 'keyword'
                },
                'ipc_code': {
                    'type': 'keyword'
                },
                'cpc_code': {
                    'type': 'keyword'
                },
                'abstract': {
                    'type': 'text',
                    'analyzer': 'standard'
                },
                'claims': {
                    'type': 'text',
                    'analyzer': 'standard'
                },
                'legal_status': {
                    'type': 'keyword'
                },
                'created_at': {
                    'type': 'date'
                },
                'updated_at': {
                    'type': 'date'
                }
            }
        }
    }

    # 인덱스가 이미 존재하는지 확인
    if client.indices.exists(index=index_name):
        print(f"인덱스 '{index_name}'가 이미 존재합니다.")
        return False

    # 인덱스 생성
    response = client.indices.create(index=index_name, body=index_body)
    print(f"인덱스 '{index_name}' 생성 완료: {response}")
    return True


def create_papers_index(client, index_name='papers'):
    """
    논문 인덱스 생성 (한글/영문 검색 최적화)
    """
    index_body = {
        'settings': {
            'index': {
                'number_of_shards': 1,
                'number_of_replicas': 1
            }
        },
        'mappings': {
            'properties': {
                'title_en': {
                    'type': 'text',
                    'analyzer': 'standard'
                },
                'title_kr': {
                    'type': 'text',
                    'analyzer': 'standard',
                    'fields': {
                        'keyword': {'type': 'keyword'}
                    }
                },
                'authors': {
                    'type': 'text',
                    'analyzer': 'standard',
                    'fields': {
                        'keyword': {'type': 'keyword'}
                    }
                },
                'abstract_en': {
                    'type': 'text',
                    'analyzer': 'standard'
                },
                'abstract_kr': {
                    'type': 'text',
                    'analyzer': 'standard'
                },
                'abstract_page_link': {
                    'type': 'keyword',
                    'index': False
                },
                'pdf_link': {
                    'type': 'keyword',
                    'index': False
                },
                'source_file': {
                    'type': 'keyword'
                },
                'created_at': {
                    'type': 'date'
                },
                'updated_at': {
                    'type': 'date'
                }
            }
        }
    }

    # 인덱스가 이미 존재하는지 확인
    if client.indices.exists(index=index_name):
        print(f"인덱스 '{index_name}'가 이미 존재합니다.")
        return False

    # 인덱스 생성
    response = client.indices.create(index=index_name, body=index_body)
    print(f"인덱스 '{index_name}' 생성 완료: {response}")
    return True


def create_reject_documents_index(client, index_name='reject_documents'):
    """
    거절결정서 인덱스 생성 (한글 검색 최적화)
    """
    index_body = {
        'settings': {
            'index': {
                'number_of_shards': 1,
                'number_of_replicas': 1
            }
        },
        'mappings': {
            'properties': {
                'doc_id': {
                    'type': 'keyword'
                },
                'send_number': {
                    'type': 'keyword'
                },
                'send_date': {
                    'type': 'keyword'
                },
                'applicant_code': {
                    'type': 'keyword'
                },
                'applicant': {
                    'type': 'text',
                    'analyzer': 'standard',
                    'fields': {
                        'keyword': {'type': 'keyword'}
                    }
                },
                'agent': {
                    'type': 'text',
                    'analyzer': 'standard'
                },
                'application_number': {
                    'type': 'keyword'
                },
                'invention_name': {
                    'type': 'text',
                    'analyzer': 'standard'
                },
                'examination_office': {
                    'type': 'text',
                    'analyzer': 'standard'
                },
                'examiner': {
                    'type': 'keyword'
                },
                'tables_raw': {
                    'type': 'text',
                    'analyzer': 'standard'
                },
                'processed_text': {
                    'type': 'text',
                    'analyzer': 'standard'
                },
                'created_at': {
                    'type': 'date'
                },
                'updated_at': {
                    'type': 'date'
                }
            }
        }
    }

    # 인덱스가 이미 존재하는지 확인
    if client.indices.exists(index=index_name):
        print(f"인덱스 '{index_name}'가 이미 존재합니다.")
        return False

    # 인덱스 생성
    response = client.indices.create(index=index_name, body=index_body)
    print(f"인덱스 '{index_name}' 생성 완료: {response}")
    return True


def delete_index(client, index_name):
    """
    인덱스 삭제
    """
    if client.indices.exists(index=index_name):
        response = client.indices.delete(index=index_name)
        print(f"인덱스 '{index_name}' 삭제 완료: {response}")
        return True
    else:
        print(f"인덱스 '{index_name}'가 존재하지 않습니다.")
        return False


if __name__ == '__main__':
    # 테스트
    print("OpenSearch 클라이언트 연결 테스트...")
    print(f"DEBUG - OPENSEARCH_HOST: {os.getenv('OPENSEARCH_HOST', 'localhost')}")
    print(f"DEBUG - OPENSEARCH_PORT: {os.getenv('OPENSEARCH_PORT', '9200')}")
    print(f"DEBUG - OPENSEARCH_USE_SSL: {os.getenv('OPENSEARCH_USE_SSL', 'False')}")
    try:
        client = get_opensearch_client()
        print("✅ OpenSearch 연결 성공")
        print(f"클러스터 정보: {client.info()}")

        # 인덱스 생성 테스트
        print("\n특허 인덱스 생성...")
        create_patents_index(client)

        print("\n논문 인덱스 생성...")
        create_papers_index(client)

        print("\n거절결정서 인덱스 생성...")
        create_reject_documents_index(client)

    except Exception as e:
        print(f"❌ OpenSearch 연결 실패: {e}")
