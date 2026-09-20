from __future__ import annotations

import re
import sys
import time
from pathlib import Path
from urllib.parse import urljoin

import pandas as pd
import requests
from bs4 import BeautifulSoup


# Windows 터미널 Unicode 출력 문제 방지
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass


BASE = Path.cwd()

OUT = (
    BASE
    / "data"
    / "raw"
    / "motie"
    / "motie_search_index_all.csv"
)

URL = "https://www.motie.go.kr/search/search.do"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 Chrome/152 Safari/537.36"
    )
}


def clean(s):
    return " ".join(str(s).split())


def classify_url(url):
    u = url.lower()

    if "/article/" in u and "/view" in u:
        return "ARTICLE"

    if "/attach/down/" in u:
        return "ATTACHMENT"

    return "OTHER"


def guess_file_type(title, url):
    s = (title + " " + url).lower()

    if ".pdf" in s:
        return "PDF"
    if ".hwp" in s:
        return "HWP"
    if ".hwpx" in s:
        return "HWPX"
    if ".doc" in s or ".docx" in s:
        return "DOC"
    if ".xls" in s or ".xlsx" in s:
        return "XLS"

    return ""


session = requests.Session()
session.headers.update(HEADERS)

rows = []
seen = set()

print("=" * 72)
print("MOTIE SEARCH INDEX COLLECTOR")
print("=" * 72)

empty_pages = 0

# 충분히 넓게 순회.
# 실제 결과가 끝나면 연속 빈 페이지에서 자동 종료.
for page in range(1, 201):

    params = {
        "site": "main",
        "kwd": "자동차산업동향",
        "category": "c1",
        "currentPage": str(page),
        "rowPerPage": "100",
        "sort": "r",
        "searchRange": "fdTot",
    }

    try:
        r = session.get(
            URL,
            params=params,
            timeout=30,
        )
        r.raise_for_status()

    except Exception as e:
        print(f"PAGE {page:03d} ERROR {type(e).__name__}")
        time.sleep(1)
        continue

    soup = BeautifulSoup(r.text, "html.parser")

    page_rows = 0

    for a in soup.find_all("a", href=True):

        title = clean(
            a.get_text(" ", strip=True)
        )

        href = urljoin(
            r.url,
            a.get("href", "")
        )

        compact = re.sub(
            r"\s+",
            "",
            title,
        )

        if (
            "자동차산업" not in compact
            and "자동차산업동향" not in compact
        ):
            continue

        kind = classify_url(href)

        # 실제 게시물 / 첨부파일만 보존
        if kind not in {
            "ARTICLE",
            "ATTACHMENT",
        }:
            continue

        key = (title, href)

        if key in seen:
            continue

        seen.add(key)

        rows.append(
            {
                "search_page": page,
                "title": title,
                "url": href,
                "url_type": kind,
                "file_type": guess_file_type(
                    title,
                    href,
                ),
            }
        )

        page_rows += 1

    print(
        f"PAGE {page:03d} "
        f"NEW={page_rows:3d} "
        f"TOTAL={len(rows):4d}"
    )

    if page_rows == 0:
        empty_pages += 1
    else:
        empty_pages = 0

    # 검색결과 종료 판단
    if empty_pages >= 3:
        print("STOP: 3 consecutive empty pages")
        break

    time.sleep(0.25)


df = pd.DataFrame(rows)

OUT.parent.mkdir(
    parents=True,
    exist_ok=True,
)

df.to_csv(
    OUT,
    index=False,
    encoding="utf-8-sig",
)


print()
print("=" * 72)
print("RESULT")
print("=" * 72)

print("TOTAL      :", len(df))

if len(df):
    print(
        "ARTICLE    :",
        (df["url_type"] == "ARTICLE").sum(),
    )
    print(
        "ATTACHMENT :",
        (df["url_type"] == "ATTACHMENT").sum(),
    )
    print(
        "PDF        :",
        (df["file_type"] == "PDF").sum(),
    )

print("OUTPUT     :", OUT)
