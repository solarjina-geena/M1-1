from pathlib import Path
import re

# ============================================================
# [작업 목적]
# 2026-03 ~ 07 공식 HWPX 표 안에서만
# 생산 / 내수 / 수출의 "해당 월 정확값"을 찾습니다.
#
# [핵심 개선]
# 문서 전체에서 '수출량'을 찾지 않습니다.
#
# 반드시:
#   표 3) 자동차 생산, 내수, 수출량
#        ↓
#   생산량
#        ↓
#   내수 판매량
#        ↓
#   수출량
#
# 이 표 범위 안에서만 값을 찾습니다.
#
# [값 선택 규칙]
# 각 행에서:
#   첫 번째 대수 = 전년동월
#   두 번째 대수 = 전월
#   세 번째 대수 = 해당월 ★
#
# [안전]
# - 결과 확인만 수행
# - VERIFIED 저장 안 함
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


# ------------------------------------------------------------
# 숫자 형태 판별
#
# 387,227 같은 '대수'만 대상으로 합니다.
# 4.5 같은 증감률은 제외합니다.
# ------------------------------------------------------------

COUNT_RE = re.compile(r"^\d{1,3}(?:,\d{3})+$")


def find_month_value(lines, start, label, max_search=100):

    """
    표 내부에서 특정 행을 찾고,
    그 뒤에 등장하는 '대수 숫자' 중 세 번째 값을 반환합니다.
    """

    row_index = None

    # 행 이름 찾기
    for i in range(
        start,
        min(start + max_search, len(lines))
    ):
        normalized = lines[i].replace(" ", "")

        if label.replace(" ", "") == normalized:
            row_index = i
            break

    if row_index is None:
        return None

    counts = []

    # 다음 행 이름이 나오기 전까지만 숫자 수집
    for j in range(
        row_index + 1,
        min(row_index + 20, len(lines))
    ):

        text = lines[j].strip()

        if COUNT_RE.fullmatch(text):
            counts.append(
                int(text.replace(",", ""))
            )

        # 필요한 3개를 얻었으면 종료
        if len(counts) == 3:
            return counts[2]

    return None


print("=" * 76)
print("2026 MOTIE HWPX EXACT MONTHLY VALUES")
print("=" * 76)

for period in PERIODS:

    path = BASE / f"{period}.txt"

    if not path.exists():
        print(f"{period} | TEXT NOT FOUND")
        continue

    lines = [
        x.strip()
        for x in path.read_text(
            encoding="utf-8",
            errors="replace"
        ).splitlines()
    ]

    # --------------------------------------------------------
    # 해당 월의 공식 '표 3)' 위치를 찾습니다.
    # --------------------------------------------------------

    month = int(period[-2:])

    table_index = None

    for i, line in enumerate(lines):

        normalized = line.replace(" ", "")

        # 해당 월 + 생산 + 내수 + 수출량이 모두 있는
        # 공식 표 제목만 인정
        if (
            "표3)" in normalized
            and f"'26년{month}월" in normalized
            and "생산" in normalized
            and "내수" in normalized
            and "수출량" in normalized
        ):
            table_index = i
            break

    if table_index is None:
        print(
            f"{period} | TABLE NOT FOUND"
        )
        continue

    # --------------------------------------------------------
    # 공식 표 안에서 세 지표 추출
    # --------------------------------------------------------

    production = find_month_value(
        lines,
        table_index,
        "생산량"
    )

    domestic = find_month_value(
        lines,
        table_index,
        "내수 판매량"
    )

    export = find_month_value(
        lines,
        table_index,
        "수출량",
        max_search=180
    )

    # --------------------------------------------------------
    # 세 값이 모두 있어야 CHECK_OK
    # --------------------------------------------------------

    status = (
        "CHECK_OK"
        if all(
            x is not None
            for x in [
                production,
                domestic,
                export
            ]
        )
        else "REVIEW"
    )

    def fmt(x):
        return (
            f"{x:,}"
            if x is not None
            else "NOT_FOUND"
        )

    print(
        f"{period} | "
        f"생산={fmt(production)} | "
        f"내수={fmt(domestic)} | "
        f"수출={fmt(export)} | "
        f"{status}"
    )


print("=" * 76)
print("※ CHECK_OK도 아직 BODY_VERIFIED 아님")
print("※ MASTER 변경 없음")
