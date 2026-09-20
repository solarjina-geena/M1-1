from pathlib import Path
import olefile
import zlib
import struct
import re

# ============================================================
# [작업 목적]
# 2026-02 / 2026-08의 실제 HWP(OLE) 원본에서
# 본문 텍스트를 추출하고 자동차 생산/내수/수출 표를 확인합니다.
#
# [확인된 사실]
# 파일명 : *.hwpx
# 실제형식 : HWP_OLE
#
# 따라서 HWPX ZIP/XML 방식이 아니라
# 구형 HWP BodyText 방식으로 읽습니다.
#
# [안전 원칙]
# 1. 원본 파일 수정 안 함
# 2. 추출 텍스트 별도 저장
# 3. 숫자 자동 VERIFIED 안 함
# 4. MASTER 변경 안 함
# ============================================================

BASE = Path("data/raw/motie/2026_attachments")
TEXT_DIR = Path("data/raw/motie/2026_hwp_text")
TEXT_DIR.mkdir(parents=True, exist_ok=True)

TARGETS = {
    "2026-02": BASE / "2026-02_02.hwpx",
    "2026-08": BASE / "2026-08_02.hwpx",
}


# ============================================================
# [HWP 레코드에서 텍스트 추출]
#
# HWP BodyText Section 내부는 여러 레코드로 구성됩니다.
# HWPTAG_PARA_TEXT(67) 레코드만 골라
# UTF-16LE 문자열을 읽습니다.
# ============================================================

def extract_para_text(section_data):

    texts = []
    pos = 0

    while pos + 4 <= len(section_data):

        header = struct.unpack_from(
            "<I",
            section_data,
            pos
        )[0]

        tag_id = header & 0x3FF
        size = (header >> 20) & 0xFFF

        pos += 4

        # 확장 크기 레코드
        if size == 0xFFF:

            if pos + 4 > len(section_data):
                break

            size = struct.unpack_from(
                "<I",
                section_data,
                pos
            )[0]

            pos += 4

        if pos + size > len(section_data):
            break

        payload = section_data[
            pos:pos + size
        ]

        pos += size

        # HWPTAG_PARA_TEXT = 67
        if tag_id != 67:
            continue

        try:
            text = payload.decode(
                "utf-16le",
                errors="ignore"
            )
        except Exception:
            continue

        # HWP 제어문자 정리
        text = re.sub(
            r"[\x00-\x08\x0b\x0c\x0e-\x1f]",
            " ",
            text
        )

        text = re.sub(
            r"\s+",
            " ",
            text
        ).strip()

        if text:
            texts.append(text)

    return texts


# ============================================================
# [HWP 전체 본문 읽기]
# ============================================================

def extract_hwp(path):

    ole = olefile.OleFileIO(str(path))

    try:

        # ----------------------------------------------------
        # 압축 여부 확인
        # FileHeader 37번째 바이트의 bit 0
        # ----------------------------------------------------

        header = ole.openstream(
            "FileHeader"
        ).read()

        compressed = bool(
            header[36] & 0x01
        )

        # ----------------------------------------------------
        # BodyText/Section 번호 수집
        # ----------------------------------------------------

        sections = []

        for item in ole.listdir():

            joined = "/".join(item)

            if joined.startswith(
                "BodyText/Section"
            ):
                try:
                    no = int(
                        item[-1].replace(
                            "Section",
                            ""
                        )
                    )
                    sections.append(
                        (no, joined)
                    )
                except ValueError:
                    pass

        sections.sort()

        all_text = []

        for _, stream_name in sections:

            data = ole.openstream(
                stream_name
            ).read()

            if compressed:

                try:
                    data = zlib.decompress(
                        data,
                        -15
                    )
                except Exception:
                    continue

            all_text.extend(
                extract_para_text(data)
            )

        return all_text

    finally:
        ole.close()


# ============================================================
# [표 후보 탐색]
#
# 문서 전체에서 단순히 "수출량" 첫 항목을 잡지 않습니다.
#
# 생산 + 내수 + 수출이 함께 나타나는 문단을 우선 찾고,
# 없으면 "생산량" 위치를 기준으로 주변 문단을 보여줍니다.
# ============================================================

def find_table_area(lines):

    candidates = []

    for i, line in enumerate(lines):

        compact = line.replace(" ", "")

        if (
            "생산" in compact
            and "내수" in compact
            and "수출" in compact
        ):
            candidates.append(i)

    # 공식 표 제목으로 보이는 후보 우선
    for i in candidates:

        if (
            "표" in lines[i]
            or "생산량" in lines[i]
        ):
            return i

    # 생산량 행을 차선책으로 사용
    for i, line in enumerate(lines):

        if "생산량" in line.replace(" ", ""):
            return i

    return None


# ============================================================
# 실행
# ============================================================

print("=" * 76)
print("2026-02 / 2026-08 HWP BODY CHECK")
print("=" * 76)

for period, path in TARGETS.items():

    print()
    print(f"[{period}]")

    if not path.exists():

        print("FILE NOT FOUND")
        continue

    try:

        lines = extract_hwp(path)

    except Exception as e:

        print(
            "HWP READ ERROR :",
            type(e).__name__,
            str(e)
        )
        continue

    # --------------------------------------------------------
    # 추출 결과는 반드시 별도 보존
    # 나중에 다시 HWP를 읽지 않아도 됩니다.
    # --------------------------------------------------------

    text_path = (
        TEXT_DIR /
        f"{period}.txt"
    )

    text_path.write_text(
        "\n".join(lines),
        encoding="utf-8"
    )

    print(
        f"TEXT : {len(lines):,} paragraphs"
    )

    idx = find_table_area(lines)

    if idx is None:

        print("TABLE AREA : NOT FOUND")
        continue

    print("TABLE AREA : FOUND")

    # --------------------------------------------------------
    # 너무 길게 출력하지 않습니다.
    # 표 후보 주변 최대 18문단만 확인합니다.
    # --------------------------------------------------------

    start = max(0, idx - 2)
    end = min(
        len(lines),
        idx + 16
    )

    for j in range(start, end):

        text = lines[j]

        # 긴 문단은 화면 출력만 축약
        # 저장된 TXT에는 원문 전체가 그대로 있습니다.
        if len(text) > 300:
            text = text[:300] + " ..."

        print(
            f"{j+1:04d} | {text}"
        )


print()
print("=" * 76)
print("CHECK COMPLETE")
print("=" * 76)
print("숫자 VERIFIED : NO")
print("MASTER        : UNCHANGED")
