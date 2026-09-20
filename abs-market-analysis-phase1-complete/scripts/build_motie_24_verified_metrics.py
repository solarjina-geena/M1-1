from pathlib import Path
import sys
import re
import zipfile
import html
import pandas as pd

BASE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE))

from scripts.build_motie_pdf_master_v2_locked import extract_metrics

DATA = BASE / "data" / "raw" / "motie"

SRC = DATA / "monthly_pdf" / "verified_download_24"
TEXT_DIR = DATA / "monthly_pdf" / "verified_download_24_text"
TEXT_DIR.mkdir(parents=True, exist_ok=True)

OUT = DATA / "motie_24_metrics_verified.csv"


def extract_hwpx(path):

    parts = []

    with zipfile.ZipFile(path) as z:

        names = [
            n for n in z.namelist()
            if n.startswith("Contents/")
            and n.lower().endswith(".xml")
        ]

        for name in sorted(names):

            raw = z.read(name).decode(
                "utf-8",
                errors="replace"
            )

            # XML 태그 사이 텍스트가 붙지 않도록 공백 처리
            raw = re.sub(r"<[^>]+>", " ", raw)

            raw = html.unescape(raw)

            raw = re.sub(
                r"[ \t]+",
                " ",
                raw
            )

            parts.append(raw)

    return "\n".join(parts)


print("=" * 100)
print("MOTIE VERIFIED 24 METRIC EXTRACTION")
print("=" * 100)

# ------------------------------------------------------------
# 1. HWPX 6개 텍스트 생성
# ------------------------------------------------------------

hwpx_files = sorted(SRC.glob("*.hwpx"))

print()
print("HWPX TEXT EXTRACTION :", len(hwpx_files))

for path in hwpx_files:

    period = path.stem

    text = extract_hwpx(path)

    out_path = TEXT_DIR / f"{period}.txt"

    out_path.write_text(
        text,
        encoding="utf-8"
    )

    chars = len(
        re.sub(r"\s+", "", text)
    )

    print(
        period,
        "| CHARS=",
        chars
    )


# ------------------------------------------------------------
# 2. 실제 다운로드된 24개월 목록
# ------------------------------------------------------------

periods = sorted({
    p.stem
    for p in SRC.iterdir()
    if p.is_file()
    and p.suffix.lower() in {".hwp", ".hwpx"}
})

print()
print("TARGET PERIODS :", len(periods))


# ------------------------------------------------------------
# 3. V2 LOCKED 추출기 실행
# ------------------------------------------------------------

rows = []

for period in periods:

    txt = TEXT_DIR / f"{period}.txt"

    if not txt.exists():

        rows.append({
            "period": period,
            "production": None,
            "domestic": None,
            "export": None,
            "production_status": "NO_TEXT",
            "domestic_status": "NO_TEXT",
            "export_status": "NO_TEXT",
            "complete": False,
        })

        print(
            period,
            "| NO_TEXT"
        )

        continue

    text = txt.read_text(
        encoding="utf-8",
        errors="replace"
    )

    metrics = extract_metrics(text)

    p = metrics.get("production")
    d = metrics.get("domestic")
    e = metrics.get("export")

    ps = metrics.get(
        "production_status",
        ""
    )

    ds = metrics.get(
        "domestic_status",
        ""
    )

    es = metrics.get(
        "export_status",
        ""
    )

    complete = (
        p is not None
        and d is not None
        and e is not None
    )

    row = {
        "period": period,
        **metrics,
        "complete": complete,
    }

    rows.append(row)

    print(
        f"{period} "
        f"P={p} "
        f"D={d} "
        f"E={e} | "
        f"{ps} "
        f"{ds} "
        f"{es}"
    )


# ------------------------------------------------------------
# 4. 저장
# ------------------------------------------------------------

df = pd.DataFrame(rows)

df = df.sort_values(
    "period"
).reset_index(drop=True)

df.to_csv(
    OUT,
    index=False,
    encoding="utf-8-sig"
)


# ------------------------------------------------------------
# 5. 검증
# ------------------------------------------------------------

complete_mask = (
    df["production"].notna()
    & df["domestic"].notna()
    & df["export"].notna()
)

review_mask = ~complete_mask

# 범위 검토도 따로 잡음
status_cols = [
    "production_status",
    "domestic_status",
    "export_status",
]

range_review = pd.Series(
    False,
    index=df.index
)

for col in status_cols:

    if col in df.columns:

        range_review |= (
            df[col]
            .fillna("")
            .astype(str)
            .str.contains(
                "REVIEW",
                case=False
            )
        )


print()
print("=" * 100)
print("RESULT")
print("=" * 100)

print("TARGET       :", len(df))
print("COMPLETE     :", int(complete_mask.sum()))
print("INCOMPLETE   :", int(review_mask.sum()))
print("RANGE REVIEW :", int(range_review.sum()))


if review_mask.any() or range_review.any():

    print()
    print("=== REVIEW ===")

    cols = [
        "period",
        "production",
        "domestic",
        "export",
        "production_status",
        "domestic_status",
        "export_status",
    ]

    check = df[
        review_mask | range_review
    ]

    print(
        check[cols].to_string(
            index=False
        )
    )


print()
print("TEXT   :", TEXT_DIR)
print("OUTPUT :", OUT)
