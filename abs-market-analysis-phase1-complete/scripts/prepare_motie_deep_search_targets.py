from pathlib import Path
import pandas as pd

BASE = Path("data/raw/motie")
SRC = BASE / "motie_month_source_content_gate.csv"
OUT = BASE / "motie_source_deep_search_targets.csv"
UPDATED = BASE / "motie_month_source_content_gate_v2.csv"

df = pd.read_csv(SRC, dtype=str).fillna("")

# 2019-06은 실제 제목:
# "2019년 상반기 및 6월 국내 자동차 산업동향"
# → 자동차 월간 원문 후보로 인정
mask = df["period"].eq("2019-06")

df.loc[mask, "content_status"] = "CONTENT_CANDIDATE"
df.loc[mask, "content_reason"] = "HALF_YEAR_AND_MONTH_AUTOMOBILE_REPORT"

# CONTENT_CANDIDATE가 아닌 월만 정밀검색 대상으로 분리
targets = df[df["content_status"] != "CONTENT_CANDIDATE"].copy()

# 기존의 잘못된 후보는 참고용으로 남기되
# 새 검색에서 그대로 신뢰하지 않음
targets["deep_search_required"] = True

df.to_csv(UPDATED, index=False, encoding="utf-8-sig")
targets.to_csv(OUT, index=False, encoding="utf-8-sig")

print("=" * 105)
print("MOTIE DEEP SEARCH TARGET PREP")
print("=" * 105)

print("TOTAL PERIODS       :", len(df))
print("CONTENT CANDIDATE   :", (df["content_status"] == "CONTENT_CANDIDATE").sum())
print("DEEP SEARCH TARGETS :", len(targets))

print()
print("=== DEEP SEARCH PERIODS ===")
print(" ".join(targets["period"].tolist()))

print()
print("=== CURRENT STATUS ===")
print(
    targets[
        ["period", "content_status", "content_reason"]
    ].to_string(index=False)
)

print()
print("UPDATED :", UPDATED)
print("TARGETS :", OUT)

print()
print("※ MASTER 변경 없음")
print("※ 숫자 VERIFIED 처리 없음")
