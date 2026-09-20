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
print("2019-04 LARGE VEHICLE COUNTS")
print("=" * 100)

shown = set()

for i, line in enumerate(lines):

    nums = re.findall(
        r"(?<![\d.])(\d{1,3}(?:,\d{3})+)(?![\d.])",
        line
    )

    large = []

    for n in nums:
        try:
            value = int(n.replace(",", ""))
            if 100000 <= value <= 1000000:
                large.append(n)
        except:
            pass

    if not large:
        continue

    start = max(0, i - 4)
    end = min(len(lines), i + 5)

    key = (start, end)

    if key in shown:
        continue

    shown.add(key)

    print()
    print(f"--- AROUND LINE {i+1} | {', '.join(large)} ---")

    for j in range(start, end):
        print(f"{j+1}: {lines[j]}")

print()
print("=" * 100)
