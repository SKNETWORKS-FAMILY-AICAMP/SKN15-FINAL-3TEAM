import requests, csv, time
from bs4 import BeautifulSoup

URL = "https://arxiv.org/search/?query=attention&searchtype=all&abstracts=show&order=-announced_date_first&size=50"
HDRS = {"User-Agent": "Mozilla/5.0"}

def parse_result(li):
    # 제목
    title = li.select_one("p.title").get_text(strip=True)
    # 저자 (comma-join)
    authors = [a.get_text(strip=True) for a in li.select("p.authors a")]
    authors_str = ", ".join(authors)
    # 초록
    abs_tag = li.select_one("span.abstract-full") or li.select_one("span.abstract-short")
    abstract = abs_tag.get_text(" ", strip=True) if abs_tag else ""
    # 논문 링크 (arXiv 페이지)
    # 보통 "list-title" 블록 내 arXiv:xxxx 링크가 상세 페이지
    a_id = li.select_one("p.list-title a[href*='arxiv.org/abs/']")
    link = a_id["href"] if a_id else ""
    return {
        "title": title,
        "authors": authors_str,
        "abstract": abstract,
        "link": link,
    }

def crawl_page(url=URL):
    r = requests.get(url, headers=HDRS, timeout=30)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "lxml")
    results = []
    for li in soup.select("li.arxiv-result"):
        results.append(parse_result(li))
    return results

rows = crawl_page(URL)




with open("arxiv_attention_page0.csv", "w", newline="", encoding="utf-8-sig") as f:
    w = csv.DictWriter(f, fieldnames=["title","authors","abstract","link"])
    w.writeheader()
    w.writerows(rows)

print("총 수집:", len(rows))