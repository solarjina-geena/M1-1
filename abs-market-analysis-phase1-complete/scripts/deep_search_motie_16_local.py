from pathlib import Path
import pandas as pd
import re
import time

BASE = Path("data/raw/motie")

SEARCH = BASE / "motie_search_full_2015_2025.csv"
TARGET = BASE / "motie_source_deep_search_targets.csv"
OUT    = BASE / "motie_16_deep_search_candidates.csv"

t0 = time.time()

print("=" * 105)
print("MOTIE 16 PERIOD DEEP SEARCH - LOCAL INDEX")
print("=" * 105)

# ---------------------------------------------------------
# 1. 대상 16개월
# ---------------------------------------------------------
targets = pd.read_csv(TARGET, dtype=str).fillna("")
periods = targets["period"].drop_duplicates().tolist()

print("TARGETS :", len(periods))
print(" ".join(periods))

# ---------------------------------------------------------
# 2. 검색 인덱스 한 번만 읽기
# ---------------------------------------------------------
print()
print("1. SEARCH INDEX 읽는 중...")

df = pd.read_csv(
    SEARCH,
    dtype=str,
    usecols=[
        "page_no",
        "currentPage",
        "year_hint",
        "type",
        "title",
        "context",
        "url",
        "target_period"
    ]
).fillna("")

print(f"   ROWS : {len(df):,}")

# ---------------------------------------------------------
# 3. 검색용 문자열 한 번만 생성
# ---------------------------------------------------------
print("2. 검색 문자열 생성 중...")

df["text"] = (
    df["title"].astype(str) + " " +
    df["context"].astype(str)
)

df["text_norm"] = (
    df["text"]
    .str.replace("’", "'", regex=False)
    .str.replace("‘", "'", regex=False)
    .str.replace(r"\s+", " ", regex=True)
)

df["compact"] = (
    df["text_norm"]
    .str.replace(" ", "", regex=False)
)

# ---------------------------------------------------------
# 4. 자동차 관련 행으로 먼저 축소
# ---------------------------------------------------------
auto = df[
    df["text_norm"].str.contains(
        "자동차",
        regex=False,
        na=False
    )
].copy()

print(f"   AUTOMOBILE ROWS : {len(auto):,}")

# ---------------------------------------------------------
# 5. 각 대상월 점수 계산
# ---------------------------------------------------------
all_results = []

for period in periods:

    year, month = period.split("-")
    yy = year[-2:]
    m = int(month)

    # 해당 연월을 표현할 수 있는 패턴
    period_patterns = [
        rf"{year}\s*년\s*0?{m}\s*월",
        rf"'{yy}\s*년\s*0?{m}\s*월",
        rf"'{yy}\s*[.]\s*0?{m}\s*월",
        rf"{year}[-./]0?{m}(?!\d)"
    ]

    period_re = re.compile(
        "|".join(period_patterns),
        flags=re.I
    )

    # 대상월 언급이 있는 자동차 자료만
    g = auto[
        auto["text_norm"].str.contains(
            period_re,
            na=False
        )
    ].copy()

    rows = []

    for idx, r in g.iterrows():

        title = str(r["title"])
        text  = str(r["text_norm"])
        compact = str(r["compact"])
        url   = str(r["url"])

        score = 0
        reasons = []

        # ------------------------------
        # 대상 연월
        # ------------------------------
        if period_re.search(title):
            score += 120
            reasons.append("PERIOD_IN_TITLE")

        elif period_re.search(text[:1500]):
            score += 60
            reasons.append("PERIOD_IN_BODY")

        # ------------------------------
        # 자동차산업 동향 문서
        # ------------------------------
        monthly_terms = [
            "자동차산업동향",
            "자동차산업월간동향",
            "자동차산업월간동향(잠정)",
            "국내자동차산업동향",
            "국내자동차산업월간동향"
        ]

        if any(x in compact for x in monthly_terms):
            score += 180
            reasons.append("AUTO_MONTHLY_REPORT")

        elif "자동차산업" in compact:
            score += 80
            reasons.append("AUTO_INDUSTRY")

        # 상반기 + 해당 월 자료 허용
        if (
            "상반기" in text
            and f"{m}월" in text
            and "자동차" in text
        ):
            score += 60
            reasons.append("HALF_YEAR_MONTH_REPORT")

        # ------------------------------
        # 핵심 지표 문맥
        # ------------------------------
        hits = 0

        for word in ["생산", "내수", "수출"]:
            if word in text:
                hits += 1

        score += hits * 20

        if hits == 3:
            reasons.append("PDE_ALL")

        if "완성차" in text:
            score += 20
            reasons.append("COMPLETE_VEHICLE")

        if "총괄" in text:
            score += 15
            reasons.append("SUMMARY_TABLE")

        # ------------------------------
        # URL 성격
        # ------------------------------
        if "/kor/article/" in url:
            score += 25
            reasons.append("ARTICLE")

        if "/attach/down/" in url:
            score += 15
            reasons.append("ATTACHMENT")

        # ------------------------------
        # 잘못된 자료 강한 감점
        # ------------------------------
        wrong_terms = [
            "수출입동향",
            "FTA현안",
            "자유무역협정현안",
            "배터리업계",
            "그린수소",
            "에너지효율등급",
            "IPEF"
        ]

        for bad in wrong_terms:
            if bad in compact and "자동차산업동향" not in compact:
                score -= 250
                reasons.append("BAD_" + bad)

        # 친환경차 단독 자료
        if (
            "친환경차" in compact
            and "자동차산업" not in compact
        ):
            score -= 80
            reasons.append("ECO_ONLY")

        rows.append({
            "period": period,
            "score": score,
            "title": title,
            "context": r["context"],
            "url": url,
            "type": r["type"],
            "target_period_original": r["target_period"],
            "reason": ";".join(reasons)
        })

    if rows:

        tmp = pd.DataFrame(rows)

        tmp = tmp.sort_values(
            ["score"],
            ascending=False
        )

        # URL/제목 중복 제거
        tmp = tmp.drop_duplicates(
            subset=["title", "url"]
        )

        # 월별 상위 10개만 저장
        tmp = tmp.head(10).copy()

        tmp["rank"] = range(1, len(tmp) + 1)

        all_results.append(tmp)

# ---------------------------------------------------------
# 6. 저장
# ---------------------------------------------------------
if all_results:
    out = pd.concat(all_results, ignore_index=True)
else:
    out = pd.DataFrame()

out.to_csv(
    OUT,
    index=False,
    encoding="utf-8-sig"
)

# ---------------------------------------------------------
# 7. 화면에는 월별 TOP 3만
# ---------------------------------------------------------
print()
print("=" * 105)
print("DEEP SEARCH RESULT - TOP 3")
print("=" * 105)

found_periods = set()

for period in periods:

    g = out[out["period"] == period].copy()

    print()
    print("-" * 105)
    print("PERIOD :", period)

    if len(g) == 0:
        print("NO CANDIDATE")
        continue

    found_periods.add(period)

    for _, r in g.head(3).iterrows():

        print(
            f'[{r["rank"]}] SCORE={r["score"]}'
        )
        print(
            "TITLE :",
            str(r["title"])[:500]
        )
        print(
            "REASON:",
            r["reason"]
        )
        print(
            "URL   :",
            r["url"]
        )
        print()

missing = [
    p for p in periods
    if p not in found_periods
]

print("=" * 105)
print("SUMMARY")
print("=" * 105)

print("TARGET       :", len(periods))
print("FOUND        :", len(found_periods))
print("NO CANDIDATE :", len(missing))
print("TIME         :", f"{time.time()-t0:.1f} sec")

if missing:
    print()
    print("=== STILL NO CANDIDATE ===")
    print(" ".join(missing))

print()
print("OUTPUT :", OUT)
print()
print("※ MASTER 변경 없음")
print("※ 후보만 검색")
print("※ 자동 VERIFIED 처리 없음")
