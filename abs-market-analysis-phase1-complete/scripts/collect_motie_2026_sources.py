from pathlib import Path
import requests
import pandas as pd
import re
import time
from bs4 import BeautifulSoup
from urllib.parse import urljoin, quote

BASE = Path("data/raw/motie")
BASE.mkdir(parents=True, exist_ok=True)

OUT = BASE / "motie_2026_source_candidates.csv"

TARGETS = [f"2026-{m:02d}" for m in range(1, 9)]

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 Chrome/152 Safari/537.36"
    )
}

print("=" * 100)
print("MOTIE 2026 SOURCE CANDIDATE COLLECTION")
print("=" * 100)
print("TARGET :", " ".join(TARGETS))
print()
print("※ 후보 수집 단계")
print("※ 숫자 추출 안 함")
print("※ MASTER 변경 없음")
print()

# ---------------------------------------------------------
# 검색
# ---------------------------------------------------------
def search_motie(period):

    year, month = map(int, period.split("-"))

    queries = [
        f'site:motir.go.kr "{year}년 {month}월 자동차산업 동향"',
        f'site:motie.go.kr "{year}년 {month}월 자동차산업 동향"',
        f'site:motir.go.kr "{month}월 자동차산업 동향" "{year}"',
    ]

    rows = []

    for query in queries:

        # Bing HTML 검색
        url = (
            "https://www.google.com/search?q="
            + quote(query)
        )

        try:
            r = requests.get(
                url,
                headers=HEADERS,
                timeout=15
            )

            if r.status_code != 200:
                continue

            soup = BeautifulSoup(
                r.text,
                "html.parser"
            )

            # 검색 결과 링크
            for a in soup.select("a"):

                href = a.get("href", "")
                text = " ".join(
                    a.get_text(" ", strip=True).split()
                )

                if not href or not text:
                    continue

                if "motir.go.kr" not in href and "motie.go.kr" not in href:
                    continue

                # google redirect 정리
                m = re.search(r"/url\?q=([^&]+)", href)

                if m:
                    href = m.group(1)

                rows.append({
                    "period": period,
                    "query": query,
                    "title": text,
                    "url": href
                })

            time.sleep(0.5)

        except Exception as e:

            rows.append({
                "period": period,
                "query": query,
                "title": "",
                "url": "",
                "error": str(e)
            })

    return rows


all_rows = []

for i, period in enumerate(TARGETS, 1):

    print(
        f"[{i}/8] {period} 검색 중...",
        flush=True
    )

    rows = search_motie(period)
    all_rows.extend(rows)


df = pd.DataFrame(all_rows)

if df.empty:

    print()
    print("검색 결과가 없습니다.")
    print("웹 검색 차단 가능성이 있습니다.")
    raise SystemExit


# ---------------------------------------------------------
# 중복 제거
# ---------------------------------------------------------
for c in ["period", "query", "title", "url"]:
    if c not in df.columns:
        df[c] = ""

df = df.drop_duplicates(
    subset=["period", "title", "url"]
).copy()


# ---------------------------------------------------------
# 후보 점수
# ---------------------------------------------------------
def score_row(row):

    period = row["period"]
    year, month = map(int, period.split("-"))

    title = str(row["title"])
    url = str(row["url"])

    compact = re.sub(r"\s+", "", title)

    score = 0
    reasons = []

    if "자동차산업" in compact:
        score += 100
        reasons.append("AUTO_INDUSTRY")

    if "동향" in title:
        score += 40
        reasons.append("TREND")

    if str(year) in title:
        score += 60
        reasons.append("YEAR")

    if re.search(
        rf"(?<!\d)0?{month}\s*월",
        title
    ):
        score += 80
        reasons.append("MONTH")

    if "/article/" in url:
        score += 20
        reasons.append("ARTICLE")

    # 3월은 1분기 자료 가능
    if (
        month == 3
        and "1분기" in title
        and "자동차" in title
    ):
        score += 80
        reasons.append("Q1_MARCH")

    # 6월은 상반기 자료 가능
    if (
        month == 6
        and "상반기" in title
        and "자동차" in title
    ):
        score += 80
        reasons.append("H1_JUNE")

    return pd.Series(
        [score, "|".join(reasons)]
    )


df[["score", "reason"]] = df.apply(
    score_row,
    axis=1
)

df = df.sort_values(
    ["period", "score"],
    ascending=[True, False]
)

# 월별 상위 10개 보존
df = (
    df.groupby("period", group_keys=False)
      .head(10)
      .reset_index(drop=True)
)

df.to_csv(
    OUT,
    index=False,
    encoding="utf-8-sig"
)


# ---------------------------------------------------------
# 결과
# ---------------------------------------------------------
print()
print("=" * 100)
print("BEST SOURCE CANDIDATES")
print("=" * 100)

found = []

for period in TARGETS:

    g = df[df["period"] == period]

    if g.empty:

        print(period, "| NONE")
        continue

    found.append(period)

    r = g.iloc[0]

    print()
    print(
        period,
        "| SCORE",
        r["score"]
    )
    print(
        "TITLE :",
        str(r["title"])[:300]
    )
    print(
        "URL   :",
        r["url"]
    )
    print(
        "REASON:",
        r["reason"]
    )


missing = [
    p for p in TARGETS
    if p not in found
]

print()
print("=" * 100)
print("RESULT")
print("=" * 100)

print("TARGET       :", len(TARGETS))
print("FOUND        :", len(found))
print("NO CANDIDATE :", len(missing))

print()
print("NO CANDIDATE:")
print(
    " ".join(missing)
    if missing else
    "NONE"
)

print()
print("OUTPUT :", OUT)

print()
print("※ 아직 BODY_VERIFIED 아님")
print("※ MASTER 변경 없음")
