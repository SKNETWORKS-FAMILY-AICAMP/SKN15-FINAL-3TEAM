"""
특허 OpenSearch 재인덱싱 Management Command
"""
from django.core.management.base import BaseCommand
from patents.models import Patent
from patents.opensearch_client import (
    get_opensearch_client,
    create_patents_index,
    delete_index
)


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
            client = get_opensearch_client()
            self.stdout.write("✅ OpenSearch 연결 성공\n")

            # 인덱스 재생성 (옵션)
            if recreate_index:
                self.stdout.write("🔄 patents 인덱스 재생성 중...")
                try:
                    delete_index(client, 'patents')
                    self.stdout.write("  ✓ 기존 인덱스 삭제")
                except Exception as e:
                    self.stdout.write(f"  ℹ 기존 인덱스 없음: {e}")

                create_patents_index(client, 'patents')
                self.stdout.write("  ✓ 새 인덱스 생성 완료\n")

            # 특허 데이터 조회
            patents = Patent.objects.all()
            total_count = patents.count()
            self.stdout.write(f"📊 총 {total_count:,}개 특허 인덱싱 시작...\n")

            # 배치 단위로 인덱싱
            success_count = 0
            error_count = 0

            for i, patent in enumerate(patents, 1):
                # 날짜 형식 변환: yyyy.MM.dd -> yyyy-MM-dd
                application_date = patent.application_date
                if application_date:
                    application_date = application_date.replace('.', '-')

                registration_date = patent.registration_date
                if registration_date:
                    registration_date = registration_date.replace('.', '-')

                # 특허 문서 생성
                doc = {
                    'title': patent.title or '',
                    'title_en': patent.title_en or '',
                    'application_number': patent.application_number,
                    'application_date': application_date or None,
                    'applicant': patent.applicant or '',
                    'registration_number': patent.registration_number or '',
                    'registration_date': registration_date or None,
                    'ipc_code': patent.ipc_code or '',
                    'cpc_code': patent.cpc_code or '',
                    'abstract': patent.abstract or '',
                    'claims': patent.claims or '',
                    'legal_status': patent.legal_status or '',
                    'created_at': patent.created_at.isoformat() if patent.created_at else None,
                    'updated_at': patent.updated_at.isoformat() if patent.updated_at else None,
                }

                # OpenSearch에 인덱싱 (재시도 로직 포함)
                retry_count = 0
                max_retries = 3
                indexed = False

                while retry_count < max_retries and not indexed:
                    try:
                        client.index(
                            index='patents',
                            id=patent.application_number,
                            body=doc,
                            timeout=60  # 개별 요청 타임아웃 (초 단위)
                        )
                        success_count += 1
                        indexed = True
                    except Exception as e:
                        retry_count += 1
                        if retry_count >= max_retries:
                            error_count += 1
                            self.stdout.write(
                                self.style.ERROR(
                                    f"  ❌ 인덱싱 실패 (ID: {patent.application_number}, 재시도 {max_retries}회): {str(e)[:100]}"
                                )
                            )
                        else:
                            # 짧은 대기 후 재시도
                            import time
                            time.sleep(1)

                # 진행 상황 출력
                if i % batch_size == 0:
                    progress = (i / total_count) * 100
                    self.stdout.write(
                        f"  ⏳ {i:,}/{total_count:,} ({progress:.1f}%) - "
                        f"성공: {success_count:,}, 실패: {error_count}"
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
