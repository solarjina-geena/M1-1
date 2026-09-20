from pathlib import Path
import pandas as pd
import re

BASE = Path("data/raw/motie")
SRC = BASE / "motie_16_deep_search_candidates.csv"
OUT = BASE / "motie_16_period_gate_v2.csv"

df = pd.read_csv(SRC, dtype=str).fillna("")

def clean(s):
    s = str(s)
    s = s.replace("’", "'").replace("‘", "'")
    return re.sub(r"\s+", " ", s).strip()

def first_part(s, n=180):
    return clean(s)[:n]

def judge(row):
    period = row["period"]
    year, month = map(int, period.split("-"))
    yy = str(year)[-2:]

    title = clean(row.get("title", ""))
    context = clean(row.get("context", ""))

    # 검색 결과 앞부분만 사용
    # 뒤쪽에 등장하는 "전년 6월 이후", "전월" 등의 오염 방지
    head = first_part(title, 180)

    # -------------------------------------------------
    # 1. 잘못된 문서 종류 차단
    # -------------------------------------------------
    wrong_doc = [
        "수출입 동향",
        "수출입동향",
        "무역 동향",
        "무역동향"
    ]

    if any(x in head for x in wrong_doc):
        return "REJECT", "WRONG_DOCUMENT_TYPE"

    # -------------------------------------------------
    # 2. 자동차산업 자료인지 확인
    # -------------------------------------------------
    automobile = (
        "자동차산업" in head.replace(" ", "")
        or "자동차 산업" in head
    )

    if not automobile:
        return "REJECT", "NOT_AUTOMOBILE_INDUSTRY"

    # -------------------------------------------------
    # 3. 제목 앞부분에서 실제 대상 연월 확인
    # -------------------------------------------------
    patterns = [
        rf"{year}\s*년\s*0?{month}\s*월",
        rf"['`]?\s*{yy}\s*년\s*0?{month}\s*월",
        rf"['`]?\s*{yy}\s*\.\s*0?{month}\s*월"
    ]

    exact = any(
        re.search(p, head, re.I)
        for p in patterns
    )

    # -------------------------------------------------
    # 4. 6월 상반기 자료 허용
    # -------------------------------------------------
    halfyear = (
        month == 6
        and "상반기" in head
        and re.search(r"(및|·|/)\s*6\s*월", head)
    )

    if halfyear:
        # 연도도 반드시 일치
        if str(year) in head or re.search(rf"['`]?\s*{yy}\s*년", head):
            return "PERIOD_MATCH", "HALFYEAR_6_MONTH"

    if exact:
        return "PERIOD_MATCH", "EXACT_DOCUMENT_PERIOD"

    return "REJECT", "DOCUMENT_PERIOD_MISMATCH"


tmp = df.apply(judge, axis=1, result_type="expand")

df["period_gate_v2"] = tmp[0]
df["period_reason_v2"] = tmp[1]

priority = {
    "PERIOD_MATCH": 0,
    "REJECT": 1
}

df["_p"] = df["period_gate_v2"].map(priority)
df["_score"] = pd.to_numeric(df["score"], errors="coerce").fillna(0)

df = df.sort_values(
    ["period", "_p", "_score"],
    ascending=[True, True, False]
)

df.drop(columns=["_p", "_score"], inplace=True)

df.to_csv(OUT, index=False, encoding="utf-8-sig")

print("=" * 105)
print("MOTIE DOCUMENT PERIOD GATE V2")
print("=" * 105)

targets = sorted(df["period"].unique())

valid_periods = []

for period in targets:

    g = df[df["period"] == period]
    good = g[g["period_gate_v2"] == "PERIOD_MATCH"]

    print()
    print("-" * 105)
    print("PERIOD :", period)

    if good.empty:
        print(">>> NO VALID DOCUMENT")
        continue

    valid_periods.append(period)

    for _, r in good.head(3).iterrows():
        print(
            "MATCH |",
            r["period_reason_v2"],
            "| SCORE",
            r["score"]
        )
        print("TITLE :", str(r["title"])[:350])
        print("URL   :", r["url"])
        print()

missing = sorted(set(targets) - set(valid_periods))

print()
print("=" * 105)
print("FINAL")
print("=" * 105)

print("TARGETS        :", len(targets))
print("PERIOD MATCH   :", len(valid_periods))
print("NO VALID       :", len(missing))

print()
print("=== PERIOD MATCH ===")
print(" ".join(valid_periods) if valid_periods else "NONE")

print()
print("=== NO VALID DOCUMENT ===")
print(" ".join(missing) if missing else "NONE")

print()
print("OUTPUT :", OUT)
print()
print("※ MASTER 변경 없음")
print("※ 숫자 추출 없음")
print("※ PERIOD_MATCH는 원문 후보일 뿐 BODY_VERIFIED 아님")
