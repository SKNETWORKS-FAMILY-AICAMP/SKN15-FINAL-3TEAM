"""
특허 데이터를 데이터베이스에 로드하는 management command
"""
import pandas as pd
from django.core.management.base import BaseCommand
from patents.models import Patent


class Command(BaseCommand):
    help = '특허 CSV 파일을 데이터베이스에 로드합니다'

    def add_arguments(self, parser):
        parser.add_argument(
            '--file',
            type=str,
            default='/home/juhyeong/workspace/mergerd_total_not_null (1).csv',
            help='특허 CSV 파일 경로'
        )
        parser.add_argument(
            '--batch-size',
            type=int,
            default=1000,
            help='한 번에 처리할 레코드 수'
        )
        parser.add_argument(
            '--limit',
            type=int,
            default=None,
            help='로드할 최대 레코드 수 (테스트용)'
        )

    def handle(self, *args, **options):
        csv_file = options['file']
        batch_size = options['batch_size']
        limit = options['limit']

        self.stdout.write(f'CSV 파일 읽는 중: {csv_file}')

        try:
            # pandas로 CSV 읽기 (첫 번째 컬럼은 인덱스)
            df = pd.read_csv(csv_file, encoding='utf-8', index_col=0)

            # limit 옵션이 있으면 제한
            if limit:
                df = df.head(limit)
                self.stdout.write(f'제한 모드: 최대 {limit}개만 로드합니다.')

            self.stdout.write(f'총 {len(df)}개의 레코드를 발견했습니다.')

            # 기존 데이터 삭제 여부 확인
            existing_count = Patent.objects.count()
            if existing_count > 0:
                self.stdout.write(
                    self.style.WARNING(f'기존 특허 데이터 {existing_count}개가 존재합니다.')
                )
                confirm = input('기존 데이터를 삭제하고 새로 로드하시겠습니까? (yes/no): ')
                if confirm.lower() == 'yes':
                    Patent.objects.all().delete()
                    self.stdout.write(self.style.SUCCESS('기존 데이터를 삭제했습니다.'))
                else:
                    self.stdout.write('기존 데이터에 추가합니다.')

            # Patent 객체 생성 (CSV 컬럼명에 맞춤)
            patents_to_create = []
            skipped_count = 0

            for idx, row in df.iterrows():
                # 필수 필드 검증 (출원번호)
                app_number = row.get('출원번호')
                if pd.isna(app_number) or str(app_number).strip() == '':
                    skipped_count += 1
                    continue

                patent = Patent(
                    title=str(row.get('발명의명칭', '')) if pd.notna(row.get('발명의명칭')) else '',
                    title_en=str(row.get('발명의명칭(영문)', '')) if pd.notna(row.get('발명의명칭(영문)')) else None,
                    application_number=str(app_number).strip(),
                    application_date=str(row.get('출원일자', '')) if pd.notna(row.get('출원일자')) else None,
                    applicant=str(row.get('출원인', '')) if pd.notna(row.get('출원인')) else None,
                    registration_number=str(row.get('등록번호', '')) if pd.notna(row.get('등록번호')) else None,
                    registration_date=str(row.get('등록일자', '')) if pd.notna(row.get('등록일자')) else None,
                    ipc_code=str(row.get('IPC분류', '')) if pd.notna(row.get('IPC분류')) else None,
                    cpc_code=str(row.get('CPC분류', '')) if pd.notna(row.get('CPC분류')) else None,
                    abstract=str(row.get('요약', '')) if pd.notna(row.get('요약')) else None,
                    claims=str(row.get('청구항', '')) if pd.notna(row.get('청구항')) else None,
                    legal_status=str(row.get('법적상태', '')) if pd.notna(row.get('법적상태')) else None,
                )

                patents_to_create.append(patent)

                # 배치 단위로 저장
                if len(patents_to_create) >= batch_size:
                    Patent.objects.bulk_create(patents_to_create, ignore_conflicts=True)
                    self.stdout.write(f'{len(patents_to_create)}개 레코드 저장 완료 (진행률: {idx + 1}/{len(df)})')
                    patents_to_create = []

            # 남은 레코드 저장
            if patents_to_create:
                Patent.objects.bulk_create(patents_to_create, ignore_conflicts=True)
                self.stdout.write(f'{len(patents_to_create)}개 레코드 저장 완료')

            # 최종 통계
            total_count = Patent.objects.count()
            unique_app_numbers = Patent.objects.values('application_number').distinct().count()

            self.stdout.write(
                self.style.SUCCESS(
                    f'\n성공적으로 로드 완료!\n'
                    f'- 총 특허: {total_count}개\n'
                    f'- 고유 출원번호: {unique_app_numbers}개\n'
                    f'- 건너뛴 레코드: {skipped_count}개 (출원번호 없음)'
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
