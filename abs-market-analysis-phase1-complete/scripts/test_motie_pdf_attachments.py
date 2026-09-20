from __future__ import annotations

from pathlib import Path
from urllib.parse import urljoin

import pandas as pd
import requests
from bs4 import BeautifulSoup


BASE_DIR = Path(__file__).resolve().parents[1]

INDEX_FILE = (
    BASE_DIR
    / "data"
    / "raw"
    / "motie"
    / "motie_auto_monthly_index_recovered.csv"
)

TEST_PERIODS = [
    "2015-02",
    "2020-02",
    "2025-01",
]

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 "
        "(Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 "
        "Chrome/120 Safari/537.36"
    )
}


def inspect_period(
    period: str,
    page_url: str,
):

    print()
    print("=" * 90)
    print("PERIOD :", period)
    print("PAGE   :", page_url)
    print("=" * 90)

    response = requests.get(
        page_url,
        headers=HEADERS,
        timeout=30,
    )

    response.raise_for_status()

    soup = BeautifulSoup(
        response.text,
        "html.parser",
    )

    title = (
        soup.title.get_text(
            " ",
            strip=True,
        )
        if soup.title
        else ""
    )

    print("TITLE  :", title[:150])

    attachments = []

    for a in soup.find_all(
        "a",
        href=True,
    ):

        href = a.get(
            "href",
            "",
        ).strip()

        text = a.get_text(
            " ",
            strip=True,
        )

        lower_text = text.lower()

        # 실제 다운로드 링크만 사용
        if "/attach/down/" not in href:
            continue

        file_type = ""

        if ".pdf" in lower_text:
            file_type = "PDF"

        elif ".hwpx" in lower_text:
            file_type = "HWPX"

        elif ".hwp" in lower_text:
            file_type = "HWP"

        else:
            continue

        full_url = urljoin(
            page_url,
            href,
        )

        attachments.append(
            {
                "type": file_type,
                "text": text,
                "url": full_url,
            }
        )

    print(
        "ATTACHMENTS:",
        len(attachments),
    )

    for i, item in enumerate(
        attachments,
        start=1,
    ):
        print()
        print(
            f"[{i}] {item['type']}"
        )
        print(
            "NAME:",
            item["text"],
        )
        print(
            "URL :",
            item["url"],
        )

        # 실제 다운로드 가능 여부까지 확인
        try:
            r = requests.get(
                item["url"],
                headers=HEADERS,
                timeout=30,
                stream=True,
            )

            print(
                "HTTP:",
                r.status_code,
            )

            print(
                "CONTENT-TYPE:",
                r.headers.get(
                    "Content-Type",
                    "",
                ),
            )

            print(
                "CONTENT-LENGTH:",
                r.headers.get(
                    "Content-Length",
                    "",
                ),
            )

            r.close()

        except Exception as exc:
            print(
                "DOWNLOAD ERROR:",
                repr(exc),
            )

    pdf_count = sum(
        x["type"] == "PDF"
        for x in attachments
    )

    print()
    print(
        "PDF FOUND:",
        pdf_count,
    )

    return pdf_count


def main():

    df = pd.read_csv(
        INDEX_FILE,
        dtype=str,
    ).fillna("")

    results = []

    for period in TEST_PERIODS:

        matched = df[
            df["period"] == period
        ]

        if matched.empty:
            print(
                period,
                ": INDEX ROW NOT FOUND",
            )
            continue

        page_url = matched.iloc[0][
            "url"
        ]

        if not page_url:
            print(
                period,
                ": VERIFIED URL NOT FOUND",
            )
            continue

        try:
            pdf_count = inspect_period(
                period,
                page_url,
            )

            results.append(
                (
                    period,
                    pdf_count,
                )
            )

        except Exception as exc:

            print(
                period,
                "ERROR:",
                repr(exc),
            )

            results.append(
                (
                    period,
                    -1,
                )
            )

    print()
    print("=" * 90)
    print("SUMMARY")
    print("=" * 90)

    for period, pdf_count in results:
        print(
            period,
            "PDF_COUNT=",
            pdf_count,
        )


if __name__ == "__main__":
    main()
