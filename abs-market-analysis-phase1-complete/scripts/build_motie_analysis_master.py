from pathlib import Path
import pandas as pd

# ============================================================
# [작업 목적]
# 현재 확보된 MOTIE 데이터를 이용해
# 분석용 MASTER를 생성합니다.
#
# ★ 없는 월은 억지로 채우지 않습니다.
# ★ 생산/내수/수출 3개 값이 모두 있는 데이터만 사용합니다.
# ★ 추정값 생성 안 함
#
# 분석기간:
# 2016-01 ~ 2026-08
# ============================================================

BASE = Path("data/raw/motie")

START = "2016-01"
END   = "2026-08"

OUTPUT = BASE / "motie_monthly_master.csv"


# ============================================================
# [파일 우선순위]
#
# 숫자가 같은 월에 여러 파일에서 발견될 경우
# 아래 순서가 높은 자료를 사용합니다.
#
# 1. 2026 공식 본문 검증
# 2. 추가 검증 24개월
# 3. 복구 검증 자료
# 4. 기존 FINAL
# 5. 기타 기존 완성 데이터
#
# ※ 동일 월 값이 서로 다르면 자동 선택하지 않고
#    CONFLICT로 중단합니다.
# ============================================================

PRIORITY = {
    "motie_2026_body_verified.csv": 100,
    "motie_24_metrics_verified.csv": 90,
    "motie_recovered_metrics_verified.csv": 80,
    "motie_pdf_metrics_final.csv": 70,
    "motie_recovered_metrics_test.csv": 50,
    "motie_pdf_metrics_v2.csv": 40,
    "motie_pdf_metrics.csv": 30,
    "motie_pdf_metrics_v3.csv": 20,
}


# ============================================================
# [1] 기존 CSV 전체 수집
# ============================================================

records = []

for path in BASE.glob("*.csv"):

    if path.name == OUTPUT.name:
        continue

    try:
        df = pd.read_csv(
            path,
            dtype={"period": str}
        )
    except Exception:
        continue

    required = {
        "period",
        "production",
        "domestic",
        "export"
    }

    if not required.issubset(df.columns):
        continue

    for _, r in df.iterrows():

        period = str(r["period"])

        if not (START <= period <= END):
            continue

        # 생산/내수/수출 중 하나라도 없으면
        # 분석 MASTER 후보에서 제외
        if pd.isna(r["production"]) \
           or pd.isna(r["domestic"]) \
           or pd.isna(r["export"]):
            continue

        records.append({
            "period": period,
            "production": int(float(r["production"])),
            "domestic": int(float(r["domestic"])),
            "export": int(float(r["export"])),
            "source_file": path.name,
            "priority": PRIORITY.get(path.name, 10)
        })


raw = pd.DataFrame(records)


# ============================================================
# [2] 월별 값 충돌 검사
#
# 같은 월에 서로 다른 숫자가 있으면
# 자동 병합하지 않습니다.
# ============================================================

selected = []
conflicts = []

for period, g in raw.groupby("period"):

    value_sets = (
        g[
            ["production", "domestic", "export"]
        ]
        .drop_duplicates()
    )

    if len(value_sets) > 1:

        # 서로 다른 값이 발견된 경우
        # 우선순위가 가장 높은 자료를 확인
        top_priority = g["priority"].max()

        top = g[
            g["priority"] == top_priority
        ]

        top_values = (
            top[
                ["production", "domestic", "export"]
            ]
            .drop_duplicates()
        )

        # 최고 우선순위 안에서도 값이 다르면
        # 자동 결정하지 않음
        if len(top_values) > 1:

            conflicts.append(period)
            continue

    # 가장 신뢰도가 높은 자료 선택
    best = (
        g.sort_values(
            "priority",
            ascending=False
        )
        .iloc[0]
    )

    selected.append(best)


master = pd.DataFrame(selected)

master = (
    master
    .sort_values("period")
    .reset_index(drop=True)
)


# ============================================================
# [3] 충돌이 있으면 저장 중단
# ============================================================

if conflicts:

    print("=" * 80)
    print("MASTER BUILD STOPPED")
    print("=" * 80)

    print(
        "UNRESOLVED CONFLICT :",
        " ".join(conflicts)
    )

    print()
    print("MASTER 저장 안 함")

    raise SystemExit(1)


# ============================================================
# [4] 없는 월 확인
# ============================================================

expected = (
    pd.period_range(
        START,
        END,
        freq="M"
    )
    .astype(str)
    .tolist()
)

actual = set(master["period"])

missing = [
    p for p in expected
    if p not in actual
]


# ============================================================
# [5] 분석용 MASTER 저장
# ============================================================

master[
    [
        "period",
        "production",
        "domestic",
        "export",
        "source_file"
    ]
].to_csv(
    OUTPUT,
    index=False,
    encoding="utf-8-sig"
)


# ============================================================
# [6] 최종 결과
# ============================================================

print("=" * 90)
print("MOTIE ANALYSIS MASTER")
print("=" * 90)

print("ANALYSIS RANGE :", START, "~", END)
print("EXPECTED       :", len(expected))
print("AVAILABLE      :", len(master))
print("MISSING        :", len(missing))

print()

if missing:
    print(
        "MISSING MONTHS :",
        " ".join(missing)
    )
else:
    print("MISSING MONTHS : NONE")

print()
print("OUTPUT :", OUTPUT)

print()
print(">>> MASTER READY FOR ANALYSIS <<<")
print()
print(
    "※ 없는 월은 추정하지 않음"
)
print(
    "※ 향후 자료 확보 시 해당 월만 추가 가능"
)
print("=" * 90)
