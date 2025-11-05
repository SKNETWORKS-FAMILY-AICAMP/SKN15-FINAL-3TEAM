"""
거절결정서 데이터를 RDS에 적재
"""
import pandas as pd
import psycopg2
from psycopg2.extras import execute_batch

# RDS 연결 정보
DB_CONFIG = {
    'dbname': 'patent_db',
    'user': 'postgres',
    'password': '3-bengio123',
    'host': 'my-patent-db.c9iw88yiic4o.ap-northeast-2.rds.amazonaws.com',
    'port': '5432'
}

# CSV 파일 경로
CSV_FILE = '/home/juhyeong/workspace/final_project/SKN15-FINAL-3TEAM/data/cleaned_reject_documents.csv'

# 배치 크기
BATCH_SIZE = 500

def load_reject_documents():
    """
    거절결정서 데이터 적재
    """

    print(f"\n{'='*60}")
    print(f"  거절결정서 데이터 RDS 적재")
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
    cur.execute("SELECT COUNT(*) FROM reject_documents")
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
    print(f"🧠 메모리 효율적 스트리밍 방식\n")

    try:
        # CSV를 청크 단위로 읽기
        for chunk_idx, df_chunk in enumerate(pd.read_csv(CSV_FILE, chunksize=chunk_size)):
            batch_data = []

            for _, row in df_chunk.iterrows():
                # doc_id와 출원번호 검증
                doc_id = row.get('doc_id')
                app_number = row.get('출원번호')

                if pd.isna(doc_id) or str(doc_id).strip() == '':
                    total_skipped += 1
                    continue

                if pd.isna(app_number) or str(app_number).strip() == '':
                    total_skipped += 1
                    continue

                # 데이터 준비
                batch_data.append((
                    str(doc_id).strip(),
                    str(row.get('발송번호', '')) if pd.notna(row.get('발송번호')) else None,
                    str(row.get('발송일자', '')) if pd.notna(row.get('발송일자')) else None,
                    str(row.get('출원인코드', '')) if pd.notna(row.get('출원인코드')) else None,
                    str(row.get('출원인', '')) if pd.notna(row.get('출원인')) else None,
                    str(row.get('대리인', '')) if pd.notna(row.get('대리인')) else None,
                    str(app_number).strip(),
                    str(row.get('발명의_명칭', '')) if pd.notna(row.get('발명의_명칭')) else None,
                    str(row.get('심사기관', '')) if pd.notna(row.get('심사기관')) else None,
                    str(row.get('심사관', '')) if pd.notna(row.get('심사관')) else None,
                    str(row.get('tables_raw', '')) if pd.notna(row.get('tables_raw')) else None,
                    str(row.get('processed_text', '')) if pd.notna(row.get('processed_text')) else None,
                ))

            # 배치 삽입
            if batch_data:
                insert_query = """
                    INSERT INTO reject_documents (
                        doc_id, send_number, send_date, applicant_code, applicant, agent,
                        application_number, invention_name, examination_office, examiner,
                        tables_raw, processed_text, created_at, updated_at
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW()
                    )
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
        cur.execute("SELECT COUNT(*) FROM reject_documents")
        final_count = cur.fetchone()[0]
        print(f"📊 총 데이터: {final_count:,}건\n")

        # 샘플 데이터 확인
        cur.execute("""
            SELECT application_number, invention_name, examiner
            FROM reject_documents
            LIMIT 3
        """)
        print("📋 샘플 거절결정서:")
        for app_num, inv_name, examiner in cur.fetchall():
            print(f"  - [{app_num}] {inv_name} (심사관: {examiner})")

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
    load_reject_documents()
