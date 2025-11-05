"""
대용량 CSV를 작은 청크로 분할
서버 용량이 작을 때 유용
"""
import pandas as pd
from pathlib import Path

# 입력 CSV
INPUT_CSV = '/home/juhyeong/workspace/mergerd_total_not_null (1).csv'

# 출력 디렉토리
OUTPUT_DIR = Path('/home/juhyeong/workspace/final_project/SKN15-FINAL-3TEAM/data/patent_chunks')
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# 청크당 행 수 (5000건씩)
CHUNK_SIZE = 5000

def split_csv():
    """CSV를 여러 개의 작은 파일로 분할"""

    print(f"\n{'='*60}")
    print(f"  CSV 파일 분할")
    print(f"{'='*60}\n")

    print(f"📂 입력: {INPUT_CSV}")
    print(f"📁 출력: {OUTPUT_DIR}")
    print(f"📊 청크 크기: {CHUNK_SIZE:,}건\n")

    chunk_num = 0

    for chunk in pd.read_csv(INPUT_CSV, chunksize=CHUNK_SIZE, index_col=0):
        chunk_num += 1
        output_file = OUTPUT_DIR / f'patents_chunk_{chunk_num:03d}.csv'

        chunk.to_csv(output_file, encoding='utf-8')

        print(f"  ✓ {output_file.name} 생성 ({len(chunk):,}건)")

    print(f"\n✅ 완료: {chunk_num}개 파일 생성")
    print(f"📁 경로: {OUTPUT_DIR}\n")

    # 각 청크 파일을 서버에 업로드하고 순차 적재하는 스크립트 생성
    load_script = OUTPUT_DIR / 'load_all_chunks.sh'

    with open(load_script, 'w') as f:
        f.write("#!/bin/bash\n")
        f.write("# 모든 청크 파일을 순차적으로 적재\n\n")

        for i in range(1, chunk_num + 1):
            filename = f'patents_chunk_{i:03d}.csv'
            f.write(f"echo '청크 {i}/{chunk_num} 적재 중...'\n")
            f.write(f"python manage.py load_patents --file /path/to/{filename}\n")
            f.write(f"echo '청크 {i} 완료'\n\n")

        f.write("echo '모든 청크 적재 완료!'\n")

    print(f"📜 적재 스크립트 생성: {load_script}")
    print("   서버에서 실행: bash load_all_chunks.sh\n")


if __name__ == '__main__':
    split_csv()
