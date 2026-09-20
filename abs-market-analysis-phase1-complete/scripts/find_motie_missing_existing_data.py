from pathlib import Path
import pandas as pd

# ============================================================
# [작업 목적]
# PRE-MERGE에서 빠진 24개월이
# 기존 CSV 어딘가에 이미 존재하는지 전부 찾습니다.
#
# ★ 숫자를 새로 추출하지 않습니다.
# ★ 원문 검색하지 않습니다.
# ★ MASTER 변경하지 않습니다.
#
# 즉, "우리가 이미 찾아놓은 데이터를 놓친 것인지"만 확인합니다.
# ============================================================

BASE = Path("data/raw/motie")

TARGETS = """
2016-02 2016-05 2016-06 2016-11
2017-01 2017-03 2017-07 2017-08
2021-03 2021-06
2022-06
2023-06 2023-07 2023-08 2023-09 2023-10 2023-11
2024-01 2024-04 2024-06 2024-07 2024-08
2025-11 2025-12
""".split()

# ------------------------------------------------------------
# 테스트/리뷰 파일도 포함해서 전부 조사합니다.
# 단, 값이 3개 모두 있는 행만 후보로 인정합니다.
# ------------------------------------------------------------

results = []

for path in sorted(BASE.glob("*.csv")):

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

    hit = df[
        df["period"].isin(TARGETS)
    ].copy()

    for _, r in hit.iterrows():

        complete = pd.notna(
            [
                r["production"],
                r["domestic"],
                r["export"]
            ]
        ).all()

        results.append({
            "period": r["period"],
            "file": path.name,
            "production": r["production"],
            "domestic": r["domestic"],
            "export": r["export"],
            "complete": bool(complete)
        })


res = pd.DataFrame(results)

print("=" * 105)
print("MOTIE 24 MISSING MONTHS - EXISTING DATA SEARCH")
print("=" * 105)

found_complete = []
not_found = []

for period in TARGETS:

    if res.empty:
        x = pd.DataFrame()
    else:
        x = res[
            (res["period"] == period) &
            (res["complete"])
        ]

    print()
    print(period)

    if x.empty:

        print("  >>> NO COMPLETE EXISTING DATA")
        not_found.append(period)

    else:

        found_complete.append(period)

        for _, r in x.iterrows():

            print(
                f"  {r['file']} | "
                f"P={int(float(r['production'])):,} | "
                f"D={int(float(r['domestic'])):,} | "
                f"E={int(float(r['export'])):,}"
            )


print()
print("=" * 105)
print("SUMMARY")
print("=" * 105)

print("TARGET             :", len(TARGETS))
print("FOUND EXISTING     :", len(set(found_complete)))
print("REALLY NOT FOUND   :", len(not_found))

print()
print(
    "REALLY NOT FOUND :",
    "NONE"
    if not not_found
    else " ".join(not_found)
)

print()
print("※ 기존 데이터 위치만 조사")
print("※ 원문 검색 없음")
print("※ MASTER 변경 없음")
print("=" * 105)

