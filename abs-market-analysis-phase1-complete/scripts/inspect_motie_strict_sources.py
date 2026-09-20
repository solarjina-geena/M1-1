from pathlib import Path
import pandas as pd

BASE = Path("data/raw/motie")
SRC  = BASE / "motie_month_source_strict_fast.csv"

df = pd.read_csv(SRC, dtype=str).fillna("")

print("=" * 110)
print("STRICT SOURCE REVIEW")
print("=" * 110)

# ---------------------------------------------------------
# 1. REVIEW / NO_SOURCE 전체
# ---------------------------------------------------------
review = df[
    df["status"] != "SOURCE_CANDIDATE"
].copy()

print()
print("=== REVIEW / NO SOURCE : ALL ===")

for _, r in review.iterrows():

    print()
    print("-" * 110)
    print("PERIOD   :", r["period"])
    print("STATUS   :", r["status"])

    if r["status"] != "NO_SOURCE":
        print("DETECTED :", r.get("detected_period", ""))
        print("METHOD   :", r.get("source_method", ""))
        print("SCORE    :", r.get("score", ""))
        print("COUNT    :", r.get("candidate_count", ""))
        print("TIED     :", r.get("top_tied", ""))
        print("TITLE    :", str(r.get("title", ""))[:600])
        print("CONTEXT  :", str(r.get("context", ""))[:1000])
        print("URL      :", r.get("url", ""))

# ---------------------------------------------------------
# 2. SOURCE_CANDIDATE 샘플
#    앞/중간/뒤 구간에서 골고루 확인
# ---------------------------------------------------------
cand = df[
    df["status"] == "SOURCE_CANDIDATE"
].reset_index(drop=True)

sample_idx = sorted(set([
    0,
    1,
    2,
    len(cand)//4,
    len(cand)//2,
    (len(cand)*3)//4,
    max(0, len(cand)-3),
    max(0, len(cand)-2),
    max(0, len(cand)-1)
]))

print()
print()
print("=" * 110)
print("SOURCE_CANDIDATE SAMPLE CHECK")
print("=" * 110)

for i in sample_idx:

    r = cand.iloc[i]

    print()
    print("-" * 110)
    print("PERIOD   :", r["period"])
    print("DETECTED :", r.get("detected_period", ""))
    print("SCORE    :", r.get("score", ""))
    print("TITLE    :", str(r.get("title", ""))[:600])
    print("CONTEXT  :", str(r.get("context", ""))[:700])

print()
print("=" * 110)
print("SUMMARY")
print("=" * 110)
print("CANDIDATE :", len(cand))
print("REVIEW    :", (df["status"] == "SOURCE_REVIEW").sum())
print("NO SOURCE :", (df["status"] == "NO_SOURCE").sum())
print("SAMPLES   :", len(sample_idx))
