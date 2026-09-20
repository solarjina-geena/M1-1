from pathlib import Path

import pandas as pd
import requests
from bs4 import BeautifulSoup


BASE_DIR = Path(__file__).resolve().parents[1]

INDEX_FILE = (
    BASE_DIR
    / "data"
    / "raw"
    / "motie"
    / "motie_auto_monthly_index.csv"
)

TEST_PERIODS = [
    "2015-01",
    "2020-01",
    "2025-01",
]


def get_page_text(url: str) -> tuple[str, str]:

    headers = {
        "User-Agent": (
            "Mozilla/5.0 "
            "(Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 "
            "Chrome/120 Safari/537.36"
        )
    }

    response = requests.get(
        url,
        headers=headers,
        timeout=30,
    )

    response.raise_for_status()

    soup = BeautifulSoup(
        response.text,
        "html.parser",
    )

    text = soup.get_text(
        "\n",
        strip=True,
    )

    return response.text, text


def show_keyword_context(
    text: str,
    keyword: str,
    width: int = 700,
):

    pos = text.find(keyword)

    if pos < 0:
        print(
            f"{keyword}: NOT FOUND"
        )
        return

    start = max(
        0,
        pos - width,
    )

    end = min(
        len(text),
        pos + width,
    )

    print()
    print(
        f"--- CONTEXT: {keyword} ---"
    )

    print(
        text[start:end]
    )


def main():

    df = pd.read_csv(
        INDEX_FILE,
        dtype=str,
    )

    for period in TEST_PERIODS:

        matched = df[
            df["period"] == period
        ]

        if matched.empty:
            print(
                f"{period}: INDEX NOT FOUND"
            )
            continue

        url = matched.iloc[0]["url"]

        print()
        print("=" * 90)
        print("PERIOD :", period)
        print("URL    :", url)
        print("=" * 90)

        try:
            html, text = get_page_text(
                url
            )

        except Exception as exc:
            print(
                "ERROR:",
                repr(exc),
            )
            continue

        print(
            "HTML LENGTH:",
            len(html),
        )

        print(
            "TEXT LENGTH:",
            len(text),
        )

        for keyword in [
            "생산",
            "내수",
            "수출",
            "자동차산업",
        ]:
            show_keyword_context(
                text,
                keyword,
            )


if __name__ == "__main__":
    main()
