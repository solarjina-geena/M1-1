import re
from pathlib import Path

import pandas as pd


BASE = Path("data/raw/motie")

SEARCH_FILE = BASE / "motie_search_full_2015_2025.csv"
INDEX_FILE = BASE / "motie_auto_monthly_index_recovered.csv"

OUT_ALL = BASE / "motie_missing_match_candidates.csv"
OUT_BEST = BASE / "motie_missing_match_best.csv"


# ------------------------------------------------------------
# 1. 파일 읽기
# ------------------------------------------------------------

search = pd.read_csv(SEARCH_FILE)
index = pd.read_csv(INDEX_FILE)

print("=" * 80)
print("MOTIE MISSING MONTH MATCHER")
print("=" * 80)

print("SEARCH ROWS :", len(search))
print("INDEX ROWS  :", len(index))


# ------------------------------------------------------------
# 2. MISSING 월 확보
# ------------------------------------------------------------

if "status" not in index.columns:
    raise RuntimeError(
        "motie_auto_monthly_index_recovered.csv 에 status 컬럼이 없습니다."
    )

missing = (
    index[index["status"].astype(str).str.upper() == "MISSING"]
    ["period"]
    .dropna()
    .astype(str)
    .drop_duplicates()
    .sort_values()
    .tolist()
)

print("MISSING     :", len(missing))


# ------------------------------------------------------------
# 3. 텍스트 정리
# ------------------------------------------------------------

def clean(v):
    if pd.isna(v):
        return ""
    return " ".join(str(v).split())


def build_text(row):
    return " ".join([
        clean(row.get("title", "")),
        clean(row.get("context", "")),
        clean(row.get("url", "")),
    ])


search["_text"] = search.apply(build_text, axis=1)


# ------------------------------------------------------------
# 4. 특정 YYYY-MM 후보 패턴
# ------------------------------------------------------------

def month_patterns(period):

    year, month = period.split("-")

    y4 = int(year)
    y2 = str(y4)[2:]
    m = int(month)

    return [
        # 2023년 3월
        rf"{y4}\s*년\s*0?{m}\s*월",

        # '23년 3월 / ’23년 3월
        rf"[\'‘’]?\s*{y2}\s*년\s*0?{m}\s*월",

        # 2023.3월
        rf"{y4}\s*[.\-/]\s*0?{m}\s*월",

        # '23.3월
        rf"[\'‘’]?\s*{y2}\s*[.\-/]\s*0?{m}\s*월",
    ]


# ------------------------------------------------------------
# 5. 자동차산업 동향 여부
# ------------------------------------------------------------

def auto_industry_score(text):

    compact = re.sub(r"\s+", "", text)

    score = 0

    if "자동차산업동향" in compact:
        score += 50

    elif "자동차산업" in compact and "동향" in compact:
        score += 40

    if "자동차" in compact:
        score += 5

    if "생산" in compact:
        score += 3

    if "내수" in compact:
        score += 3

    if "수출" in compact:
        score += 3

    return score


# ------------------------------------------------------------
# 6. 월별 후보 검색
# ------------------------------------------------------------

results = []

for period in missing:

    pats = month_patterns(period)

    period_rows = []

    for idx, row in search.iterrows():

        text = row["_text"]

        matched = False

        for pat in pats:
            if re.search(pat, text, flags=re.I):
                matched = True
                break

        if not matched:
            continue

        score = 100
        score += auto_industry_score(text)

        title = clean(row.get("title", ""))
        url = clean(row.get("url", ""))
        typ = clean(row.get("type", ""))

        title_compact = re.sub(r"\s+", "", title)

        # 제목에 자동차산업 동향이 있으면 강하게 우선
        if "자동차산업동향" in title_compact:
            score += 80
        elif "자동차산업" in title_compact and "동향" in title_compact:
            score += 60

        # ARTICLE 우선
        if typ.upper() == "ARTICLE":
            score += 20

        # PDF 첨부도 높은 가치
        if ".pdf" in title.lower():
            score += 15

        # HWP
        if ".hwp" in title.lower():
            score += 5

        period_rows.append({
            "period": period,
            "score": score,
            "type": typ,
            "title": title,
            "url": url,
            "page_no": row.get("page_no"),
            "currentPage": row.get("currentPage"),
        })

    period_rows.sort(
        key=lambda x: x["score"],
        reverse=True
    )

    # 한 월당 상위 10개만 저장
    period_rows = period_rows[:10]

    for rank, item in enumerate(period_rows, start=1):
        item["rank"] = rank
        results.append(item)

    print(
        f"{period} : "
        f"{len(period_rows):2d} candidates"
    )


# ------------------------------------------------------------
# 7. 저장
# ------------------------------------------------------------

cols = [
    "period",
    "rank",
    "score",
    "type",
    "title",
    "url",
    "page_no",
    "currentPage",
]

if results:
    result_df = pd.DataFrame(results)[cols]
else:
    result_df = pd.DataFrame(columns=cols)

result_df.to_csv(
    OUT_ALL,
    index=False,
    encoding="utf-8-sig"
)


# ------------------------------------------------------------
# 8. 월별 BEST
# ------------------------------------------------------------

if not result_df.empty:

    best = (
        result_df
        .sort_values(
            ["period", "score"],
            ascending=[True, False]
        )
        .groupby("period", as_index=False)
        .first()
    )

else:
    best = pd.DataFrame(columns=cols)


# 후보가 하나도 없는 MISSING 월도 표시
base_missing = pd.DataFrame({
    "period": missing
})

best = base_missing.merge(
    best,
    on="period",
    how="left"
)

best["match_status"] = best["url"].apply(
    lambda x: "CANDIDATE" if pd.notna(x) else "NO_MATCH"
)

best.to_csv(
    OUT_BEST,
    index=False,
    encoding="utf-8-sig"
)


# ------------------------------------------------------------
# 9. 결과
# ------------------------------------------------------------

print()
print("=" * 80)
print("RESULT")
print("=" * 80)

print("MISSING       :", len(missing))
print(
    "MATCHED       :",
    (best["match_status"] == "CANDIDATE").sum()
)
print(
    "NO MATCH      :",
    (best["match_status"] == "NO_MATCH").sum()
)

print()
print("=== BEST CANDIDATES ===")

show_cols = [
    "period",
    "score",
    "type",
    "title",
    "url",
    "match_status",
]

print(
    best[show_cols]
    .to_string(index=False)
)

print()
print("ALL  :", OUT_ALL.resolve())
print("BEST :", OUT_BEST.resolve())