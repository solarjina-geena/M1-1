from pathlib import Path
import re

# ============================================================
# [작업 목적]
# 이미 HWP에서 추출해 저장한 2026-02 / 2026-08 TXT에서
# 공식 "표 3) 자동차 생산, 내수, 수출량"만 찾아
# 해당 월의 정확한 생산 / 내수 / 수출 대수를 확인합니다.
#
# [중요]
# 본문의 "16.0만대", "11만대" 같은 요약 숫자는 사용하지 않습니다.
# 공식 표의 해당 월 열에 있는 정확한 대수만 사용합니다.
#
# [값 선택 규칙]
# 각 지표 행 뒤:
#   1번째 대수 = 전년동월
#   2번째 대수 = 전월
#   3번째 대수 = 해당월 ★
#
# [안전]
# 숫자 확인만 수행
# BODY_VERIFIED 저장 안 함
# MASTER 변경 안 함
# ============================================================

BASE = Path("data/raw/motie/2026_hwp_text")

PERIODS = [
    "2026-02",
    "2026-08",
]

# 387,227 같은 실제 '대수' 형태만 인정
# 10.2, △20.8 같은 증감률은 제외
COUNT_RE = re.compile(r"^\d{1,3}(?:,\d{3})+$")


def find_table(lines, period):

    month = int(period[-2:])

    # --------------------------------------------------------
    # 반드시 해당 월의 "표 3)"을 찾습니다.
    # 본문에 먼저 등장하는 생산/내수/수출 문장은 무시합니다.
    # --------------------------------------------------------

    for i, line in enumerate(lines):

        x = line.replace(" ", "")

        if (
            "표3)" in x
            and f"'26년{month}월" in x
            and "자동차" in x
            and "생산" in x
            and "내수" in x
            and "수출량" in x
        ):
            return i

    return None


def find_value(lines, table_idx, label):

    # --------------------------------------------------------
    # 표 시작 이후에서 정확한 행 이름을 찾습니다.
    # --------------------------------------------------------

    row_idx = None

    for i in range(
        table_idx,
        min(table_idx + 250, len(lines))
    ):

        x = lines[i].replace(" ", "").strip()

        if x == label.replace(" ", ""):
            row_idx = i
            break

    if row_idx is None:
        return None

    counts = []

    # --------------------------------------------------------
    # 행 이름 뒤에서 쉼표가 있는 대수만 수집합니다.
    # 세 번째 값이 해당 월 값입니다.
    # --------------------------------------------------------

    for j in range(
        row_idx + 1,
        min(row_idx + 25, len(lines))
    ):

        text = lines[j].strip()

        if COUNT_RE.fullmatch(text):

            counts.append(
                int(text.replace(",", ""))
            )

            if len(counts) == 3:
                return counts[2]

    return None


print("=" * 76)
print("2026-02 / 2026-08 EXACT HWP TABLE VALUES")
print("=" * 76)

for period in PERIODS:

    path = BASE / f"{period}.txt"

    if not path.exists():
        print(f"{period} | TEXT NOT FOUND")
        continue

    lines = path.read_text(
        encoding="utf-8",
        errors="replace"
    ).splitlines()

    table_idx = find_table(
        lines,
        period
    )

    if table_idx is None:

        print(
            f"{period} | "
            "OFFICIAL TABLE NOT FOUND"
        )

        # 표 제목 후보만 짧게 보여줌
        candidates = [
            x.strip()
            for x in lines
            if "표 3)" in x
        ]

        for x in candidates[:5]:
            print("   CANDIDATE :", x)

        continue

    production = find_value(
        lines,
        table_idx,
        "생산량"
    )

    domestic = find_value(
        lines,
        table_idx,
        "내수 판매량"
    )

    export = find_value(
        lines,
        table_idx,
        "수출량"
    )

    def fmt(value):

        if value is None:
            return "NOT_FOUND"

        return f"{value:,}"

    status = (
        "CHECK_OK"
        if (
            production is not None
            and domestic is not None
            and export is not None
        )
        else "REVIEW"
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
