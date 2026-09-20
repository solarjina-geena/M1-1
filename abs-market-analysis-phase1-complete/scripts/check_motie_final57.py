import pandas as pd
from pathlib import Path

BASE = Path("data/raw/motie")

old = pd.read_csv(BASE / "motie_pdf_metrics_final.csv")
new = pd.read_csv(BASE / "motie_24_metrics_verified.csv")

old["period"] = old["period"].astype(str).str.strip()
new["period"] = new["period"].astype(str).str.strip()

print("=" * 100)
print("FINAL 57 CHECK")
print("=" * 100)

# 기존 57개 중 미완성
bad = old[
    old[["production", "domestic", "export"]]
    .isna()
    .any(axis=1)
]

print()
print("OLD ROWS       :", len(old))
print("OLD COMPLETE   :", len(old) - len(bad))
print("OLD INCOMPLETE :", len(bad))

print()
print("=== OLD INCOMPLETE ===")
if len(bad):
    cols = [
        c for c in [
            "period",
            "production",
            "domestic",
            "export",
            "production_status",
            "domestic_status",
            "export_status"
        ]
        if c in bad.columns
    ]
    print(bad[cols].to_string(index=False))
else:
    print("NONE")

# 새 24개와 중복 확인
overlap = sorted(
    set(old["period"]) &
    set(new["period"])
)

print()
print("=== OLD 57 / NEW 24 OVERLAP ===")
print("COUNT :", len(overlap))
print(" ".join(overlap) if overlap else "NONE")

# 합집합 계산
union = sorted(
    set(old["period"]) |
    set(new["period"])
)

print()
print("=== UNION ===")
print("OLD PERIODS :", old["period"].nunique())
print("NEW PERIODS :", new["period"].nunique())
print("UNION       :", len(union))
