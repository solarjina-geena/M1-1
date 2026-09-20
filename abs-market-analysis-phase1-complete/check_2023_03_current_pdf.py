import requests
from bs4 import BeautifulSoup

url = "https://www.motir.go.kr/kor/article/ATCL3f49a5a8c/170535/view"

# 먼저 검색 인덱스에서 2023-03 게시물 URL을 찾음
import pandas as pd
from pathlib import Path

base = Path("data/raw/motie")
files = list(base.glob("*search*.csv")) + list(base.glob("*match*.csv"))

print("=" * 90)
print("2023-03 ARTICLE SEARCH")
print("=" * 90)

article_urls = []

for f in files:
    try:
        df = pd.read_csv(f)
    except Exception:
        continue

    rows = df[
        df.astype(str)
          .apply(lambda r: r.str.contains("2023-03|3월 자동차", case=False, regex=True).any(), axis=1)
    ]

    if len(rows):
        print("\nFILE:", f)
        print(rows.to_string(index=False))

        for col in rows.columns:
            if "url" in col.lower():
                for v in rows[col].dropna().astype(str):
                    if "/article/" in v and "/view" in v:
                        article_urls.append(v)

article_urls = list(dict.fromkeys(article_urls))

print("\n" + "=" * 90)
print("ARTICLE URLS")
print("=" * 90)

for u in article_urls:
    print(u)

print("\n" + "=" * 90)
print("CURRENT PDF LINKS")
print("=" * 90)

for u in article_urls:
    u = u.replace("www.motie.go.kr", "www.motir.go.kr")

    try:
        r = requests.get(u, timeout=30)
        print("\nARTICLE:", u)
        print("STATUS :", r.status_code)

        soup = BeautifulSoup(r.text, "html.parser")

        for a in soup.find_all("a", href=True):
            text = " ".join(a.stripped_strings)
            href = a["href"]

            if ".pdf" in text.lower() or "/attach/" in href:
                if href.startswith("/"):
                    href = "https://www.motir.go.kr" + href

                print("TITLE :", text)
                print("URL   :", href)
                print("-" * 70)

    except Exception as e:
        print("ERROR:", e)
