from pathlib import Path
import zipfile

# ============================================================
# [작업 목적]
#
# ① 2026-02 / 2026-08 파일이 왜 HWPX로 안 읽히는지 확인
# ② 정상 HWPX(3~7월)의 "생산/내수/수출량 표" 주변을
#    넓게 출력하여 정확한 대수 확인
#
# ------------------------------------------------------------
# [중요]
#
# 이번에도:
# X MASTER 변경 안 함
# X VERIFIED 처리 안 함
# X 숫자 자동 저장 안 함
#
# 먼저 사람이 공식 표 구조를 확인합니다.
# ============================================================

BASE = Path("data/raw/motie")
ATTACH = BASE / "2026_attachments"
TEXT   = BASE / "2026_hwpx_text"


# ============================================================
# [1] 2월 / 8월 실제 파일 형식 확인
#
# 확장자가 .hwpx여도 실제 파일이
# HWP 또는 다른 형식일 수 있습니다.
#
# 파일 앞부분(signature)을 보면 구분할 수 있습니다.
# ============================================================

print("=" * 100)
print("2026-02 / 2026-08 FILE TYPE DIAGNOSIS")
print("=" * 100)

for period in ["2026-02", "2026-08"]:

    files = sorted(ATTACH.glob(f"{period}_*"))

    print()
    print("###", period)

    for f in files:

        raw = f.read_bytes()[:32]

        print()
        print("FILE :", f.name)
        print("SIZE :", f.stat().st_size)
        print("HEAD :", raw.hex(" "))

        if raw.startswith(b"PK"):
            detected = "ZIP/HWPX"

        elif raw.startswith(b"%PDF"):
            detected = "PDF"

        elif raw.startswith(bytes.fromhex("D0CF11E0A1B11AE1")):
            detected = "HWP/OLE"

        else:
            detected = "UNKNOWN"

        print("TYPE :", detected)


# ============================================================
# [2] 정상 추출된 3~7월 TXT에서
#     공식 생산/내수/수출량 표 찾기
#
# 본문에는 '39.4만대'처럼 반올림 값이 있습니다.
#
# MASTER에는 가능하면 공식 표의
# 정확한 대수 값을 사용해야 합니다.
# ============================================================

print()
print("=" * 100)
print("2026-03 ~ 2026-07 OFFICIAL TABLE CHECK")
print("=" * 100)


for period in [
    "2026-03",
    "2026-04",
    "2026-05",
    "2026-06",
    "2026-07",
]:

    file = TEXT / f"{period}.txt"

    print()
    print("=" * 100)
    print(period)
    print("=" * 100)

    if not file.exists():

        print("TEXT FILE NOT FOUND")
        continue

    lines = file.read_text(
        encoding="utf-8"
    ).splitlines()


    # --------------------------------------------------------
    # 공식 표 제목 후보
    # --------------------------------------------------------

    candidates = []

    for i, line in enumerate(lines):

        normalized = line.replace(" ", "")

        # 가장 강한 조건:
        # 한 줄에 생산/내수/수출 관련 표 제목이 있는 경우
        if (
            "생산" in normalized
            and "내수" in normalized
            and "수출" in normalized
        ):
            candidates.append(i)

        # 표가 줄바꿈되어 있을 수도 있으므로
        # '잠정실적 수치'도 후보로 사용
        elif "잠정실적수치" in normalized:
            candidates.append(i)


    # 중복 제거
    candidates = sorted(set(candidates))


    if not candidates:

        print("TABLE CANDIDATE NOT FOUND")
        continue


    print(
        "TABLE CANDIDATES:",
        len(candidates)
    )


    # --------------------------------------------------------
    # 후보 주변 140개 항목 출력
    #
    # HWPX 표는 셀 하나가 텍스트 한 줄로
    # 떨어지는 경우가 많기 때문에 넓게 봅니다.
    # --------------------------------------------------------

    for n, idx in enumerate(
        candidates[:4],
        start=1
    ):

        print()
        print(
            f"--- TABLE CANDIDATE {n} / "
            f"ITEM {idx+1} ---"
        )

        start = max(
            0,
            idx - 10
        )

        end = min(
            len(lines),
            idx + 140
        )

        for j in range(start, end):

            marker = (
                ">>"
                if j == idx
                else "  "
            )

            print(
                f"{marker} {j+1:4}: "
                f"{lines[j]}"
            )


print()
print("=" * 100)
print("CHECK COMPLETE")
print("=" * 100)

print()
print("※ 정확한 표 구조 확인 단계")
print("※ 숫자 저장 안 함")
print("※ VERIFIED 처리 안 함")
print("※ MASTER 변경 없음")
