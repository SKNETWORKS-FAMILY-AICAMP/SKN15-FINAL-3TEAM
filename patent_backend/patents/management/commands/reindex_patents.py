"""
특허 OpenSearch 재인덱싱 Management Command
"""
from django.core.management.base import BaseCommand
from patents.models import Patent
from patents.opensearch_client import OpenSearchClient


class Command(BaseCommand):
    help = 'Reindex all patents to OpenSearch'

    def add_arguments(self, parser):
        parser.add_argument(
            '--recreate-index',
            action='store_true',
            help='Delete and recreate the patents index before reindexing'
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
        self.stdout.write("  특허 OpenSearch 재인덱싱")
        self.stdout.write("="*60 + "\n")

        try:
            # OpenSearch 클라이언트 초기화
            client = OpenSearchClient()
            self.stdout.write("✅ OpenSearch 연결 성공\n")

            # 인덱스 재생성 (옵션)
            if recreate_index:
                self.stdout.write("🔄 patents 인덱스 재생성 중...")
                try:
                    client.client.indices.delete(index='patents')
                    self.stdout.write("  ✓ 기존 인덱스 삭제")
                except Exception as e:
                    self.stdout.write(f"  ℹ 기존 인덱스 없음: {e}")

                client.create_patents_index()
                self.stdout.write("  ✓ 새 인덱스 생성 완료\n")

            # 특허 데이터 조회
            patents = Patent.objects.all()
            total_count = patents.count()
            self.stdout.write(f"📊 총 {total_count:,}개 특허 인덱싱 시작...\n")

            # 배치 단위로 인덱싱
            success_count = 0
            error_count = 0

            for i, patent in enumerate(patents, 1):
                try:
                    client.index_patent(patent)
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
                            f"  ❌ 인덱싱 실패 (ID: {patent.application_number}): {e}"
                        )
                    )

            # 최종 결과
            self.stdout.write("\n" + "="*60)
            self.stdout.write("📈 인덱싱 완료")
            self.stdout.write("="*60)
            self.stdout.write(f"  총 특허 수: {total_count:,}")
            self.stdout.write(f"  성공: {success_count:,}")
            self.stdout.write(f"  실패: {error_count}")

            if error_count == 0:
                self.stdout.write(self.style.SUCCESS("\n✅ 모든 특허가 성공적으로 인덱싱되었습니다!"))
            else:
                self.stdout.write(self.style.WARNING(f"\n⚠️  {error_count}개 특허 인덱싱 실패"))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"\n❌ 오류 발생: {e}"))
            import traceback
            traceback.print_exc()
            return

        self.stdout.write("")
