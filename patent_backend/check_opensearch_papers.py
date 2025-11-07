"""
OpenSearch papers 인덱스 상태 확인
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from patents.opensearch_client import get_opensearch_client

def check_papers_index():
    print("\n" + "="*60)
    print("  OpenSearch papers 인덱스 상태 확인")
    print("="*60 + "\n")
    
    try:
        client = get_opensearch_client()
        print("✅ OpenSearch 연결 성공\n")
        
        # 1. 인덱스 존재 확인
        if client.indices.exists(index='papers'):
            print("✅ papers 인덱스 존재\n")
        else:
            print("❌ papers 인덱스 없음\n")
            return
        
        # 2. 인덱스 통계
        stats = client.indices.stats(index='papers')
        total_docs = stats['_all']['primaries']['docs']['count']
        print(f"📊 총 문서 수: {total_docs:,}개\n")
        
        # 3. 인덱스 매핑 확인
        mapping = client.indices.get_mapping(index='papers')
        properties = mapping['papers']['mappings']['properties']
        print("📋 인덱스 필드 목록:")
        for field_name in sorted(properties.keys()):
            field_type = properties[field_name].get('type', 'object')
            print(f"  - {field_name}: {field_type}")
        print()
        
        # 4. 샘플 문서 확인 (첫 3개)
        print("🔍 샘플 문서 확인 (최신 3개):\n")
        result = client.search(
            index='papers',
            body={
                'size': 3,
                'sort': [{'created_at': {'order': 'desc'}}],
                '_source': ['title_kr', 'authors', 'published_date', 'created_at']
            }
        )
        
        for i, hit in enumerate(result['hits']['hits'], 1):
            source = hit['_source']
            print(f"문서 {i}:")
            print(f"  제목: {source.get('title_kr', 'N/A')[:50]}")
            print(f"  저자: {source.get('authors', 'N/A')[:50]}")
            print(f"  발행일: {source.get('published_date', 'N/A')}")
            print(f"  작성일: {source.get('created_at', 'N/A')}")
            print()
        
        # 5. 날짜 필드 확인
        print("📅 날짜 필드 통계:")
        
        # published_date가 있는 문서 수
        result = client.count(
            index='papers',
            body={
                'query': {
                    'exists': {
                        'field': 'published_date'
                    }
                }
            }
        )
        published_count = result['count']
        print(f"  published_date 있음: {published_count:,}개 ({published_count/total_docs*100:.1f}%)")
        
        # created_at이 있는 문서 수
        result = client.count(
            index='papers',
            body={
                'query': {
                    'exists': {
                        'field': 'created_at'
                    }
                }
            }
        )
        created_count = result['count']
        print(f"  created_at 있음: {created_count:,}개 ({created_count/total_docs*100:.1f}%)")
        
        print("\n" + "="*60)
        
        if published_count == 0:
            print("\n⚠️  경고: published_date 필드가 없는 문서가 있습니다!")
            print("재인덱싱이 필요합니다.\n")
        else:
            print("\n✅ 모든 문서에 날짜 필드가 있습니다.\n")
        
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    check_papers_index()
