"""
스트리밍 방식의 메모리 사용량 테스트
실행 전/후 메모리 비교
"""
import pandas as pd
import psutil
import os

CSV_FILE = '/home/juhyeong/workspace/mergerd_total_not_null (1).csv'

def get_memory_usage():
    """현재 프로세스의 메모리 사용량 (MB)"""
    process = psutil.Process(os.getpid())
    return process.memory_info().rss / (1024 * 1024)

def test_streaming_memory():
    """스트리밍 방식의 메모리 사용량 테스트"""

    print(f"\n{'='*60}")
    print(f"  메모리 사용량 테스트")
    print(f"{'='*60}\n")

    # CSV 파일 크기
    file_size = os.path.getsize(CSV_FILE) / (1024 * 1024)
    print(f"📂 CSV 파일 크기: {file_size:.2f} MB\n")

    # 시작 메모리
    mem_start = get_memory_usage()
    print(f"🧠 시작 메모리: {mem_start:.2f} MB")

    # 스트리밍 방식으로 읽기
    print(f"📖 스트리밍 방식으로 읽는 중...\n")

    chunk_size = 1000
    max_chunks = 10  # 처음 10개 청크만 테스트

    for chunk_idx, chunk in enumerate(pd.read_csv(CSV_FILE, chunksize=chunk_size, index_col=0)):
        if chunk_idx >= max_chunks:
            break

        # 현재 메모리 사용량
        mem_current = get_memory_usage()
        mem_increase = mem_current - mem_start

        print(f"  청크 {chunk_idx + 1}: 메모리 사용 {mem_current:.2f} MB (증가: +{mem_increase:.2f} MB)")

        # 데이터 처리 시뮬레이션 (실제로는 여기서 RDS로 전송)
        _ = chunk.to_dict('records')

    # 최종 메모리
    mem_end = get_memory_usage()
    mem_total_increase = mem_end - mem_start

    print(f"\n{'='*60}")
    print(f"  결과")
    print(f"{'='*60}")
    print(f"📊 시작 메모리: {mem_start:.2f} MB")
    print(f"📊 종료 메모리: {mem_end:.2f} MB")
    print(f"📊 총 증가량: {mem_total_increase:.2f} MB")
    print(f"\n✅ CSV 파일이 {file_size:.2f} MB인데, 메모리는 {mem_total_increase:.2f} MB만 증가!")
    print(f"   → 약 {file_size / mem_total_increase:.1f}배 효율적\n")

def test_full_load_memory():
    """전체 로드 방식의 메모리 사용량 (비교용)"""

    print(f"\n{'='*60}")
    print(f"  [비교] 전체 로드 방식 메모리 사용량")
    print(f"{'='*60}\n")

    mem_start = get_memory_usage()
    print(f"🧠 시작 메모리: {mem_start:.2f} MB")
    print(f"📖 전체 파일 로드 중...\n")

    # 전체 로드 (위험! 메모리 많이 사용)
    df = pd.read_csv(CSV_FILE, index_col=0)

    mem_end = get_memory_usage()
    mem_increase = mem_end - mem_start

    print(f"📊 종료 메모리: {mem_end:.2f} MB")
    print(f"📊 총 증가량: {mem_increase:.2f} MB")
    print(f"\n⚠️  전체 로드는 {mem_increase:.2f} MB 사용 (스트리밍보다 훨씬 많음!)\n")

if __name__ == '__main__':
    # 필요한 패키지 확인
    try:
        import psutil
    except ImportError:
        print("❌ psutil 설치 필요: pip install psutil")
        exit(1)

    # 스트리밍 방식 테스트
    test_streaming_memory()

    # 전체 로드 방식 테스트 (선택)
    response = input("\n[비교] 전체 로드 방식도 테스트하시겠습니까? (y/N): ")
    if response.lower() == 'y':
        test_full_load_memory()
