"""
샘플 특허 데이터 적재 스크립트 (100건)
"""
import os
import sys
import django
import pandas as pd
from pathlib import Path

# Django 설정 초기화
BASE_DIR = Path(__file__).resolve().parent
sys.path.append(str(BASE_DIR))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from patents.models import Patent

# CSV 파일 경로
CSV_PATH = '/home/juhyeong/workspace/mergerd_total_not_null (1).csv'


def load_sample_data(n_samples=100):
    """샘플 데이터 적재"""
    
    print(f"\n{'='*60}")
    print(f"  샘플 특허 데이터 적재 ({n_samples}건)")
    print(f"{'='*60}\n")
    
    # 1. CSV 읽기
    print(f"📂 CSV 파일 로드 중... ({CSV_PATH})")
    try:
        df = pd.read_csv(CSV_PATH, nrows=n_samples)
        print(f"✅ {len(df)}건 로드 완료\n")
    except Exception as e:
        print(f"❌ CSV 로드 실패: {e}")
        return
    
    # 2. 기존 데이터 삭제 여부 확인
    existing_count = Patent.objects.count()
    if existing_count > 0:
        response = input(f"\n⚠️  기존 데이터 {existing_count}건이 있습니다. 삭제하고 진행할까요? (y/N): ")
        if response.lower() == 'y':
            Patent.objects.all().delete()
            print(f"🗑️  기존 데이터 삭제 완료\n")
        else:
            print("ℹ️  기존 데이터 유지\n")
    
    # 3. 데이터 변환 및 적재
    print("💾 데이터베이스에 적재 중...")
    success_count = 0
    error_count = 0
    
    for idx, row in df.iterrows():
        try:
            Patent.objects.create(
                title=str(row['발명의명칭']) if pd.notna(row['발명의명칭']) else '',
                title_en=str(row['발명의명칭(영문)']) if pd.notna(row['발명의명칭(영문)']) else None,
                application_number=str(row['출원번호']) if pd.notna(row['출원번호']) else '',
                application_date=str(row['출원일자']) if pd.notna(row['출원일자']) else None,
                applicant=str(row['출원인']) if pd.notna(row['출원인']) else None,
                registration_number=str(row['등록번호']) if pd.notna(row['등록번호']) else None,
                registration_date=str(row['등록일자']) if pd.notna(row['등록일자']) else None,
                ipc_code=str(row['IPC분류']) if pd.notna(row['IPC분류']) else None,
                cpc_code=str(row['CPC분류']) if pd.notna(row['CPC분류']) else None,
                abstract=str(row['요약']) if pd.notna(row['요약']) else None,
                claims=str(row['청구항']) if pd.notna(row['청구항']) else None,
                legal_status=str(row['법적상태']) if pd.notna(row['법적상태']) else None,
            )
            success_count += 1
            
            # 진행상황 표시
            if (idx + 1) % 10 == 0:
                print(f"  진행: {idx + 1}/{n_samples}건")
                
        except Exception as e:
            error_count += 1
            print(f"  ⚠️  {idx + 1}번째 행 오류: {e}")
    
    # 4. 결과 출력
    print(f"\n{'='*60}")
    print(f"  적재 완료!")
    print(f"{'='*60}")
    print(f"✅ 성공: {success_count}건")
    print(f"❌ 실패: {error_count}건")
    print(f"📊 총 데이터: {Patent.objects.count()}건\n")
    
    # 5. 샘플 데이터 확인
    print("📋 샘플 데이터 미리보기:\n")
    for patent in Patent.objects.all()[:3]:
        print(f"  [{patent.application_number}] {patent.title[:50]}...")
    print()


if __name__ == '__main__':
    load_sample_data(100)
