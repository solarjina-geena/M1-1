from pathlib import Path
import re
import time

import pandas as pd
import requests
from bs4 import BeautifulSoup


BASE_DIR = Path(__file__).resolve().parents[1]

OLD_INDEX = (
    BASE_DIR
    / "data"
    / "raw"
    / "motie"
    / "motie_auto_monthly_index.csv"
)

OUTPUT_FILE = (
    BASE_DIR
    / "data"
    / "raw"
    / "motie"
    / "motie_auto_monthly_index_verified.csv"
)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 "
        "(Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 "
        "Chrome/120 Safari/537.36"
    )
}


def normalize(text):
    if text is None:
        return ""

    text = str(text)

    text = re.sub(
        r"\s+",
        "",
        text,
    )

    return text


def expected_patterns(year, month):
    y4 = str(year)
    y2 = str(year)[-2:]

    return [
        normalize(
            f"{y4}년{month}월자동차산업동향"
        ),
        normalize(
            f"{y4}년{month}월자동차산업동향"
        ),
        normalize(
            f"{y2}년{month}월자동차산업동향"
        ),
        normalize(
            f"'{y2}년{month}월자동차산업동향"
        ),
    ]


def inspect_page(url, year, month):

    try:
        response = requests.get(
            url,
            headers=HEADERS,
            timeout=30,
        )

        response.raise_for_status()

    except Exception as exc:
        return {
            "verified": False,
            "page_title": "",
            "reason": f"HTTP_ERROR:{exc}",
        }

    soup = BeautifulSoup(
        response.text,
        "html.parser",
    )

    title = ""

    if soup.title:
        title = soup.title.get_text(
            " ",
            strip=True,
        )

    text = soup.get_text(
        " ",
        strip=True,
    )

    normalized_title = normalize(title)
    normalized_text = normalize(text)

    patterns = expected_patterns(
        year,
        month,
    )

    title_match = any(
        pattern in normalized_title
        for pattern in patterns
    )

    body_match = any(
        pattern in normalized_text
        for pattern in patterns
    )

    # 제목 형식이 조금 달라도
    # 본문에 해당 연월 + 자동차 산업 동향이 있으면 허용
    year_month_patterns = [
        normalize(
            f"{year}년{month}월"
        ),
        normalize(
            f"{str(year)[-2:]}년{month}월"
        ),
    ]

    has_year_month = any(
        pattern in normalized_text
        for pattern in year_month_patterns
    )

    has_auto = (
        "자동차산업동향"
        in normalized_text
    )

    verified = (
        title_match
        or body_match
        or (
            has_year_month
            and has_auto
        )
    )

    if verified:
        reason = "MATCH"
    else:
        reason = "PERIOD_OR_TITLE_MISMATCH"

    return {
        "verified": verified,
        "page_title": title,
        "reason": reason,
    }


def main():

    if not OLD_INDEX.exists():
        raise FileNotFoundError(
            f"Index not found: {OLD_INDEX}"
        )

    df = pd.read_csv(
        OLD_INDEX,
        dtype=str,
    )

    results = []

    print("=" * 72)
    print("MOTIE MONTHLY INDEX VERIFICATION")
    print("=" * 72)

    for idx, row in df.iterrows():

        period = row["period"]
        url = row["url"]

        year = int(period[:4])
        month = int(period[5:7])

        checked = inspect_page(
            url,
            year,
            month,
        )

        status = (
            "VERIFIED"
            if checked["verified"]
            else "REJECTED"
        )

        results.append(
            {
                "period": period,
                "keyword": row.get(
                    "keyword",
                    "",
                ),
                "url": url,
                "old_status": row.get(
                    "status",
                    "",
                ),
                "verify_status": status,
                "verify_reason": checked[
                    "reason"
                ],
                "page_title": checked[
                    "page_title"
                ],
            }
        )

        print(
            f"{idx + 1:03d}/{len(df):03d}",
            period,
            status,
        )

        time.sleep(0.05)

    result_df = pd.DataFrame(
        results
    )

    result_df.to_csv(
        OUTPUT_FILE,
        index=False,
        encoding="utf-8-sig",
    )

    verified = result_df[
        result_df["verify_status"]
        == "VERIFIED"
    ]

    rejected = result_df[
        result_df["verify_status"]
        != "VERIFIED"
    ]

    duplicate_verified = verified[
        verified["url"].duplicated(
            keep=False
        )
    ]

    print()
    print("=" * 72)
    print("VERIFICATION RESULT")
    print("=" * 72)

    print(
        "TOTAL PERIODS       :",
        len(result_df),
    )

    print(
        "VERIFIED            :",
        len(verified),
    )

    print(
        "REJECTED            :",
        len(rejected),
    )

    print(
        "VERIFIED UNIQUE URLS:",
        verified["url"].nunique(),
    )

    print(
        "VERIFIED DUP ROWS   :",
        len(duplicate_verified),
    )

    print(
        "OUTPUT              :",
        OUTPUT_FILE,
    )

    if not rejected.empty:

        print()
        print("=" * 72)
        print("REJECTED PERIODS")
        print("=" * 72)

        print(
            rejected[
                [
                    "period",
                    "verify_reason",
                    "url",
                ]
            ].to_string(
                index=False
            )
        )

    if not duplicate_verified.empty:

        print()
        print("=" * 72)
        print("DUPLICATES STILL VERIFIED")
        print("=" * 72)

        print(
            duplicate_verified[
                [
                    "period",
                    "url",
                ]
            ]
            .sort_values("url")
            .to_string(
                index=False
            )
        )


if __name__ == "__main__":
    main()
