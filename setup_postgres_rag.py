#!/usr/bin/env python3
"""
PostgreSQL pgvector를 사용한 RAG 시스템 설정 스크립트
corpus.csv 데이터를 PostgreSQL에 임포트하고 벡터 인덱스 생성
"""

import os
import sys
import django
import pandas as pd
import numpy as np
import requests
from tqdm import tqdm

# Django 설정
sys.path.append('/home/ubuntu/SKN15-FINAL-3TEAM/patent_backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.db import connection
from patents.models import PatentRAGDocument

# 설정
CORPUS_PATH = "/home/ubuntu/rag_data/corpus.csv"
MODEL_SERVER_URL = os.getenv('MODEL_SERVER_URL', 'http://localhost:8001')
BATCH_SIZE = 100  # 100개씩 배치 처리


def check_pgvector_extension():
    """pgvector 확장 설치 확인"""
    print("\n=== 1. pgvector 확장 확인 ===")
    with connection.cursor() as cursor:
        cursor.execute("SELECT * FROM pg_extension WHERE extname = 'vector';")
        result = cursor.fetchone()
        if result:
            print("✅ pgvector 확장이 설치되어 있습니다.")
            return True
        else:
            print("❌ pgvector 확장이 없습니다. 설치를 시도합니다...")
            try:
                cursor.execute("CREATE EXTENSION IF NOT EXISTS vector;")
                print("✅ pgvector 확장 설치 완료")
                return True
            except Exception as e:
                print(f"❌ pgvector 설치 실패: {e}")
                print("PostgreSQL 서버에 pgvector가 설치되어 있는지 확인하세요.")
                return False


def check_table():
    """patent_rag_documents 테이블 확인"""
    print("\n=== 2. 테이블 확인 ===")
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT COUNT(*) FROM information_schema.tables
            WHERE table_name = 'patent_rag_documents';
        """)
        exists = cursor.fetchone()[0] > 0

        if exists:
            cursor.execute("SELECT COUNT(*) FROM patent_rag_documents;")
            count = cursor.fetchone()[0]
            print(f"✅ patent_rag_documents 테이블이 존재합니다. (레코드 수: {count}개)")
            return count
        else:
            print("❌ patent_rag_documents 테이블이 없습니다.")
            print("Django 마이그레이션을 먼저 실행해야 합니다:")
            print("  cd /home/ubuntu/SKN15-FINAL-3TEAM/patent_backend")
            print("  source /home/ubuntu/venv/bin/activate")
            print("  python manage.py makemigrations")
            print("  python manage.py migrate")
            return 0


def load_corpus():
    """corpus.csv 로드"""
    print(f"\n=== 3. corpus.csv 로드 ===")
    if not os.path.exists(CORPUS_PATH):
        print(f"❌ corpus.csv 파일이 없습니다: {CORPUS_PATH}")
        return None

    df = pd.read_csv(CORPUS_PATH)
    print(f"✅ corpus.csv 로드 완료: {len(df)}개 문서")
    print(f"컬럼: {list(df.columns)}")
    return df


def get_embedding(text: str, max_retries=3):
    """Runpod 모델 서버로 임베딩 생성"""
    for attempt in range(max_retries):
        try:
            response = requests.post(
                f"{MODEL_SERVER_URL}/embed",
                json={"text": text[:2000], "normalize": True},  # 2000자로 제한
                timeout=30
            )
            response.raise_for_status()
            return response.json()['embedding']
        except Exception as e:
            if attempt < max_retries - 1:
                print(f"  재시도 {attempt + 1}/{max_retries}: {e}")
                continue
            else:
                raise Exception(f"임베딩 생성 실패: {e}")


def import_data(df):
    """corpus 데이터를 PostgreSQL에 임포트"""
    print(f"\n=== 4. 데이터 임포트 ===")

    # 컬럼 매핑
    title_col = None
    for cand in ["title_ko", "title", "title_en"]:
        if cand in df.columns:
            title_col = cand
            break

    text_col = None
    for cand in ["full_text", "text", "body", "contents"]:
        if cand in df.columns:
            text_col = cand
            break

    if not text_col:
        print("❌ 텍스트 컬럼을 찾을 수 없습니다.")
        return False

    print(f"사용할 컬럼: doc_id, {title_col or '(title 없음)'}, {text_col}")

    # 기존 데이터 삭제 여부 확인
    with connection.cursor() as cursor:
        cursor.execute("SELECT COUNT(*) FROM patent_rag_documents;")
        existing_count = cursor.fetchone()[0]

        if existing_count > 0:
            print(f"\n⚠️  기존 데이터 {existing_count}개가 있습니다.")
            response = input("기존 데이터를 삭제하고 새로 임포트하시겠습니까? (y/N): ")
            if response.lower() != 'y':
                print("임포트를 취소합니다.")
                return False

            cursor.execute("TRUNCATE TABLE patent_rag_documents;")
            print("✅ 기존 데이터 삭제 완료")

    # 배치 처리로 데이터 임포트
    total_rows = len(df)
    success_count = 0
    error_count = 0

    print(f"\n임포트 시작: {total_rows}개 문서 (배치 크기: {BATCH_SIZE})")

    for i in tqdm(range(0, total_rows, BATCH_SIZE), desc="임포트 진행"):
        batch = df.iloc[i:i+BATCH_SIZE]

        for idx, row in batch.iterrows():
            try:
                doc_id = str(row['doc_id'])
                title_ko = str(row[title_col]) if title_col and pd.notna(row[title_col]) else ""
                text = str(row[text_col]) if pd.notna(row[text_col]) else ""

                if not text:
                    continue

                # 임베딩 생성
                embedding = get_embedding(text)

                # DB 저장 (raw SQL로 직접 삽입)
                with connection.cursor() as cursor:
                    cursor.execute("""
                        INSERT INTO patent_rag_documents
                        (doc_id, application_number, title_ko, title_en, ipc, text, source_ids, embedding)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s::vector)
                    """, [
                        doc_id,
                        doc_id,  # application_number = doc_id
                        title_ko,
                        "",  # title_en
                        "",  # ipc
                        text[:5000],  # 5000자로 제한
                        [],  # source_ids
                        embedding
                    ])

                success_count += 1

            except Exception as e:
                error_count += 1
                print(f"\n❌ 오류 (doc_id: {doc_id}): {e}")
                if error_count > 10:
                    print("오류가 너무 많습니다. 중단합니다.")
                    return False

    print(f"\n✅ 임포트 완료: 성공 {success_count}개, 실패 {error_count}개")
    return True


def create_index():
    """벡터 검색 성능 최적화를 위한 인덱스 생성"""
    print("\n=== 5. 벡터 인덱스 생성 ===")

    with connection.cursor() as cursor:
        # 기존 인덱스 확인
        cursor.execute("""
            SELECT indexname FROM pg_indexes
            WHERE tablename = 'patent_rag_documents'
            AND indexname LIKE '%embedding%';
        """)
        existing = cursor.fetchall()

        if existing:
            print(f"✅ 벡터 인덱스가 이미 존재합니다: {existing[0][0]}")
            return True

        print("벡터 인덱스 생성 중... (수 분 소요될 수 있습니다)")

        try:
            # IVFFlat 인덱스 생성 (빠른 근사 검색)
            cursor.execute("""
                CREATE INDEX patent_rag_embedding_idx
                ON patent_rag_documents
                USING ivfflat (embedding vector_l2_ops)
                WITH (lists = 100);
            """)
            print("✅ IVFFlat 인덱스 생성 완료")
            return True
        except Exception as e:
            print(f"⚠️  인덱스 생성 실패 (검색은 가능하지만 느릴 수 있음): {e}")
            return False


def test_search():
    """RAG 검색 테스트"""
    print("\n=== 6. RAG 검색 테스트 ===")

    test_query = "반도체 칩 스택 구조"
    print(f"테스트 쿼리: '{test_query}'")

    try:
        # 임베딩 생성
        query_embedding = get_embedding(test_query)

        # 벡터 검색
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT
                    doc_id,
                    title_ko,
                    LEFT(text, 200) as text_preview,
                    (embedding <=> %s::vector) AS distance
                FROM patent_rag_documents
                ORDER BY distance
                LIMIT 5
            """, [query_embedding])

            results = cursor.fetchall()

            print(f"\n검색 결과 {len(results)}개:")
            for i, (doc_id, title, text, dist) in enumerate(results, 1):
                print(f"\n{i}. doc_id: {doc_id}")
                print(f"   title: {title[:50]}...")
                print(f"   distance: {dist:.4f}")
                print(f"   text: {text[:100]}...")

        print("\n✅ RAG 검색 테스트 성공!")
        return True

    except Exception as e:
        print(f"❌ 검색 테스트 실패: {e}")
        return False


def main():
    """메인 실행 함수"""
    print("=" * 60)
    print("PostgreSQL pgvector RAG 시스템 설정")
    print("=" * 60)

    # 1. pgvector 확장 확인
    if not check_pgvector_extension():
        return

    # 2. 테이블 확인
    existing_count = check_table()
    if existing_count < 0:  # 테이블 없음
        return

    # 3. corpus.csv 로드
    df = load_corpus()
    if df is None:
        return

    # 4. 데이터 임포트 (선택적)
    if existing_count == 0:
        print("\n테이블이 비어있습니다. 데이터를 임포트해야 합니다.")
        if not import_data(df):
            return
    else:
        response = input(f"\n기존 데이터 {existing_count}개가 있습니다. 재임포트하시겠습니까? (y/N): ")
        if response.lower() == 'y':
            if not import_data(df):
                return

    # 5. 인덱스 생성
    create_index()

    # 6. 검색 테스트
    test_search()

    print("\n" + "=" * 60)
    print("✅ PostgreSQL RAG 시스템 설정 완료!")
    print("=" * 60)
    print("\n다음 명령으로 백엔드 서버를 재시작하세요:")
    print("  sudo systemctl restart gunicorn")


if __name__ == "__main__":
    main()
