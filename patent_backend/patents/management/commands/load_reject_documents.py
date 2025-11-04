"""
거절 사유 문서 CSV 파일을 PostgreSQL 데이터베이스에 로드하는 management command
"""
import pandas as pd
from django.core.management.base import BaseCommand
from patents.models import RejectDocument


class Command(BaseCommand):
    help = 'Load reject documents from CSV file into PostgreSQL database'

    def add_arguments(self, parser):
        parser.add_argument(
            '--file',
            type=str,
            default='/home/juhyeong/workspace/final_project/SKN15-FINAL-3TEAM/data/cleaned_reject_documents.csv',
            help='Path to the CSV file'
        )
        parser.add_argument(
            '--batch-size',
            type=int,
            default=500,
            help='Number of records to insert at once'
        )

    def handle(self, *args, **options):
        csv_file = options['file']
        batch_size = options['batch_size']

        self.stdout.write(self.style.WARNING(f'Deleting existing reject documents...'))
        RejectDocument.objects.all().delete()
        self.stdout.write(self.style.SUCCESS('Deleted all existing reject documents'))

        self.stdout.write(self.style.WARNING(f'Loading reject documents from {csv_file}...'))

        # pandas로 CSV 읽기 (줄바꿈 처리)
        df = pd.read_csv(csv_file, encoding='utf-8')

        self.stdout.write(f'Found {len(df)} rows in CSV file')

        reject_docs_to_create = []
        total_count = 0

        for idx, row in df.iterrows():
            reject_doc = RejectDocument(
                doc_id=str(row.get('doc_id', '')),
                send_number=str(row.get('발송번호', '')) if pd.notna(row.get('발송번호')) else '',
                send_date=str(row.get('발송일자', '')) if pd.notna(row.get('발송일자')) else '',
                applicant_code=str(row.get('출원인코드', '')) if pd.notna(row.get('출원인코드')) else '',
                applicant=str(row.get('출원인', '')) if pd.notna(row.get('출원인')) else '',
                agent=str(row.get('대리인', '')) if pd.notna(row.get('대리인')) else '',
                application_number=str(row.get('출원번호', '')) if pd.notna(row.get('출원번호')) else '',
                invention_name=str(row.get('발명의_명칭', '')) if pd.notna(row.get('발명의_명칭')) else '',
                examination_office=str(row.get('심사기관', '')) if pd.notna(row.get('심사기관')) else '',
                examiner=str(row.get('심사관', '')) if pd.notna(row.get('심사관')) else '',
                tables_raw=str(row.get('tables_raw', '')) if pd.notna(row.get('tables_raw')) else '',
                processed_text=str(row.get('processed_text', '')) if pd.notna(row.get('processed_text')) else ''
            )
            reject_docs_to_create.append(reject_doc)

            if len(reject_docs_to_create) >= batch_size:
                RejectDocument.objects.bulk_create(reject_docs_to_create, ignore_conflicts=True)
                total_count += len(reject_docs_to_create)
                self.stdout.write(f'Loaded {total_count} reject documents...')
                reject_docs_to_create = []

        # 나머지 데이터 삽입
        if reject_docs_to_create:
            RejectDocument.objects.bulk_create(reject_docs_to_create, ignore_conflicts=True)
            total_count += len(reject_docs_to_create)

        self.stdout.write(self.style.SUCCESS(f'Successfully loaded {total_count} reject documents'))
