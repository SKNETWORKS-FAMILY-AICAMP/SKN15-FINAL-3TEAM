"""
논문 CSV 데이터를 PostgreSQL에 로드하는 Management Command
"""
import csv
from django.core.management.base import BaseCommand
from papers.models import Paper
from django.contrib.postgres.search import SearchVector


class Command(BaseCommand):
    help = 'Load papers from CSV file into PostgreSQL database'

    def add_arguments(self, parser):
        parser.add_argument(
            '--file',
            type=str,
            default='/home/juhyeong/workspace/papers_final_translated_with_dates.csv',
            help='Path to CSV file'
        )
        parser.add_argument(
            '--batch-size',
            type=int,
            default=1000,
            help='Batch size for bulk insert'
        )

    def handle(self, *args, **options):
        csv_file = options['file']
        batch_size = options['batch_size']

        self.stdout.write(f"Loading papers from {csv_file}...")

        # 기존 데이터 삭제 (선택사항)
        Paper.objects.all().delete()
        self.stdout.write("Cleared existing papers data")

        papers_to_create = []
        total_count = 0

        with open(csv_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)

            for row in reader:
                paper = Paper(
                    title_en=row.get('Title_EN', ''),
                    title_kr=row.get('Title_KR', ''),
                    authors=row.get('Authors', ''),
                    abstract_en=row.get('Abstract_EN', ''),
                    abstract_kr=row.get('Abstract_KR', ''),
                    abstract_page_link=row.get('Abstract_Page_Link', ''),
                    pdf_link=row.get('PDF_Link', ''),
                    source_file=row.get('source_file', ''),
                    published_date=row.get('Published_Date', '')
                )
                papers_to_create.append(paper)
                total_count += 1

                # Batch insert
                if len(papers_to_create) >= batch_size:
                    Paper.objects.bulk_create(papers_to_create)
                    self.stdout.write(f"Inserted {total_count} papers...")
                    papers_to_create = []

            # 남은 데이터 insert
            if papers_to_create:
                Paper.objects.bulk_create(papers_to_create)

        self.stdout.write(self.style.SUCCESS(f"Successfully loaded {total_count} papers"))

        # SearchVector 업데이트
        self.stdout.write("Updating search vectors...")
        Paper.objects.update(
            search_vector=(
                SearchVector('title_kr', weight='A') +
                SearchVector('title_en', weight='B') +
                SearchVector('abstract_kr', weight='B') +
                SearchVector('authors', weight='C')
            )
        )
        self.stdout.write(self.style.SUCCESS("Search vectors updated successfully"))
