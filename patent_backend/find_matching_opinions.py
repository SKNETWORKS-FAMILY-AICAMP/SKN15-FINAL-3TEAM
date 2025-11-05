"""
현재 거절 데이터와 매칭되는 의견 제출 통지서 데이터 100개 찾기
"""
import os
import sys
import django
import pandas as pd

# Django 설정
sys.path.append('/home/juhyeong/workspace/final_project/SKN15-FINAL-3TEAM/patent_backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from patents.models import RejectDocument

# 거절 문서의 출원번호 가져오기
reject_app_numbers = set(RejectDocument.objects.values_list('application_number', flat=True))
print(f"총 거절 문서 출원번호 개수: {len(reject_app_numbers)}")

# 의견 제출 통지서 CSV 파일 읽기
opinion_csv_path = '/home/juhyeong/workspace/opinion_v0.1.csv'
df = pd.read_csv(opinion_csv_path, encoding='utf-8')
print(f"총 의견 제출 통지서 개수: {len(df)}")

# 매칭되는 출원번호 찾기
matching_opinions = df[df['application_number'].isin(reject_app_numbers)]
print(f"매칭되는 의견 제출 통지서 개수: {len(matching_opinions)}")

# 100개 샘플 추출
if len(matching_opinions) >= 100:
    sample_opinions = matching_opinions.head(100)
else:
    sample_opinions = matching_opinions

print(f"\n추출한 샘플 개수: {len(sample_opinions)}")
print(f"\n샘플 출원번호 예시:")
print(sample_opinions['application_number'].head(10).tolist())

# 샘플 데이터 저장
output_path = '/home/juhyeong/workspace/final_project/SKN15-FINAL-3TEAM/data/opinion_sample_100.csv'
sample_opinions.to_csv(output_path, index=False, encoding='utf-8')
print(f"\n샘플 데이터 저장 완료: {output_path}")
