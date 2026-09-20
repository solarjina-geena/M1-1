from pathlib import Path
import re

# ============================================================
# [작업 목적]
# 2026년 원문에서 생산 / 내수 / 수출과 관련된
# "숫자가 들어 있는 핵심 문장"만 화면에 보여줍니다.
#
# [왜 하는가?]
# 단순히 "생산"이라는 단어 근처 첫 숫자를 가져오면
# 증가율, 누적실적, 친환경차 실적 등을 잘못 가져올 수 있습니다.
#
# 따라서 자동 숫자 추출 전에
# 실제 원문 문장이 어떤 구조인지 확인합니다.
#
# [입력]
# data/raw/motie/2026_body_text/*.txt
#
# [출력]
# 터미널 확인용
#
# [중요]
# - 파일 수정 없음
# - VERIFIED 처리 없음
# - MASTER 변경 없음
# ============================================================


# ------------------------------------------------------------
# [1단계] 저장된 2026년 본문 폴더
# ------------------------------------------------------------

TEXT_DIR = Path(
    "data/raw/motie/2026_body_text"
)


# ------------------------------------------------------------
# [2단계] 확인할 월
#
# 1월은 본문에 지표가 없었으므로 일단 제외합니다.
# 2~8월의 본문 구조부터 확인합니다.
# ------------------------------------------------------------

PERIODS = [
    "2026-02",
    "2026-03",
    "2026-04",
    "2026-05",
    "2026-06",
    "2026-07",
    "2026-08",
]


# ------------------------------------------------------------
# [3단계] 숫자가 포함된 자동차산업 핵심 줄 판별
#
# 조건:
# - 생산 / 내수 / 수출 중 하나가 있어야 함
# - 숫자도 있어야 함
#
# 너무 넓게 출력하지 않기 위해
# 핵심 키워드가 있는 줄만 골라냅니다.
# ------------------------------------------------------------

def is_candidate(line):

    # 숫자가 하나도 없으면 제외
    if not re.search(r"\d", line):
        return False

    # 자동차산업 핵심 지표
    metric_words = [
        "생산",
        "내수",
        "수출"
    ]

    if not any(
        word in line
        for word in metric_words
    ):
        return False

    return True


# ------------------------------------------------------------
# [4단계] 월별 핵심 문맥 출력
#
# 한 줄만 보면 표의 앞뒤 관계를 알 수 없는 경우가 있으므로
# 후보 줄의 앞 1줄 + 현재 줄 + 뒤 1줄을 같이 보여줍니다.
#
# 동일한 블록은 중복 출력하지 않습니다.
# ------------------------------------------------------------

for period in PERIODS:

    file = TEXT_DIR / f"{period}.txt"

    print()
    print("=" * 100)
    print(period, "BODY METRIC CHECK")
    print("=" * 100)

    if not file.exists():

        print("TEXT FILE NOT FOUND")
        continue

    text = file.read_text(
        encoding="utf-8",
        errors="ignore"
    )

    lines = [
        x.strip()
        for x in text.splitlines()
        if x.strip()
    ]

    candidate_indexes = []

    for i, line in enumerate(lines):

        if is_candidate(line):
            candidate_indexes.append(i)

    # --------------------------------------------------------
    # 너무 많은 줄이 검색될 수 있으므로
    # 앞쪽 핵심 후보 최대 20개만 확인
    # --------------------------------------------------------

    candidate_indexes = candidate_indexes[:20]

    if not candidate_indexes:

        print("NO NUMERIC METRIC LINE")
        continue

    shown = set()

    for i in candidate_indexes:

        start = max(
            0,
            i - 1
        )

        end = min(
            len(lines),
            i + 2
        )

        block_key = (
            start,
            end
        )

        if block_key in shown:
            continue

        shown.add(block_key)

        print()
        print(
            f"--- LINE {i+1} ---"
        )

        for j in range(
            start,
            end
        ):

            marker = (
                ">>"
                if j == i
                else "  "
            )

            print(
                f"{marker} {j+1}: "
                f"{lines[j]}"
            )


# ------------------------------------------------------------
# [5단계] 안내
# ------------------------------------------------------------

print()
print("=" * 100)
print("CHECK COMPLETE")
print("=" * 100)

print()
print(
    "※ 숫자를 아직 저장하지 않았습니다."
)

print(
    "※ BODY_VERIFIED 처리하지 않았습니다."
)

print(
    "※ MASTER 변경 없음"
)
