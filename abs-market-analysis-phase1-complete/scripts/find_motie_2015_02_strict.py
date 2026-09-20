import pandas as pd
import re
from pathlib import Path

SRC = Path("data/raw/motie/motie_search_full_2015_2025.csv")
OUT = Path("data/raw/motie/motie_2015_02_candidates_strict.csv")

df = pd.read_csv(SRC, dtype=str).fillna("")

def norm(s):
    return re.sub(r"\s+", " ", str(s)).strip()

rows = []

for _, r in df.iterrows():
    title = norm(r.get("title", ""))
    context = norm(r.get("context", ""))
    url = norm(r.get("url", ""))
    text = title + " " + context

    # 자동차 산업 자료만
    auto = (
        "자동차산업" in text.replace(" ", "")
        or "자동차 산업" in text
    )

    if not auto:
        continue

    # 2015년 2월을 직접 가리키는 표현
    month_patterns = [
        r"['‘’]?\s*15\s*년\s*2\s*월",
        r"2015\s*년\s*2\s*월",
        r"['‘’]?\s*15\s*[.\-]\s*2\s*월",
        r"2015\s*[.\-]\s*2\s*월",
    ]

    month_hit = any(re.search(p, text) for p in month_patterns)

    if not month_hit:
        continue

    # 월간 동향 성격 가점
    score = 100

    compact = text.replace(" ", "")

    if "자동차산업동향" in compact:
        score += 50

    if "자동차산업월간동향" in compact:
        score += 50

    if "생산" in text:
        score += 10

    if "내수" in text:
        score += 10

    if "수출" in text:
        score += 10

    rows.append({
        "score": score,
        "title": title,
        "context": context,
        "url": url,
        "page_no": r.get("page_no", ""),
        "currentPage": r.get("currentPage", ""),
        "year_hint": r.get("year_hint", ""),
        "type": r.get("type", ""),
    })

out = pd.DataFrame(rows)

if not out.empty:
    out = (
        out.drop_duplicates(subset=["title", "url"])
           .sort_values(["score", "title"], ascending=[False, True])
    )

out.to_csv(OUT, index=False, encoding="utf-8-sig")

print("=" * 100)
print("2015-02 STRICT AUTOMOBILE MONTHLY SEARCH")
print("=" * 100)
print("FOUND :", len(out))

if len(out):
    for i, (_, r) in enumerate(out.head(30).iterrows(), 1):
        print()
        print(f"[{i}] SCORE={r['score']}")
        print("TITLE  :", r["title"][:300])
        print("CONTEXT:", r["context"][:500])
        print("URL    :", r["url"])
else:
    print("NO STRICT CANDIDATE")

print()
print("OUTPUT :", OUT)
