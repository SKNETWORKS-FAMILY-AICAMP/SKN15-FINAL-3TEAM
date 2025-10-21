import re
import pandas as pd
from pathlib import Path
import json

# ===== 경로 설정 =====
SRC = Path("preprocessed/patent_text_tables_clean_final.csv")  # 네 최신 통합 CSV
OUTDIR = Path("dataset")
OUTDIR.mkdir(parents=True, exist_ok=True)

TXT_OUT = OUTDIR / "text_only.txt"
JSONL_OUT = OUTDIR / "text_only.jsonl"

CSV_MIN = Path("preprocessed/patent_text_only.csv")  # 최소 컬럼 버전 저장

# ===== 유틸: 안전한 텍스트 선택 =====
def pick_text_column(df: pd.DataFrame) -> pd.Series:
    """
    text_cleaned -> text -> tables_cleaned -> tables_raw 순으로 사용.
    (없으면 빈 문자열)
    """
    for c in ["text_cleaned", "text", "tables_cleaned", "tables_raw"]:
        if c in df.columns:
            return df[c].fillna("").astype(str)
    return pd.Series([""] * len(df), index=df.index)

# ===== ‘자’ 제거용(날짜 뒤) =====
def strip_ja_after_dates(s: str) -> str:
    # YYYY.MM.DD. 자  -> YYYY.MM.DD.
    s = re.sub(r"(\d{4}\.\d{1,2}\.\d{1,2}\.)\s*자\b", r"\1", s)
    # YYYY.MM. 자 -> YYYY.MM.
    s = re.sub(r"(\d{4}\.\d{1,2}\.)\s*자\b", r"\1", s)
    return s

# ===== 본문 정리 함수 =====
def clean_text(s: str) -> str:
    if not s:
        return s

    # 1) CR/LF 정리 & 이중따옴표 제거
    s = s.replace("\r", "")
    s = s.replace("“", '"').replace("”", '"')
    s = s.replace("‘", "'").replace("’", "'")

    # 2) 날짜 뒤 '자' 제거
    s = strip_ja_after_dates(s)

    # 3) 명백한 라벨/머릿말/조각 제거 (라인 단위)
    #    - 발송번호/발송일자 라벨
    #    - << 안내 >>, 거절결정 불복심판 안내, 문의/콜센터/담당심사관/전화
    #    - 페이지 마커, TABLE_BREAK, 숫자표 파편, - - - 줄, 제출기일/수신 같은 머리글
    BAD_LINE_RX = re.compile(
        r"""(?x)
        ^
        (
          \s*발송번호\s*:.* |
          \s*발송일자\s*:.* |
          \s*<<\s*안내\s*>>\s* |
          .*거절결정\s*불복심판\s*안내.* |
          .*문의사항.* | .*문의\b.* | .*콜센터.* | .*담당심사관.* |
          .*☎.* | \s*\d{2,4}[-)\s]*\d{3,4}[-\s]*\d{3,4}\s* |
          \s*---TABLE_BREAK---\s* |
          \s*-\s*\d+\s*-\s* |
          \s*(?:\d+\s*,\s*){2,}\d+\s* |   # 0,1,2,3 같은 테이블 잔재
          \s*-+\s*-\s*-+\s* |             # - - - 형태
          ^\s*제출기일\s*$ |
          ^\s*수신\s*:?\s*$ |
          ^\s*특\s*허\s*청\s*$ | ^\s*특허거절결정서\s*$ |
          ^\s*심사관\s*$ | ^\s*심사\d*\s*팀?\s*$ |
          ^\s*기계금속.*심사.*$          # 심사 본부/국/팀 라인들
        )
        $
        """,
        flags=re.IGNORECASE | re.MULTILINE,
    )

    # 4) 문단 단위로 한번 걸러내기
    lines = s.split("\n")
    kept = []
    for line in lines:
        L = line.strip()

        # 공백 라인
        if not L:
            continue

        # 나쁜 라인 패턴이면 제거
        if BAD_LINE_RX.match(L):
            continue

        # 너무 짧은 표제/조각(한글 1~2글자만 있는 줄) 제거 (ex: "출", "원" 같은 분리된 칸)
        if re.fullmatch(r"[가-힣]{1,2}", L):
            continue

        kept.append(L)

    s = "\n".join(kept)

    # 5) 본문에 남은 고정문구 삭제 (문장 내부 패턴)
    #    - 불복안내 블록, 콜센터/문의/담당심사관 등 통짜 문구
    BAD_CHUNK_PATTERNS = [
        r"<<\s*안내\s*>>",
        r"거절결정\s*불복심판\s*안내",
        r"문의사항|문의\b|콜센터|담당심사관|☎",
    ]
    for pat in BAD_CHUNK_PATTERNS:
        s = re.sub(pat, " ", s, flags=re.IGNORECASE | re.DOTALL)

    # 6) 자주 나오는 결정문 고정 문장 제거(띄어쓰기 들쭉날쭉/개행 감안)
    #    “거절이유를 번복할 만한 사항을 발견할 수 없으므로 … 거절결정합니다. 끝.”
    s = re.sub(
        r"""(?sx)
        거\s*절\s*이\s*유\s*를\s*번\s*복\s*할\s*만\s*한\s*사\s*항\s*을\s*발\s*견\s*할\s*수\s*없\s*으\s*므\s*로
        .*?
        (거\s*절\s*결\s*정\s*합\s*니\s*다\s*\.\s*끝\s*\.)?
        """,
        " ",
        s,
    )

    # 7) 불필요한 따옴표 정리 & 다중 공백 축소
    s = s.replace('""', '"')
    s = s.strip()
    s = re.sub(r"[ \t]{2,}", " ", s)
    s = re.sub(r"\n{3,}", "\n\n", s)

    return s.strip()

# ===== 메인 처리 =====
def main():
    if not SRC.exists():
        raise SystemExit(f"입력 파일을 찾을 수 없음: {SRC}")

    df = pd.read_csv(SRC)

    # 최소 컬럼만 남기기: doc_id + 본문 하나
    text_series = pick_text_column(df)
    if "doc_id" in df.columns:
        out_df = pd.DataFrame({"doc_id": df["doc_id"].astype(str), "text_src": text_series})
    else:
        out_df = pd.DataFrame({"doc_id": [f"row_{i}" for i in range(len(df))], "text_src": text_series})

    # 정리 적용
    cleaned = out_df["text_src"].map(clean_text)

    # 빈 라인/매우 짧은 샘플 제거
    MIN_CHARS = 40
    mask_len = cleaned.str.replace(r"\s+", "", regex=True).str.len() >= MIN_CHARS
    removed_short = int((~mask_len).sum())
    out_df["text_final"] = cleaned.where(mask_len, "")

    # 완전 빈 값 제거
    before = len(out_df)
    out_df = out_df[out_df["text_final"].str.strip().astype(bool)].copy()
    removed_empty = before - len(out_df)

    # 중복 제거
    before2 = len(out_df)
    out_df = out_df.drop_duplicates(subset=["text_final"]).reset_index(drop=True)
    removed_dup = before2 - len(out_df)

    # ===== 저장: 최소 CSV (doc_id, text_final) =====
    out_df[["doc_id", "text_final"]].to_csv(CSV_MIN, index=False, encoding="utf-8")
    print(f"[CSV] {CSV_MIN}  (rows={len(out_df)}, 짧아서 제거={removed_short}, 빈값={removed_empty}, 중복={removed_dup})")

    # ===== 저장: TXT (한 줄 한 문서) =====
    with open(TXT_OUT, "w", encoding="utf-8") as ftxt:
        for t in out_df["text_final"]:
            ftxt.write(t.replace("\r", "").strip() + "\n")
    print(f"[TXT] {TXT_OUT}")

    # ===== 저장: JSONL (한 줄: {\"text\": ...}) =====
    with open(JSONL_OUT, "w", encoding="utf-8") as fj:
        for t in out_df["text_final"]:
            fj.write(json.dumps({"text": t}, ensure_ascii=False) + "\n")

    # ===== 잔여 금지패턴 스팟체크(있으면 예시 5개 출력) =====
    CHECKS = {
        "date_자": re.compile(r"(\d{4}\.\d{1,2}\.\d{1,2}\.)\s*자\b"),
        "dateYm_자": re.compile(r"(\d{4}\.\d{1,2}\.)\s*자\b"),
        "불복안내": re.compile(r"거절결정\s*불복심판\s*안내"),
        "안내블럭": re.compile(r"<<\s*안내\s*>>"),
        "콜센터/문의": re.compile(r"콜센터|문의사항|문의\b"),
        "담당심사관/전화": re.compile(r"담당심사관|☎|\d{2,4}[-)\s]*\d{3,4}[-\s]*\d{3,4}"),
        "페이지마커": re.compile(r"-\s*\d+\s*-"),
        "라벨": re.compile(r"발송번호\s*:|발송일자\s*:"),
        "TABLE_BREAK": re.compile(r"---TABLE_BREAK---"),
    }
    print("\n[잔여 패턴 점검]")
    texts = out_df["text_final"]
    any_hit = False
    for name, rx in CHECKS.items():
        mask = texts.str.contains(rx)
        cnt = int(mask.sum())
        if cnt > 0:
            any_hit = True
            print(f"  ❗ {name}: {cnt}건 (예시 5개)")
            for ex in texts[mask].head(5):
                print("    -", ex.replace("\n", " ")[:120])
    if not any_hit:
        print("  ✅ 문제 패턴 없음")

if __name__ == "__main__":
    main()


import pandas as pd
import re

df = pd.read_csv("patent_text_SAFE.csv")  # 네 현재 파일명

# .ipynb
# 1) 텍스트 컬럼 자동 선택
text_col = None
for c in ["text_final", "text_cleaned", "text"]:
    if c in df.columns:
        text_col = c
        break
if text_col is None:
    raise ValueError("텍스트 컬럼을 찾을 수 없어요. (text_final / text_cleaned / text 중 하나 필요)")

# 2) 최종 3컬럼으로 슬림
keep = ["doc_id", text_col, "Application Number"]
df_slim = df[keep].rename(columns={text_col: "text"})

# (선택) doc_id의 .pdf 제거
# df_slim["doc_id"] = df_slim["doc_id"].astype(str).str.replace(".pdf", "", regex=False)

# (선택) 텍스트 안의 리터럴/실제 줄바꿈 & 탭 제거
df_slim["text"] = (
    df_slim["text"].astype(str)
        .str.replace(r"\\[nrt]", " ", regex=True)   # literal \n \r \t
        .str.replace(r"[\n\r\t]+", " ", regex=True) # real newlines/tabs
        .str.replace(r"\s{2,}", " ", regex=True)    # collapse spaces
        .str.strip()
)

# 3) 저장
df_slim.to_csv("dataset_3cols.csv", index=False, encoding="utf-8-sig")
print("Saved: dataset_3cols.csv")
