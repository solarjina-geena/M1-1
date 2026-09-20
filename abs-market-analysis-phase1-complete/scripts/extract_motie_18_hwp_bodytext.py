from pathlib import Path
import re
import struct
import zlib
import pandas as pd
import olefile

BASE = Path("data/raw/motie")
SRC = BASE / "monthly_pdf" / "verified_download_24"
OUT_DIR = BASE / "monthly_pdf" / "verified_download_24_text"
OUT_DIR.mkdir(parents=True, exist_ok=True)

RESULT = BASE / "motie_18_hwp_text_check.csv"


def get_hwp_compressed(ole):
    try:
        data = ole.openstream("\x05HwpSummaryInformation").read()
    except:
        return True

    # FileHeader에서 직접 확인하는 것이 더 정확
    try:
        header = ole.openstream("FileHeader").read()
        flags = struct.unpack("<I", header[36:40])[0]
        return bool(flags & 0x01)
    except:
        return True


def extract_section_text(data):
    pos = 0
    texts = []

    while pos + 4 <= len(data):

        header = struct.unpack_from("<I", data, pos)[0]

        tag_id = header & 0x3FF
        level = (header >> 10) & 0x3FF
        size = (header >> 20) & 0xFFF

        pos += 4

        if size == 0xFFF:
            if pos + 4 > len(data):
                break

            size = struct.unpack_from("<I", data, pos)[0]
            pos += 4

        if pos + size > len(data):
            break

        record = data[pos:pos + size]
        pos += size

        # HWPTAG_PARA_TEXT = 67
        if tag_id != 67:
            continue

        try:
            text = record.decode(
                "utf-16le",
                errors="ignore"
            )
        except:
            continue

        # HWP 제어문자 제거
        text = re.sub(
            r"[\x00-\x08\x0b\x0c\x0e-\x1f]",
            " ",
            text
        )

        text = re.sub(r"\s+", " ", text).strip()

        if text:
            texts.append(text)

    return "\n".join(texts)


def extract_hwp(path):

    ole = olefile.OleFileIO(str(path))

    try:
        streams = ole.listdir()

        sections = []

        for item in streams:
            name = "/".join(item)

            if name.startswith("BodyText/Section"):
                sections.append(name)

        sections.sort(
            key=lambda x:
            int(re.search(r"Section(\d+)", x).group(1))
        )

        compressed = get_hwp_compressed(ole)

        result = []

        for section in sections:

            data = ole.openstream(section).read()

            if compressed:
                try:
                    data = zlib.decompress(
                        data,
                        -15
                    )
                except Exception:
                    pass

            text = extract_section_text(data)

            if text:
                result.append(text)

        return "\n".join(result)

    finally:
        ole.close()


def detect_periods(text):

    found = []

    patterns = [
        r"(20\d{2})\s*년\s*(\d{1,2})\s*월",
        r"[’'‘]?\s*(\d{2})\s*년\s*(\d{1,2})\s*월",
        r"[’'‘]?\s*(\d{2})\s*[.]\s*(\d{1,2})\s*월",
    ]

    for pattern in patterns:

        for y, m in re.findall(pattern, text):

            yy = int(y)
            mm = int(m)

            if yy < 100:
                yy += 2000

            if 2015 <= yy <= 2026 and 1 <= mm <= 12:

                period = f"{yy:04d}-{mm:02d}"

                if period not in found:
                    found.append(period)

    return found


rows = []

files = sorted(SRC.glob("*.hwp"))

print("=" * 100)
print("MOTIE HWP BODYTEXT EXTRACTION")
print("=" * 100)
print("HWP FILES :", len(files))
print()

for path in files:

    period = path.stem

    try:

        text = extract_hwp(path)

        chars = len(
            re.sub(r"\s+", "", text)
        )

        dates = detect_periods(text[:50000])

        txt_path = OUT_DIR / f"{period}.txt"

        txt_path.write_text(
            text,
            encoding="utf-8"
        )

        if period in dates:
            status = "MATCH"
        elif chars > 100:
            status = "REVIEW"
        else:
            status = "EMPTY"

        rows.append({
            "period": period,
            "file": path.name,
            "chars": chars,
            "status": status,
            "detected_periods": ",".join(dates[:15]),
        })

        print(
            f"{period} | "
            f"CHARS={chars} | "
            f"{status}"
        )

        if status != "MATCH":
            print(
                "  DATES:",
                ", ".join(dates[:10]) or "NONE"
            )

    except Exception as e:

        rows.append({
            "period": period,
            "file": path.name,
            "chars": 0,
            "status": "ERROR",
            "detected_periods": "",
        })

        print(
            period,
            "| ERROR |",
            type(e).__name__,
            str(e)[:180]
        )


df = pd.DataFrame(rows)

df.to_csv(
    RESULT,
    index=False,
    encoding="utf-8-sig"
)

print()
print("=" * 100)
print("RESULT")
print("=" * 100)

print("FILES  :", len(df))
print("MATCH  :", (df["status"] == "MATCH").sum())
print("REVIEW :", (df["status"] == "REVIEW").sum())
print("EMPTY  :", (df["status"] == "EMPTY").sum())
print("ERROR  :", (df["status"] == "ERROR").sum())

bad = df[df["status"] != "MATCH"]

if len(bad):

    print()
    print("=== REVIEW ===")

    for _, r in bad.iterrows():

        print(
            r["period"],
            "|",
            r["status"],
            "|",
            r["detected_periods"] or "NONE"
        )

print()
print("TEXT   :", OUT_DIR)
print("OUTPUT :", RESULT)
