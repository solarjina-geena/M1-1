import pandas as pd
from pathlib import Path

p = Path("data/raw/motie/motie_body_crosscheck.csv")
d = pd.read_csv(p)

x = d[d["cross_status"] == "VALUE_MISMATCH"].copy()

x["P"] = x["production_candidate"] == x["ref_production"]
x["D"] = x["domestic_candidate"] == x["ref_domestic"]
x["E"] = x["export_candidate"] == x["ref_export"]

# 세 값 모두 다른 경우 10건
x = x[
    (~x["P"]) &
    (~x["D"]) &
    (~x["E"])
].head(10)

print("=" * 110)
print("BODY EXTRACTION ERROR SAMPLE")
print("=" * 110)

for _, r in x.iterrows():

    print()
    print("-" * 110)
    print("PERIOD :", r["period"])

    print(
        "BODY   :",
        r["production_candidate"],
        r["domestic_candidate"],
        r["export_candidate"]
    )

    print(
        "REF    :",
        r["ref_production"],
        r["ref_domestic"],
        r["ref_export"]
    )

    print("SOURCE :", r.get("reference_sources", ""))

    print()
    print("TITLE  :", str(r.get("title", ""))[:500])

    # body_validation_fast에 문맥 컬럼이 있다면 같이 표시
    bodyfile = Path("data/raw/motie/motie_body_validation_fast.csv")

    if bodyfile.exists():

        b = pd.read_csv(bodyfile, dtype=str).fillna("")
        row = b[b["period"] == str(r["period"])]

        if len(row):

            rr = row.iloc[0]

            print()
            print("=== AVAILABLE BODY FIELDS ===")

            for c in b.columns:

                if any(k in c.lower() for k in [
                    "context",
                    "text",
                    "production",
                    "domestic",
                    "export",
                    "title"
                ]):

                    val = str(rr.get(c, ""))

                    if val:
                        print(f"{c}: {val[:1500]}")

print()
print("=" * 110)
print("SAMPLES :", len(x))
print("=" * 110)
