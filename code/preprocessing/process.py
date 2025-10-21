# ✅ 설치 (처음 한 번)
# %pip -q install PyPDF2 pdfminer.six pandas

from pathlib import Path
from typing import List, Union
import pandas as pd
import re, unicodedata

# ============================
# 1) PDF → pages.csv (문서별 '마지막 페이지 제외' 저장)
# ============================

def extract_text_per_page(pdf_path: Union[str, Path], skip_last_page: bool = True) -> List[str]:
    """PyPDF2 먼저 시도 → 실패/빈문자면 pdfminer.six로 폴백. 마지막 페이지는 선택적으로 제외."""
    pdf_path = str(pdf_path)
    pages = []
    # 1) PyPDF2
    try:
        from PyPDF2 import PdfReader
        reader = PdfReader(pdf_path)
        for p in reader.pages:
            pages.append(p.extract_text() or "")
        if any(pages):   # 한 페이지만이라도 추출되면 사용
            return pages[:-1] if (skip_last_page and len(pages) > 0) else pages
    except Exception:
        pass
    # 2) pdfminer.six (form-feed로 페이지 분리)
    from pdfminer.high_level import extract_text
    full = extract_text(pdf_path) or ""
    parts = re.split(r"\f+", full)
    parts = [p.strip("\n") for p in parts if p is not None]
    if skip_last_page and len(parts) > 0:
        parts = parts[:-1]
    return parts

def convert_pdf_to_pages_csv(src: Union[str, Path], out_dir: Union[str, Path], skip_last_page: bool = True):
    """단일 PDF → pages.csv (append)"""
    src = Path(src)
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    pages_csv = out_dir / "pages.csv"

    pages = extract_text_per_page(src, skip_last_page=skip_last_page)
    rows = [{"file_name": src.name, "page": i+1, "text": t} for i, t in enumerate(pages)]
    df = pd.DataFrame(rows, columns=["file_name", "page", "text"])

    if pages_csv.exists():
        df.to_csv(pages_csv, index=False, mode="a", header=False, encoding="utf-8-sig")
    else:
        df.to_csv(pages_csv, index=False, encoding="utf-8-sig")

def batch_convert_pages(input_path: Union[str, Path], out_dir: Union[str, Path], skip_last_page: bool = True):
    """파일이면 그 파일 하나, 폴더면 하위 모든 PDF를 pages.csv로 누적 저장."""
    input_path = Path(input_path)
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    pages_csv = out_dir / "pages.csv"
    if pages_csv.exists():
        pages_csv.unlink()  # 새로 시작

    pdfs = [input_path] if input_path.is_file() else list(input_path.rglob("*.pdf"))
    for pdf in pdfs:
        try:
            convert_pdf_to_pages_csv(pdf, out_dir, skip_last_page=skip_last_page)
        except Exception as e:
            print(f"❌ Failed: {pdf} ({e})")

# ============================
# 2) pages.csv → docs.csv (문서별 1행으로 합치기: 전처리만 수행)
# ============================

# ---------- 보일러플레이트 패턴 ----------
BOILER_PATTERNS = [
    r"^\s*\d{2}-\d{4}-\d{7}\s*$",      # 10-2020-0070641 형태(출원번호)
    r"^\s*-+\s*\d+\s*-+\s*$",          # - 1 - (페이지 넘버)
    r"^\s*Page\s+\d+\s+of\s+\d+\s*$",
    r"^\s*발\s*송\s*번\s*호.*$",
    r"^\s*발\s*송\s*일\s*자.*$",
    r"^\s*제\s*출\s*기\s*일.*$",
    r"^\s*YOUR INVENTION PARTNER\s*$",
    r"^\s*\[.*서식.*\]\s*$",
]
BOILER_RX = re.compile("|".join(BOILER_PATTERNS))

# ---------- 정리 함수 ----------
def normalize_text(s: str) -> str:
    """유니코드/공백 정리"""
    if s is None:
        return ""
    s = unicodedata.normalize("NFKC", str(s))
    s = s.replace("\u00A0", " ")                 # nbsp → space
    s = re.sub(r"[ \t]{2,}", " ", s)             # 연속 공백 축소
    s = "\n".join(ln.rstrip() for ln in s.splitlines())  # 행 끝 공백 제거
    return s

# 문장부호/다음 줄 시작문자 기반 개행 보정(보수적)
TERM = re.compile(r"[\.。!?！？…)]$")         # 이전 줄이 문장부호로 끝나는가
START_OK = re.compile(r"^[가-힣A-Za-z0-9\(]")  # 다음 줄이 자연스러운 시작인가

def join_broken_lines(s: str) -> str:
    lines = s.splitlines()
    if not lines:
        return s
    out = [lines[0]]
    for ln in lines[1:]:
        prev = out[-1]
        if prev and not TERM.search(prev.strip()) and START_OK.search(ln.strip()):
            out[-1] = (prev.rstrip() + " " + ln.lstrip()).strip()
        else:
            out.append(ln)
    return "\n".join(out)

def remove_boilerplate(text: str) -> str:
    """머리말/꼬리말/템플릿 라인 제거 (라인 단위 필터)"""
    kept = []
    for ln in (text or "").splitlines():
        if not BOILER_RX.search(ln):
            kept.append(ln)
    return "\n".join(kept)

def clean_page_text(raw: str) -> str:
    t = normalize_text(raw)
    t = remove_boilerplate(t)
    t = join_broken_lines(t)
    # 과도한 빈 줄 축소
    t = re.sub(r"\n{3,}", "\n\n", t).strip()
    return t

def pages_to_docs(input_csv: Union[str, Path], out_csv: Union[str, Path], page_sep: str = "\n\n"):
    """pages.csv → docs.csv (file_name, full_text)"""
    in_path = Path(input_csv)
    df = pd.read_csv(in_path)

    # 컬럼명 추정(소문자로 대조)
    cols_lower = {c.lower(): c for c in df.columns}
    file_col = cols_lower.get("file_name") or cols_lower.get("filename") or df.columns[0]
    page_col = cols_lower.get("page") or df.columns[1]
    text_col = cols_lower.get("text") or df.columns[-1]

    # 페이지 정렬(숫자 변환 시도 후 실패하면 문자열 정렬)
    def _to_int_safe(x):
        try:
            return int(x)
        except Exception:
            return x
    df["_page_sort"] = df[page_col].apply(_to_int_safe)
    df = df.sort_values([file_col, "_page_sort"]).drop(columns=["_page_sort"])

    # 페이지별 정제 텍스트 생성
    df["text_clean"] = df[text_col].apply(clean_page_text)

    # 파일(문서)별 페이지 텍스트 합치기
    docs = (
        df.groupby(file_col, sort=False)["text_clean"]
          .apply(lambda parts: page_sep.join([p for p in parts if isinstance(p, str) and p.strip()]))
          .reset_index()
          .rename(columns={file_col: "file_name", "text_clean": "full_text"})
    )

    # 결과 저장
    out_path = Path(out_csv)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    docs.to_csv(out_path, index=False, encoding="utf-8-sig")

    print("✅ saved:", out_path)
    print("rows:", len(docs))

# ============================
# 🔁 실행 예시
# ============================
# 1) PDF → pages.csv (마지막 페이지 제외)
PDF_INPUT = "/home/laydata/workspace/final_project/opinion/file/opinion_pdfs"  # ← 폴더(또는 단일 파일 가능)
INPUT_DIR = "/home/laydata/workspace/final_project/opinion"                      # pages.csv가 저장될 폴더
OUT_CSV   = "/home/laydata/workspace/final_project/opinion/opinion_decision_merged.csv"      # 최종 출력

# 1) PDF → pages.csv (마지막 페이지 제외)
batch_convert_pages(
    PDF_INPUT,        # 폴더 또는 단일 PDF 파일 경로
    INPUT_DIR,        # pages.csv 저장 폴더
    skip_last_page=True
)

# 2) pages.csv → docs_merged.csv (전처리만, 꼬리 자르기 없음)
pages_to_docs(
    str(Path(INPUT_DIR) / "pages.csv"),
    OUT_CSV,
    page_sep="\n\n"
)