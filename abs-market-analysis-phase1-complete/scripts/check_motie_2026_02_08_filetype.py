from pathlib import Path

# ============================================================
# [작업 목적]
# 2026-02 / 2026-08 첨부파일의 "실제 파일 형식" 확인
#
# [왜 확인하는가?]
# 확장자는 .hwpx인데 ZIP/HWPX 방식으로 열리지 않았습니다.
# 따라서 파일 내용 자체가
#   - 정상 HWPX
#   - 구형 HWP
#   - PDF
#   - HTML/기타
# 중 무엇인지 확인합니다.
#
# [이번 단계]
# 파일 형식 확인만 수행
# 숫자 추출 X
# VERIFIED 변경 X
# MASTER 변경 X
# ============================================================

from pathlib import Path

BASE = Path("data/raw/motie/2026_attachments")


def detect_type(path):

    data = path.read_bytes()

    # PDF
    if data.startswith(b"%PDF"):
        return "PDF"

    # 구형 HWP = OLE Compound File
    if data.startswith(
        bytes.fromhex("D0CF11E0A1B11AE1")
    ):
        return "HWP_OLE"

    # 정상 HWPX = ZIP
    if data.startswith(b"PK"):
        return "HWPX_ZIP"

    # 혹시 HTML이 저장된 경우
    head = data[:1000].lower()

    if (
        b"<html" in head
        or b"<!doctype html" in head
    ):
        return "HTML"

    return "UNKNOWN"


print("=" * 70)
print("2026-02 / 2026-08 REAL FILE TYPE")
print("=" * 70)

for period in ["2026-02", "2026-08"]:

    files = sorted(
        BASE.glob(f"{period}_*")
    )

    for path in files:

        print(
            f"{path.name} | "
            f"SIZE={path.stat().st_size:,} | "
            f"TYPE={detect_type(path)}"
        )

print("=" * 70)
print("VERIFIED : UNCHANGED")
print("MASTER   : UNCHANGED")
