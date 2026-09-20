from pathlib import Path
import olefile
import zlib
import struct
import re

src = Path(
    "data/raw/motie/monthly_pdf/"
    "verified_download_24/2019-04.hwp"
)

print("=" * 100)
print("2019-04 HWP RAW RECORD CHECK")
print("=" * 100)

ole = olefile.OleFileIO(str(src))

streams = [
    "/".join(x)
    for x in ole.listdir()
    if x[0] == "BodyText"
]

print("BODY STREAMS:", len(streams))

for stream in streams:

    raw = ole.openstream(stream).read()

    try:
        data = zlib.decompress(raw, -15)
    except:
        data = raw

    pos = 0
    texts = []

    while pos + 4 <= len(data):

        header = struct.unpack_from("<I", data, pos)[0]

        tag_id = header & 0x3FF
        size = (header >> 20) & 0xFFF
        pos += 4

        if size == 0xFFF:
            if pos + 4 > len(data):
                break
            size = struct.unpack_from("<I", data, pos)[0]
            pos += 4

        payload = data[pos:pos + size]
        pos += size

        # HWPTAG_PARA_TEXT
        if tag_id != 67:
            continue

        try:
            txt = payload.decode(
                "utf-16le",
                errors="ignore"
            )
        except:
            continue

        # 제어문자 정리
        txt = re.sub(
            r"[\x00-\x08\x0b\x0c\x0e-\x1f]",
            " ",
            txt
        )

        txt = re.sub(r"\s+", " ", txt).strip()

        if txt:
            texts.append(txt)

    joined = "\n".join(texts)

    keywords = [
        "생산",
        "내수",
        "수출",
        "합계",
        "총계",
        "자동차"
    ]

    if any(k in joined for k in keywords):

        print()
        print("-" * 100)
        print("STREAM:", stream)
        print("-" * 100)

        lines = joined.splitlines()

        for i, line in enumerate(lines):

            if any(k in line for k in keywords):

                start = max(0, i - 3)
                end = min(len(lines), i + 8)

                for j in range(start, end):
                    print(f"{j+1}: {lines[j]}")

                print()

ole.close()

print("=" * 100)
print("DONE")
print("=" * 100)
