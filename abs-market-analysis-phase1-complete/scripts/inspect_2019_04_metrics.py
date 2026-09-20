from pathlib import Path
import re

p = Path(
    "data/raw/motie/monthly_pdf/"
    "verified_download_24_text/2019-04.txt"
)

text = p.read_text(
    encoding="utf-8",
    errors="replace"
)

lines = text.splitlines()

print("=" * 100)
print("2019-04 PRODUCTION / DOMESTIC / EXPORT CHECK")
print("=" * 100)

keywords = [
    "생산",
    "내수",
    "수출",
    "종합",
]

for i, line in enumerate(lines):

    if not any(k in line for k in keywords):
        continue

    # 주변에 자동차 대수 형태 숫자가 있는 경우만
    start = max(0, i - 3)
    end = min(len(lines), i + 9)

    block = "\n".join(lines[start:end])

    nums = re.findall(
        r"\b\d{1,3}(?:,\d{3})+\s*대?",
        block
    )

    if not nums:
        continue

    print()
    print(f"--- LINE {i+1} ---")

    for n, s in enumerate(
        lines[start:end],
        start=start + 1
    ):
        print(f"{n}: {s}")

print()
print("=" * 100)
