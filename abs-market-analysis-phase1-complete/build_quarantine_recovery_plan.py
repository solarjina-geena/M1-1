from pathlib import Path
import pandas as pd
import shutil

BASE = Path("data/raw/motie")
PDF_BASE = BASE / "monthly_pdf"

VALIDATION = BASE / "motie_recovered_source_validation.csv"

# 격리 폴더 자동 탐색
candidates = [
    p for p in PDF_BASE.iterdir()
    if p.is_dir()
    and "wrong" in p.name.lower()
]

print("=" * 100)
print("QUARANTINE RECOVERY CHECK")
print("=" * 100)

if not candidates:
    print("ERROR: wrong/quarantine folder not found")
    print()
    print("AVAILABLE DIRS:")
    for p in PDF_BASE.iterdir():
        if p.is_dir():
            print(" -", p.name)
    raise SystemExit(1)

print("QUARANTINE DIRS:")
for p in candidates:
    print(" -", p)

v = pd.read_csv(VALIDATION, dtype=str).fillna("")

wrong = v[
    v["status"].eq("WRONG_MONTH_CONFIRMED")
].copy()

# 현재 80개월
old = pd.read_csv(
    BASE / "motie_pdf_metrics_final.csv",
    dtype={"period": str}
)

new = pd.read_csv(
    BASE / "motie_recovered_metrics_verified.csv",
    dtype={"period": str}
)

have = set(old["period"]) | set(new["period"])

start = pd.Period("2015-02", freq="M")
end = pd.Period("2025-10", freq="M")

expected = {
    str(p)
    for p in pd.period_range(start, end, freq="M")
}

missing = expected - have

rows = []

for _, r in wrong.iterrows():

    claimed = r.get("period", "").strip()
    actual = r.get("same_as_old_period", "").strip()
    filename = r.get("file", "").strip()

    if not actual:
        continue

    source = None

    for folder in candidates:
        test = folder / filename
        if test.exists():
            source = test
            break

    rows.append({
        "claimed_period": claimed,
        "actual_period": actual,
        "file": filename,
        "source_exists": source is not None,
        "needed_now": actual in missing,
        "source_path": str(source) if source else "",
    })

df = pd.DataFrame(rows)

print()
print("WRONG-MONTH FILES WITH KNOWN ACTUAL PERIOD :", len(df))
print("SOURCE EXISTS                             :", int(df["source_exists"].sum()))
print("CAN FILL CURRENT MISSING                  :", int((df["source_exists"] & df["needed_now"]).sum()))

print()
print("=== RECOVERABLE MISSING MONTHS ===")

recover = df[
    df["source_exists"]
    & df["needed_now"]
].sort_values("actual_period")

if recover.empty:
    print("NONE")
else:
    print(
        recover[
            [
                "actual_period",
                "file",
                "claimed_period",
            ]
        ].to_string(index=False)
    )

recoverable = set(recover["actual_period"])

still_missing = sorted(missing - recoverable)

print()
print("=== AFTER REASSIGNMENT ===")
print("CURRENT MISSING :", len(missing))
print("RECOVERABLE     :", len(recoverable))
print("STILL MISSING   :", len(still_missing))

print()
print("=== TRUE REMAINING MISSING ===")
print(
    " ".join(still_missing)
    if still_missing
    else "NONE"
)

out = BASE / "motie_quarantine_recovery_plan.csv"

df.to_csv(
    out,
    index=False,
    encoding="utf-8-sig",
)

print()
print("OUTPUT :", out)
