from __future__ import annotations

import re
from pathlib import Path

import pandas as pd


BASE_DIR = Path(__file__).resolve().parents[1]

TEXT_DIR = (
    BASE_DIR
    / "data"
    / "raw"
    / "motie"
    / "monthly_pdf"
    / "text"
)

OUTPUT_FILE = (
    BASE_DIR
    / "data"
    / "raw"
    / "motie"
    / "motie_pdf_metrics.csv"
)

def clean_text(text: str) -> str:
    text = text.replace("\xa0", " ")
    text = text.replace("\u200b", "")
    text = text.replace("△", "-")

    text = re.sub(
        r"[ \t]+",
        " ",
        text,
    )

    return text


def number(value: str) -> int:
    return int(
        value.replace(",", "")
    )


def find_first(
    text: str,
    patterns: list[str],
):
    for pattern in patterns:
        match = re.search(
            pattern,
            text,
            flags=re.MULTILINE,
        )

        if match:
            try:
                return number(
                    match.group(1)
                )
            except Exception:
                continue

    return None


def extract_metrics(text: str) -> dict:

    text = clean_text(text)

    production = find_first(
        text,
        [
            # 예: 189,235대 생산
            r"(\d{1,3}(?:,\d{3})+)\s*대\s*생산",

            # 예: 생산량 290,590
            r"생산량\s+(\d{1,3}(?:,\d{3})+)",

            # 표 형식
            r"생\s*산\s+(\d{1,3}(?:,\d{3})+)",
        ],
    )

    domestic = find_first(
        text,
        [
            # 예: 97,897대 판매
            r"\(내수\)[\s\S]{0,250}?"
            r"(\d{1,3}(?:,\d{3})+)\s*대\s*판매",

            # 예: 내수 판매량 105,928
            r"내수\s*판매량\s+"
            r"(\d{1,3}(?:,\d{3})+)",

            # 표 형식
            r"내\s*수\s+"
            r"(\d{1,3}(?:,\d{3})+)",
        ],
    )

    export = find_first(
        text,
        [
            # 예: 감소(123,022대)
            r"\(수출\)[\s\S]{0,300}?"
            r"(?:감소|증가)"
            r"[\s\S]{0,80}?"
            r"(\d{1,3}(?:,\d{3})+)\s*대",

            # 예: 수출량 199,663
            r"수출량\s+"
            r"(\d{1,3}(?:,\d{3})+)",

            # 업체별 수출현황 합계
            r"업체별\s*수출\s*현황"
            r"[\s\S]{0,500}?"
            r"합\s*계\s+"
            r"(\d{1,3}(?:,\d{3})+)",
        ],
    )

    return {
        "production": production,
        "domestic": domestic,
        "export": export,
    }


def main():

    rows = []

    files = sorted(
        TEXT_DIR.glob("*.txt")
    )

    print("=" * 72)
    print("MOTIE PDF METRIC TEST")
    print("=" * 72)

    for path in files:

        period = path.stem

        text = path.read_text(
            encoding="utf-8",
            errors="replace",
        )

        metrics = extract_metrics(
            text
        )

        text_chars = len(
            re.sub(r"\s+", "", text)
        )

        usable = text_chars > 100

        row = {
            "period": period,
            "text_chars": text_chars,
            "usable_text": usable,
            **metrics,
        }

        rows.append(row)

        print(
            period,
            f"CHARS={text_chars}",
            f"P={metrics['production']}",
            f"D={metrics['domestic']}",
            f"E={metrics['export']}",
        )

    df = pd.DataFrame(rows)

    df.to_csv(
        OUTPUT_FILE,
        index=False,
        encoding="utf-8-sig",
    )

    print()
    print("=" * 72)
    print("RESULT")
    print("=" * 72)
    print("FILES :", len(df))
    print("OUTPUT:", OUTPUT_FILE)


if __name__ == "__main__":
    main()