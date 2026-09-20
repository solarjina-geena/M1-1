from pathlib import Path

# ============================================================
# [작업 목적]
# 이미 추출된 HWPX TXT에서
# "자동차 생산, 내수, 수출량" 표 주변만 짧게 확인합니다.
#
# [중요]
# - 숫자 확정 안 함
# - VERIFIED 처리 안 함
# - MASTER 변경 없음
# ============================================================

BASE = Path("data/raw/motie/2026_hwpx_text")

PERIODS = [
    "2026-03",
    "2026-04",
    "2026-05",
    "2026-06",
    "2026-07",
]

for period in PERIODS:

    path = BASE / f"{period}.txt"

    print()
    print("=" * 70)
    print(period)
    print("=" * 70)

    if not path.exists():
        print("TEXT NOT FOUND")
        continue

    lines = path.read_text(
        encoding="utf-8",
        errors="replace"
    ).splitlines()

    # --------------------------------------------------------
    # 표 제목 찾기
    # --------------------------------------------------------

    found = None

    for i, line in enumerate(lines):

        x = line.replace(" ", "")

        if (
            "생산" in x
            and "내수" in x
            and "수출" in x
        ):
            found = i
            break

    if found is None:
        print("TABLE NOT FOUND")
        continue

    print("TABLE :", lines[found])

    # --------------------------------------------------------
    # 표 제목 이후 45개 셀만 표시
    #
    # 이전처럼 140개씩 출력하지 않습니다.
    # --------------------------------------------------------

    end = min(
        len(lines),
        found + 46
    )

    for j in range(found + 1, end):

        text = lines[j].strip()

        if text:
            print(
                f"{j+1:04d} | {text}"
            )

print()
print("=" * 70)
print("END")
print("=" * 70)
print("VERIFIED : NO")
print("MASTER   : UNCHANGED")
