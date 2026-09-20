from pathlib import Path
import pandas as pd
import re
import time

SRC = Path("data/raw/motie/motie_search_full_2015_2025.csv")
OUT = Path("data/raw/motie/motie_body_validation_fast.csv")

print("=" * 100)
print("MOTIE BODY VALIDATION - FAST")
print("=" * 100)

t0 = time.time()

print("1. CSV 읽는 중...")
df = pd.read_csv(
    SRC,
    dtype=str,
    usecols=["title", "context", "url"]
).fillna("")

print(f"   ROWS : {len(df):,}")

# ---------------------------------------------------------
# 1. 전체 문자열을 딱 한 번 생성
# ---------------------------------------------------------
print("2. 자동차산업 자료 필터링...")

df["text"] = (
    df["title"].str.replace(r"\s+", " ", regex=True).str.strip()
    + " "
    + df["context"].str.replace(r"\s+", " ", regex=True).str.strip()
)

compact = df["text"].str.replace(" ", "", regex=False)

mask = (
    compact.str.contains("자동차산업", regex=False)
    | df["text"].str.contains("자동차 산업", regex=False)
)

auto = df.loc[mask, ["title", "context", "url", "text"]].copy()

print(f"   AUTOMOBILE ROWS : {len(auto):,}")

# ---------------------------------------------------------
# 2. 각 행에서 대상 연월 추출
# ---------------------------------------------------------
print("3. 대상 연월 식별...")

def detect_period(text):
    patterns = [
        # 2019년 4월
        r"(20\d{2})\s*년\s*(1[0-2]|[1-9])\s*월",

        # '19. 4월 / ’19.4월
        r"[‘’'\"]?\s*(\d{2})\s*[.]\s*(1[0-2]|[1-9])\s*월",
    ]

    found = []

    for i, pat in enumerate(patterns):
        for y, m in re.findall(pat, text):
            y = int(y)
            m = int(m)

            if i == 1:
                y += 2000

            if 2015 <= y <= 2025:
                p = f"{y:04d}-{m:02d}"
                if p not in found:
                    found.append(p)

    return found

auto["periods"] = auto["text"].map(detect_period)

auto = auto[auto["periods"].map(len) > 0].copy()

print(f"   PERIOD ROWS : {len(auto):,}")

# ---------------------------------------------------------
# 3. 한 행 → 여러 period 행으로 전개
# ---------------------------------------------------------
auto = auto.explode("periods").rename(columns={"periods": "period"})

auto = auto[
    (auto["period"] >= "2015-02")
    & (auto["period"] <= "2025-10")
].copy()

# ---------------------------------------------------------
# 4. 문서 우선순위
# ---------------------------------------------------------
def source_score(row):
    text = row["text"]
    c = text.replace(" ", "")

    score = 0

    if "자동차산업동향" in c:
        score += 100

    if "자동차산업월간동향" in c:
        score += 30

    if "생산" in text:
        score += 10

    if "내수" in text:
        score += 10

    if "수출" in text:
        score += 10

    return score

print("4. 후보 우선순위 계산...")

auto["score"] = auto.apply(source_score, axis=1)

# ---------------------------------------------------------
# 5. 생산/내수/수출 숫자 후보
# ---------------------------------------------------------
num = r"([0-9]{1,3}(?:,[0-9]{3})+)"

patterns = {
    "production_candidate":
        rf"(?:\(생산\)|생\s*산).{{0,120}}?{num}\s*대",

    "domestic_candidate":
        rf"(?:\(내수\)|내\s*수).{{0,120}}?{num}\s*대",

    "export_candidate":
        rf"(?:\(수출\)|수\s*출).{{0,120}}?{num}\s*대",
}

print("5. 생산 / 내수 / 수출 후보 추출...")

for col, pat in patterns.items():

    extracted = auto["text"].str.extract(
        pat,
        flags=re.I,
        expand=False
    )

    auto[col] = (
        extracted
        .str.replace(",", "", regex=False)
    )

# ---------------------------------------------------------
# 6. 월별 가장 강한 자료 선택
# ---------------------------------------------------------
print("6. 월별 본문 후보 정리...")

auto["complete"] = (
    auto["production_candidate"].notna()
    & auto["domestic_candidate"].notna()
    & auto["export_candidate"].notna()
)

auto = auto.sort_values(
    ["period", "complete", "score"],
    ascending=[True, False, False]
)

best = auto.groupby("period", as_index=False).first()

# ---------------------------------------------------------
# 7. 129개월 전체와 비교
# ---------------------------------------------------------
expected = pd.DataFrame({
    "period": pd.period_range(
        "2015-02",
        "2025-10",
        freq="M"
    ).astype(str)
})

result = expected.merge(
    best[
        [
            "period",
            "production_candidate",
            "domestic_candidate",
            "export_candidate",
            "score",
            "title",
            "url",
            "complete",
        ]
    ],
    on="period",
    how="left"
)

result["status"] = "NEEDS_REVIEW"

result.loc[
    result["complete"] == True,
    "status"
] = "BODY_CANDIDATE"

result.to_csv(
    OUT,
    index=False,
    encoding="utf-8-sig"
)

# ---------------------------------------------------------
# 결과
# ---------------------------------------------------------
body = (result["status"] == "BODY_CANDIDATE").sum()
review = (result["status"] == "NEEDS_REVIEW").sum()

print()
print("=" * 100)
print("RESULT")
print("=" * 100)

print("EXPECTED       :", len(result))
print("BODY CANDIDATE :", body)
print("NEEDS REVIEW   :", review)

print()
print("=== NEEDS REVIEW ===")

x = result[result["status"] == "NEEDS_REVIEW"]

print(
    " ".join(x["period"].tolist())
    if len(x)
    else "NONE"
)

print()
print(f"TIME   : {time.time()-t0:.1f} sec")
print("OUTPUT :", OUT)

print()
print("※ BODY_CANDIDATE = 아직 VERIFIED 아님")
print("※ MASTER 변경 없음")
