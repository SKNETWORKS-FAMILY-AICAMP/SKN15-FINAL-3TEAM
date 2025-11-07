"""
논문 OpenSearch 재인덱싱 Management Command
"""
from django.core.management.base import BaseCommand
from papers.models import Paper
from patents.opensearch_client import (
    get_opensearch_client,
    create_papers_index,
    delete_index
)


class Command(BaseCommand):
    help = 'Reindex all papers to OpenSearch'

    def add_arguments(self, parser):
        parser.add_argument(
            '--recreate-index',
            action='store_true',
            help='Delete and recreate the papers index before reindexing'
        )
        parser.add_argument(
            '--batch-size',
            type=int,
            default=100,
            help='Batch size for indexing (default: 100)'
        )

    def handle(self, *args, **options):
        recreate_index = options['recreate_index']
        batch_size = options['batch_size']

        self.stdout.write("\n" + "="*60)
        self.stdout.write("  논문 OpenSearch 재인덱싱")
        self.stdout.write("="*60 + "\n")

        try:
            # OpenSearch 클라이언트 초기화
            client = get_opensearch_client()
            self.stdout.write("✅ OpenSearch 연결 성공\n")

            # 인덱스 재생성 (옵션)
            if recreate_index:
                self.stdout.write("🔄 papers 인덱스 재생성 중...")
                try:
                    delete_index(client, 'papers')
                    self.stdout.write("  ✓ 기존 인덱스 삭제")
                except Exception as e:
                    self.stdout.write(f"  ℹ 기존 인덱스 없음: {e}")

                create_papers_index(client, 'papers')
                self.stdout.write("  ✓ 새 인덱스 생성 완료\n")

            # 논문 데이터 조회
            papers = Paper.objects.all()
            total_count = papers.count()
            self.stdout.write(f"📊 총 {total_count:,}개 논문 인덱싱 시작...\n")

            # 배치 단위로 인덱싱
            success_count = 0
            error_count = 0

            for i, paper in enumerate(papers, 1):
                try:
                    # 논문 문서 생성
                    doc = {
                        'title_en': paper.title_en or '',
                        'title_kr': paper.title_kr or '',
                        'authors': paper.authors or '',
                        'abstract_en': paper.abstract_en or '',
                        'abstract_kr': paper.abstract_kr or '',
                        'abstract_page_link': paper.abstract_page_link or '',
                        'pdf_link': paper.pdf_link or '',
                        'source_file': paper.source_file or '',
                        'published_date': paper.published_date or None,
                        'created_at': paper.created_at.isoformat() if paper.created_at else None,
                        'updated_at': paper.updated_at.isoformat() if paper.updated_at else None,
                    }

                    # OpenSearch에 인덱싱
                    client.index(
                        index='papers',
                        id=paper.id,
                        body=doc
                    )
                    success_count += 1

                    # 진행 상황 출력
                    if i % batch_size == 0:
                        progress = (i / total_count) * 100
                        self.stdout.write(
                            f"  ⏳ {i:,}/{total_count:,} ({progress:.1f}%) - "
                            f"성공: {success_count:,}, 실패: {error_count}"
                        )
                except Exception as e:
                    error_count += 1
                    self.stdout.write(
                        self.style.ERROR(
                            f"  ❌ 인덱싱 실패 (ID: {paper.id}): {e}"
                        )
                    )

            # 최종 결과
            self.stdout.write("\n" + "="*60)
            self.stdout.write("📈 인덱싱 완료")
            self.stdout.write("="*60)
            self.stdout.write(f"  총 논문 수: {total_count:,}")
            self.stdout.write(f"  성공: {success_count:,}")
            self.stdout.write(f"  실패: {error_count}")

            if error_count == 0:
                self.stdout.write(self.style.SUCCESS("\n✅ 모든 논문이 성공적으로 인덱싱되었습니다!"))
            else:
                self.stdout.write(self.style.WARNING(f"\n⚠️  {error_count}개 논문 인덱싱 실패"))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"\n❌ 오류 발생: {e}"))
            import traceback
            traceback.print_exc()
            return

        self.stdout.write("")
