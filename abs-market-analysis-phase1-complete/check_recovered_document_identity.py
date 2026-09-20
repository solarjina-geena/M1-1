from pathlib import Path
import re

BASE = Path("data/raw/motie/monthly_pdf/recovered_text")

def compact(s):
    return re.sub(r"\s+", " ", s).strip()

print("=" * 110)
print("RECOVERED DOCUMENT IDENTITY CHECK")
print("=" * 110)

for p in sorted(BASE.glob("*.txt")):
    text = p.read_text(encoding="utf-8", errors="replace")

    # PAGE 표시는 제거
    lines = []
    for line in text.splitlines():
        s = compact(line)
        if not s:
            continue
        if s.startswith("===== PAGE"):
            continue
        lines.append(s)

    head = " | ".join(lines[:8])

    # 문서 앞부분에서 연/월 표현 탐색
    sample = compact(text[:8000])

    ym = re.findall(
        r"(?:['‘’]?\s*)?(\d{2,4})\s*년?\s*[.\-]?\s*(\d{1,2})\s*월",
        sample
    )

    found = []
    for y, m in ym:
        try:
            yy = int(y)
            mm = int(m)
        except:
            continue

        if yy < 100:
            yy += 2000

        if 2010 <= yy <= 2030 and 1 <= mm <= 12:
            val = f"{yy:04d}-{mm:02d}"
            if val not in found:
                found.append(val)

    print()
    print("FILE :", p.stem)
    print("DATES:", ", ".join(found[:10]) if found else "NONE")
    print("HEAD :", head[:500] if head else "[EMPTY]")
