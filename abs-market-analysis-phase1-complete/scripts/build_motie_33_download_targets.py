from pathlib import Path
import pandas as pd

SRC = Path("data/raw/motie/motie_missing49_auto_filtered.csv")
OUT = Path("data/raw/motie/motie_33_download_targets.csv")

df = pd.read_csv(SRC, dtype=str, keep_default_na=False)

# 검증 우선순위
rank = {
    "STRONG": 0,
    "LIKELY": 1,
    "REVIEW": 2,
}

df["validation_rank"] = df["validation"].map(rank).fillna(9)

if "score_num" in df.columns:
    df["score_sort"] = pd.to_numeric(
        df["score_num"], errors="coerce"
    ).fillna(0)
elif "score" in df.columns:
    df["score_sort"] = pd.to_numeric(
        df["score"], errors="coerce"
    ).fillna(0)
else:
    df["score_sort"] = 0

# 월별 가장 좋은 후보 1개
best = (
    df.sort_values(
        ["period", "validation_rank", "score_sort"],
        ascending=[True, True, False]
    )
    .drop_duplicates("period", keep="first")
    .sort_values("period")
    .copy()
)

keep = [
    c for c in
    ["period", "validation", "score", "title", "url"]
    if c in best.columns
]

best[keep].to_csv(
    OUT,
    index=False,
    encoding="utf-8-sig"
)

print("=" * 100)
print("MOTIE DOWNLOAD TARGETS")
print("=" * 100)
print("PERIODS :", len(best))
print()

for _, r in best.iterrows():
    print(
        f"{r['period']} | "
        f"{r['validation']} | "
        f"{str(r['title'])[:90]}"
    )

print()
print("OUTPUT :", OUT)
