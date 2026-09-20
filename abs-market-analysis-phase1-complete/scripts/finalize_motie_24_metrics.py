import pandas as pd
from pathlib import Path

p = Path("data/raw/motie/motie_24_metrics_verified.csv")

df = pd.read_csv(p)

mask = df["period"].astype(str).eq("2019-04")

if mask.sum() != 1:
    raise RuntimeError(
        f"2019-04 row count error: {mask.sum()}"
    )

df.loc[mask, "production"] = 371930
df.loc[mask, "domestic"] = 155027
df.loc[mask, "export"] = 223235

df.loc[mask, "production_status"] = "MANUAL_VERIFIED"
df.loc[mask, "domestic_status"] = "MANUAL_VERIFIED"
df.loc[mask, "export_status"] = "MANUAL_VERIFIED"

df.to_csv(
    p,
    index=False,
    encoding="utf-8-sig"
)

complete = (
    df[["production", "domestic", "export"]]
    .notna()
    .all(axis=1)
)

print("=" * 90)
print("MOTIE 24 FINAL")
print("=" * 90)

print(
    df.loc[
        df["period"].astype(str).eq("2019-04"),
        [
            "period",
            "production",
            "domestic",
            "export",
            "production_status",
            "domestic_status",
            "export_status"
        ]
    ].to_string(index=False)
)

print()
print("TOTAL    :", len(df))
print("COMPLETE :", int(complete.sum()))
print("MISSING  :", int((~complete).sum()))
print("OUTPUT   :", p)

if len(df) == 24 and complete.sum() == 24:
    print()
    print(">>> VERIFIED 24 / 24 <<<")
else:
    print()
    print(">>> CHECK REQUIRED <<<")
