"""
PostgreSQL 데이터를 OpenSearch로 마이그레이션
"""
import os
import sys
import django
from datetime import datetime

# Django 설정
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from patents.models import Patent
from papers.models import Paper
from patents.opensearch_client import get_opensearch_client, create_patents_index, create_papers_index
from opensearchpy.helpers import bulk


def migrate_patents_to_opensearch(batch_size=500):
    """
    특허 데이터를 OpenSearch로 마이그레이션
    """
    print("\n" + "="*60)
    print("  특허 데이터 OpenSearch 마이그레이션")
    print("="*60 + "\n")

    # OpenSearch 클라이언트 연결
    client = get_opensearch_client()
    print("✅ OpenSearch 연결 성공\n")

    # 인덱스 생성 (이미 존재하면 스킵)
    create_patents_index(client, index_name='patents')

    # PostgreSQL에서 특허 데이터 가져오기
    total_count = Patent.objects.count()
    print(f"📊 총 특허 데이터: {total_count:,}건\n")

    if total_count == 0:
        print("⚠️  마이그레이션할 데이터가 없습니다.")
        return

    # 배치 처리로 데이터 마이그레이션
    migrated_count = 0
    failed_count = 0

    print(f"💾 데이터 마이그레이션 중... (배치 크기: {batch_size})\n")

    # 전체 데이터를 배치로 나눠서 처리
    for offset in range(0, total_count, batch_size):
        patents = Patent.objects.all()[offset:offset + batch_size]

        # OpenSearch bulk insert 형식으로 변환
        actions = []
        for patent in patents:
            doc = {
                '_index': 'patents',
                '_id': patent.id,
                '_source': {
                    'title': patent.title,
                    'title_en': patent.title_en,
                    'application_number': patent.application_number,
                    'application_date': patent.application_date.isoformat() if patent.application_date else None,
                    'applicant': patent.applicant,
                    'registration_number': patent.registration_number,
                    'registration_date': patent.registration_date.isoformat() if patent.registration_date else None,
                    'ipc_code': patent.ipc_code,
                    'cpc_code': patent.cpc_code,
                    'abstract': patent.abstract,
                    'claims': patent.claims,
                    'legal_status': patent.legal_status,
                    'created_at': patent.created_at.isoformat() if patent.created_at else datetime.now().isoformat(),
                    'updated_at': patent.updated_at.isoformat() if patent.updated_at else datetime.now().isoformat()
                }
            }
            actions.append(doc)

        # Bulk insert
        try:
            success, failed = bulk(client, actions, raise_on_error=False, stats_only=True)
            migrated_count += success
            failed_count += failed
            print(f"  ✓ {migrated_count:,}건 마이그레이션 완료")
        except Exception as e:
            print(f"  ❌ 배치 오류: {e}")
            failed_count += len(actions)

    print(f"\n{'='*60}")
    print(f"  마이그레이션 완료!")
    print(f"{'='*60}")
    print(f"✅ 성공: {migrated_count:,}건")
    print(f"❌ 실패: {failed_count:,}건")

    # 인덱스 통계
    client.indices.refresh(index='patents')
    stats = client.cat.count(index='patents', format='json')
    print(f"📊 OpenSearch 인덱스: {stats[0]['count']}건\n")


def migrate_papers_to_opensearch(batch_size=100):
    """
    논문 데이터를 OpenSearch로 마이그레이션
    """
    print("\n" + "="*60)
    print("  논문 데이터 OpenSearch 마이그레이션")
    print("="*60 + "\n")

    # OpenSearch 클라이언트 연결
    client = get_opensearch_client()
    print("✅ OpenSearch 연결 성공\n")

    # 인덱스 생성 (이미 존재하면 스킵)
    create_papers_index(client, index_name='papers')

    # PostgreSQL에서 논문 데이터 가져오기
    total_count = Paper.objects.count()
    print(f"📊 총 논문 데이터: {total_count:,}건\n")

    if total_count == 0:
        print("⚠️  마이그레이션할 데이터가 없습니다.")
        return

    # 배치 처리로 데이터 마이그레이션
    migrated_count = 0
    failed_count = 0

    print(f"💾 데이터 마이그레이션 중... (배치 크기: {batch_size})\n")

    # 전체 데이터를 배치로 나눠서 처리
    for offset in range(0, total_count, batch_size):
        papers = Paper.objects.all()[offset:offset + batch_size]

        # OpenSearch bulk insert 형식으로 변환
        actions = []
        for paper in papers:
            doc = {
                '_index': 'papers',
                '_id': paper.id,
                '_source': {
                    'title_en': paper.title_en,
                    'title_kr': paper.title_kr,
                    'authors': paper.authors,
                    'abstract_en': paper.abstract_en,
                    'abstract_kr': paper.abstract_kr,
                    'abstract_page_link': paper.abstract_page_link,
                    'pdf_link': paper.pdf_link,
                    'source_file': paper.source_file,
                    'created_at': paper.created_at.isoformat() if paper.created_at else datetime.now().isoformat(),
                    'updated_at': paper.updated_at.isoformat() if paper.updated_at else datetime.now().isoformat()
                }
            }
            actions.append(doc)

        # Bulk insert
        try:
            success, failed = bulk(client, actions, raise_on_error=False, stats_only=True)
            migrated_count += success
            failed_count += failed
            print(f"  ✓ {migrated_count:,}건 마이그레이션 완료")
        except Exception as e:
            print(f"  ❌ 배치 오류: {e}")
            failed_count += len(actions)

    print(f"\n{'='*60}")
    print(f"  마이그레이션 완료!")
    print(f"{'='*60}")
    print(f"✅ 성공: {migrated_count:,}건")
    print(f"❌ 실패: {failed_count:,}건")

    # 인덱스 통계
    client.indices.refresh(index='papers')
    stats = client.cat.count(index='papers', format='json')
    print(f"📊 OpenSearch 인덱스: {stats[0]['count']}건\n")


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='PostgreSQL 데이터를 OpenSearch로 마이그레이션')
    parser.add_argument('--type', choices=['patents', 'papers', 'all'], default='all',
                        help='마이그레이션할 데이터 타입 (patents, papers, all)')
    args = parser.parse_args()

    try:
        if args.type in ['patents', 'all']:
            migrate_patents_to_opensearch()

        if args.type in ['papers', 'all']:
            migrate_papers_to_opensearch()

        print("\n✅ 전체 마이그레이션 완료!")

    except Exception as e:
        print(f"\n❌ 마이그레이션 오류: {e}")
        import traceback
        traceback.print_exc()
