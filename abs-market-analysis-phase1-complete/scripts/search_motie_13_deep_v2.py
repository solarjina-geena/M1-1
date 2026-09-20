from pathlib import Path
import pandas as pd
import re
import time

BASE = Path("data/raw/motie")

SRC = BASE / "motie_search_full_2015_2025.csv"
GATE = BASE / "motie_16_period_gate_v2.csv"
OUT = BASE / "motie_13_deep_candidates_v2.csv"

print("=" * 100)
print("MOTIE 13 DEEP CANDIDATE SEARCH V2")
print("=" * 100)

# --------------------------------------------------
# TARGET
# --------------------------------------------------
g = pd.read_csv(GATE, dtype=str).fillna("")

targets = sorted(
    g.loc[
        g["period_gate_v2"].ne("PERIOD_MATCH"),
        "period"
    ].unique()
)

print("TARGETS :", len(targets))
print(" ".join(targets))
print()

# --------------------------------------------------
# SOURCE
# --------------------------------------------------
print("1. 전체 검색 인덱스 읽는 중...")
t0 = time.time()

df = pd.read_csv(
    SRC,
    dtype=str,
    low_memory=False
).fillna("")

print(f"   ROWS : {len(df):,}")
print(f"   TIME : {time.time()-t0:.1f} sec")

for c in ["title", "context", "url", "type"]:
    if c not in df.columns:
        df[c] = ""

# --------------------------------------------------
# NORMALIZE
# --------------------------------------------------
def norm(s):
    s = str(s)
    s = s.replace("’", "'").replace("‘", "'")
    s = re.sub(r"\s+", " ", s)
    return s.strip()

df["_title"] = df["title"].map(norm)
df["_context"] = df["context"].map(norm)

rows = []

# --------------------------------------------------
# SEARCH
# --------------------------------------------------
print()
print("2. 후보 탐색...")

for period in targets:

    year, month = map(int, period.split("-"))
    yy = str(year)[-2:]

    # 제목의 앞부분을 가장 중요하게 본다.
    # context 전체는 보조 점수만 준다.
    y1 = rf"{year}\s*년"
    y2 = rf"['`]?\s*{yy}\s*년"

    m1 = rf"0?{month}\s*월"

    for idx, r in df.iterrows():

        title = r["_title"]
        context = r["_context"]

        head = title[:220]
        body_head = context[:600]

        score = 0
        reasons = []

        # 자동차산업 문서
        auto_title = (
            "자동차산업" in head.replace(" ", "")
            or "자동차 산업" in head
        )

        if auto_title:
            score += 120
            reasons.append("AUTO_TITLE")

        # 정확한 연도 + 월이 제목 앞부분에 있는지
        year_title = (
            re.search(y1, head)
            or re.search(y2, head)
        )

        month_title = re.search(m1, head)

        if year_title:
            score += 100
            reasons.append("YEAR_TITLE")

        if month_title:
            score += 80
            reasons.append("MONTH_TITLE")

        # 6월 상반기 문서
        if (
            month == 6
            and "상반기" in head
            and re.search(r"(및|·|/)\s*6\s*월", head)
        ):
            score += 100
            reasons.append("HALFYEAR")

        # 본문 앞부분 보조 확인
        year_context = (
            re.search(y1, body_head)
            or re.search(y2, body_head)
        )

        month_context = re.search(m1, body_head)

        if year_context:
            score += 25
            reasons.append("YEAR_CONTEXT")

        if month_context:
            score += 20
            reasons.append("MONTH_CONTEXT")

        # 잘못된 문서 유형 감점
        wrong = (
            "수출입 동향" in head
            or "수출입동향" in head
        )

        if wrong:
            score -= 180
            reasons.append("WRONG_DOC")

        # 최소한 자동차 관련이어야 후보
        automobile_any = (
            "자동차" in head
            or "자동차" in body_head
        )

        if not automobile_any:
            continue

        # 너무 약한 후보 제외
        if score < 100:
            continue

        rows.append({
            "period": period,
            "score": score,
            "reason": "|".join(reasons),
            "type": r.get("type", ""),
            "title": r.get("title", ""),
            "context": r.get("context", ""),
            "url": r.get("url", "")
        })

res = pd.DataFrame(rows)

if res.empty:
    print("후보 없음")
    raise SystemExit

# 중복 제거
res = res.drop_duplicates(
    subset=["period", "url", "title"]
)

res = res.sort_values(
    ["period", "score"],
    ascending=[True, False]
)

# 월별 상위 15개만
res = (
    res.groupby("period", group_keys=False)
       .head(15)
       .reset_index(drop=True)
)

res.to_csv(
    OUT,
    index=False,
    encoding="utf-8-sig"
)

# --------------------------------------------------
# RESULT
# --------------------------------------------------
print()
print("=" * 100)
print("RESULT")
print("=" * 100)

found = sorted(res["period"].unique())
missing = sorted(set(targets) - set(found))

print("TARGETS     :", len(targets))
print("FOUND       :", len(found))
print("NO CANDIDATE:", len(missing))
print("CANDIDATES  :", len(res))

print()
print("=== BEST CANDIDATE ===")

for period in targets:

    x = res[res["period"] == period]

    if x.empty:
        print(period, "| NONE")
        continue

    r = x.iloc[0]

    print(
        period,
        "| SCORE", r["score"],
        "|", str(r["title"])[:160]
    )

print()
print("=== NO CANDIDATE ===")
print(" ".join(missing) if missing else "NONE")

print()
print("OUTPUT :", OUT)
print()
print("※ 후보 검색만 수행")
print("※ BODY_VERIFIED 아님")
print("※ MASTER 변경 없음")
