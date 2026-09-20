from pathlib import Path
import re
import zipfile
import html
import pandas as pd

BASE = Path("data/raw/motie")
SRC = BASE / "monthly_pdf" / "verified_download_24"
OUT = BASE / "motie_24_content_validation.csv"

def clean(s):
    s = html.unescape(s or "")
    s = re.sub(r"<[^>]+>", " ", s)
    s = re.sub(r"\s+", " ", s)
    return s.strip()

def extract_hwpx(path):
    parts = []

    with zipfile.ZipFile(path) as z:
        names = [
            n for n in z.namelist()
            if n.startswith("Contents/")
            and n.lower().endswith(".xml")
        ]

        for name in sorted(names):
            raw = z.read(name).decode(
                "utf-8",
                errors="replace"
            )
            parts.append(clean(raw))

    return "\n".join(parts)

def extract_hwp(path):
    try:
        import olefile
    except ImportError:
        raise RuntimeError(
            "olefile 없음: python -m pip install olefile"
        )

    ole = olefile.OleFileIO(path)

    try:
        # HWP 본문은 압축되어 있을 수 있으므로
        # 기존 설치 라이브러리 사용 가능 여부를 먼저 확인
        from scripts.extract_motie_recovered_text import extract_hwp
        return extract_hwp(path)

    except (ImportError, AttributeError):
        # 현재 프로젝트 extractor에 HWP 함수가 없으면
        # 우선 메타/미리보기 텍스트를 수집
        parts = []

        for stream in ole.listdir():
            name = "/".join(stream)

            if any(
                x in name
                for x in [
                    "PrvText",
                    "SummaryInformation"
                ]
            ):
                try:
                    data = ole.openstream(stream).read()

                    for enc in [
                        "utf-16le",
                        "utf-8",
                        "cp949"
                    ]:
                        try:
                            text = data.decode(
                                enc,
                                errors="ignore"
                            )
                            if text.strip():
                                parts.append(text)
                                break
                        except:
                            pass
                except:
                    pass

        return "\n".join(parts)

    finally:
        ole.close()

def detect_periods(text):
    found = []

    patterns = [
        # 2020년 8월
        r"(20\d{2})\s*년\s*(\d{1,2})\s*월",

        # '20년 8월
        r"[’'‘]?\s*(\d{2})\s*년\s*(\d{1,2})\s*월",

        # '20.8월
        r"[’'‘]?\s*(\d{2})\s*[.]\s*(\d{1,2})\s*월",
    ]

    for pattern in patterns:
        for y, m in re.findall(pattern, text):

            yy = int(y)
            mm = int(m)

            if yy < 100:
                yy += 2000

            if 2015 <= yy <= 2026 and 1 <= mm <= 12:
                value = f"{yy:04d}-{mm:02d}"

                if value not in found:
                    found.append(value)

    return found

rows = []

print("=" * 100)
print("MOTIE 24 CONTENT VALIDATION")
print("=" * 100)

for path in sorted(SRC.iterdir()):

    if not path.is_file():
        continue

    period = path.stem
    ext = path.suffix.lower()

    status = "ERROR"
    chars = 0
    dates = []
    preview = ""
    error = ""

    try:
        if ext == ".hwpx":
            text = extract_hwpx(path)

        elif ext == ".hwp":
            text = extract_hwp(path)

        else:
            text = ""

        chars = len(
            re.sub(r"\s+", "", text)
        )

        sample = clean(text[:30000])

        dates = detect_periods(sample)

        preview = sample[:300]

        if period in dates:
            status = "MATCH"

        elif chars < 100:
            status = "TEXT_INSUFFICIENT"

        else:
            status = "REVIEW"

    except Exception as e:
        error = (
            type(e).__name__
            + ": "
            + str(e)
        )

    rows.append({
        "period": period,
        "file": path.name,
        "type": ext,
        "chars": chars,
        "status": status,
        "detected_periods": ",".join(dates[:15]),
        "preview": preview,
        "error": error,
    })

    print(
        f"{period} | "
        f"{ext} | "
        f"CHARS={chars} | "
        f"{status}"
    )

    if status != "MATCH":
        print(
            "  DATES:",
            ", ".join(dates[:10]) or "NONE"
        )

        if error:
            print(
                "  ERROR:",
                error[:180]
            )

df = pd.DataFrame(rows)

df.to_csv(
    OUT,
    index=False,
    encoding="utf-8-sig"
)

print()
print("=" * 100)
print("RESULT")
print("=" * 100)

print("FILES             :", len(df))
print("MATCH             :", (df["status"] == "MATCH").sum())
print("REVIEW            :", (df["status"] == "REVIEW").sum())
print(
    "TEXT INSUFFICIENT :",
    (df["status"] == "TEXT_INSUFFICIENT").sum()
)
print("ERROR             :", (df["status"] == "ERROR").sum())

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
print("OUTPUT :", OUT)
