"""
FAISS 인덱스를 PostgreSQL pgvector로 마이그레이션하는 스크립트
"""
import os
import sys
import django
import numpy as np
import pandas as pd
import faiss
from tqdm import tqdm

# Django 설정
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from patents.models import PatentRAGDocument

# RAG 파일 경로
RAG_DIR = '/home/juhyeong/workspace/final_project/rag_extracted'
CORPUS_FILE = os.path.join(RAG_DIR, 'corpus.csv')
INDEX_FILE = os.path.join(RAG_DIR, 'index_ip_bgem3_v2.faiss')
DOC_IDS_FILE = os.path.join(RAG_DIR, 'doc_ids_bgem3_v2.npy')

def load_faiss_index():
    """FAISS 인덱스와 문서 ID 로드"""
    print("📂 FAISS 인덱스 로딩 중...")
    index = faiss.read_index(INDEX_FILE)
    doc_ids = np.load(DOC_IDS_FILE, allow_pickle=True)
    print(f"✅ 인덱스 로드 완료: {index.ntotal}개 벡터")
    return index, doc_ids

def load_corpus():
    """코퍼스 CSV 로드"""
    print("📂 코퍼스 로딩 중...")
    corpus = pd.read_csv(CORPUS_FILE)
    print(f"✅ 코퍼스 로드 완료: {len(corpus)}개 문서")
    return corpus

def extract_vectors_from_faiss(index):
    """FAISS 인덱스에서 모든 벡터 추출"""
    print("🔄 FAISS 인덱스에서 벡터 추출 중...")

    # IndexFlatIP는 내부적으로 벡터를 평탄하게 저장
    # reconstruct_n을 사용하여 모든 벡터 추출
    n_vectors = index.ntotal
    vectors = np.zeros((n_vectors, index.d), dtype=np.float32)

    for i in tqdm(range(n_vectors), desc="벡터 추출"):
        vectors[i] = index.reconstruct(i)

    print(f"✅ {n_vectors}개 벡터 추출 완료 (차원: {index.d})")
    return vectors

def migrate_to_postgres(corpus, doc_ids, vectors):
    """PostgreSQL로 마이그레이션"""
    print("🔄 PostgreSQL로 마이그레이션 시작...")

    # 기존 데이터 삭제
    print("🗑️  기존 데이터 삭제 중...")
    PatentRAGDocument.objects.all().delete()

    # 배치 사이즈
    BATCH_SIZE = 1000
    documents = []

    for idx, doc_id in enumerate(tqdm(doc_ids, desc="문서 처리")):
        # 코퍼스에서 해당 문서 찾기
        doc_row = corpus[corpus['doc_id'] == doc_id]

        if doc_row.empty:
            print(f"⚠️  경고: doc_id {doc_id}를 코퍼스에서 찾을 수 없습니다.")
            continue

        doc_data = doc_row.iloc[0]

        # PatentRAGDocument 객체 생성
        document = PatentRAGDocument(
            doc_id=str(doc_id),
            application_number=str(doc_data['application_number_raw']),
            title_ko=doc_data['title_ko'] if pd.notna(doc_data['title_ko']) else '',
            title_en=doc_data['title_en'] if pd.notna(doc_data['title_en']) else '',
            ipc=doc_data['ipc'] if pd.notna(doc_data['ipc']) else '',
            text=doc_data['text'] if pd.notna(doc_data['text']) else '',
            source_ids=doc_data['source_ids'] if pd.notna(doc_data['source_ids']) else '',
            embedding=vectors[idx].tolist()  # 벡터를 리스트로 변환
        )
        documents.append(document)

        # 배치 저장
        if len(documents) >= BATCH_SIZE:
            PatentRAGDocument.objects.bulk_create(documents, ignore_conflicts=True)
            print(f"✅ {len(documents)}개 문서 저장 완료")
            documents = []

    # 남은 문서 저장
    if documents:
        PatentRAGDocument.objects.bulk_create(documents, ignore_conflicts=True)
        print(f"✅ {len(documents)}개 문서 저장 완료")

    print("✅ PostgreSQL 마이그레이션 완료!")

def create_vector_index():
    """벡터 검색용 인덱스 생성"""
    print("🔧 벡터 검색 인덱스 생성 중...")
    from django.db import connection

    with connection.cursor() as cursor:
        # IVFFlat 인덱스 생성 (빠른 근사 검색)
        # lists=100: 100개의 클러스터로 분할
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS patent_rag_documents_embedding_idx
            ON patent_rag_documents
            USING ivfflat (embedding vector_cosine_ops)
            WITH (lists = 100);
        """)
        print("✅ 벡터 인덱스 생성 완료!")

def main():
    """메인 실행 함수"""
    print("=" * 60)
    print("🚀 FAISS → PostgreSQL pgvector 마이그레이션")
    print("=" * 60)

    # 1. FAISS 인덱스 로드
    index, doc_ids = load_faiss_index()

    # 2. 코퍼스 로드
    corpus = load_corpus()

    # 3. FAISS에서 벡터 추출
    vectors = extract_vectors_from_faiss(index)

    # 4. PostgreSQL로 마이그레이션
    migrate_to_postgres(corpus, doc_ids, vectors)

    # 5. 벡터 인덱스 생성
    create_vector_index()

    print("=" * 60)
    print("✅ 마이그레이션 완료!")
    print("=" * 60)

    # 6. 통계 출력
    total_docs = PatentRAGDocument.objects.count()
    print(f"📊 총 문서 수: {total_docs:,}개")

if __name__ == '__main__':
    main()
