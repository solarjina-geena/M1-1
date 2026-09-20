from pathlib import Path
import pandas as pd
import re

BASE = Path("data/raw/motie")
SRC = BASE / "motie_month_source_strict_fast.csv"
OUT = BASE / "motie_month_source_content_gate.csv"

df = pd.read_csv(SRC, dtype=str).fillna("")

def norm(s):
    return re.sub(r"\s+", " ", str(s)).strip()

def judge(row):
    period = row["period"]
    text = norm(
        row.get("title", "") + " " +
        row.get("context", "")
    )

    if not text:
        return "NO_SOURCE", "EMPTY"

    year, month = period.split("-")
    m = int(month)

    # 자동차 월간동향 문서 성격
    auto_doc = any(x in text for x in [
        "자동차산업 동향",
        "자동차 산업 동향",
        "자동차산업 월간 동향",
        "자동차 산업 월간 동향",
        "국내 자동차산업 동향",
        "국내 자동차 산업 월간 동향"
    ])

    # 전체 자동차 실적 문맥
    metric_hits = sum(
        x in text for x in ["생산", "내수", "수출"]
    )

    # 명백한 타 자료
    bad_doc = any(x in text for x in [
        "FTA 현안",
        "자유무역협정 현안",
        "수출입 동향"
    ]) and not auto_doc

    if bad_doc:
        return "REJECT", "WRONG_DOCUMENT_TYPE"

    if not auto_doc:
        return "REVIEW", "NO_AUTOMOBILE_MONTHLY_TITLE"

    if metric_hits < 2:
        return "REVIEW", "METRIC_CONTEXT_WEAK"

    # 연도 확인
    year_ok = (
        year in text or
        f"'{year[-2:]}" in text or
        f"’{year[-2:]}" in text or
        f"‘{year[-2:]}" in text
    )

    # 월 표현 확인
    month_patterns = [
        rf"(?<!\d)0?{m}\s*월",
        rf"{year}\s*년\s*0?{m}\s*월",
        rf"[’‘']{year[-2:]}\s*[\.\-]?\s*0?{m}\s*월"
    ]
    month_ok = any(re.search(p, text) for p in month_patterns)

    if not year_ok:
        return "REVIEW", "TARGET_YEAR_NOT_CONFIRMED"

    if not month_ok:
        return "REVIEW", "TARGET_MONTH_NOT_CONFIRMED"

    return "CONTENT_CANDIDATE", "TITLE_PERIOD_METRIC_CONTEXT_OK"


results = df.apply(judge, axis=1)

df["content_status"] = [x[0] for x in results]
df["content_reason"] = [x[1] for x in results]

df.to_csv(OUT, index=False, encoding="utf-8-sig")

print("=" * 105)
print("MOTIE SOURCE CONTENT GATE")
print("=" * 105)

print()
print(df["content_status"].value_counts().to_string())

print()
print("=== NOT AUTO PASS ===")

bad = df[df["content_status"] != "CONTENT_CANDIDATE"]

for _, r in bad.iterrows():
    print(
        f'{r["period"]} | '
        f'{r["content_status"]} | '
        f'{r["content_reason"]} | '
        f'{str(r.get("title",""))[:120]}'
    )

print()
print("OUTPUT :", OUT)
print()
print("※ 아직 VERIFIED 아님")
print("※ 숫자 추출 안 함")
print("※ MASTER 변경 없음")
