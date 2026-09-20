from pathlib import Path
import pandas as pd
import numpy as np

BASE = Path("data/raw/motie")

BODY = BASE / "motie_body_validation_fast.csv"

SOURCES = [
    ("OLD57", BASE / "motie_pdf_metrics_final.csv"),
    ("RECOVERED23", BASE / "motie_recovered_metrics_verified.csv"),
    ("VERIFIED24", BASE / "motie_24_metrics_verified.csv"),
    ("MANUAL_BODY", BASE / "motie_manual_body_verified.csv"),
]

OUT = BASE / "motie_body_crosscheck.csv"

print("=" * 100)
print("MOTIE BODY CROSS CHECK")
print("=" * 100)

# --------------------------------------------------
# 숫자 정리
# --------------------------------------------------
def num(v):
    if pd.isna(v):
        return np.nan

    s = str(v).strip().replace(",", "")

    if s == "" or s.lower() == "nan":
        return np.nan

    try:
        return int(float(s))
    except:
        return np.nan


# --------------------------------------------------
# BODY 후보
# --------------------------------------------------
body = pd.read_csv(BODY, dtype=str).fillna("")

for c in [
    "production_candidate",
    "domestic_candidate",
    "export_candidate"
]:
    body[c] = body[c].map(num)

body = body[
    body["status"] == "BODY_CANDIDATE"
].copy()

print("BODY CANDIDATES :", len(body))


# --------------------------------------------------
# 기존 검증자료 통합
# --------------------------------------------------
all_old = []

for label, path in SOURCES:

    if not path.exists():
        print("SKIP :", path.name)
        continue

    x = pd.read_csv(path, dtype=str)

    if "period" not in x.columns:
        continue

    needed = ["production", "domestic", "export"]

    if not all(c in x.columns for c in needed):
        continue

    x = x[["period"] + needed].copy()

    for c in needed:
        x[c] = x[c].map(num)

    x["source"] = label

    # 3개 값 모두 있는 것만 비교 기준으로 사용
    x = x[
        x["production"].notna()
        & x["domestic"].notna()
        & x["export"].notna()
    ]

    all_old.append(x)

if not all_old:
    raise SystemExit("비교 가능한 기존 자료가 없습니다.")

old = pd.concat(all_old, ignore_index=True)

print("REFERENCE ROWS  :", len(old))


# --------------------------------------------------
# 같은 period에 여러 자료가 있으면
# 값 조합별로 확인
# --------------------------------------------------
ref_rows = []

for period, g in old.groupby("period"):

    combos = (
        g.groupby(
            ["production", "domestic", "export"],
            dropna=False
        )
        .agg(
            source_count=("source", "count"),
            sources=("source", lambda s: ",".join(sorted(set(s))))
        )
        .reset_index()
        .sort_values("source_count", ascending=False)
    )

    best = combos.iloc[0]

    ref_rows.append({
        "period": period,
        "ref_production": best["production"],
        "ref_domestic": best["domestic"],
        "ref_export": best["export"],
        "reference_sources": best["sources"],
        "reference_agreement": int(best["source_count"]),
        "reference_variants": len(combos),
    })

ref = pd.DataFrame(ref_rows)


# --------------------------------------------------
# BODY ↔ 기존자료 비교
# --------------------------------------------------
m = body.merge(ref, on="period", how="left")

def eq(a, b):
    if pd.isna(a) or pd.isna(b):
        return False
    return int(a) == int(b)

statuses = []

for _, r in m.iterrows():

    # 기존 비교값 자체가 없음
    if pd.isna(r.get("ref_production")):
        statuses.append("BODY_ONLY_REVIEW")
        continue

    p = eq(r["production_candidate"], r["ref_production"])
    d = eq(r["domestic_candidate"], r["ref_domestic"])
    e = eq(r["export_candidate"], r["ref_export"])

    # 기존 자료끼리도 값이 여러 종류
    variants = r.get("reference_variants", 1)

    try:
        variants = int(variants)
    except:
        variants = 1

    if p and d and e and variants == 1:
        statuses.append("CROSS_VERIFIED")

    elif p and d and e:
        statuses.append("MATCH_BUT_REFERENCE_CONFLICT")

    else:
        statuses.append("VALUE_MISMATCH")

m["cross_status"] = statuses


# --------------------------------------------------
# 저장
# --------------------------------------------------
cols = [
    "period",

    "production_candidate",
    "domestic_candidate",
    "export_candidate",

    "ref_production",
    "ref_domestic",
    "ref_export",

    "reference_sources",
    "reference_agreement",
    "reference_variants",

    "cross_status",
    "title",
    "url",
]

m[cols].to_csv(
    OUT,
    index=False,
    encoding="utf-8-sig"
)


# --------------------------------------------------
# 결과
# --------------------------------------------------
print()
print("=" * 100)
print("RESULT")
print("=" * 100)

print("BODY CANDIDATES :", len(m))

counts = m["cross_status"].value_counts()

for name in [
    "CROSS_VERIFIED",
    "MATCH_BUT_REFERENCE_CONFLICT",
    "VALUE_MISMATCH",
    "BODY_ONLY_REVIEW",
]:
    print(f"{name:<29}: {counts.get(name, 0)}")


print()
print("=== NEEDS REVIEW ===")

review = m[
    m["cross_status"] != "CROSS_VERIFIED"
]

if len(review) == 0:
    print("NONE")
else:
    for _, r in review.iterrows():

        print(
            f"{r['period']} | "
            f"{r['cross_status']} | "
            f"BODY={r['production_candidate']}/"
            f"{r['domestic_candidate']}/"
            f"{r['export_candidate']} | "
            f"REF={r['ref_production']}/"
            f"{r['ref_domestic']}/"
            f"{r['ref_export']}"
        )

print()
print("OUTPUT :", OUT)

print()
print("※ CROSS_VERIFIED도 아직 MASTER 병합 전")
print("※ VALUE_MISMATCH는 자동 병합 금지")
print("※ MASTER 파일 변경 없음")
