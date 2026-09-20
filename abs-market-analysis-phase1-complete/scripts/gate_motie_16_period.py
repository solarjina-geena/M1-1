from pathlib import Path
import pandas as pd
import re

BASE = Path("data/raw/motie")
SRC = BASE / "motie_16_deep_search_candidates.csv"
OUT = BASE / "motie_16_period_gate.csv"

df = pd.read_csv(SRC, dtype=str).fillna("")

def norm(s):
    return (
        str(s)
        .replace("’", "'")
        .replace("‘", "'")
        .replace(" ", "")
    )

def judge(row):
    period = row["period"]
    year, month = period.split("-")
    yy = year[-2:]
    m = int(month)

    title = norm(row["title"])
    context = norm(row["context"])

    # -----------------------------------------
    # 정확한 실적월 표현
    # -----------------------------------------
    patterns = [
        rf"{year}년0?{m}월",
        rf"'{yy}년0?{m}월",
        rf"'{yy}\.0?{m}월",
        rf"{yy}년0?{m}월"
    ]

    exact_title = any(
        re.search(p, title, re.I)
        for p in patterns
    )

    exact_context = any(
        re.search(p, context, re.I)
        for p in patterns
    )

    # -----------------------------------------
    # 6월은 상반기+6월 자료 허용
    # -----------------------------------------
    halfyear = (
        m == 6
        and "상반기" in title
        and (
            "및6월" in title
            or "6월자동차" in title
        )
    )

    # -----------------------------------------
    # 자동차산업 자료 여부
    # -----------------------------------------
    automobile = (
        "자동차산업" in title
        or "자동차산업" in context
    )

    metrics = all(
        x in context
        for x in ["생산", "내수", "수출"]
    )

    # -----------------------------------------
    # 판정
    # -----------------------------------------
    if halfyear and automobile and metrics:
        return "PERIOD_MATCH", "HALFYEAR_6_MONTH"

    if exact_title and automobile and metrics:
        return "PERIOD_MATCH", "EXACT_PERIOD_TITLE"

    if exact_context and automobile and metrics:
        return "PERIOD_REVIEW", "PERIOD_IN_CONTEXT"

    return "REJECT", "PERIOD_MISMATCH"


result = df.copy()

tmp = result.apply(
    judge,
    axis=1,
    result_type="expand"
)

result["period_gate"] = tmp[0]
result["period_reason"] = tmp[1]

# 월별 우선순위
priority = {
    "PERIOD_MATCH": 0,
    "PERIOD_REVIEW": 1,
    "REJECT": 2
}

result["_priority"] = result["period_gate"].map(priority)

result["score_num"] = pd.to_numeric(
    result["score"],
    errors="coerce"
).fillna(0)

result = result.sort_values(
    ["period", "_priority", "score_num"],
    ascending=[True, True, False]
)

result.drop(
    columns=["_priority"],
    inplace=True
)

result.to_csv(
    OUT,
    index=False,
    encoding="utf-8-sig"
)

print("=" * 100)
print("MOTIE 16 PERIOD CONTENT GATE")
print("=" * 100)

for period, g in result.groupby("period"):

    print()
    print("-" * 100)
    print("PERIOD :", period)

    good = g[g["period_gate"] != "REJECT"]

    if good.empty:
        print(">>> NO VALID PERIOD CANDIDATE")
        continue

    for _, r in good.head(5).iterrows():
        print(
            r["period_gate"],
            "|",
            r["period_reason"],
            "| SCORE",
            r["score"]
        )
        print("TITLE :", r["title"][:400])
        print("URL   :", r["url"])
        print()

summary = (
    result.groupby(["period", "period_gate"])
    .size()
    .unstack(fill_value=0)
)

print()
print("=" * 100)
print("SUMMARY")
print("=" * 100)
print(summary)

no_valid = []

for period, g in result.groupby("period"):
    if not (g["period_gate"] == "PERIOD_MATCH").any():
        no_valid.append(period)

print()
print("NO PERIOD_MATCH :", len(no_valid))
print(" ".join(no_valid))

print()
print("OUTPUT :", OUT)
print()
print("※ MASTER 변경 없음")
print("※ 숫자 추출 없음")
print("※ PERIOD_MATCH도 아직 BODY_VERIFIED 아님")
