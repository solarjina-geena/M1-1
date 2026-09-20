from pathlib import Path
import pandas as pd

# ============================================================
# [작업 목적]
# MASTER 병합 전에 현재 보유한 MOTIE 지표 CSV를 조사합니다.
#
# 확인할 것:
# 1. 파일별 기간 범위
# 2. 행 수 / 월 수
# 3. 생산·내수·수출 완성 행 수
# 4. BODY_VERIFIED 등 검증상태 존재 여부
# 5. 2026 자료 포함 여부
#
# [중요]
# 아직 어떤 파일도 MASTER로 선택하지 않습니다.
# 파일 수정도 하지 않습니다.
# ============================================================

BASE = Path("data/raw/motie")

files = sorted(
    p for p in BASE.glob("*.csv")
    if (
        "metric" in p.name.lower()
        or "verified" in p.name.lower()
    )
)

print("=" * 100)
print("MOTIE PRE-MERGE DATA INVENTORY")
print("=" * 100)

for path in files:

    try:
        df = pd.read_csv(path)
    except Exception:
        continue

    # 지표 데이터가 아닌 CSV 제외
    required = {
        "period",
        "production",
        "domestic",
        "export"
    }

    if not required.issubset(df.columns):
        continue

    periods = (
        df["period"]
        .dropna()
        .astype(str)
    )

    complete = df[
        ["production", "domestic", "export"]
    ].notna().all(axis=1).sum()

    # 검증 상태 집계
    if "verification_status" in df.columns:

        verified = (
            df["verification_status"]
            .astype(str)
            .str.contains(
                "VERIFIED",
                case=False,
                na=False
            )
            .sum()
        )

    else:
        verified = 0

    print()
    print("FILE     :", path.name)
    print("ROWS     :", len(df))
    print("PERIODS  :", periods.nunique())

    if len(periods):
        print(
            "RANGE    :",
            periods.min(),
            "~",
            periods.max()
        )

    print("COMPLETE :", complete)
    print("VERIFIED :", verified)

print()
print("=" * 100)
print("※ 조사만 수행")
print("※ MASTER 변경 없음")
print("=" * 100)
