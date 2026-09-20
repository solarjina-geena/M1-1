from pathlib import Path
import pandas as pd

# ============================================================
# [작업 목적]
# 과거 MOTIE 데이터 중 서로 겹치는 월의 값이
# 같은지 / 다른지 확인합니다.
#
# [왜 필요한가?]
# 단순히 CSV를 이어붙이면 같은 월에 서로 다른 값이
# 존재할 가능성이 있습니다.
#
# 따라서 MASTER 생성 전에:
#
#   1. 어떤 월이 여러 파일에 존재하는지
#   2. 생산/내수/수출 값이 같은지
#   3. 어떤 파일을 우선해야 하는지
#
# 를 먼저 확인합니다.
#
# [중요]
# MASTER 생성 안 함
# 기존 CSV 수정 안 함
# ============================================================

BASE = Path("data/raw/motie")

FILES = [
    "motie_pdf_metrics_final.csv",
    "motie_recovered_metrics_verified.csv",
    "motie_24_metrics_verified.csv",
]

records = []

for filename in FILES:

    path = BASE / filename

    if not path.exists():
        print("FILE NOT FOUND :", filename)
        continue

    df = pd.read_csv(
        path,
        dtype={"period": str}
    )

    for _, r in df.iterrows():

        period = str(r["period"])

        # 최종 분석기간 시작 이전은 이번 비교에서 제외
        if period < "2016-01":
            continue

        records.append({
            "period": period,
            "source": filename,
            "production": r.get("production"),
            "domestic": r.get("domestic"),
            "export": r.get("export"),
        })


all_df = pd.DataFrame(records)

print("=" * 100)
print("MOTIE HISTORICAL SOURCE CONFLICT CHECK")
print("=" * 100)

# ============================================================
# [1] 여러 파일에 동시에 존재하는 월만 조사
# ============================================================

counts = (
    all_df.groupby("period")["source"]
    .nunique()
)

overlap_periods = counts[
    counts > 1
].index.tolist()

print()
print("OVERLAP PERIODS :", len(overlap_periods))


# ============================================================
# [2] 겹치는 월에서 값이 실제로 다른지 검사
# ============================================================

conflicts = []
matches = []

for period in overlap_periods:

    x = all_df[
        all_df["period"] == period
    ].copy()

    # 비교용 값
    value_sets = set()

    for _, r in x.iterrows():

        def norm(v):
            if pd.isna(v):
                return None
            return int(float(v))

        value_sets.add((
            norm(r["production"]),
            norm(r["domestic"]),
            norm(r["export"]),
        ))

    if len(value_sets) == 1:
        matches.append(period)
    else:
        conflicts.append(period)


print("VALUE MATCH     :", len(matches))
print("VALUE CONFLICT  :", len(conflicts))


# ============================================================
# [3] 충돌 월만 상세 출력
#
# 정상 일치 월은 수십 줄 출력하지 않습니다.
# ============================================================

if conflicts:

    print()
    print("=== CONFLICT PERIODS ===")

    for period in conflicts:

        print()
        print(period)

        x = all_df[
            all_df["period"] == period
        ]

        for _, r in x.iterrows():

            def fmt(v):
                if pd.isna(v):
                    return "NA"
                return f"{int(float(v)):,}"

            print(
                "  "
                f"{r['source']} | "
                f"P={fmt(r['production'])} | "
                f"D={fmt(r['domestic'])} | "
                f"E={fmt(r['export'])}"
            )

else:

    print()
    print("CONFLICT PERIODS : NONE")


# ============================================================
# [4] 각 파일이 단독으로 가지고 있는 월 수
# ============================================================

print()
print("=== SOURCE COVERAGE ===")

for filename in FILES:

    x = all_df[
        all_df["source"] == filename
    ]

    if x.empty:
        continue

    unique_only = 0

    for period in x["period"].unique():

        if counts.get(period, 0) == 1:
            unique_only += 1

    print(
        f"{filename} | "
        f"PERIODS={x['period'].nunique()} | "
        f"UNIQUE_ONLY={unique_only}"
    )


print()
print("=" * 100)
print("※ 비교만 수행")
print("※ 기존 파일 변경 없음")
print("※ MASTER 변경 없음")
print("=" * 100)
