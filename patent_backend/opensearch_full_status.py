"""
OpenSearch 전체 상태 확인 스크립트
- 인덱스 목록
- 각 인덱스의 문서 수
- 인덱스 매핑 (필드 구조)
- 샘플 문서 내용
"""
import os
import django
import json

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from patents.opensearch_client import get_opensearch_client


def print_header(text):
    """헤더 출력"""
    print("\n" + "="*70)
    print(f"  {text}")
    print("="*70)


def check_opensearch_status():
    """OpenSearch 전체 상태 확인"""

    print_header("OpenSearch 전체 상태 확인")

    try:
        client = get_opensearch_client()
        print("\n✅ OpenSearch 연결 성공\n")

        # 1. 모든 인덱스 목록
        print_header("1. 인덱스 목록")
        indices = client.cat.indices(format='json')

        print(f"\n총 {len(indices)}개 인덱스:\n")
        for idx in indices:
            print(f"  📁 {idx['index']}")
            print(f"     - 문서 수: {idx['docs.count']}")
            print(f"     - 크기: {idx['store.size']}")
            print(f"     - 상태: {idx['health']}")
            print()

        # 2. papers 인덱스 상세 정보
        if client.indices.exists(index='papers'):
            print_header("2. papers 인덱스 상세 정보")

            # 2-1. 통계
            stats = client.indices.stats(index='papers')
            total_docs = stats['_all']['primaries']['docs']['count']
            total_size = stats['_all']['primaries']['store']['size_in_bytes']

            print(f"\n📊 통계:")
            print(f"  - 총 문서 수: {total_docs:,}개")
            print(f"  - 총 크기: {total_size / 1024 / 1024:.2f} MB")

            # 2-2. 매핑 (필드 구조)
            print(f"\n📋 필드 구조 (매핑):")
            mapping = client.indices.get_mapping(index='papers')
            properties = mapping['papers']['mappings']['properties']

            for field_name in sorted(properties.keys()):
                field_info = properties[field_name]
                field_type = field_info.get('type', 'object')

                print(f"  - {field_name}: {field_type}", end='')

                # analyzer 정보가 있으면 표시
                if 'analyzer' in field_info:
                    print(f" (analyzer: {field_info['analyzer']})", end='')

                # fields 정보가 있으면 표시
                if 'fields' in field_info:
                    subfields = list(field_info['fields'].keys())
                    print(f" [subfields: {', '.join(subfields)}]", end='')

                print()

            # 2-3. 날짜 필드 통계
            print(f"\n📅 날짜 필드 통계:")

            # published_date
            result = client.count(
                index='papers',
                body={'query': {'exists': {'field': 'published_date'}}}
            )
            pub_count = result['count']
            pub_percent = (pub_count / total_docs * 100) if total_docs > 0 else 0
            print(f"  - published_date 있음: {pub_count:,}개 ({pub_percent:.1f}%)")

            # created_at
            result = client.count(
                index='papers',
                body={'query': {'exists': {'field': 'created_at'}}}
            )
            created_count = result['count']
            created_percent = (created_count / total_docs * 100) if total_docs > 0 else 0
            print(f"  - created_at 있음: {created_count:,}개 ({created_percent:.1f}%)")

            # 2-4. 샘플 문서 (최신 3개)
            print(f"\n🔍 샘플 문서 (최신 3개):\n")

            # created_at으로 정렬 시도, 없으면 _id로
            try:
                result = client.search(
                    index='papers',
                    body={
                        'size': 3,
                        'sort': [{'created_at': {'order': 'desc'}}],
                    }
                )
            except:
                # created_at 필드가 없을 수 있음
                result = client.search(
                    index='papers',
                    body={'size': 3}
                )

            for i, hit in enumerate(result['hits']['hits'], 1):
                source = hit['_source']

                print(f"문서 #{i} (ID: {hit['_id']}):")
                print(f"  제목(한글): {source.get('title_kr', 'N/A')[:60]}")
                if source.get('title_en'):
                    print(f"  제목(영문): {source.get('title_en', 'N/A')[:60]}")
                print(f"  저자: {source.get('authors', 'N/A')[:60]}")
                print(f"  발행일: {source.get('published_date', 'N/A')}")
                print(f"  작성일: {source.get('created_at', 'N/A')}")

                # 전체 필드 목록 표시
                all_fields = list(source.keys())
                print(f"  전체 필드 ({len(all_fields)}개): {', '.join(all_fields)}")
                print()

            # 2-5. 하나의 문서 전체 내용 (JSON)
            print(f"\n📄 샘플 문서 1개 전체 내용 (JSON):\n")
            if result['hits']['hits']:
                sample_doc = result['hits']['hits'][0]['_source']
                print(json.dumps(sample_doc, indent=2, ensure_ascii=False))

        else:
            print("\n❌ papers 인덱스가 존재하지 않습니다!")

        # 3. patents 인덱스 간단 정보
        if client.indices.exists(index='patents'):
            print_header("3. patents 인덱스 간단 정보")

            stats = client.indices.stats(index='patents')
            total_docs = stats['_all']['primaries']['docs']['count']

            print(f"\n📊 통계:")
            print(f"  - 총 문서 수: {total_docs:,}개")

            # 샘플 1개
            result = client.search(index='patents', body={'size': 1})
            if result['hits']['hits']:
                sample = result['hits']['hits'][0]['_source']
                fields = list(sample.keys())
                print(f"  - 필드 목록 ({len(fields)}개): {', '.join(fields)}")

        # 4. 최종 진단
        print_header("4. 최종 진단")

        if client.indices.exists(index='papers'):
            stats = client.indices.stats(index='papers')
            total_docs = stats['_all']['primaries']['docs']['count']

            result = client.count(
                index='papers',
                body={'query': {'exists': {'field': 'published_date'}}}
            )
            pub_count = result['count']

            print()
            if pub_count == 0 and total_docs > 0:
                print("❌ 문제 발견: papers 인덱스에 published_date 필드가 없습니다!")
                print("   → 해결: DJANGO_SETTINGS_MODULE=config.settings python3 manage.py reindex_papers")
            elif pub_count < total_docs:
                print(f"⚠️  경고: 일부 문서에만 published_date가 있습니다 ({pub_count}/{total_docs})")
                print("   → 해결: DJANGO_SETTINGS_MODULE=config.settings python3 manage.py reindex_papers")
            else:
                print("✅ 모든 문서에 published_date 필드가 있습니다!")
                print("   → 날짜 필터와 정렬이 정상 작동합니다.")
        else:
            print("\n❌ papers 인덱스가 없습니다!")
            print("   → 해결: DJANGO_SETTINGS_MODULE=config.settings python3 manage.py reindex_papers")

        print()

    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    check_opensearch_status()
