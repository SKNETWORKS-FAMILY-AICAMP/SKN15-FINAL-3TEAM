"""
자동으로 N 입력하는 특허 데이터 적재 스크립트
"""
import sys
import subprocess

# load_patents_remote.py 실행하되, 자동으로 입력 제공
process = subprocess.Popen(
    ['python3', 'load_patents_remote.py'],
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,
    text=True,
    bufsize=1
)

# 첫 번째 질문: "계속 진행하시겠습니까?"에 'y' 입력
# 두 번째 질문: "삭제하고 진행할까요?"에 'N' 입력
inputs = "y\nN\n"

print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
print("  특허 데이터 자동 적재 시작")
print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
print()

# 입력 제공 및 실시간 출력
try:
    process.stdin.write(inputs)
    process.stdin.flush()
    process.stdin.close()

    # 실시간 출력
    for line in process.stdout:
        print(line, end='')
        sys.stdout.flush()

    process.wait()

    if process.returncode == 0:
        print()
        print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        print("✅ 적재 완료!")
        print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    else:
        print()
        print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        print(f"⚠️  종료 코드: {process.returncode}")
        print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

except KeyboardInterrupt:
    print("\n\n⚠️  사용자가 중단했습니다.")
    process.terminate()
except Exception as e:
    print(f"\n\n❌ 오류 발생: {e}")
    process.terminate()
