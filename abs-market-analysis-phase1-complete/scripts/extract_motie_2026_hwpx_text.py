from pathlib import Path
import zipfile
import xml.etree.ElementTree as ET
import re

# ============================================================
# [작업 목적]
# 2026-02 ~ 2026-08 HWPX 원본의
# 실제 본문 + 표 텍스트를 직접 읽습니다.
#
# ------------------------------------------------------------
# [왜 HWPX부터 읽는가?]
#
# 정부 자료 읽기 우선순위:
#
#   1순위 HWP/HWPX  ← 현재 여기
#   2순위 PDF
#   3순위 공식 웹 본문
#   4순위 검색/미리보기
#
# HWPX는 한글 문서의 XML 구조를 직접 읽을 수 있어
# PDF 변환 과정에서 발생하는 표 깨짐을 피할 수 있습니다.
#
# ------------------------------------------------------------
# [이번 단계에서 하는 일]
#
# ① HWPX 압축 내부 XML 읽기
# ② 한글 문서의 텍스트 추출
# ③ 월별 TXT 저장
# ④ 생산/내수/수출 관련 문맥 화면 출력
#
# ------------------------------------------------------------
# [이번 단계에서 하지 않는 일]
#
# X 숫자 자동 확정
# X BODY_VERIFIED 처리
# X MASTER 병합
#
# ============================================================


BASE = Path("data/raw/motie")

SOURCE_DIR = BASE / "2026_attachments"
TEXT_DIR   = BASE / "2026_hwpx_text"

TEXT_DIR.mkdir(
    parents=True,
    exist_ok=True
)


# ============================================================
# [1] HWPX에서 텍스트 추출
#
# HWPX는 실제로 ZIP 파일입니다.
#
# 내부 예:
#
# Contents/
#   section0.xml
#   section1.xml
#   ...
#
# section XML 안의 텍스트 노드를 순서대로 읽습니다.
# ============================================================

def extract_hwpx_text(file):

    collected = []

    with zipfile.ZipFile(file, "r") as z:

        # --------------------------------------------
        # 본문 section XML만 선택
        # --------------------------------------------

        sections = [
            name
            for name in z.namelist()
            if re.search(
                r"Contents/section\d+\.xml$",
                name,
                re.I
            )
        ]

        # section0 → section1 → section2 순서 보장
        def section_number(name):

            m = re.search(
                r"section(\d+)\.xml$",
                name,
                re.I
            )

            return int(m.group(1)) if m else 9999

        sections.sort(
            key=section_number
        )

        # --------------------------------------------
        # 각 section 읽기
        # --------------------------------------------

        for section in sections:

            raw = z.read(section)

            try:
                root = ET.fromstring(raw)

            except Exception as e:

                collected.append(
                    f"[XML ERROR: {section} / {e}]"
                )

                continue

            # ----------------------------------------
            # XML 태그 namespace를 무시하고
            # 텍스트 노드(t)를 찾습니다.
            # ----------------------------------------

            for elem in root.iter():

                tag = elem.tag.split("}")[-1]

                if tag == "t":

                    text = elem.text

                    if text:

                        text = text.strip()

                        if text:
                            collected.append(text)


    return collected


# ============================================================
# [2] 생산/내수/수출 관련 줄인지 판단
#
# 여기서는 숫자를 고르는 것이 아닙니다.
#
# 사람이 원문 구조를 확인하기 위한
# "후보 문맥"만 찾습니다.
# ============================================================

KEYWORDS = [
    "생산",
    "내수",
    "수출",
    "판매량",
    "생산량",
    "수출량",
    "자동차산업",
    "자동차 산업",
]


def important(text):

    return any(
        word in text
        for word in KEYWORDS
    )


# ============================================================
# [3] 2026년 HWPX 전체 처리
# ============================================================

files = sorted(
    SOURCE_DIR.glob("2026-??_*.hwpx")
)

print("=" * 100)
print("MOTIE 2026 HWPX ORIGINAL TEXT CHECK")
print("=" * 100)

print()
print("HWPX FILES :", len(files))


summary = []


for file in files:

    # 파일명의 앞 7자리 = YYYY-MM
    period = file.name[:7]

    print()
    print("=" * 100)
    print(period, "|", file.name)
    print("=" * 100)

    try:

        texts = extract_hwpx_text(file)

    except Exception as e:

        print(
            "HWPX READ ERROR:",
            e
        )

        summary.append(
            (
                period,
                "ERROR",
                0,
                0
            )
        )

        continue


    # --------------------------------------------
    # TXT 저장
    #
    # 추후 검증할 때 같은 HWPX를 매번 다시
    # 해석하지 않아도 되도록 원문 텍스트 보존
    # --------------------------------------------

    out_file = (
        TEXT_DIR /
        f"{period}.txt"
    )

    out_file.write_text(
        "\n".join(texts),
        encoding="utf-8"
    )


    # --------------------------------------------
    # 핵심 문맥 후보 찾기
    # --------------------------------------------

    indexes = [
        i
        for i, text in enumerate(texts)
        if important(text)
    ]


    print(
        f"TEXT ITEMS : {len(texts)}"
    )

    print(
        f"KEY ITEMS  : {len(indexes)}"
    )


    # --------------------------------------------
    # 너무 많이 출력하면 확인이 어려우므로
    # 우선 앞쪽 핵심 문맥 25개까지만 출력
    #
    # 각 후보의 앞뒤 2개 항목도 같이 표시
    # --------------------------------------------

    shown_ranges = set()

    for i in indexes[:25]:

        start = max(
            0,
            i - 2
        )

        end = min(
            len(texts),
            i + 3
        )

        key = (
            start,
            end
        )

        if key in shown_ranges:
            continue

        shown_ranges.add(key)

        print()
        print(
            f"--- ITEM {i+1} ---"
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
                f"{texts[j]}"
            )


    # --------------------------------------------
    # 간단 상태 기록
    # --------------------------------------------

    status = (
        "TEXT_OK"
        if len(texts) > 0
        else "EMPTY"
    )

    summary.append(
        (
            period,
            status,
            len(texts),
            len(indexes)
        )
    )


# ============================================================
# [4] 최종 요약
# ============================================================

print()
print("=" * 100)
print("RESULT")
print("=" * 100)

for (
    period,
    status,
    text_count,
    key_count
) in summary:

    print(
        f"{period} | "
        f"{status} | "
        f"TEXT={text_count} | "
        f"KEY={key_count}"
    )


print()
print(
    "TEXT OUTPUT :",
    TEXT_DIR
)

print()
print(
    "※ HWPX 원문 텍스트만 추출"
)

print(
    "※ 숫자 확정 안 함"
)

print(
    "※ BODY_VERIFIED 처리 안 함"
)

print(
    "※ MASTER 변경 없음"
)
