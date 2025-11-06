"""
현재 OpenSearch 도메인에 Nori 플러그인이 설치되어 있는지 확인
"""
import os
import sys
import django

# Django 설정
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from patents.opensearch_client import get_opensearch_client

print("\n" + "="*80)
print("  OpenSearch 플러그인 확인")
print("="*80 + "\n")

try:
    client = get_opensearch_client()

    # 1. 버전 정보
    info = client.info()
    print(f"✅ OpenSearch 연결 성공")
    print(f"   버전: {info['version']['number']}")
    print(f"   클러스터: {info['cluster_name']}")
    print()

    # 2. Nori 테스트 (간단한 analyzer 생성 시도)
    print("="*80)
    print("  Nori 플러그인 테스트")
    print("="*80 + "\n")

    test_index = 'nori_test_temp'

    # 기존 테스트 인덱스 삭제
    if client.indices.exists(index=test_index):
        client.indices.delete(index=test_index)
        print(f"✓ 기존 테스트 인덱스 삭제")

    # Nori tokenizer를 사용하는 인덱스 생성 시도
    try:
        client.indices.create(
            index=test_index,
            body={
                'settings': {
                    'analysis': {
                        'analyzer': {
                            'nori_analyzer': {
                                'type': 'nori'
                            }
                        }
                    }
                },
                'mappings': {
                    'properties': {
                        'text': {
                            'type': 'text',
                            'analyzer': 'nori'
                        }
                    }
                }
            }
        )

        print("✅ Nori 플러그인 사용 가능!")
        print("   - Nori tokenizer가 설치되어 있습니다.")
        print("   - 한국어 형태소 분석을 사용할 수 있습니다.")

        # 테스트 인덱스 삭제
        client.indices.delete(index=test_index)
        print(f"\n✓ 테스트 인덱스 삭제 완료")

        print("\n" + "="*80)
        print("  결과: Nori를 사용할 수 있습니다!")
        print("="*80)
        print("\n다음 단계:")
        print("1. reindex_with_synonyms.py 실행")
        print("2. 또는 opensearch_client.py에서 create_patents_index_with_nori 함수 사용")
        print()

    except Exception as e:
        error_msg = str(e)

        if 'nori' in error_msg.lower():
            print("❌ Nori 플러그인을 사용할 수 없습니다.")
            print(f"   오류: {error_msg}")
            print("\n해결 방법:")
            print("1. 동의어 사전 방식 사용 (현재 구현됨)")
            print("2. 또는 새로운 OpenSearch 도메인 생성 필요")
        else:
            print(f"❌ 예상치 못한 오류: {error_msg}")

except Exception as e:
    print(f"❌ 연결 실패: {e}")
    import traceback
    traceback.print_exc()
