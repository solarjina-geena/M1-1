import pandas as pd
from pathlib import Path

BASE = Path("data/raw/motie")

old_file = BASE / "motie_pdf_metrics_verified.csv"
new_file = BASE / "motie_24_metrics_verified.csv"
out_file = BASE / "motie_monthly_metrics_master.csv"

print("=" * 100)
print("MOTIE FINAL MASTER MERGE")
print("=" * 100)

if not old_file.exists():
    print("OLD FILE NOT FOUND:", old_file)
    print()
    print("후보 파일:")
    for p in sorted(BASE.glob("*metrics*.csv")):
        print(" -", p.name)
    raise SystemExit(1)

if not new_file.exists():
    raise FileNotFoundError(new_file)

old = pd.read_csv(old_file)
new = pd.read_csv(new_file)

old["period"] = old["period"].astype(str).str.strip()
new["period"] = new["period"].astype(str).str.strip()

print("OLD :", old_file.name, "|", len(old))
print("NEW :", new_file.name, "|", len(new))

overlap = sorted(
    set(old["period"]) &
    set(new["period"])
)

print("OVERLAP :", len(overlap))

if overlap:
    print("OVERLAP PERIODS:")
    print(" ".join(overlap))
    raise SystemExit(
        "중복 기간이 있으므로 병합 중단"
    )

# 필요한 핵심 열 확인
required = [
    "period",
    "production",
    "domestic",
    "export"
]

for name, df in [
    ("OLD", old),
    ("NEW", new)
]:
    missing_cols = [
        c for c in required
        if c not in df.columns
    ]

    if missing_cols:
        raise RuntimeError(
            f"{name} missing columns: {missing_cols}"
        )

# 병합
master = pd.concat(
    [old, new],
    ignore_index=True,
    sort=False
)

master = (
    master
    .sort_values("period")
    .reset_index(drop=True)
)

# 기간 중복 검사
dup = master[
    master["period"].duplicated(False)
]

# 핵심 수치 누락 검사
incomplete = master[
    master[
        ["production", "domestic", "export"]
    ].isna().any(axis=1)
]

# 전체 예상기간
expected = pd.period_range(
    "2015-02",
    "2025-10",
    freq="M"
).astype(str)

have = set(master["period"])

missing_periods = [
    x for x in expected
    if x not in have
]

master.to_csv(
    out_file,
    index=False,
    encoding="utf-8-sig"
)

print()
print("=" * 100)
print("FINAL RESULT")
print("=" * 100)

print("MASTER ROWS      :", len(master))
print("MASTER PERIODS   :", master["period"].nunique())
print("DUPLICATE        :", len(dup))
print("INCOMPLETE       :", len(incomplete))
print("EXPECTED PERIODS :", len(expected))
print("MISSING PERIODS  :", len(missing_periods))
print("RANGE            :", master["period"].min(),
      "~", master["period"].max())

print()
print("=== REMAINING MISSING ===")
print(
    " ".join(missing_periods)
    if missing_periods
    else "NONE"
)

print()
print("OUTPUT :", out_file)

if (
    len(master) == master["period"].nunique()
    and len(dup) == 0
    and len(incomplete) == 0
):
    print()
    print(">>> MASTER MERGE VERIFIED <<<")
else:
    print()
    print(">>> MASTER CHECK REQUIRED <<<")
