from pathlib import Path
import pandas as pd

BASE = Path("data/raw/motie")

OLD = BASE / "motie_pdf_metrics_final.csv"
NEW = BASE / "motie_recovered_metrics_verified.csv"

old = pd.read_csv(OLD)
new = pd.read_csv(NEW)

old["period"] = old["period"].astype(str).str.strip()
new["period"] = new["period"].astype(str).str.strip()

old_periods = set(old["period"])
new_periods = set(new["period"])

overlap = sorted(old_periods & new_periods)
union = sorted(old_periods | new_periods)

print("=" * 90)
print("FINAL MERGE PRECHECK")
print("=" * 90)

print("OLD ROWS       :", len(old))
print("OLD PERIODS    :", len(old_periods))
print("NEW ROWS       :", len(new))
print("NEW PERIODS    :", len(new_periods))
print("OVERLAP        :", len(overlap))
print("UNION PERIODS  :", len(union))

print()
print("OLD RANGE      :", min(old_periods), "~", max(old_periods))
print("NEW RANGE      :", min(new_periods), "~", max(new_periods))
print("UNION RANGE    :", min(union), "~", max(union))

print()
print("=== OVERLAP PERIODS ===")
print(" ".join(overlap) if overlap else "NONE")

# 전체 기간 기준 월 누락 계산
start = pd.Period(min(union), freq="M")
end = pd.Period(max(union), freq="M")

expected = {
    str(p)
    for p in pd.period_range(start, end, freq="M")
}

missing = sorted(expected - set(union))

print()
print("=== COVERAGE ===")
print("EXPECTED       :", len(expected))
print("HAVE           :", len(union))
print("MISSING        :", len(missing))

print()
print("=== MISSING PERIODS ===")
print(" ".join(missing) if missing else "NONE")

print()
print("=== NEW 23 PERIODS ===")
print(" ".join(sorted(new_periods)))
