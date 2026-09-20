from pathlib import Path

# ============================================================
# [작업 목적]
# 2026-03 ~ 07 HWPX 원문에서
# "수출량" 행만 찾아 짧게 확인합니다.
#
# [검증 규칙]
# 수출량 다음 숫자:
#   1번째 = 전년 동월
#   2번째 = 전월
#   3번째 = 해당 월  ← 우리가 사용할 값
#
# [이번 단계]
# 확인만 수행
# MASTER 변경 없음
# ============================================================

BASE = Path("data/raw/motie/2026_hwpx_text")

for period in [
    "2026-03",
    "2026-04",
    "2026-05",
    "2026-06",
    "2026-07",
]:
    path = BASE / f"{period}.txt"

    print()
    print("=" * 60)
    print(period)
    print("=" * 60)

    lines = path.read_text(
        encoding="utf-8",
        errors="replace"
    ).splitlines()

    found = False

    for i, line in enumerate(lines):

        # '수출량' 항목을 찾음
        if "수출량" in line.replace(" ", ""):

            found = True
            print("ROW :", line.strip())

            # 수출량 이후 12개 셀만 표시
            for j in range(
                i + 1,
                min(i + 13, len(lines))
            ):
                if lines[j].strip():
                    print(lines[j].strip())

            break

    if not found:
        print("EXPORT ROW NOT FOUND")

print()
print("=" * 60)
print("MASTER : UNCHANGED")
print("=" * 60)
