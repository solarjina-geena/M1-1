from pathlib import Path
import pandas as pd

# ============================================================
# [작업 목적]
# 공식 HWP 표에서 직접 확인한
# 2026-02 / 2026-08 값을 기존 BODY_VERIFIED 파일에 추가
#
# [검증 근거]
# - 실제 파일형식 HWP_OLE 확인
# - HWP BodyText 직접 추출
# - 해당 월 "표 3) 자동차 생산, 내수, 수출량" 확인
# - 생산량 / 내수판매량 / 수출량의 해당월 열 확인
#
# [안전]
# MASTER는 변경하지 않습니다.
# 기존 3~7월 검증값도 변경하지 않습니다.
# ============================================================

PATH = Path(
    "data/raw/motie/motie_2026_body_verified.csv"
)

# 기존 검증자료 읽기
df = pd.read_csv(
    PATH,
    dtype={"period": str}
)

# 새로 검증 완료한 2개월
new = pd.DataFrame([
    {
        "period": "2026-02",
        "production": 278248,
        "domestic": 123275,
        "export": 189885,
        "verification_status": "BODY_VERIFIED",
        "verification_method": "MOTIE_OFFICIAL_HWP_TABLE",
        "source_file": "2026-02_02.hwpx",
        "source_table":
            "표 3) '26년 2월 자동차 생산, 내수, 수출량",
        "note":
            "공식 HWP 표의 해당월 생산량/내수판매량/수출량 직접 확인"
    },
    {
        "period": "2026-08",
        "production": 206064,
        "domestic": 109920,
        "export": 146499,
        "verification_status": "BODY_VERIFIED",
        "verification_method": "MOTIE_OFFICIAL_HWP_TABLE",
        "source_file": "2026-08_02.hwpx",
        "source_table":
            "표 3) '26년 8월 자동차 생산, 내수, 수출량",
        "note":
            "공식 HWP 표의 해당월 생산량/내수판매량/수출량 직접 확인"
    }
])

# ============================================================
# [중복 안전장치]
# 같은 월이 이미 있으면 무조건 덮어쓰지 않습니다.
# 값이 같은지 먼저 확인합니다.
# ============================================================

for _, row in new.iterrows():

    old = df[df["period"] == row["period"]]

    if not old.empty:

        same = (
            int(old.iloc[0]["production"]) == row["production"]
            and int(old.iloc[0]["domestic"]) == row["domestic"]
            and int(old.iloc[0]["export"]) == row["export"]
        )

        if not same:
            raise ValueError(
                f"{row['period']} 기존 검증값과 충돌"
            )

        continue

    df = pd.concat(
        [df, pd.DataFrame([row])],
        ignore_index=True
    )

# 월 순서 정렬
df = df.sort_values("period").reset_index(drop=True)

# 같은 월 중복 여부 확인
if df["period"].duplicated().any():
    raise ValueError("중복 PERIOD 발견")

# 저장
df.to_csv(
    PATH,
    index=False,
    encoding="utf-8-sig"
)

# ============================================================
# [결과]
# 화면에는 짧게만 표시
# ============================================================

print("=" * 76)
print("MOTIE 2026 BODY VERIFIED STATUS")
print("=" * 76)

for _, r in df.iterrows():

    print(
        f"{r['period']} | "
        f"생산={int(r['production']):,} | "
        f"내수={int(r['domestic']):,} | "
        f"수출={int(r['export']):,} | "
        f"{r['verification_status']}"
    )

print("=" * 76)
print("BODY_VERIFIED :", len(df), "/ 8")
print("REMAINING     :", "2026-01")
print("OUTPUT        :", PATH)
print("MASTER        : UNCHANGED")
