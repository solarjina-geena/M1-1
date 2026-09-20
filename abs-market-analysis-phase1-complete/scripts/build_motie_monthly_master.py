from __future__ import annotations

import re
import time
from pathlib import Path

import pandas as pd
import requests
from bs4 import BeautifulSoup


BASE_DIR = Path(__file__).resolve().parents[1]

RAW_DIR = BASE_DIR / "data" / "raw" / "motie"
RAW_DIR.mkdir(parents=True, exist_ok=True)

RECOVERED_FILE = RAW_DIR / "motie_auto_monthly_index_recovered.csv"
OUTPUT_FILE = RAW_DIR / "motie_auto_monthly_master.csv"

SEARCH_URL = "https://www.motir.go.kr/search/search.do"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 "
        "(Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 "
        "Chrome/120 Safari/537.36"
    )
}


def clean_text(text: str) -> str:
    text = text.replace("\xa0", " ")
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def page_text(url: str) -> str:
    r = requests.get(
        url,
        headers=HEADERS,
        timeout=30,
    )
    r.raise_for_status()

    soup = BeautifulSoup(
        r.text,
        "html.parser",
    )

    return clean_text(
        soup.get_text(" ", strip=True)
    )


def expected_patterns(year: int, month: int):
    yy = str(year)[2:]

    return [
        rf"{year}\s*년\s*{month}\s*월",
        rf"{yy}\s*년\s*{month}\s*월",
        rf"[`'’]?\s*{yy}\s*[년\.]\s*{month}\s*월",
    ]


def verify_period(
    text: str,
    year: int,
    month: int,
) -> bool:

    if not (
        "자동차" in text
        and (
            "산업 동향" in text
            or "산업동향" in text
        )
    ):
        return False

    for pattern in expected_patterns(
        year,
        month,
    ):
        if re.search(pattern, text):
            return True

    return False


def extract_number(
    text: str,
    keyword_patterns: list[str],
):

    for keyword in keyword_patterns:

        patterns = [
            rf"{keyword}.{{0,50}}?([\d,]+(?:\.\d+)?)\s*만\s*대",
            rf"{keyword}.{{0,50}}?([\d,]+)\s*대",
        ]

        for pattern in patterns:

            m = re.search(
                pattern,
                text,
                flags=re.IGNORECASE,
            )

            if not m:
                continue

            value = float(
                m.group(1).replace(",", "")
            )

            if "만" in m.group(0):
                value *= 10000

            return int(round(value))

    return None


def extract_metrics(text: str):

    production = extract_number(
        text,
        [
            r"생산량은",
            r"생산은",
            r"생산량",
            r"생산",
        ],
    )

    domestic = extract_number(
        text,
        [
            r"내수 판매는",
            r"내수판매는",
            r"내수는",
            r"내수 판매",
            r"내수",
        ],
    )

    export = extract_number(
        text,
        [
            r"수출대수는",
            r"수출은",
            r"수출대수",
            r"수출",
        ],
    )

    return {
        "production_qty": production,
        "domestic_qty": domestic,
        "export_qty": export,
    }


def inspect_existing(
    period: str,
    url: str,
):

    if not url:
        return None

    year, month = map(
        int,
        period.split("-"),
    )

    try:
        text = page_text(url)
    except Exception:
        return None

    if not verify_period(
        text,
        year,
        month,
    ):
        return None

    metrics = extract_metrics(text)

    return {
        "period": period,
        "year": year,
        "month": month,
        "url": url,
        "source": "MOTIE",
        "verified": True,
        **metrics,
    }


def main():

    if not RECOVERED_FILE.exists():
        raise FileNotFoundError(
            RECOVERED_FILE
        )

    source = pd.read_csv(
        RECOVERED_FILE,
        dtype=str,
    ).fillna("")

    rows = []

    total = len(source)

    for i, row in source.iterrows():

        period = row["period"]
        url = row.get("url", "")

        result = inspect_existing(
            period,
            url,
        )

        if result is None:

            year, month = map(
                int,
                period.split("-"),
            )

            result = {
                "period": period,
                "year": year,
                "month": month,
                "url": "",
                "source": "",
                "verified": False,
                "production_qty": None,
                "domestic_qty": None,
                "export_qty": None,
            }

        rows.append(result)

        print(
            f"{i + 1:03d}/{total} "
            f"{period} "
            f"VERIFIED={result['verified']} "
            f"P={result['production_qty']} "
            f"D={result['domestic_qty']} "
            f"E={result['export_qty']}"
        )

        time.sleep(0.15)

    df = pd.DataFrame(rows)

    df.to_csv(
        OUTPUT_FILE,
        index=False,
        encoding="utf-8-sig",
    )

    print()
    print("=" * 72)
    print("MOTIE MONTHLY MASTER")
    print("=" * 72)

    print("TOTAL       :", len(df))
    print(
        "VERIFIED    :",
        int(df["verified"].sum()),
    )

    print(
        "PRODUCTION  :",
        df["production_qty"].notna().sum(),
    )

    print(
        "DOMESTIC    :",
        df["domestic_qty"].notna().sum(),
    )

    print(
        "EXPORT      :",
        df["export_qty"].notna().sum(),
    )

    print("OUTPUT      :", OUTPUT_FILE)


if __name__ == "__main__":
    main()
