from pathlib import Path
import pandas as pd

# ============================================================
# [작업 목적]
# 최종 MASTER 생성 직전의 마지막 안전검사입니다.
#
# 4개 데이터 묶음을 메모리에서만 합쳐서 확인합니다.
#
#   ① 기존 PDF 최종 데이터
#   ② 복구 검증 데이터
#   ③ 추가 원문 검증 24개월
#   ④ 2026 BODY_VERIFIED
#
# [검사 항목]
# - 중복 월
# - 생산/내수/수출 빈값
# - 분석기간 2016-01 ~ 2026-08 중 빠진 월
#
# [중요]
# 아직 MASTER 파일은 만들지 않습니다.
# ============================================================

from pathlib import Path
import pandas as pd

BASE = Path("data/raw/motie")

FILES = [
    ("BASE_FINAL", "motie_pdf_metrics_final.csv"),
    ("RECOVERED_VERIFIED", "motie_recovered_metrics_verified.csv"),
    ("24_VERIFIED", "motie_24_metrics_verified.csv"),
    ("2026_BODY_VERIFIED", "motie_2026_body_verified.csv"),
]

START = "2016-01"
END   = "2026-08"

frames = []

for source, filename in FILES:

    path = BASE / filename

    df = pd.read_csv(
        path,
        dtype={"period": str}
    )

    # --------------------------------------------------------
    # 분석에 필요한 핵심 컬럼만 사용
    # --------------------------------------------------------

    x = df[
        ["period", "production", "domestic", "export"]
    ].copy()

    x["source_group"] = source

    # --------------------------------------------------------
    # 최종 분석기간만 사용
    # 2015 자료는 원본에 그대로 보존되고 MASTER에서는 제외
    # --------------------------------------------------------

    x = x[
        (x["period"] >= START) &
        (x["period"] <= END)
    ]

    frames.append(x)


combined = pd.concat(
    frames,
    ignore_index=True
)

combined = combined.sort_values(
    "period"
).reset_index(drop=True)


# ============================================================
# [1] 중복 월 검사
# ============================================================

dup = combined[
    combined["period"].duplicated(False)
]


# ============================================================
# [2] 생산/내수/수출 빈값 검사
# ============================================================

missing_value = combined[
    combined[
        ["production", "domestic", "export"]
    ].isna().any(axis=1)
]


# ============================================================
# [3] 전체 월 목록 생성
# ============================================================

expected = pd.period_range(
    START,
    END,
    freq="M"
).astype(str).tolist()

actual = set(
    combined["period"].tolist()
)

missing_periods = [
    p for p in expected
    if p not in actual
]


# ============================================================
# [4] 예상하지 않은 기간 검사
# ============================================================

extra_periods = sorted(
    actual - set(expected)
)


# ============================================================
# [결과]
# ============================================================

print("=" * 100)
print("MOTIE FINAL PRE-MERGE GATE")
print("=" * 100)

print()
print("ANALYSIS RANGE :", START, "~", END)
print("EXPECTED MONTHS:", len(expected))
print("CURRENT ROWS   :", len(combined))
print("CURRENT PERIODS:", combined["period"].nunique())

print()
print("DUPLICATES     :", len(dup))
print("MISSING VALUES :", len(missing_value))
print("MISSING MONTHS :", len(missing_periods))
print("EXTRA MONTHS   :", len(extra_periods))


if not dup.empty:
    print()
    print("=== DUPLICATE MONTHS ===")
    print(
        dup[
            ["period", "source_group"]
        ].to_string(index=False)
    )


if not missing_value.empty:
    print()
    print("=== MISSING VALUE ROWS ===")
    print(
        missing_value.to_string(index=False)
    )


if missing_periods:
    print()
    print("=== MISSING MONTHS ===")
    print(" ".join(missing_periods))


if extra_periods:
    print()
    print("=== EXTRA MONTHS ===")
    print(" ".join(extra_periods))


print()
print("=" * 100)

if (
    len(dup) == 0
    and len(missing_value) == 0
    and len(missing_periods) == 0
    and len(extra_periods) == 0
    and len(combined) == len(expected)
):

    print(">>> PRE-MERGE GATE : PASS <<<")
    print()
    print(
        "2016-01 ~ 2026-08 "
        "월별 생산/내수/수출 데이터 연속성 정상"
    )

else:

    print(">>> PRE-MERGE GATE : REVIEW REQUIRED <<<")

print()
print("※ MASTER 파일 생성 안 함")
print("※ 기존 데이터 변경 없음")
print("=" * 100)
