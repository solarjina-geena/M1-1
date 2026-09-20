import pandas as pd
import re
from pathlib import Path

BASE = Path.cwd()
src = BASE / "data" / "raw" / "motie" / "motie_auto_recovery_candidates.csv"
out = BASE / "data" / "raw" / "motie" / "motie_exact_candidates.csv"

df = pd.read_csv(src, dtype=str).fillna("")

def norm(s):
    return re.sub(r"\s+", "", str(s))

def exact_title(row):
    period = row["period"]
    title = norm(row["page_title"])

    if not re.fullmatch(r"\d{4}-\d{2}", period):
        return False

    year = int(period[:4])
    month = int(period[5:7])
    y2 = str(year)[-2:]

    patterns = [
        f"{year}년{month}월자동차산업동향",
        f"{y2}년{month}월자동차산업동향",
    ]

    return any(p in title for p in patterns)

df["exact_title"] = df.apply(exact_title, axis=1)

exact = (
    df[df["exact_title"]]
    .sort_values(["period", "score"], ascending=[True, False])
    .drop_duplicates("period", keep="first")
    .reset_index(drop=True)
)

exact.to_csv(out, index=False, encoding="utf-8-sig")

print("=" * 60)
print("EXACT CANDIDATE CHECK")
print("=" * 60)
print("전체 후보 :", len(df))
print("정확 월수 :", exact["period"].nunique())
print("저장 파일 :", out)
print()

if len(exact):
    print(exact[
        ["period", "score", "page_title", "url"]
    ].to_string(index=False))
