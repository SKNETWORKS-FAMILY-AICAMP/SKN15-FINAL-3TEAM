"""
Nori 기반 OpenSearch 인덱스 증분 업데이트 스크립트

사용 전 필수 작업:
1. AWS Console → OpenSearch 도메인 선택
2. Packages 탭 → Associate package
3. analysis-nori 패키지 선택 및 연결
4. 도메인 상태가 Active가 될 때까지 대기 (10-15분 소요)
5. 이 스크립트 실행

주의사항:
- 인덱스가 없으면 새로 생성합니다
- 이미 인덱싱된 데이터는 건너뜁니다 (증분 업데이트)
- PostgreSQL 데이터 중 OpenSearch에 없는 것만 추가합니다
"""
import os
import sys
import django

# Django 설정
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from patents.models import Patent, RejectDocument
from papers.models import Paper
from patents.opensearch_client import get_opensearch_client, create_patents_index, create_papers_index, create_reject_documents_index, delete_index


def reindex_patents(client):
    """특허 데이터 전체 재인덱싱 (날짜 타입 수정 반영)"""
    print("\n" + "="*60)
    print("특허 데이터 전체 재인덱싱 시작")
    print("="*60)

    # 기존 인덱스 삭제 (날짜 타입 변경을 위해 필수)
    print("\n1️⃣  기존 patents 인덱스 삭제 중...")
    if client.indices.exists(index='patents'):
        delete_index(client, 'patents')
        print("✅ 기존 인덱스 삭제 완료")
    else:
        print("✅ 삭제할 인덱스가 없습니다")

    # 새 인덱스 생성 (Nori 기반, 날짜 타입 포함)
    print("\n2️⃣  새로운 patents 인덱스 생성...")
    if not create_patents_index(client):
        print("⚠️  인덱스 생성 실패")
        return
    print("✅ 인덱스 생성 완료")

    # PostgreSQL에서 데이터 읽기
    print("\n3️⃣  PostgreSQL에서 특허 데이터 읽기...")
    patents = Patent.objects.all()
    total = patents.count()
    print(f"총 {total:,}건의 특허 데이터 발견")

    if total == 0:
        print("⚠️  마이그레이션할 데이터가 없습니다")
        return

    # OpenSearch에 전체 재인덱싱
    print("\n4️⃣  OpenSearch에 데이터 인덱싱 중...")
    batch_size = 500
    success_count = 0
    error_count = 0

    actions = []
    for i, patent in enumerate(patents, 1):
        patent_id = str(patent.id)

        doc = {
            '_index': 'patents',
            '_id': patent_id,
            '_source': {
                'title': patent.title or '',
                'title_en': patent.title_en or '',
                'application_number': patent.application_number or '',
                'application_date': patent.application_date or '',
                'applicant': patent.applicant or '',
                'registration_number': patent.registration_number or '',
                'registration_date': patent.registration_date or '',
                'ipc_code': patent.ipc_code or '',
                'cpc_code': patent.cpc_code or '',
                'abstract': patent.abstract or '',
                'claims': patent.claims or '',
                'legal_status': patent.legal_status or '',
                'created_at': patent.created_at.isoformat() if patent.created_at else None,
                'updated_at': patent.updated_at.isoformat() if patent.updated_at else None
            }
        }
        actions.append(doc)

        # 배치 단위로 bulk 인덱싱
        if len(actions) >= batch_size:
            try:
                from opensearchpy import helpers
                helpers.bulk(client, actions)
                success_count += len(actions)
                print(f"  진행률: 처리 {i}/{total} | 추가 {success_count}건 | 건너뜀 {skip_count}건")
                actions = []
            except Exception as e:
                print(f"❌ Bulk 인덱싱 오류: {e}")
                error_count += len(actions)
                actions = []

    # 남은 데이터 인덱싱
    if actions:
        try:
            from opensearchpy import helpers
            helpers.bulk(client, actions)
            success_count += len(actions)
        except Exception as e:
            print(f"❌ Bulk 인덱싱 오류: {e}")
            error_count += len(actions)

    print(f"\n✅ 특허 인덱싱 완료!")
    print(f"   신규 추가: {success_count:,}건")
    print(f"   기존 데이터 건너뜀: {skip_count:,}건")
    if error_count > 0:
        print(f"   실패: {error_count:,}건")


def reindex_papers(client):
    """논문 데이터 증분 인덱싱"""
    print("\n" + "="*60)
    print("논문 데이터 증분 인덱싱 시작")
    print("="*60)

    # 인덱스가 없으면 생성 (Nori 기반)
    print("\n1️⃣  papers 인덱스 확인 및 생성...")
    if not client.indices.exists(index='papers'):
        print("   인덱스가 없습니다. 새로 생성합니다...")
        if not create_papers_index(client):
            print("⚠️  인덱스 생성 실패")
            return
        print("✅ 인덱스 생성 완료")
    else:
        print("✅ 인덱스가 이미 존재합니다")

    # PostgreSQL에서 데이터 읽기
    print("\n2️⃣  PostgreSQL에서 논문 데이터 읽기...")
    papers = Paper.objects.all()
    total = papers.count()
    print(f"총 {total:,}건의 논문 데이터 발견")

    if total == 0:
        print("⚠️  마이그레이션할 데이터가 없습니다")
        return

    # 기존 인덱싱된 ID 확인
    print("\n3️⃣  기존 인덱싱된 데이터 확인 중...")
    existing_count = client.count(index='papers')['count']
    print(f"OpenSearch에 이미 {existing_count:,}건 인덱싱됨")

    # OpenSearch에 증분 인덱싱
    print("\n4️⃣  OpenSearch에 데이터 인덱싱 중 (이미 있는 데이터는 건너뜀)...")
    batch_size = 500
    success_count = 0
    skip_count = 0
    error_count = 0

    actions = []
    for i, paper in enumerate(papers, 1):
        paper_id = str(paper.id)

        # 이미 인덱싱되어 있는지 확인
        try:
            if client.exists(index='papers', id=paper_id):
                skip_count += 1
                continue
        except Exception as e:
            pass  # 확인 실패 시 인덱싱 시도

        doc = {
            '_index': 'papers',
            '_id': paper_id,
            '_source': {
                'title_en': paper.title_en or '',
                'title_kr': paper.title_kr or '',
                'authors': paper.authors or '',
                'abstract_en': paper.abstract_en or '',
                'abstract_kr': paper.abstract_kr or '',
                'abstract_page_link': paper.abstract_page_link or '',
                'pdf_link': paper.pdf_link or '',
                'source_file': paper.source_file or '',
                'created_at': paper.created_at.isoformat() if paper.created_at else None,
                'updated_at': paper.updated_at.isoformat() if paper.updated_at else None
            }
        }
        actions.append(doc)

        # 배치 단위로 bulk 인덱싱
        if len(actions) >= batch_size:
            try:
                from opensearchpy import helpers
                helpers.bulk(client, actions)
                success_count += len(actions)
                print(f"  진행률: 처리 {i}/{total} | 추가 {success_count}건 | 건너뜀 {skip_count}건")
                actions = []
            except Exception as e:
                print(f"❌ Bulk 인덱싱 오류: {e}")
                error_count += len(actions)
                actions = []

    # 남은 데이터 인덱싱
    if actions:
        try:
            from opensearchpy import helpers
            helpers.bulk(client, actions)
            success_count += len(actions)
        except Exception as e:
            print(f"❌ Bulk 인덱싱 오류: {e}")
            error_count += len(actions)

    print(f"\n✅ 논문 인덱싱 완료!")
    print(f"   신규 추가: {success_count:,}건")
    print(f"   기존 데이터 건너뜀: {skip_count:,}건")
    if error_count > 0:
        print(f"   실패: {error_count:,}건")


def reindex_reject_documents(client):
    """거절결정서 데이터 증분 인덱싱"""
    print("\n" + "="*60)
    print("거절결정서 데이터 증분 인덱싱 시작")
    print("="*60)

    # 인덱스가 없으면 생성
    print("\n1️⃣  reject_documents 인덱스 확인 및 생성...")
    if not client.indices.exists(index='reject_documents'):
        print("   인덱스가 없습니다. 새로 생성합니다...")
        if not create_reject_documents_index(client):
            print("⚠️  인덱스 생성 실패")
            return
        print("✅ 인덱스 생성 완료")
    else:
        print("✅ 인덱스가 이미 존재합니다")

    # PostgreSQL에서 데이터 읽기
    print("\n2️⃣  PostgreSQL에서 거절결정서 데이터 읽기...")
    docs = RejectDocument.objects.all()
    total = docs.count()
    print(f"총 {total:,}건의 거절결정서 데이터 발견")

    if total == 0:
        print("⚠️  마이그레이션할 데이터가 없습니다")
        return

    # 기존 인덱싱된 ID 확인
    print("\n3️⃣  기존 인덱싱된 데이터 확인 중...")
    existing_count = client.count(index='reject_documents')['count']
    print(f"OpenSearch에 이미 {existing_count:,}건 인덱싱됨")

    # OpenSearch에 증분 인덱싱
    print("\n4️⃣  OpenSearch에 데이터 인덱싱 중 (이미 있는 데이터는 건너뜀)...")
    batch_size = 500
    success_count = 0
    skip_count = 0
    error_count = 0

    actions = []
    for i, doc in enumerate(docs, 1):
        doc_id = str(doc.id)

        # 이미 인덱싱되어 있는지 확인
        try:
            if client.exists(index='reject_documents', id=doc_id):
                skip_count += 1
                continue
        except Exception as e:
            pass  # 확인 실패 시 인덱싱 시도

        action = {
            '_index': 'reject_documents',
            '_id': doc_id,
            '_source': {
                'doc_id': doc.doc_id or '',
                'send_number': doc.send_number or '',
                'send_date': doc.send_date or '',
                'applicant_code': doc.applicant_code or '',
                'applicant': doc.applicant or '',
                'agent': doc.agent or '',
                'application_number': doc.application_number or '',
                'invention_name': doc.invention_name or '',
                'examination_office': doc.examination_office or '',
                'examiner': doc.examiner or '',
                'tables_raw': doc.tables_raw or '',
                'processed_text': doc.processed_text or '',
                'created_at': doc.created_at.isoformat() if doc.created_at else None,
                'updated_at': doc.updated_at.isoformat() if doc.updated_at else None
            }
        }
        actions.append(action)

        # 배치 단위로 bulk 인덱싱
        if len(actions) >= batch_size:
            try:
                from opensearchpy import helpers
                helpers.bulk(client, actions)
                success_count += len(actions)
                print(f"  진행률: 처리 {i}/{total} | 추가 {success_count}건 | 건너뜀 {skip_count}건")
                actions = []
            except Exception as e:
                print(f"❌ Bulk 인덱싱 오류: {e}")
                error_count += len(actions)
                actions = []

    # 남은 데이터 인덱싱
    if actions:
        try:
            from opensearchpy import helpers
            helpers.bulk(client, actions)
            success_count += len(actions)
        except Exception as e:
            print(f"❌ Bulk 인덱싱 오류: {e}")
            error_count += len(actions)

    print(f"\n✅ 거절결정서 인덱싱 완료!")
    print(f"   신규 추가: {success_count:,}건")
    print(f"   기존 데이터 건너뜀: {skip_count:,}건")
    if error_count > 0:
        print(f"   실패: {error_count:,}건")


def main():
    print("="*60)
    print("Nori 기반 OpenSearch 증분 인덱싱 스크립트")
    print("="*60)
    print("\n⚠️  주의사항:")
    print("1. AWS Console에서 analysis-nori 패키지를 먼저 연결해야 합니다")
    print("2. 인덱스가 없으면 새로 생성합니다")
    print("3. 이미 인덱싱된 데이터는 건너뜁니다 (증분 업데이트)")
    print("4. PostgreSQL에 있지만 OpenSearch에 없는 데이터만 추가합니다")

    response = input("\n계속하시겠습니까? (yes/no): ")
    if response.lower() != 'yes':
        print("작업을 취소했습니다.")
        return

    try:
        # OpenSearch 클라이언트 생성
        print("\n📡 OpenSearch 연결 중...")
        client = get_opensearch_client()

        # 연결 테스트
        info = client.info()
        print(f"✅ OpenSearch 연결 성공!")
        print(f"   클러스터: {info['cluster_name']}")
        print(f"   버전: {info['version']['number']}")

        # 특허 재인덱싱
        reindex_patents(client)

        # 논문 재인덱싱
        reindex_papers(client)

        # 거절결정서 재인덱싱
        reindex_reject_documents(client)

        print("\n" + "="*60)
        print("✅ 전체 재인덱싱 완료!")
        print("="*60)

        # 최종 통계
        print("\n📊 최종 인덱스 통계:")
        for index_name in ['patents', 'papers', 'reject_documents']:
            if client.indices.exists(index=index_name):
                stats = client.cat.count(index=index_name, format='json')
                count = int(stats[0]['count'])
                print(f"   {index_name}: {count:,}건")

    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
