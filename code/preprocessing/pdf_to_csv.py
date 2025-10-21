from pathlib import Path
import re
from typing import List, Dict, Union
import pandas as pd

def extract_text_per_page(pdf_path: Union[str, Path]) -> List[str]:
    pdf_path = str(pdf_path)
    pages: List[str] = []
    try:
        from PyPDF2 import PdfReader
        reader = PdfReader(pdf_path)
        for p in reader.pages:
            t = p.extract_text() or ""
            pages.append(t)
        if not any(pages):
            raise ValueError("PyPDF2 returned empty text; fallback to pdfminer")
        return pages
    except Exception:
        pass
    from pdfminer.high_level import extract_text
    full = extract_text(pdf_path) or ""
    pages = re.split(r"\f+", full)
    pages = [p.strip("\n") for p in pages if p is not None]
    return pages

def extract_meta(full_text: str) -> Dict[str, str]:
    meta = {}
    m = re.search(r"\b(\d{2}-\d{4}-\d{7})\b", full_text)  
    if m: meta["application_number"] = m.group(1)

    m = re.search(r"발\s*송\s*번\s*호[:：]?\s*([0-9\-]+)", full_text) or \
        re.search(r"발송번호\s*([0-9\-]+)", full_text)
    if m: meta["dispatch_number"] = m.group(1)

    m = re.search(r"발\s*송\s*일\s*자[:：]?\s*([0-9]{4}\.[0-9]{2}\.[0-9]{2})", full_text) or \
        re.search(r"발송일자[:：]?\s*([0-9]{4}\.[0-9]{2}\.[0-9]{2})", full_text)
    if m: meta["dispatch_date"] = m.group(1)

    m = re.search(r"제\s*출\s*기\s*일.*?([0-9]{4}\.[0-9]{2}\.[0-9]{2})", full_text) or \
        re.search(r"제출기일.*?([0-9]{4}\.[0-9]{2}\.[0-9]{2})", full_text)
    if m: meta["due_date"] = re.sub(r"[^\d\.]", "", m.group(1)).rstrip(".")

    m = re.search(r"출원인[:：]?\s*([^\n]+)", full_text)
    if m: meta["applicant"] = m.group(1).strip()

    m = re.search(r"발명자[:：]?\s*([^\n]+)", full_text)
    if m: meta["inventor"] = m.group(1).strip()

    return meta

def convert_pdf_to_csv(src: Union[str, Path], out_dir: Union[str, Path]):
    src = Path(src); out_dir = Path(out_dir); out_dir.mkdir(parents=True, exist_ok=True)
    pages_csv = out_dir / "pages.csv"
    docs_csv  = out_dir / "docs.csv"

    pages = extract_text_per_page(src)
    rows = [{"file_name": src.name, "page": i+1, "text": t} for i, t in enumerate(pages)]
    df_pages = pd.DataFrame(rows, columns=["file_name", "page", "text"])
    if pages_csv.exists():
        df_pages.to_csv(pages_csv, index=False, mode="a", header=False, encoding="utf-8-sig")
    else:
        df_pages.to_csv(pages_csv, index=False, encoding="utf-8-sig")

    full_text = "\n\n".join(p["text"] for p in rows)
    meta = extract_meta(full_text)
    doc_row = {"file_name": src.name, "full_text": full_text, **meta}
    df_doc = pd.DataFrame([doc_row], columns=[
        "file_name","full_text","application_number","dispatch_number",
        "dispatch_date","due_date","applicant","inventor",
    ])
    if docs_csv.exists():
        df_doc.to_csv(docs_csv, index=False, mode="a", header=False, encoding="utf-8-sig")
    else:
        df_doc.to_csv(docs_csv, index=False, encoding="utf-8-sig")

def batch_convert(input_path: Union[str, Path], out_dir: Union[str, Path]):
    input_path = Path(input_path); out_dir = Path(out_dir); out_dir.mkdir(parents=True, exist_ok=True)
    pages_csv = out_dir / "pages.csv"; docs_csv = out_dir / "docs.csv"
    if pages_csv.exists(): pages_csv.unlink()
    if docs_csv.exists(): docs_csv.unlink()

    pdfs = [input_path] if input_path.is_file() else list(input_path.rglob("*.pdf"))
    for pdf in pdfs:
        try:
            convert_pdf_to_csv(pdf, out_dir)
        except Exception as e:
            print(f"Failed: {pdf} ({e})")


