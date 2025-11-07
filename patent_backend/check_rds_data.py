"""
RDS 데이터 확인 스크립트
"""
import psycopg2

# RDS 연결 정보
DB_CONFIG = {
    'dbname': 'patent_db',
    'user': 'postgres',
    'password': '3-bengio123',
    'host': 'my-patent-db.c9iw88yiic4o.ap-northeast-2.rds.amazonaws.com',
    'port': '5432'
}

def check_rds_data():
    """RDS 데이터 확인"""

    print(f"\n{'='*60}")
    print(f"  RDS 데이터 확인")
    print(f"{'='*60}\n")

    try:
        # RDS 연결
        print("📡 RDS 연결 중...")
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        print("✅ RDS 연결 성공\n")

        # 1. 전체 테이블 목록
        print("📋 테이블 목록:")
        cur.execute("""
            SELECT tablename
            FROM pg_tables
            WHERE schemaname = 'public'
            ORDER BY tablename;
        """)
        tables = cur.fetchall()
        for table in tables:
            print(f"  - {table[0]}")

        print(f"\n{'='*60}\n")

        # 2. Papers 테이블 통계
        print("📊 Papers 테이블 통계:")

        # 전체 개수
        cur.execute("SELECT COUNT(*) FROM papers;")
        total_count = cur.fetchone()[0]
        print(f"  총 논문 수: {total_count:,}건")

        # published_date가 있는 개수
        cur.execute("SELECT COUNT(*) FROM papers WHERE published_date IS NOT NULL AND published_date != '';")
        with_date = cur.fetchone()[0]
        print(f"  발행일 포함: {with_date:,}건")

        # 테이블 구조
        print(f"\n  컬럼 구조:")
        cur.execute("""
            SELECT column_name, data_type, character_maximum_length, is_nullable
            FROM information_schema.columns
            WHERE table_name = 'papers'
            ORDER BY ordinal_position;
        """)
        columns = cur.fetchall()
        for col in columns:
            col_name, data_type, max_len, nullable = col
            if max_len:
                print(f"    - {col_name}: {data_type}({max_len}) {'NULL' if nullable == 'YES' else 'NOT NULL'}")
            else:
                print(f"    - {col_name}: {data_type} {'NULL' if nullable == 'YES' else 'NOT NULL'}")

        print(f"\n{'='*60}\n")

        # 3. 샘플 데이터 (최신 5건)
        print("📄 최신 논문 샘플 (5건):")
        cur.execute("""
            SELECT id, title_kr, published_date, created_at
            FROM papers
            ORDER BY created_at DESC
            LIMIT 5;
        """)
        samples = cur.fetchall()
        for idx, (paper_id, title, pub_date, created) in enumerate(samples, 1):
            print(f"\n  [{idx}] ID: {paper_id}")
            print(f"      제목: {title[:60]}...")
            print(f"      발행일: {pub_date or 'N/A'}")
            print(f"      생성일: {created}")

        print(f"\n{'='*60}\n")

        # 4. Patents 테이블 통계
        print("📊 Patents 테이블 통계:")
        cur.execute("SELECT COUNT(*) FROM patents;")
        patent_count = cur.fetchone()[0]
        print(f"  총 특허 수: {patent_count:,}건")

        # 5. 기타 테이블 통계
        print(f"\n📊 기타 테이블:")
        for table in ['reject_documents', 'opinion_documents']:
            try:
                cur.execute(f"SELECT COUNT(*) FROM {table};")
                count = cur.fetchone()[0]
                print(f"  {table}: {count:,}건")
            except:
                print(f"  {table}: 테이블 없음")

        print(f"\n{'='*60}\n")

        cur.close()
        conn.close()
        print("✅ 데이터 확인 완료")

    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    check_rds_data()
