from pathlib import Path
import pdfplumber
import re

PDF = Path("data/raw/motie/monthly_pdf/pdf/2015-02.pdf")

print("=" * 100)
print("2015-02 ORIGINAL PDF CHECK")
print("=" * 100)
print("FILE :", PDF)
print("SIZE :", PDF.stat().st_size if PDF.exists() else "NOT FOUND")

if not PDF.exists():
    raise SystemExit("2015-02.pdf NOT FOUND")

texts = []

with pdfplumber.open(PDF) as pdf:
    print("PAGES:", len(pdf.pages))

    for i, page in enumerate(pdf.pages, 1):
        text = page.extract_text() or ""
        texts.append(text)

text = "\n".join(texts)

print("CHARS:", len(text))

lines = [
    re.sub(r"\s+", " ", x).strip()
    for x in text.splitlines()
    if x.strip()
]

keywords = (
    "생산", "내수", "국내판매", "국내 판매",
    "수출", "자동차산업", "자동차 산업"
)

print()
print("=" * 100)
print("RELEVANT LINES")
print("=" * 100)

count = 0

for i, line in enumerate(lines):
    if any(k in line for k in keywords):
        start = max(0, i - 2)
        end = min(len(lines), i + 4)

        print()
        print(f"--- LINE {i + 1} ---")

        for j in range(start, end):
            print(f"{j + 1}: {lines[j]}")

        count += 1

        if count >= 30:
            break

print()
print("=" * 100)
print("MATCH BLOCKS:", count)
print("=" * 100)

out = Path("data/raw/motie/2015-02_original_text.txt")
out.write_text(text, encoding="utf-8")

print("TEXT OUTPUT:", out)

