from pathlib import Path
import pandas as pd
import re

SRC = Path("data/raw/motie/motie_search_full_2015_2025.csv")
OUT = Path("data/raw/motie/motie_missing49_search_candidates.csv")

MISSING = set("""
2015-03 2015-05 2015-12
2016-02 2016-05 2016-06 2016-11
2017-01 2017-03 2017-07 2017-08
2018-04
2019-01 2019-02 2019-03 2019-04 2019-05
2020-01 2020-08 2020-09 2020-10 2020-11
2021-01 2021-02 2021-03 2021-04 2021-05 2021-06 2021-07 2021-08
2022-06 2022-10
2023-06 2023-07 2023-08 2023-09 2023-10 2023-11 2023-12
2024-01 2024-02 2024-04 2024-05 2024-06 2024-07 2024-08 2024-09 2024-10
2025-03
""".split())

print("=" * 90, flush=True)
print("MOTIE MISSING 49 FAST SEARCH", flush=True)
print("=" * 90, flush=True)
print("1. CSV 읽는 중...", flush=True)

df = pd.read_csv(
    SRC,
    usecols=["title", "context", "url", "target_period"],
    dtype=str,
    keep_default_na=False
)

print(f"   ROWS: {len(df):,}", flush=True)
print("2. 후보 추출 중...", flush=True)

# 먼저 target_period가 정확히 누락월인 행을 한 번에 추출
a = df[df["target_period"].isin(MISSING)].copy()
a["match_type"] = "TARGET_PERIOD"
a["score"] = 100

# 제목에서 YYYY년 M월 / YY년 M월 추출
title = df["title"].str.replace(r"\s+", " ", regex=True)

ym4 = title.str.extract(
    r"(?<!\d)(20(?:1[5-9]|2[0-5]))\s*년\s*0?([1-9]|1[0-2])\s*월"
)

ym2 = title.str.extract(
    r"(?:^|[^\d])['‘’]?(1[5-9]|2[0-5])\s*년\s*0?([1-9]|1[0-2])\s*월"
)

period4 = (
    ym4[0].fillna("") + "-" +
    ym4[1].fillna("").str.zfill(2)
)

period2 = (
    "20" + ym2[0].fillna("") + "-" +
    ym2[1].fillna("").str.zfill(2)
)

mask4 = period4.isin(MISSING)
mask2 = period2.isin(MISSING)

b = df[mask4 | mask2].copy()

b["period_from_title"] = ""
b.loc[mask4, "period_from_title"] = period4[mask4]
b.loc[mask2 & ~mask4, "period_from_title"] = period2[mask2 & ~mask4]

# 자동차 관련 자료만
auto = (
    b["title"].str.contains("자동차", na=False) |
    b["context"].str.contains("자동차", na=False)
)

b = b[auto].copy()
b["match_type"] = "TITLE_MONTH"
b["score"] = 150

# target_period 후보에 period 부여
a["period"] = a["target_period"]

# 제목 후보
b["period"] = b["period_from_title"]

cols = [
    "period",
    "score",
    "match_type",
    "target_period",
    "title",
    "url",
    "context"
]

result = pd.concat(
    [a[cols], b[cols]],
    ignore_index=True
)

# 중복 제거
result = result.drop_duplicates(
    subset=["period", "title", "url"]
)

# 자동차산업 동향 제목에 가점
result.loc[
    result["title"].str.contains(
        r"자동차\s*산업.*동향|자동차산업.*동향",
        regex=True,
        na=False
    ),
    "score"
] += 50

# 생산/내수/수출 모두 포함 시 가점
ctx = result["title"] + " " + result["context"]

for word in ["생산", "내수", "수출"]:
    result.loc[ctx.str.contains(word, na=False), "score"] += 5

result = result.sort_values(
    ["period", "score"],
    ascending=[True, False]
)

# 월별 상위 10개만 저장
result = result.groupby(
    "period",
    group_keys=False
).head(10)

result.to_csv(
    OUT,
    index=False,
    encoding="utf-8-sig"
)

found = sorted(set(result["period"]))
missing = sorted(MISSING - set(found))

print("3. 완료", flush=True)
print("=" * 90, flush=True)
print("RESULT", flush=True)
print("=" * 90, flush=True)
print("TARGET       :", len(MISSING), flush=True)
print("FOUND        :", len(found), flush=True)
print("NOT FOUND    :", len(missing), flush=True)
print("CANDIDATES   :", len(result), flush=True)
print(flush=True)

for period in sorted(MISSING):
    x = result[result["period"] == period]

    if x.empty:
        print(f"{period} | NONE", flush=True)
    else:
        best = x.iloc[0]
        t = str(best["title"]).replace("\n", " ")[:80]
        print(
            f"{period} | {len(x)} | "
            f"SCORE={best['score']} | {t}",
            flush=True
        )

print()
print("=== STILL NOT FOUND ===")
print(" ".join(missing) if missing else "NONE")

print()
print("OUTPUT :", OUT)
