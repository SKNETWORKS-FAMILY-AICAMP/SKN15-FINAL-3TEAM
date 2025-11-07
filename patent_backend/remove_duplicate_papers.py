"""
논문 중복 데이터 제거 스크립트
동일한 제목의 논문 중 ID가 가장 작은 것만 남기고 나머지 삭제
"""
import psycopg2
import os
import django

# Django 설정
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

# RDS 연결 정보
DB_CONFIG = {
    'dbname': 'patent_db',
    'user': 'postgres',
    'password': '3-bengio123',
    'host': 'my-patent-db.c9iw88yiic4o.ap-northeast-2.rds.amazonaws.com',
    'port': '5432'
}


def remove_duplicate_papers():
    """중복 논문 제거"""

    print(f"\n{'='*60}")
    print(f"  논문 중복 데이터 제거")
    print(f"{'='*60}\n")

    try:
        # RDS 연결
        print("📡 RDS 연결 중...")
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        print("✅ RDS 연결 성공\n")

        # 중복 확인
        print("🔍 중복 데이터 확인 중...")
        cur.execute("""
            SELECT title_kr, COUNT(*) as count
            FROM papers
            GROUP BY title_kr
            HAVING COUNT(*) > 1
        """)
        duplicates = cur.fetchall()
        print(f"  중복된 제목: {len(duplicates)}개\n")

        if len(duplicates) == 0:
            print("✅ 중복 데이터가 없습니다.")
            return

        # 중복 제거 쿼리 실행
        print("🗑️  중복 데이터 제거 중...")

        # ID가 가장 작은 것만 남기고 나머지 삭제
        cur.execute("""
            DELETE FROM papers
            WHERE id IN (
                SELECT id
                FROM (
                    SELECT id,
                           ROW_NUMBER() OVER (PARTITION BY title_kr ORDER BY id) as rnum
                    FROM papers
                ) t
                WHERE rnum > 1
            )
        """)

        deleted_count = cur.rowcount
        conn.commit()

        print(f"  ✓ {deleted_count}개의 중복 데이터 삭제 완료\n")

        # 최종 확인
        print("📊 최종 데이터 확인...")
        cur.execute("SELECT COUNT(*) FROM papers")
        total_count = cur.fetchone()[0]
        print(f"  총 논문 수: {total_count:,}건")

        # 중복 재확인
        cur.execute("""
            SELECT COUNT(*)
            FROM (
                SELECT title_kr, COUNT(*) as count
                FROM papers
                GROUP BY title_kr
                HAVING COUNT(*) > 1
            ) t
        """)
        remaining_duplicates = cur.fetchone()[0]

        if remaining_duplicates == 0:
            print(f"  ✅ 모든 중복이 제거되었습니다!\n")
        else:
            print(f"  ⚠️  아직 {remaining_duplicates}개의 중복이 남아있습니다.\n")

        print(f"{'='*60}\n")

        cur.close()
        conn.close()
        print("✅ 중복 제거 완료")

    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    # 사용자 확인
    print("\n⚠️  경고: 이 스크립트는 RDS의 중복 논문 데이터를 삭제합니다.")
    confirm = input("계속하시겠습니까? (yes/no): ")

    if confirm.lower() == 'yes':
        remove_duplicate_papers()
    else:
        print("작업이 취소되었습니다.")
