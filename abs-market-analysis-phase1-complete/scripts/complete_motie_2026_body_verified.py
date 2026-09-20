from pathlib import Path
import pandas as pd

# ============================================================
# [작업 목적]
# 2026-01 공식 산업통상부 원문에서 확인한 값을
# 기존 2026 BODY_VERIFIED 파일에 추가합니다.
#
# [2026-01 검증 근거]
#
# 산업통상부 공식 보도자료:
# "2026년 1월 자동차수출 60.7억불, 역대 1월 중 2위"
#
# 공식 본문 표 3)
# '26년 1월 자동차 생산, 내수, 수출량
#
# 생산량      = 360,500
# 내수 판매량 = 120,787
# 수출량      = 246,574
#
# 산업부 공식 카드뉴스에서도 동일값 교차확인
#
# [안전]
# - 기존 2~8월 검증값 변경 안 함
# - 중복/충돌 검사
# - MASTER 변경 안 함
# ============================================================

PATH = Path(
    "data/raw/motie/motie_2026_body_verified.csv"
)

df = pd.read_csv(
    PATH,
    dtype={"period": str}
)

new_row = {
    "period": "2026-01",
    "production": 360500,
    "domestic": 120787,
    "export": 246574,
    "verification_status": "BODY_VERIFIED",
    "verification_method":
        "MOTIR_OFFICIAL_WEB_TABLE_CROSSCHECK",
    "source_file":
        "OFFICIAL_WEB_BODY",
    "source_table":
        "표 3) '26년 1월 자동차 생산, 내수, 수출량",
    "note":
        "산업통상부 공식 보도자료 본문 표 및 공식 카드뉴스 동일값 교차확인"
}

# ============================================================
# [중복/충돌 안전장치]
# ============================================================

old = df[
    df["period"] == new_row["period"]
]

if not old.empty:

    same = (
        int(old.iloc[0]["production"])
        == new_row["production"]
        and
        int(old.iloc[0]["domestic"])
        == new_row["domestic"]
        and
        int(old.iloc[0]["export"])
        == new_row["export"]
    )

    if not same:
        raise ValueError(
            "2026-01 기존 값과 공식 원문 값 충돌"
        )

else:

    df = pd.concat(
        [
            df,
            pd.DataFrame([new_row])
        ],
        ignore_index=True
    )

# ============================================================
# [최종 구조 검사]
# ============================================================

df = (
    df
    .sort_values("period")
    .reset_index(drop=True)
)

if df["period"].duplicated().any():
    raise ValueError(
        "중복 PERIOD 발견"
    )

expected = [
    f"2026-{m:02d}"
    for m in range(1, 9)
]

actual = df["period"].tolist()

missing = sorted(
    set(expected) - set(actual)
)

extra = sorted(
    set(actual) - set(expected)
)

# 저장
df.to_csv(
    PATH,
    index=False,
    encoding="utf-8-sig"
)

# ============================================================
# [짧은 최종 결과]
# ============================================================

print("=" * 78)
print("MOTIE 2026 BODY VERIFIED FINAL")
print("=" * 78)

for _, r in df.iterrows():

    print(
        f"{r['period']} | "
        f"생산={int(r['production']):,} | "
        f"내수={int(r['domestic']):,} | "
        f"수출={int(r['export']):,} | "
        f"{r['verification_status']}"
    )

print("=" * 78)
print("EXPECTED      :", 8)
print("BODY_VERIFIED :", len(df))
print(
    "MISSING       :",
    "NONE" if not missing else " ".join(missing)
)
print(
    "EXTRA         :",
    "NONE" if not extra else " ".join(extra)
)

if (
    len(df) == 8
    and not missing
    and not extra
    and
    (df["verification_status"]
        == "BODY_VERIFIED").all()
):
    print()
    print(
        ">>> 2026-01 ~ 2026-08 "
        "BODY VERIFIED 8 / 8 <<<"
    )

print()
print("OUTPUT :", PATH)
print("MASTER : UNCHANGED")
