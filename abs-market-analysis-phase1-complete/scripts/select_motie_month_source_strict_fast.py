from pathlib import Path
import pandas as pd
import re
import time

BASE = Path("data/raw/motie")
SRC  = BASE / "motie_search_full_2015_2025.csv"
OUT  = BASE / "motie_month_source_strict_fast.csv"

t0 = time.time()

print("=" * 100)
print("MOTIE STRICT MONTH SOURCE SELECTOR - FAST")
print("=" * 100)

# ---------------------------------------------------------
# 1. 필요한 컬럼만 한 번 읽기
# ---------------------------------------------------------
print("1. 검색자료 읽는 중...")

df = pd.read_csv(
    SRC,
    dtype=str,
    usecols=[
        "type",
        "title",
        "context",
        "url",
        "target_period"
    ]
).fillna("")

print(f"   ROWS : {len(df):,}")

# ---------------------------------------------------------
# 2. 문자열 정리 - 한 번만
# ---------------------------------------------------------
print("2. 자료 전처리 중...")

df["search_text"] = (
    df["title"].astype(str) + " " +
    df["context"].astype(str).str[:2500]
)

df["search_text"] = (
    df["search_text"]
    .str.replace("’", "'", regex=False)
    .str.replace("‘", "'", regex=False)
    .str.replace(r"\s+", " ", regex=True)
)

# 자동차 관련 자료만 먼저 축소
auto_mask = (
    df["search_text"].str.contains(
        "자동차",
        regex=False,
        na=False
    )
)

df = df[auto_mask].copy()

print(f"   AUTOMOBILE ROWS : {len(df):,}")

# ---------------------------------------------------------
# 3. 자료 자체의 '실적 대상 연월' 추출
#    게시일이 아니라 제목/본문의 자동차 동향 연월
# ---------------------------------------------------------
print("3. 실제 대상 월 판정 중...")

def detect_period(text):

    s = str(text)[:1800]

    patterns = [
        # 2021년 5월 자동차산업
        r"(20\d{2})\s*년\s*(1[0-2]|0?[1-9])\s*월",

        # '17. 5월 / ’17.5월
        r"['\"]?(\d{2})\s*[.]\s*(1[0-2]|0?[1-9])\s*월",

        # '17년 5월
        r"['\"]?(\d{2})\s*년\s*(1[0-2]|0?[1-9])\s*월",
    ]

    found = []

    for i, pat in enumerate(patterns):

        for m in re.finditer(pat, s):

            y = int(m.group(1))
            mo = int(m.group(2))

            if i > 0:
                y = 2000 + y

            if 2015 <= y <= 2025:
                found.append(
                    (m.start(), f"{y:04d}-{mo:02d}")
                )

    if not found:
        return ""

    # 문서 앞쪽에서 가장 먼저 명확히 언급된 연월
    found.sort(key=lambda x: x[0])

    return found[0][1]


df["detected_period"] = df["search_text"].map(detect_period)

# ---------------------------------------------------------
# 4. 자동차 월간동향 점수
# ---------------------------------------------------------
def quality_score(row):

    title = str(row["title"])
    text  = str(row["search_text"])

    score = 0

    if "자동차산업" in text.replace(" ", ""):
        score += 100

    if "월간 동향" in text or "월간동향" in text:
        score += 80

    if "생산" in text:
        score += 20

    if "내수" in text:
        score += 20

    if "수출" in text:
        score += 20

    if "완성차" in text:
        score += 20

    if "총괄" in text:
        score += 20

    # 검색결과 본문 페이지 우선
    u = str(row["url"])

    if "/kor/article/" in u:
        score += 30

    # 첨부파일도 허용
    if "/attach/down/" in u:
        score += 10

    # 자동차산업이 아닌 일반 수출입자료 감점
    compact_title = title.replace(" ", "")

    if (
        "수출입동향" in compact_title
        and "자동차산업" not in compact_title
    ):
        score -= 200

    # 친환경차 단독자료 감점
    if (
        "친환경차" in compact_title
        and "자동차산업" not in compact_title
    ):
        score -= 100

    return score


df["quality_score"] = df.apply(
    quality_score,
    axis=1
)

# ---------------------------------------------------------
# 5. 129개월 각각 후보 선택
# ---------------------------------------------------------
print("4. 129개월 원문 후보 선택 중...")

periods = pd.period_range(
    "2015-02",
    "2025-10",
    freq="M"
).astype(str)

results = []

for period in periods:

    # 가장 안전:
    # 실제 문서에서 감지한 월이 목표 월과 동일
    g = df[
        df["detected_period"] == period
    ].copy()

    source_method = "DETECTED_PERIOD"

    # 감지 실패 시에만 기존 target_period 보조 사용
    if len(g) == 0:

        g = df[
            (df["target_period"] == period)
            & (df["detected_period"] == "")
        ].copy()

        source_method = "TARGET_PERIOD_FALLBACK"

    if len(g) == 0:

        results.append({
            "period": period,
            "status": "NO_SOURCE"
        })

        continue

    g = g.sort_values(
        ["quality_score"],
        ascending=False
    )

    best = g.iloc[0]

    best_score = int(best["quality_score"])

    tied = g[
        g["quality_score"] == best_score
    ]

    # fallback은 자동확정하지 않음
    if source_method == "TARGET_PERIOD_FALLBACK":
        status = "SOURCE_REVIEW"

    elif len(tied) > 1:
        status = "SOURCE_REVIEW"

    else:
        status = "SOURCE_CANDIDATE"

    results.append({
        "period": period,
        "status": status,
        "source_method": source_method,
        "detected_period": best["detected_period"],
        "score": best_score,
        "candidate_count": len(g),
        "top_tied": len(tied),
        "title": best["title"],
        "context": best["context"],
        "url": best["url"],
        "type": best["type"]
    })


out = pd.DataFrame(results)

out.to_csv(
    OUT,
    index=False,
    encoding="utf-8-sig"
)

# ---------------------------------------------------------
# 6. 결과
# ---------------------------------------------------------
elapsed = time.time() - t0

print()
print("=" * 100)
print("RESULT")
print("=" * 100)

print("EXPECTED :", len(periods))

for name, count in out["status"].value_counts().items():
    print(f"{name:<20}: {count}")

print()
print("=== NEEDS REVIEW ===")

review = out[
    out["status"] != "SOURCE_CANDIDATE"
]

if len(review) == 0:
    print("NONE")
else:
    print(
        review[
            ["period", "status", "source_method"]
        ].to_string(index=False)
    )

print()
print(f"TIME   : {elapsed:.1f} sec")
print("OUTPUT :", OUT)

print()
print("※ 숫자 추출 안 함")
print("※ VERIFIED 처리 안 함")
print("※ MASTER 변경 없음")
