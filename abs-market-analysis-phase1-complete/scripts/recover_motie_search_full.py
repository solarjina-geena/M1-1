import re
import time
from pathlib import Path
from urllib.parse import urljoin

import pandas as pd
import requests
from bs4 import BeautifulSoup


BASE = "https://www.motie.go.kr"
SEARCH_URL = BASE + "/search/search.do"

OUT = Path("data/raw/motie/motie_search_full_2015_2025.csv")
OUT.parent.mkdir(parents=True, exist_ok=True)

KEYWORD = "자동차산업동향"

session = requests.Session()
session.headers.update({
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/152.0.0.0 Safari/537.36"
    )
})


def clean(text):
    return " ".join((text or "").split())


def extract_year(text):
    years = re.findall(r"20(?:0\d|1\d|2\d)", text)
    if not years:
        return None

    years = [int(x) for x in years]

    # 검색 결과 본문의 과거 비교연도보다
    # 게시물 제목/날짜 쪽 최신 연도를 우선하기 위한 단순 처리
    return max(years)


rows = []
seen_urls = set()

print("=" * 80)
print("MOTIE SEARCH FULL RECOVERY")
print("=" * 80)

for page_no in range(1, 545):

    # 사이트 JS:
    # currentPage = obj * 10 - 9
    current_page = page_no * 10 - 9

    params = {
        "site": "main",
        "kwd": KEYWORD,
        "category": "c1",
        "reSrchFlag": "",
        "currentPage": str(current_page),
        "detailSearch": "false",
        "srchFd": "",
        "sort": "r",
        "date": "",
        "start-date": "0",
        "end-date": "0",
        "preCondi": "",
        "rowPerPage": "10",
        "fdTot": "",
        "fdTitle": "",
        "fdContent": "",
        "fdFile": "",
        "fdNotice": "",
        "ppkFlag": "weekly",
        "searchRange": "fdTot",
        "searchOptionAnd": "",
        "searchOptionOr": "",
        "pageNum": str(page_no),
    }

    try:
        r = session.get(
            SEARCH_URL,
            params=params,
            timeout=30,
        )
        r.raise_for_status()

    except Exception as e:
        print(
            f"PAGE {page_no:03d} "
            f"currentPage={current_page}: ERROR {e}"
        )
        continue

    soup = BeautifulSoup(r.text, "html.parser")

    page_rows = []
    page_years = []

    for a in soup.find_all("a", href=True):

        href = a.get("href", "")
        title = clean(a.get_text(" ", strip=True))

        if not title:
            continue

        full_url = urljoin(BASE, href)

        is_article = "/article/" in full_url and "/view" in full_url
        is_attach = "/attach/down/" in full_url

        if not (is_article or is_attach):
            continue

        if full_url in seen_urls:
            continue

        parent = a.parent
        context = clean(
            parent.get_text(" ", strip=True)
            if parent else title
        )

        # 너무 짧으면 상위 부모에서 날짜/설명 확보
        if len(context) < 30 and parent is not None:
            p2 = parent.parent
            if p2 is not None:
                context = clean(p2.get_text(" ", strip=True))

        year = extract_year(title + " " + context)

        if year:
            page_years.append(year)

        row = {
            "page_no": page_no,
            "currentPage": current_page,
            "year_hint": year,
            "type": "ARTICLE" if is_article else "ATTACHMENT",
            "title": title,
            "context": context,
            "url": full_url,
        }

        page_rows.append(row)
        seen_urls.add(full_url)

    rows.extend(page_rows)

    yr_min = min(page_years) if page_years else None
    yr_max = max(page_years) if page_years else None

    print(
        f"PAGE {page_no:03d} "
        f"currentPage={current_page:<5} "
        f"items={len(page_rows):<3} "
        f"years={yr_min}~{yr_max}"
    )

    # 최신순 검색이므로 페이지 전체가 2014 이하로 내려간 경우 종료
    # 단, 초반 몇 페이지에서 잘못 감지되는 것을 방지
    if page_no >= 3 and page_years:
        if max(page_years) <= 2014:
            print()
            print("2014년 이하 구간 도달 -> 검색 종료")
            break

    time.sleep(0.15)


df = pd.DataFrame(rows)

if not df.empty:

    df = df.drop_duplicates(subset=["url"]).copy()

    # 최종적으로 우리가 필요한 기간 중심으로 저장
    df["target_period"] = df["year_hint"].apply(
        lambda x: (
            2015 <= int(x) <= 2025
            if pd.notna(x)
            else False
        )
    )

    df = df.sort_values(
        ["page_no", "type", "title"],
        kind="stable",
    )

df.to_csv(
    OUT,
    index=False,
    encoding="utf-8-sig",
)

print()
print("=" * 80)
print("RESULT")
print("=" * 80)
print("TOTAL :", len(df))

if not df.empty:
    print("ARTICLE :", (df["type"] == "ARTICLE").sum())
    print("ATTACH  :", (df["type"] == "ATTACHMENT").sum())
    print("TARGET  :", df["target_period"].sum())

print("OUTPUT :", OUT.resolve())
