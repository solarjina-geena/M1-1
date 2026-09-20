import pandas as pd
from pathlib import Path

BASE = Path("data/raw/motie")

files = sorted(BASE.glob("*metrics*.csv"))

print("=" * 100)
print("MOTIE METRIC FILE INVENTORY")
print("=" * 100)

for p in files:
    try:
        df = pd.read_csv(p)

        periods = "NO_PERIOD"
        unique = "-"

        if "period" in df.columns:
            s = df["period"].dropna().astype(str).str.strip()
            if len(s):
                periods = f"{s.min()} ~ {s.max()}"
                unique = s.nunique()

        complete = "-"

        cols = {"production", "domestic", "export"}
        if cols.issubset(df.columns):
            complete = (
                df[["production", "domestic", "export"]]
                .notna()
                .all(axis=1)
                .sum()
            )

        print()
        print("FILE     :", p.name)
        print("ROWS     :", len(df))
        print("PERIODS  :", unique)
        print("RANGE    :", periods)
        print("COMPLETE :", complete)

    except Exception as e:
        print()
        print("FILE     :", p.name)
        print("ERROR    :", e)
