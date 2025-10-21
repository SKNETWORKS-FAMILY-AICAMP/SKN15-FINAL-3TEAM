# -*- coding: utf-8 -*-
import os, re, time, csv, requests
from xml.etree import ElementTree as ET
from tqdm import tqdm

# ====== 설정 ======
ACCESS_KEY = "enter your key"   # <- 발급키로 교체
BASE_URL   = "http://plus.kipris.or.kr/openapi/rest/IntermediateDocumentREService/advancedSearchInfo"

INPUT_CSV  = "2.csv"   # <- 출원번호 목록 CSV 경로
OUT_CSV    = "reject_infos.csv"        # <- 결과 저장 CSV
SLEEP_SEC  = 0.3                       # 속도제어 (초당 ~3건)

# ====== 유틸 ======
def normalize_app_no(x: str) -> str:
    """하이픈/공백 제거하고 숫자만 남김"""
    if x is None: return ""
    return re.sub(r"[^0-9]", "", str(x))

def read_app_numbers(csv_path: str):
    """
    CSV에서 출원번호 컬럼을 찾아 읽어옴.
    - 우선 '출원번호', 'applicationNumber' 헤더를 찾고
    - 없으면 첫 번째 컬럼을 사용
    - 인코딩은 utf-8-sig -> cp949 순서로 시도
    """
    def _read(path, encoding):
        with open(path, "r", encoding=encoding, newline="") as f:
            reader = csv.reader(f)
            rows = list(reader)
        return rows

    # 인코딩 트라이
    rows = None
    for enc in ("utf-8", "utf-8-sig", "cp949"):
        try:
            rows = _read(csv_path, enc)
            break
        except Exception:
            pass
    if rows is None:
        raise RuntimeError("CSV 읽기 실패: utf-8-sig/cp949 모두 실패")

    header = rows[0] if rows else []
    # 컬럼 인덱스 탐색
    idx = None
    for i, name in enumerate(header):
        if str(name).strip() in ("출원번호", "applicationNumber"):
            idx = i; break
    if idx is None:
        idx = 0  # 첫 컬럼 사용

    app_list = []
    for r in rows[1:]:
        if not r: continue
        app = normalize_app_no(r[idx] if idx < len(r) else "")
        if app:
            app_list.append(app)
    # 중복 제거(원본 순서 유지)
    seen = set(); uniq = []
    for a in app_list:
        if a not in seen:
            seen.add(a); uniq.append(a)
    return uniq

def ensure_out_csv(path: str):
    if not os.path.exists(path):
        with open(path, "w", encoding="utf-8-sig", newline="") as f:
            w = csv.DictWriter(f, fieldnames=["applicationNumber","sendNumber","sendDate","title","pdfUrl"])
            w.writeheader()

def load_processed_set(path: str):
    """이미 저장된 applicationNumber 세트 (재시작 시 스킵용)"""
    if not os.path.exists(path): return set()
    s = set()
    with open(path, "r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            app = normalize_app_no(row.get("applicationNumber",""))
            if app: s.add(app)
    return s

def strip_ns(xml_str: str) -> str:
    return re.sub(r'xmlns(:\w+)?="[^"]+"', "", xml_str)

def fetch_one_app(app_no: str):
    """
    출원번호 1개 호출 → advancedSearchInfo 리스트 반환
    """
    params = {
        "applicationNumber": app_no,
        "patent": "true", "utility": "true", "design": "true", "tradeMark": "true",
        "docsStart": "1", "docsCount": "50",
        "descSort": "true", "sortSpec": "AN",
        "accessKey": ACCESS_KEY,
    }
    try:
        r = requests.get(BASE_URL, params=params, timeout=20)
        # print(f"[HTTP] {app_no} → status={r.status_code}, content-type={r.headers.get('Content-Type')}")

        if r.status_code != 200 or "xml" not in r.headers.get("Content-Type","").lower():
            print(f"[WARN] {app_no} → XML 아님 / 결과 없음")
            return []

        root = ET.fromstring(strip_ns(r.text))
        items = root.findall(".//advancedSearchInfo")
        print(f"[RESULT] {app_no} → {len(items)}건")

        rows = []
        for n in items:
            rows.append({
                "applicationNumber": (n.findtext("applicationNumber") or "").strip(),
                "sendNumber": (n.findtext("sendNumber") or "").strip(),
                "sendDate": (n.findtext("sendDate") or "").strip(),
                "title": (n.findtext("title") or "").strip(),
                "pdfUrl": (n.findtext("filePath") or "").strip(),
            })
        return rows

    except Exception as e:
        print(f"[ERROR] {app_no} → {e}")
        return []

# ====== 실행 ======
app_numbers = read_app_numbers(INPUT_CSV)
app_numbers = app_numbers[2000:3001]
ensure_out_csv(OUT_CSV)
already = load_processed_set(OUT_CSV)

print(f"총 {len(app_numbers)}건 읽음. (이미 저장된 출원번호 {len(already)}건 스킵)")
cnt_write = 0

with open(OUT_CSV, "a", encoding="utf-8-sig", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=["applicationNumber","sendNumber","sendDate","title","pdfUrl"])
    for app_no in tqdm(app_numbers):
        if app_no in already:
            continue
        rows = fetch_one_app(app_no)
        if rows:
            writer.writerows(rows)
            f.flush()   # 중간 저장
            cnt_write += len(rows)
        time.sleep(SLEEP_SEC)  # 속도제어

print(f"완료. 새로 저장: {cnt_write}건")
