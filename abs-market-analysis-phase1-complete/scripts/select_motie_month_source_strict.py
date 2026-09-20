from pathlib import Path
import pandas as pd
import re

BASE = Path("data/raw/motie")

INDEX = BASE / "motie_search_full_2015_2025.csv"
OUT   = BASE / "motie_month_source_strict.csv"

print("=" * 100)
print("MOTIE STRICT MONTH SOURCE SELECTOR")
print("=" * 100)

# ---------------------------------------------------------
# 검색 인덱스
# ---------------------------------------------------------
df = pd.read_csv(
    INDEX,
    dtype=str,
    usecols=[
        "year_hint",
        "type",
        "title",
        "context",
        "url",
        "target_period"
    ]
).fillna("")

# 중복 최소화
df = df.drop_duplicates(
    subset=["title", "url", "target_period"]
).copy()


def normalize(s):
    s = str(s)
    s = s.replace("’", "'").replace("‘", "'")
    s = re.sub(r"\s+", " ", s)
    return s.strip()


def month_patterns(period):
    y, m = map(int, period.split("-"))
    yy = str(y)[2:]

    return [
        rf"{y}\s*년\s*0?{m}\s*월",
        rf"'{yy}\s*년?\s*\.?\s*0?{m}\s*월",
        rf"{yy}\s*년\s*0?{m}\s*월",
    ]


def wrong_month_penalty(text, period):
    """
    제목/초반부가 다른 연월을 명시하면 강하게 제외.
    """
    y, m = map(int, period.split("-"))

    head = normalize(text)[:500]

    found = []

    # 4자리 연도
    for yy, mm in re.findall(
        r"(20\d{2})\s*년?\s*[.\-/]?\s*(\d{1,2})\s*월",
        head
    ):
        found.append((int(yy), int(mm)))

    # '17. 3월 형태
    for yy, mm in re.findall(
        r"['\"]?(\d{2})\s*년?\s*[.\-/]\s*(\d{1,2})\s*월",
        head
    ):
        yy = int(yy)
        yy = 2000 + yy
        found.append((yy, int(mm)))

    if not found:
        return 0

    if (y, m) in found:
        return 0

    return -500


def score(row, period):

    title = normalize(row["title"])
    ctx   = normalize(row["context"])

    text = title + " " + ctx

    score = 0

    # 정확한 대상 연월
    pats = month_patterns(period)

    if any(re.search(p, title) for p in pats):
        score += 500

    elif any(re.search(p, text[:1500]) for p in pats):
        score += 250

    else:
        return -9999

    # 자동차산업 자료 여부
    if re.search(r"자동차\s*산업", text):
        score += 150

    if re.search(r"자동차산업\s*(월간\s*)?동향", text):
        score += 200

    # 생산/내수/수출이 함께 존재
    if "생산" in text:
        score += 30

    if "내수" in text:
        score += 30

    if "수출" in text:
        score += 30

    # 총괄표/전체 자료 우선
    if "총괄" in text:
        score += 40

    if "완성차" in text:
        score += 30

    # 잘못된 자료 감점
    if "수출입 동향" in title and "자동차산업" not in title:
        score -= 300

    if "친환경차" in title and "자동차산업" not in title:
        score -= 200

    # 다른 연월 제목 강한 감점
    score += wrong_month_penalty(title, period)

    return score


# ---------------------------------------------------------
# 129개월
# 2015-02 ~ 2025-10
# ---------------------------------------------------------
periods = pd.period_range(
    "2015-02",
    "2025-10",
    freq="M"
).astype(str)

results = []

for period in periods:

    # target_period가 있는 행을 우선 사용
    g = df[df["target_period"] == period].copy()

    # target_period가 없어도 본문에서 정확 연월 탐색
    if len(g) == 0:
        pats = month_patterns(period)

        mask = df.apply(
            lambda r: any(
                re.search(
                    p,
                    normalize(r["title"]) + " " +
                    normalize(r["context"])[:1500]
                )
                for p in pats
            ),
            axis=1
        )

        g = df[mask].copy()

    if len(g) == 0:
        results.append({
            "period": period,
            "status": "NO_SOURCE"
        })
        continue

    g["strict_score"] = g.apply(
        lambda r: score(r, period),
        axis=1
    )

    g = g[
        g["strict_score"] > 0
    ].sort_values(
        "strict_score",
        ascending=False
    )

    if len(g) == 0:
        results.append({
            "period": period,
            "status": "NO_VALID_SOURCE"
        })
        continue

    best = g.iloc[0]

    # 같은 점수 후보가 여러 개인지
    top_score = best["strict_score"]

    tied = g[
        g["strict_score"] == top_score
    ]

    status = (
        "SOURCE_CANDIDATE"
        if len(tied) == 1
        else "SOURCE_REVIEW"
    )

    results.append({
        "period": period,
        "status": status,
        "score": top_score,
        "candidate_count": len(g),
        "top_tied": len(tied),
        "title": best["title"],
        "context": best["context"],
        "url": best["url"],
        "type": best["type"],
    })


out = pd.DataFrame(results)

out.to_csv(
    OUT,
    index=False,
    encoding="utf-8-sig"
)

print()
print("=" * 100)
print("RESULT")
print("=" * 100)

print("EXPECTED :", len(periods))

for status, n in out["status"].value_counts().items():
    print(f"{status:<22}: {n}")

print()
print("=== REVIEW ===")

review = out[
    out["status"] != "SOURCE_CANDIDATE"
]

if len(review) == 0:
    print("NONE")
else:
    print(
        review[
            ["period", "status"]
        ].to_string(index=False)
    )

print()
print("OUTPUT :", OUT)

print()
print("IMPORTANT")
print("- 아직 생산/내수/수출 추출 안 함")
print("- 아직 VERIFIED 처리 안 함")
print("- MASTER 변경 없음")
