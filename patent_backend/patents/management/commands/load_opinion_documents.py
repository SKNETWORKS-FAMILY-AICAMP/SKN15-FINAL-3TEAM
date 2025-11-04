"""
의견 제출 통지서 데이터를 데이터베이스에 로드하는 management command
"""
import pandas as pd
from django.core.management.base import BaseCommand
from patents.models import OpinionDocument


class Command(BaseCommand):
    help = '의견 제출 통지서 CSV 파일을 데이터베이스에 로드합니다'

    def add_arguments(self, parser):
        parser.add_argument(
            '--file',
            type=str,
            default='/home/juhyeong/workspace/final_project/SKN15-FINAL-3TEAM/data/opinion_sample_100.csv',
            help='의견 제출 통지서 CSV 파일 경로'
        )
        parser.add_argument(
            '--batch-size',
            type=int,
            default=100,
            help='한 번에 처리할 레코드 수'
        )

    def handle(self, *args, **options):
        csv_file = options['file']
        batch_size = options['batch_size']

        self.stdout.write(f'CSV 파일 읽는 중: {csv_file}')

        try:
            # pandas로 CSV 읽기 (줄바꿈 처리)
            df = pd.read_csv(csv_file, encoding='utf-8')

            self.stdout.write(f'총 {len(df)}개의 레코드를 발견했습니다.')

            # 기존 데이터 삭제 여부 확인
            existing_count = OpinionDocument.objects.count()
            if existing_count > 0:
                self.stdout.write(
                    self.style.WARNING(f'기존 의견 제출 통지서 데이터 {existing_count}개가 존재합니다.')
                )
                confirm = input('기존 데이터를 삭제하고 새로 로드하시겠습니까? (yes/no): ')
                if confirm.lower() == 'yes':
                    OpinionDocument.objects.all().delete()
                    self.stdout.write(self.style.SUCCESS('기존 데이터를 삭제했습니다.'))
                else:
                    self.stdout.write('기존 데이터에 추가합니다.')

            # OpinionDocument 객체 생성
            opinion_docs_to_create = []

            for idx, row in df.iterrows():
                # 출원번호를 문자열로 변환
                app_num = str(row.get('application_number', ''))

                opinion_doc = OpinionDocument(
                    application_number=app_num,
                    full_text=str(row.get('full_text', '')) if pd.notna(row.get('full_text')) else ''
                )

                opinion_docs_to_create.append(opinion_doc)

                # 배치 단위로 저장
                if len(opinion_docs_to_create) >= batch_size:
                    OpinionDocument.objects.bulk_create(opinion_docs_to_create, ignore_conflicts=True)
                    self.stdout.write(f'{len(opinion_docs_to_create)}개 레코드 저장 완료 (진행률: {idx + 1}/{len(df)})')
                    opinion_docs_to_create = []

            # 남은 레코드 저장
            if opinion_docs_to_create:
                OpinionDocument.objects.bulk_create(opinion_docs_to_create, ignore_conflicts=True)
                self.stdout.write(f'{len(opinion_docs_to_create)}개 레코드 저장 완료')

            # 최종 통계
            total_count = OpinionDocument.objects.count()
            unique_app_numbers = OpinionDocument.objects.values('application_number').distinct().count()

            self.stdout.write(
                self.style.SUCCESS(
                    f'\n성공적으로 로드 완료!\n'
                    f'- 총 의견 제출 통지서: {total_count}개\n'
                    f'- 고유 출원번호: {unique_app_numbers}개'
                )
            )

        except FileNotFoundError:
            self.stdout.write(
                self.style.ERROR(f'파일을 찾을 수 없습니다: {csv_file}')
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'오류 발생: {str(e)}')
            )
            import traceback
            traceback.print_exc()
