from pathlib import Path
import pandas as pd

# ============================================================
# [작업 목적]
# 2026-03 ~ 2026-07에서 확인 완료한 값을
# "검증 완료 데이터"로 별도 보존합니다.
#
# [검증 기준]
# 산업부 공식 HWPX
#   → 해당 월 자동차산업 표 확인
#   → 생산량 행 확인
#   → 내수 판매량 행 확인
#   → 수출량 행 확인
#   → 해당 월 열의 정확한 대수 확인
#
# [중요]
# BODY_VERIFIED 파일만 생성합니다.
# MASTER는 아직 변경하지 않습니다.
# ============================================================

BASE = Path("data/raw/motie")

OUT = BASE / "motie_2026_body_verified.csv"

rows = [
    ["2026-03", 387227, 164813, 259635],
    ["2026-04", 361926, 151693, 244990],
    ["2026-05", 329559, 127315, 230072],
    ["2026-06", 394210, 159725, 268169],
    ["2026-07", 352070, 139256, 244181],
]

df = pd.DataFrame(
    rows,
    columns=[
        "period",
        "production",
        "domestic",
        "export"
    ]
)

# ------------------------------------------------------------
# [검증 근거]
# 숫자만 저장하지 않고
# 어떻게 확인했는지도 같이 남깁니다.
# ------------------------------------------------------------

df["verification_status"] = "BODY_VERIFIED"

df["verification_method"] = (
    "MOTIE_OFFICIAL_HWPX_TABLE"
)

df["source_file"] = df["period"].apply(
    lambda x: f"{x}_02.hwpx"
)

df["source_table"] = df["period"].apply(
    lambda x:
    f"표 3) '{x[2:4]}년 {int(x[-2:])}월 "
    "자동차 생산, 내수, 수출량"
)

df["note"] = (
    "공식 HWPX 표의 해당월 생산량/내수판매량/"
    "수출량 직접 확인"
)

# ------------------------------------------------------------
# [저장]
# ------------------------------------------------------------

df.to_csv(
    OUT,
    index=False,
    encoding="utf-8-sig"
)

# ------------------------------------------------------------
# [짧은 결과만 출력]
# ------------------------------------------------------------

print("=" * 76)
print("MOTIE 2026 BODY VERIFIED")
print("=" * 76)

for _, r in df.iterrows():

    print(
        f"{r['period']} | "
        f"생산={r['production']:,} | "
        f"내수={r['domestic']:,} | "
        f"수출={r['export']:,} | "
        f"{r['verification_status']}"
    )

print("=" * 76)
print("VERIFIED :", len(df))
print("OUTPUT   :", OUT)
print()
print("MASTER   : UNCHANGED")
