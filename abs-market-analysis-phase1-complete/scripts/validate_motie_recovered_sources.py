from pathlib import Path
import hashlib
import re
import pandas as pd

BASE = Path("data/raw/motie/monthly_pdf")
OLD_PDF = BASE / "pdf"
REC_PDF = BASE / "recovered_pdf"
REC_TEXT = BASE / "recovered_text"
OUT = Path("data/raw/motie/motie_recovered_source_validation.csv")

def sha256(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def canonical(stem):
    m = re.match(r"^(\d{4}-\d{2})", stem)
    return m.group(1) if m else stem

# 기존 PDF 해시 → 실제 기존 월
old_hash = {}
for p in OLD_PDF.glob("*.pdf"):
    if p.stat().st_size > 10000:
        old_hash.setdefault(sha256(p), []).append(canonical(p.stem))

# recovered 해시 그룹
rec_files = [
    p for p in REC_PDF.iterdir()
    if p.is_file()
    and p.stat().st_size > 10000
    and p.suffix.lower() in {".pdf", ".hwpx", ".hwp"}
]

rec_hash = {}
for p in rec_files:
    # HWP/HWPX는 PDF와 직접 hash 비교 의미가 없지만
    # recovered 내부 중복 확인에는 사용 가능
    rec_hash.setdefault(sha256(p), []).append(p)

rows = []

for p in sorted(rec_files):
    period = canonical(p.stem)
    h = sha256(p)

    old_matches = old_hash.get(h, [])

    same_rec = [
        x.name for x in rec_hash[h]
        if x != p
    ]

    text_path = REC_TEXT / f"{period}.txt"

    chars = 0
    if text_path.exists():
        text = text_path.read_text(
            encoding="utf-8",
            errors="replace"
        )
        body = re.sub(r"===== PAGE \d+ =====", "", text)
        chars = len(re.sub(r"\s+", "", body))

    # 판정
    if old_matches:
        if period in old_matches:
            status = "SAME_AS_CORRECT_OLD"
            reason = "기존 동일 월 PDF와 동일"
        else:
            status = "WRONG_MONTH_CONFIRMED"
            reason = "다른 월 기존 PDF와 SHA256 동일"

    elif same_rec:
        other_periods = {
            canonical(Path(x).stem)
            for x in same_rec
        }

        if any(x != period for x in other_periods):
            status = "DUPLICATE_REVIEW"
            reason = "서로 다른 recovered 월이 동일 파일"
        else:
            status = "REVIEW"
            reason = "동일 월 복수 첨부"
    else:
        status = "CANDIDATE_OK"
        reason = "해시 기준 명백한 오매칭 없음"

    if chars < 100 and status == "CANDIDATE_OK":
        status = "TEXT_EMPTY_REVIEW"
        reason = "텍스트 추출 불가/스캔 PDF"

    rows.append({
        "period": period,
        "file": p.name,
        "extension": p.suffix.lower(),
        "bytes": p.stat().st_size,
        "text_chars": chars,
        "status": status,
        "reason": reason,
        "same_as_old_period": ",".join(old_matches),
        "same_recovered_files": ",".join(same_rec),
        "sha256": h,
    })

df = pd.DataFrame(rows)

OUT.parent.mkdir(parents=True, exist_ok=True)
df.to_csv(OUT, index=False, encoding="utf-8-sig")

print("=" * 90)
print("RECOVERED SOURCE VALIDATION")
print("=" * 90)
print("FILES :", len(df))
print()

print(df["status"].value_counts().to_string())

print()
print("=" * 90)
print("WRONG MONTH / DUPLICATE REVIEW")
print("=" * 90)

bad = df[
    df["status"].isin([
        "WRONG_MONTH_CONFIRMED",
        "DUPLICATE_REVIEW",
        "TEXT_EMPTY_REVIEW",
    ])
]

if len(bad):
    print(
        bad[
            [
                "period",
                "file",
                "status",
                "same_as_old_period",
                "same_recovered_files",
            ]
        ].to_string(index=False)
    )
else:
    print("NONE")

print()
print("OUTPUT :", OUT.resolve())
