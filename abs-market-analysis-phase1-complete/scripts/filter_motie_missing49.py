from pathlib import Path
import pandas as pd
import re

SRC = Path("data/raw/motie/motie_missing49_search_candidates.csv")
OUT = Path("data/raw/motie/motie_missing49_auto_filtered.csv")

df = pd.read_csv(SRC, dtype=str, keep_default_na=False)

def normalize(s):
    return re.sub(r"\s+", " ", str(s)).strip()

def classify(row):
    period = row["period"]
    title = normalize(row["title"])
    context = normalize(row["context"])
    text = title + " " + context

    y, m = period.split("-")
    yy = y[2:]
    mi = str(int(m))

    # 명백히 다른 종류의 자료 제거
    reject_words = [
        "수출입 동향",
        "외국인직접투자",
        "수입규제",
        "비관세장벽",
        "세라믹의 날",
    ]

    if any(x in title for x in reject_words):
        return "REJECT"

    # 자동차 + 월간/산업/생산·내수·수출 구조
    auto = "자동차" in text

    industry = (
        "자동차산업" in text
        or "자동차 산업" in text
        or "자동차산업 동향" in text
        or "자동차 산업동향" in text
        or "자동차 산업 월간 동향" in text
        or "자동차산업 월간 동향" in text
    )

    metrics = sum(
        word in text
        for word in ["생산", "내수", "수출"]
    )

    # 제목에 목표 연월이 실제 존재하는지
    month_patterns = [
        rf"{re.escape(y)}\s*년\s*0?{mi}\s*월",
        rf"['‘’]?\s*{re.escape(yy)}\s*년\s*0?{mi}\s*월",
        rf"{re.escape(y)}[.\-/]\s*0?{mi}(?!\d)",
    ]

    month_match = any(
        re.search(p, title)
        for p in month_patterns
    )

    if auto and industry and month_match:
        return "STRONG"

    if auto and month_match and metrics >= 2:
        return "LIKELY"

    # 제목은 짧지만 본문에 해당 월 자동차산업 구조가 있는 경우
    if auto and industry and metrics >= 3:
        return "REVIEW"

    return "REJECT"


df["validation"] = df.apply(classify, axis=1)

rank = {
    "STRONG": 0,
    "LIKELY": 1,
    "REVIEW": 2,
    "REJECT": 9,
}

df["rank"] = df["validation"].map(rank)

valid = df[df["validation"] != "REJECT"].copy()

valid["score_num"] = pd.to_numeric(
    valid["score"],
    errors="coerce"
).fillna(0)

valid = valid.sort_values(
    ["period", "rank", "score_num"],
    ascending=[True, True, False]
)

valid.to_csv(
    OUT,
    index=False,
    encoding="utf-8-sig"
)

targets = sorted(set(df["period"]))
good_periods = sorted(set(valid["period"]))
missing = sorted(set(targets) - set(good_periods))

print("=" * 100)
print("MOTIE AUTOMOBILE MONTHLY FILTER")
print("=" * 100)

print("TARGET PERIODS :", len(targets))
print("VALID PERIODS  :", len(good_periods))
print("NO VALID       :", len(missing))
print()

for period in targets:
    x = valid[valid["period"] == period]

    if x.empty:
        print(f"{period} | NONE")
        continue

    best = x.iloc[0]

    print(
        f"{period} | {best['validation']:6} | "
        f"{normalize(best['title'])[:100]}"
    )

print()
print("=" * 100)
print("NO VALID CANDIDATE")
print("=" * 100)
print(" ".join(missing) if missing else "NONE")

print()
print("OUTPUT :", OUT)
