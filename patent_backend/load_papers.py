"""
논문 데이터를 RDS에 적재
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
CSV_FILE = '/home/juhyeong/workspace/papers_final_translated.csv'

# 배치 크기
BATCH_SIZE = 100

def load_papers():
    """
    논문 데이터 적재
    """

    print(f"\n{'='*60}")
    print(f"  논문 데이터 RDS 적재")
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
    cur.execute("SELECT COUNT(*) FROM papers")
    existing_count = cur.fetchone()[0]

    print(f"ℹ️  기존 데이터: {existing_count:,}건")
    print(f"ℹ️  기존 데이터 유지하고 새 데이터만 추가합니다.\n")

    # CSV 파일 크기 확인
    import os
    file_size_mb = os.path.getsize(CSV_FILE) / (1024 * 1024)
    print(f"📂 CSV 파일: {CSV_FILE}")
    print(f"📏 파일 크기: {file_size_mb:.2f} MB\n")

    print(f"💾 데이터 적재 중... (배치 크기: {BATCH_SIZE})\n")

    try:
        # CSV 전체 읽기 (작은 파일이라 한 번에 읽어도 됨)
        df = pd.read_csv(CSV_FILE, encoding='utf-8-sig')  # BOM 제거

        print(f"📊 CSV에서 {len(df)}건 로드 완료\n")

        batch_data = []
        total_inserted = 0
        total_skipped = 0

        for _, row in df.iterrows():
            # title_kr 검증 (필수 필드)
            title_kr = row.get('Title_KR')

            if pd.isna(title_kr) or str(title_kr).strip() == '':
                total_skipped += 1
                continue

            # 데이터 준비
            batch_data.append((
                str(row.get('Title_EN', '')) if pd.notna(row.get('Title_EN')) else None,
                str(title_kr).strip(),
                str(row.get('Authors', '')) if pd.notna(row.get('Authors')) else None,
                str(row.get('Abstract_EN', '')) if pd.notna(row.get('Abstract_EN')) else None,
                str(row.get('Abstract_KR', '')) if pd.notna(row.get('Abstract_KR')) else None,
                str(row.get('Abstract_Page_Link', '')) if pd.notna(row.get('Abstract_Page_Link')) else None,
                str(row.get('PDF_Link', '')) if pd.notna(row.get('PDF_Link')) else None,
                str(row.get('source_file', '')) if pd.notna(row.get('source_file')) else None,
            ))

            # 배치 크기마다 삽입
            if len(batch_data) >= BATCH_SIZE:
                insert_query = """
                    INSERT INTO papers (
                        title_en, title_kr, authors, abstract_en, abstract_kr,
                        abstract_page_link, pdf_link, source_file,
                        created_at, updated_at
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW()
                    )
                """

                execute_batch(cur, insert_query, batch_data, page_size=BATCH_SIZE)
                conn.commit()

                total_inserted += len(batch_data)
                print(f"  ✓ {total_inserted:,}건 적재 완료")
                batch_data = []

        # 남은 데이터 삽입
        if batch_data:
            insert_query = """
                INSERT INTO papers (
                    title_en, title_kr, authors, abstract_en, abstract_kr,
                    abstract_page_link, pdf_link, source_file,
                    created_at, updated_at
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW()
                )
            """

            execute_batch(cur, insert_query, batch_data, page_size=BATCH_SIZE)
            conn.commit()

            total_inserted += len(batch_data)
            print(f"  ✓ {total_inserted:,}건 적재 완료")

        print(f"\n{'='*60}")
        print(f"  적재 완료!")
        print(f"{'='*60}")
        print(f"✅ 성공: {total_inserted:,}건")
        print(f"⚠️  건너뜀: {total_skipped:,}건")

        # 최종 확인
        cur.execute("SELECT COUNT(*) FROM papers")
        final_count = cur.fetchone()[0]
        print(f"📊 총 데이터: {final_count:,}건\n")

        # 샘플 데이터 확인
        cur.execute("SELECT title_kr, authors FROM papers LIMIT 3")
        print("📋 샘플 논문:")
        for title, authors in cur.fetchall():
            print(f"  - {title[:50]}... (저자: {authors})")

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
    load_papers()
