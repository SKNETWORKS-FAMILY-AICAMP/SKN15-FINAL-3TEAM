"""
로컬 PC에서 직접 RDS로 특허 데이터 적재 (프롬프트 없음 버전)
서버 용량 걱정 없이 로컬에서 실행
"""
import pandas as pd
import psycopg2
from psycopg2.extras import execute_batch
from tqdm import tqdm

# RDS 연결 정보
DB_CONFIG = {
    'dbname': 'patent_db',
    'user': 'postgres',
    'password': '3-bengio123',
    'host': 'my-patent-db.c9iw88yiic4o.ap-northeast-2.rds.amazonaws.com',
    'port': '5432'
}

# CSV 파일 경로 (로컬 PC)
CSV_FILE = '/home/juhyeong/workspace/mergerd_total_not_null (1).csv'

# 배치 크기
BATCH_SIZE = 500

def load_patents_streaming():
    """
    스트리밍 방식으로 CSV를 읽어서 바로 RDS에 적재
    메모리 효율적 - 한 번에 전체 파일을 로드하지 않음
    """

    print(f"\n{'='*60}")
    print(f"  특허 데이터 RDS 적재 (스트리밍 방식)")
    print(f"{'='*60}\n")

    # RDS 연결
    print("📡 RDS 연결 중...")
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        print("✅ RDS 연결 성공\n")
    except Exception as e:
        print(f"❌ RDS 연결 실패: {e}")
        return

    # 기존 데이터 확인
    cur.execute("SELECT COUNT(*) FROM patents")
    existing_count = cur.fetchone()[0]

    print(f"ℹ️  기존 데이터: {existing_count:,}건")
    print(f"ℹ️  기존 데이터 유지하고 새 데이터만 추가합니다.\n")

    # CSV 파일 크기 확인
    import os
    file_size_mb = os.path.getsize(CSV_FILE) / (1024 * 1024)
    print(f"📂 CSV 파일: {CSV_FILE}")
    print(f"📏 파일 크기: {file_size_mb:.2f} MB\n")

    # pandas chunksize로 스트리밍 읽기
    chunk_size = 1000
    total_inserted = 0
    total_skipped = 0

    print(f"💾 데이터 적재 중... (배치 크기: {BATCH_SIZE})")
    print(f"🧠 예상 메모리 사용: 약 20-30 MB (전체 파일 로드 안함)\n")

    try:
        # CSV를 청크 단위로 읽기 (메모리 절약)
        for chunk_idx, df_chunk in enumerate(pd.read_csv(CSV_FILE, chunksize=chunk_size, index_col=0)):
            batch_data = []

            for _, row in df_chunk.iterrows():
                # 출원번호 검증
                app_number = row.get('출원번호')
                if pd.isna(app_number) or str(app_number).strip() == '':
                    total_skipped += 1
                    continue

                # 데이터 준비
                batch_data.append((
                    str(row.get('발명의명칭', '')) if pd.notna(row.get('발명의명칭')) else '',
                    str(row.get('발명의명칭(영문)', '')) if pd.notna(row.get('발명의명칭(영문)')) else None,
                    str(app_number).strip(),
                    str(row.get('출원일자', '')) if pd.notna(row.get('출원일자')) else None,
                    str(row.get('출원인', '')) if pd.notna(row.get('출원인')) else None,
                    str(row.get('등록번호', '')) if pd.notna(row.get('등록번호')) else None,
                    str(row.get('등록일자', '')) if pd.notna(row.get('등록일자')) else None,
                    str(row.get('IPC분류', '')) if pd.notna(row.get('IPC분류')) else None,
                    str(row.get('CPC분류', '')) if pd.notna(row.get('CPC분류')) else None,
                    str(row.get('요약', '')) if pd.notna(row.get('요약')) else None,
                    str(row.get('청구항', '')) if pd.notna(row.get('청구항')) else None,
                    str(row.get('법적상태', '')) if pd.notna(row.get('법적상태')) else None,
                ))

            # 배치 삽입
            if batch_data:
                insert_query = """
                    INSERT INTO patents (
                        title, title_en, application_number, application_date,
                        applicant, registration_number, registration_date,
                        ipc_code, cpc_code, abstract, claims, legal_status,
                        created_at, updated_at
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                        NOW(), NOW()
                    )
                    ON CONFLICT (application_number) DO NOTHING
                """

                execute_batch(cur, insert_query, batch_data, page_size=BATCH_SIZE)
                conn.commit()

                total_inserted += len(batch_data)
                print(f"  ✓ {total_inserted:,}건 처리 완료 (청크 {chunk_idx + 1})")

        print(f"\n{'='*60}")
        print(f"  적재 완료!")
        print(f"{'='*60}")
        print(f"✅ 처리: {total_inserted:,}건")
        print(f"⚠️  건너뜀: {total_skipped:,}건")

        # 최종 확인
        cur.execute("SELECT COUNT(*) FROM patents")
        final_count = cur.fetchone()[0]
        print(f"📊 총 데이터: {final_count:,}건\n")

        # 법적상태별 통계
        cur.execute("""
            SELECT legal_status, COUNT(*)
            FROM patents
            WHERE legal_status IS NOT NULL AND legal_status != ''
            GROUP BY legal_status
            ORDER BY COUNT(*) DESC
            LIMIT 10
        """)

        print("📋 법적상태별 통계 (상위 10개):")
        for status, count in cur.fetchall():
            print(f"  {status}: {count:,}건")

    except Exception as e:
        conn.rollback()
        print(f"\n❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()
    finally:
        cur.close()
        conn.close()
        print("\n🔌 RDS 연결 종료")


if __name__ == '__main__':
    load_patents_streaming()
