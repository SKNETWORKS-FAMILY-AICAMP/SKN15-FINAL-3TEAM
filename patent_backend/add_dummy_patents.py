"""
거절 사유가 있는 출원번호로 더미 특허 데이터를 생성하는 스크립트
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from patents.models import Patent, RejectDocument

# 거절 사유가 있는 출원번호 가져오기
reject_app_numbers = list(RejectDocument.objects.values_list('application_number', flat=True).distinct()[:400])

print(f"Found {len(reject_app_numbers)} unique application numbers with reject reasons")

# 이미 존재하는 특허의 출원번호 제외
existing_app_numbers = set(Patent.objects.values_list('application_number', flat=True))
new_app_numbers = [num for num in reject_app_numbers if num not in existing_app_numbers]

print(f"Will create {len(new_app_numbers)} new patents")

# 더미 특허 데이터 생성
patents_to_create = []
for app_num in new_app_numbers:
    # 해당 출원번호의 거절 문서에서 발명명칭 가져오기
    reject_doc = RejectDocument.objects.filter(application_number=app_num).first()

    patent = Patent(
        title=reject_doc.invention_name if reject_doc and reject_doc.invention_name else f"발명 {app_num}",
        application_number=app_num,
        application_date=reject_doc.send_date.replace('.', '') if reject_doc and reject_doc.send_date else '',
        applicant=reject_doc.applicant if reject_doc and reject_doc.applicant else '',
        abstract=f"이것은 출원번호 {app_num}의 요약입니다.",
        claims=f"이것은 출원번호 {app_num}의 청구항입니다."
    )
    patents_to_create.append(patent)

# 배치로 생성
batch_size = 100
total_created = 0
for i in range(0, len(patents_to_create), batch_size):
    batch = patents_to_create[i:i+batch_size]
    Patent.objects.bulk_create(batch, ignore_conflicts=True)
    total_created += len(batch)
    print(f"Created {total_created} patents...")

print(f"Successfully created {total_created} patents!")

# 총 특허 수 확인
total_patents = Patent.objects.count()
print(f"Total patents in database: {total_patents}")

# 거절 사유와 매칭되는 특허 수 확인
matching_count = Patent.objects.filter(
    application_number__in=RejectDocument.objects.values_list('application_number', flat=True)
).count()
print(f"Patents with reject reasons: {matching_count}")
