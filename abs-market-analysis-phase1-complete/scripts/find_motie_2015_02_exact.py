import pandas as pd
import re
from pathlib import Path

FILE = Path("data/raw/motie/motie_search_full_2015_2025.csv")

print("=" * 100)
print("2015-02 MOTIE SEARCH INDEX CHECK")
print("=" * 100)

df = pd.read_csv(FILE, low_memory=False)

for c in ["title", "context", "target_period", "url"]:
    if c not in df.columns:
        df[c] = ""

    df[c] = df[c].fillna("").astype(str)

text = (
    df["title"] + " " +
    df["context"] + " " +
    df["target_period"]
)

# 자동차 관련 자료만
auto = text.str.contains(
    r"자동차.*산업|자동차산업|자동차.*동향",
    regex=True,
    case=False,
    na=False
)

# 2015년 2월을 명시적으로 가리키는 자료
month = text.str.contains(
    r"(?:2015|['’‘]?15)\s*년?\s*[.\-]?\s*0?2\s*월|"
    r"(?:2015|['’‘]?15)[.\-/]\s*0?2(?:\D|$)",
    regex=True,
    case=False,
    na=False
)

cand = df[auto & month].copy()

# 동일 URL/제목 중복 제거
cand = cand.drop_duplicates(
    subset=["title", "url"],
    keep="first"
)

print("FOUND :", len(cand))
print()

if cand.empty:
    print("NO EXACT CANDIDATE")
else:
    for n, (_, r) in enumerate(cand.head(10).iterrows(), 1):
        print("-" * 100)
        print("NO.   :", n)
        print("TITLE :", r["title"][:300])
        print("TARGET:", r["target_period"])
        print("URL   :", r["url"])

        context = re.sub(r"\s+", " ", r["context"]).strip()
        print("TEXT  :", context[:700])

print()
print("=" * 100)
