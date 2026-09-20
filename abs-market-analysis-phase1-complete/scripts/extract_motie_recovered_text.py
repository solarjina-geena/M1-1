from __future__ import annotations

import re
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

try:
    import pdfplumber
except ImportError:
    pdfplumber = None


BASE_DIR = Path(__file__).resolve().parents[1]

SOURCE_DIR = (
    BASE_DIR
    / "data"
    / "raw"
    / "motie"
    / "monthly_pdf"
    / "recovered_pdf"
)

OUTPUT_DIR = (
    BASE_DIR
    / "data"
    / "raw"
    / "motie"
    / "monthly_pdf"
    / "recovered_text"
)


def canonical_period(stem: str) -> str:
    """
    2016-10_01 -> 2016-10
    2016-10_02 -> 2016-10
    """
    m = re.match(r"^(\d{4}-\d{2})", stem)
    return m.group(1) if m else stem


def extract_pdf(path: Path) -> str:
    if pdfplumber is None:
        raise RuntimeError(
            "pdfplumber가 없습니다. "
            "python -m pip install pdfplumber 실행 필요"
        )

    pages = []

    with pdfplumber.open(path) as pdf:
        for i, page in enumerate(pdf.pages, start=1):
            text = page.extract_text() or ""

            pages.append(
                f"\n===== PAGE {i} =====\n\n{text}"
            )

    return "\n".join(pages)


def extract_hwpx(path: Path) -> str:
    """
    HWPX는 ZIP/XML 구조이므로 별도 프로그램 없이
    XML의 텍스트 노드를 읽는다.
    """
    chunks = []

    with zipfile.ZipFile(path, "r") as zf:
        names = sorted(
            n for n in zf.namelist()
            if n.startswith("Contents/section")
            and n.endswith(".xml")
        )

        for name in names:
            raw = zf.read(name)

            root = ET.fromstring(raw)

            section_text = []

            for elem in root.iter():
                tag = elem.tag.split("}")[-1]

                if tag == "t" and elem.text:
                    section_text.append(elem.text)

                elif tag in {"p", "lineBreak"}:
                    section_text.append("\n")

            chunks.append(
                "\n".join(section_text)
            )

    return "\n".join(chunks)


def text_score(text: str) -> int:
    return len(
        re.sub(r"\s+", "", text)
    )


def main():

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    # 342 byte 실패 PDF 같은 파일 제외
    files = [
        p for p in SOURCE_DIR.iterdir()
        if p.is_file()
        and p.stat().st_size > 10000
        and p.suffix.lower() in {".pdf", ".hwpx"}
    ]

    files = sorted(files)

    candidates = {}

    print("=" * 88)
    print("MOTIE RECOVERED SOURCE -> TEXT")
    print("=" * 88)

    for path in files:

        period = canonical_period(path.stem)
        ext = path.suffix.lower()

        try:
            if ext == ".pdf":
                text = extract_pdf(path)

            elif ext == ".hwpx":
                text = extract_hwpx(path)

            else:
                continue

            chars = text_score(text)

            print(
                f"{path.name:<22}",
                f"PERIOD={period}",
                f"CHARS={chars}",
            )

            # 같은 월에 원본이 여러 개면
            # 텍스트가 더 많이 나온 파일을 우선 선택
            current = candidates.get(period)

            if (
                current is None
                or chars > current["chars"]
            ):
                candidates[period] = {
                    "source": path,
                    "text": text,
                    "chars": chars,
                }

        except Exception as e:
            print(
                f"{path.name:<22}",
                "ERROR",
                repr(e),
            )

    print()
    print("=" * 88)
    print("WRITE CANONICAL TEXT")
    print("=" * 88)

    written = 0

    for period in sorted(candidates):

        item = candidates[period]

        out = OUTPUT_DIR / f"{period}.txt"

        out.write_text(
            item["text"],
            encoding="utf-8",
        )

        written += 1

        print(
            period,
            "<-",
            item["source"].name,
            f"CHARS={item['chars']}",
        )

    print()
    print("=" * 88)
    print("RESULT")
    print("=" * 88)
    print("SOURCE FILES :", len(files))
    print("TEXT PERIODS :", written)
    print("OUTPUT       :", OUTPUT_DIR)


if __name__ == "__main__":
    main()
