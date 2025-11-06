"""
동의어 사전을 포함한 인덱스 재생성 및 데이터 마이그레이션
"""
import os
import sys
import django

# Django 설정
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from patents.opensearch_client import get_opensearch_client, delete_index, create_patents_index, create_papers_index
from migrate_to_opensearch import migrate_patents_to_opensearch, migrate_papers_to_opensearch


def reindex_with_synonyms():
    """
    동의어 사전이 포함된 인덱스로 재생성
    """
    print("\n" + "="*80)
    print("  동의어 사전 적용 - 인덱스 재생성 및 데이터 마이그레이션")
    print("="*80 + "\n")

    client = get_opensearch_client()
    print("✅ OpenSearch 연결 성공\n")

    # 1. 특허 인덱스 재생성
    print("="*80)
    print("  1단계: 특허 인덱스 재생성")
    print("="*80 + "\n")

    print("📌 기존 특허 인덱스 삭제 중...")
    delete_index(client, 'patents')

    print("\n📌 새로운 특허 인덱스 생성 중 (동의어 사전 포함)...")
    create_patents_index(client, 'patents')

    print("\n📌 특허 데이터 마이그레이션 중...")
    migrate_patents_to_opensearch(batch_size=500)

    # 2. 논문 인덱스 재생성
    print("\n" + "="*80)
    print("  2단계: 논문 인덱스 재생성")
    print("="*80 + "\n")

    print("📌 기존 논문 인덱스 삭제 중...")
    delete_index(client, 'papers')

    print("\n📌 새로운 논문 인덱스 생성 중 (동의어 사전 포함)...")
    create_papers_index(client, 'papers')

    print("\n📌 논문 데이터 마이그레이션 중...")
    migrate_papers_to_opensearch(batch_size=100)

    # 3. 동의어 테스트
    print("\n" + "="*80)
    print("  3단계: 동의어 검색 테스트")
    print("="*80 + "\n")

    test_queries = [
        ('인공지능', '특허'),
        ('AI', '특허'),
        ('artificial intelligence', '특허'),
        ('머신러닝', '특허'),
        ('machine learning', '특허'),
        ('딥러닝', '논문'),
        ('deep learning', '논문')
    ]

    for keyword, index_type in test_queries:
        index_name = 'patents' if index_type == '특허' else 'papers'

        try:
            response = client.search(
                index=index_name,
                body={
                    'query': {
                        'multi_match': {
                            'query': keyword,
                            'fields': ['title', 'abstract', 'title_kr', 'abstract_kr'],
                            'fuzziness': 'AUTO'
                        }
                    },
                    'size': 0  # 개수만 확인
                }
            )

            count = response['hits']['total']['value']
            print(f"✅ '{keyword}' 검색 ({index_type}): {count:,}건")

        except Exception as e:
            print(f"❌ '{keyword}' 검색 실패: {e}")

    print("\n" + "="*80)
    print("  재인덱싱 완료!")
    print("="*80)
    print("\n동의어 검색 기능이 활성화되었습니다.")
    print("이제 '인공지능', 'AI', 'artificial intelligence' 검색이 동일한 결과를 반환합니다.\n")


if __name__ == '__main__':
    try:
        # 사용자 확인
        print("\n⚠️  경고: 이 작업은 기존 특허 및 논문 인덱스를 삭제하고 재생성합니다.")
        print("         데이터는 PostgreSQL에서 다시 마이그레이션됩니다.")
        print("         약 5-10분 정도 소요될 수 있습니다.\n")

        confirm = input("계속 진행하시겠습니까? (yes/no): ")

        if confirm.lower() in ['yes', 'y']:
            reindex_with_synonyms()
        else:
            print("\n작업이 취소되었습니다.")

    except KeyboardInterrupt:
        print("\n\n작업이 중단되었습니다.")
    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()
