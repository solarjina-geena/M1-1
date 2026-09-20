from pathlib import Path
import pandas as pd
import re

SRC = Path("data/raw/motie/motie_search_full_2015_2025.csv")
OUT = Path("data/raw/motie/motie_body_validation_scan.csv")

df = pd.read_csv(SRC, dtype=str).fillna("")

periods = pd.period_range("2015-02", "2025-10", freq="M").astype(str)

def clean(s):
    return re.sub(r"\s+", " ", str(s)).strip()

def numbers_after_keyword(text, keyword):
    patterns = [
        rf"{keyword}\s*[\)\]】〉>：:]?\s*[^0-9]{{0,100}}?([0-9]{{1,3}}(?:,[0-9]{{3}})+)\s*대",
        rf"{keyword}\s+([0-9]{{1,3}}(?:,[0-9]{{3}})+)",
    ]

    vals = []
    for pat in patterns:
        for x in re.findall(pat, text, flags=re.I):
            try:
                n = int(x.replace(",", ""))
                if 20000 <= n <= 1000000 and n not in vals:
                    vals.append(n)
            except:
                pass
    return vals

results = []

for period in periods:
    year, month = map(int, period.split("-"))
    yy = year % 100

    month_patterns = [
        rf"{year}\s*년\s*{month}\s*월",
        rf"[‘’'\"]?{yy:02d}\s*[.\-]?\s*{month}\s*월",
    ]

    candidates = []

    for idx, r in df.iterrows():
        title = clean(r.get("title", ""))
        context = clean(r.get("context", ""))
        text = title + " " + context
        compact = text.replace(" ", "")

        if "자동차산업" not in compact and "자동차 산업" not in text:
            continue

        if not any(re.search(p, text) for p in month_patterns):
            continue

        # 다른 산업 일반 수출입 자료보다 자동차산업 자료 우선
        score = 0

        if "자동차산업동향" in compact:
            score += 100
        if "자동차산업월간동향" in compact:
            score += 30
        if "생산" in text:
            score += 10
        if "내수" in text:
            score += 10
        if "수출" in text:
            score += 10

        P = numbers_after_keyword(text, r"(?:생\s*산|\(생산\))")
        D = numbers_after_keyword(text, r"(?:내\s*수|\(내수\))")
        E = numbers_after_keyword(text, r"(?:수\s*출|\(수출\))")

        candidates.append({
            "score": score,
            "title": title,
            "context": context,
            "url": clean(r.get("url", "")),
            "P": P,
            "D": D,
            "E": E,
        })

    candidates.sort(key=lambda x: x["score"], reverse=True)

    chosen = None

    # 3개 값이 모두 잡히는 가장 강한 자동차산업 본문
    for c in candidates:
        if c["P"] and c["D"] and c["E"]:
            chosen = c
            break

    if chosen:
        # 여러 후보가 있을 경우 첫 값만 무조건 확정하지 않고
        # 상태를 REVIEW로 두고 다음 단계에서 교차검증
        status = "BODY_CANDIDATE"

        results.append({
            "period": period,
            "production_candidate": chosen["P"][0],
            "domestic_candidate": chosen["D"][0],
            "export_candidate": chosen["E"][0],
            "status": status,
            "candidate_count": len(candidates),
            "source_title": chosen["title"],
            "source_url": chosen["url"],
        })

    else:
        results.append({
            "period": period,
            "production_candidate": "",
            "domestic_candidate": "",
            "export_candidate": "",
            "status": "NEEDS_REVIEW",
            "candidate_count": len(candidates),
            "source_title": candidates[0]["title"] if candidates else "",
            "source_url": candidates[0]["url"] if candidates else "",
        })

out = pd.DataFrame(results)
out.to_csv(OUT, index=False, encoding="utf-8-sig")

print("=" * 100)
print("MOTIE FULL BODY VALIDATION SCAN")
print("=" * 100)

print("PERIODS        :", len(out))
print("BODY CANDIDATE :", (out.status == "BODY_CANDIDATE").sum())
print("NEEDS REVIEW   :", (out.status == "NEEDS_REVIEW").sum())

print()
print("=== NEEDS REVIEW ===")

review = out[out.status == "NEEDS_REVIEW"]

if review.empty:
    print("NONE")
else:
    for _, r in review.iterrows():
        print(
            f"{r['period']} | "
            f"CANDIDATES={r['candidate_count']} | "
            f"{r['source_title'][:100]}"
        )

print()
print("OUTPUT :", OUT)
print()
print("※ BODY_CANDIDATE는 아직 VERIFIED가 아닙니다.")
print("※ MASTER에는 아무 데이터도 추가하지 않았습니다.")
