from __future__ import annotations

import re
import time
from pathlib import Path
from urllib.parse import urljoin

import pandas as pd
import requests
from bs4 import BeautifulSoup


BASE_DIR = Path(__file__).resolve().parents[1]

DATA_DIR = (
    BASE_DIR
    / "data"
    / "raw"
    / "motie"
)

INPUT_FILE = (
    DATA_DIR
    / "motie_auto_monthly_index_verified.csv"
)

OUTPUT_FILE = (
    DATA_DIR
    / "motie_auto_monthly_index_recovered.csv"
)

CANDIDATE_FILE = (
    DATA_DIR
    / "motie_auto_recovery_candidates.csv"
)

SEARCH_URL = (
    "https://www.motir.go.kr/search/search.do"
)

BASE_URL = "https://www.motir.go.kr"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 "
        "(Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 "
        "Chrome/120 Safari/537.36"
    )
}

session = requests.Session()
session.headers.update(HEADERS)


def normalize(text: str) -> str:
    if text is None:
        return ""

    text = str(text)

    text = text.replace("\xa0", " ")

    return re.sub(
        r"\s+",
        "",
        text,
    )


def search_keywords(
    year: int,
    month: int,
) -> list[str]:

    y2 = str(year)[-2:]

    return [
        f"{year}년 {month}월 자동차산업 동향",
        f"{year}년 {month}월 자동차 산업 동향",
        f"{y2}년 {month}월 자동차산업 동향",
        f"{y2}년 {month}월 자동차 산업 동향",
        f"{year} {month} 자동차산업 동향",
    ]


def extract_candidate_urls(
    html: str,
) -> list[str]:

    patterns = [
        (
            r'href=["\']'
            r'([^"\']*ATCL3f49a5a8c'
            r'[^"\']*/view[^"\']*)'
            r'["\']'
        ),
        (
            r'href=["\']'
            r'([^"\']*/kor/article/'
            r'[^"\']*/view[^"\']*)'
            r'["\']'
        ),
    ]

    urls = []

    for pattern in patterns:

        matches = re.findall(
            pattern,
            html,
            flags=re.IGNORECASE,
        )

        for url in matches:

            url = (
                url
                .replace("&amp;", "&")
                .strip()
            )

            full_url = urljoin(
                BASE_URL,
                url,
            )

            if full_url not in urls:
                urls.append(full_url)

    return urls


def get_search_candidates(
    keyword: str,
) -> list[str]:

    urls = []

    # 검색 결과가 뒤 페이지에 있을 수 있으므로
    # 1~5페이지 검사
    for page in range(1, 6):

        params = {
            "kwd": keyword,
            "category": "c1",
            "currentPage": page,
            "rowPerPage": 20,
        }

        try:
            response = session.get(
                SEARCH_URL,
                params=params,
                timeout=30,
            )

            response.raise_for_status()

        except Exception:
            continue

        page_urls = extract_candidate_urls(
            response.text
        )

        for url in page_urls:
            if url not in urls:
                urls.append(url)

        time.sleep(0.10)

    return urls


def page_matches_period(
    url: str,
    year: int,
    month: int,
) -> dict:

    try:
        response = session.get(
            url,
            timeout=30,
        )

        response.raise_for_status()

    except Exception as exc:
        return {
            "matched": False,
            "score": 0,
            "title": "",
            "reason": f"HTTP_ERROR:{exc!r}",
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

    body = soup.get_text(
        " ",
        strip=True,
    )

    nt = normalize(title)
    nb = normalize(body)

    y4 = str(year)
    y2 = str(year)[-2:]
    m = str(month)

    exact_phrases = [
        f"{y4}년{m}월자동차산업동향",
        f"{y4}년{m}월자동차산업동향",
        f"{y2}년{m}월자동차산업동향",
    ]

    exact_phrases = [
        normalize(x)
        for x in exact_phrases
    ]

    score = 0
    reasons = []

    # 가장 강한 조건:
    # 제목 자체에 목표 연월 + 자동차산업동향
    if any(
        phrase in nt
        for phrase in exact_phrases
    ):
        score += 100
        reasons.append("TITLE_EXACT")

    # 본문에도 정확한 문구가 있는지
    if any(
        phrase in nb
        for phrase in exact_phrases
    ):
        score += 50
        reasons.append("BODY_EXACT")

    year_month_patterns = [
        normalize(
            f"{year}년 {month}월"
        ),
        normalize(
            f"{y2}년 {month}월"
        ),
    ]

    if any(
        p in nt
        for p in year_month_patterns
    ):
        score += 30
        reasons.append("TITLE_PERIOD")

    if any(
        p in nb
        for p in year_month_patterns
    ):
        score += 10
        reasons.append("BODY_PERIOD")

    if "자동차산업동향" in nt:
        score += 30
        reasons.append("TITLE_AUTO")

    if "자동차산업동향" in nb:
        score += 10
        reasons.append("BODY_AUTO")

    # 오탐 방지를 위해
    # 제목 정확 일치 또는 매우 강한 조합만 통과
    matched = (
        "TITLE_EXACT" in reasons
        or (
            "TITLE_PERIOD" in reasons
            and "TITLE_AUTO" in reasons
        )
    )

    return {
        "matched": matched,
        "score": score,
        "title": title,
        "reason": "|".join(reasons),
    }


def recover_period(
    year: int,
    month: int,
) -> tuple[dict | None, list[dict]]:

    candidate_records = []

    seen_urls = set()

    for keyword in search_keywords(
        year,
        month,
    ):

        print(
            "   SEARCH:",
            keyword,
        )

        urls = get_search_candidates(
            keyword
        )

        print(
            "      candidates:",
            len(urls),
        )

        for url in urls:

            if url in seen_urls:
                continue

            seen_urls.add(url)

            check = page_matches_period(
                url,
                year,
                month,
            )

            record = {
                "period": (
                    f"{year}-{month:02d}"
                ),
                "keyword": keyword,
                "url": url,
                "matched": check[
                    "matched"
                ],
                "score": check[
                    "score"
                ],
                "page_title": check[
                    "title"
                ],
                "reason": check[
                    "reason"
                ],
            }

            candidate_records.append(
                record
            )

            if check["matched"]:

                return (
                    record,
                    candidate_records,
                )

            time.sleep(0.08)

    return (
        None,
        candidate_records,
    )


def main():

    if not INPUT_FILE.exists():
        raise FileNotFoundError(
            INPUT_FILE
        )

    df = pd.read_csv(
        INPUT_FILE,
        dtype=str,
    )

    output_rows = []
    all_candidates = []

    rejected_count = int(
        (
            df["verify_status"]
            != "VERIFIED"
        ).sum()
    )

    current = 0

    print("=" * 78)
    print("MOTIE MONTHLY INDEX RECOVERY")
    print("=" * 78)
    print(
        "ALREADY VERIFIED:",
        len(df) - rejected_count,
    )
    print(
        "TO RECOVER      :",
        rejected_count,
    )
    print()

    for _, row in df.iterrows():

        period = row["period"]

        if (
            row["verify_status"]
            == "VERIFIED"
        ):

            output_rows.append(
                {
                    "period": period,
                    "url": row["url"],
                    "status": "VERIFIED_EXISTING",
                    "keyword": row.get(
                        "keyword",
                        "",
                    ),
                    "page_title": row.get(
                        "page_title",
                        "",
                    ),
                }
            )

            continue

        current += 1

        year = int(period[:4])
        month = int(period[5:7])

        print()
        print("-" * 78)
        print(
            f"{current:02d}/{rejected_count:02d}",
            period,
        )
        print("-" * 78)

        recovered, candidates = (
            recover_period(
                year,
                month,
            )
        )

        all_candidates.extend(
            candidates
        )

        if recovered:

            print(
                "   >>> RECOVERED:",
                recovered["url"],
            )

            print(
                "   >>> TITLE:",
                recovered[
                    "page_title"
                ],
            )

            output_rows.append(
                {
                    "period": period,
                    "url": recovered[
                        "url"
                    ],
                    "status": "RECOVERED",
                    "keyword": recovered[
                        "keyword"
                    ],
                    "page_title": recovered[
                        "page_title"
                    ],
                }
            )

        else:

            print(
                "   >>> MISSING"
            )

            output_rows.append(
                {
                    "period": period,
                    "url": "",
                    "status": "MISSING",
                    "keyword": "",
                    "page_title": "",
                }
            )

        time.sleep(0.20)

    result = pd.DataFrame(
        output_rows
    ).sort_values(
        "period"
    ).reset_index(
        drop=True
    )

    result.to_csv(
        OUTPUT_FILE,
        index=False,
        encoding="utf-8-sig",
    )

    pd.DataFrame(
        all_candidates
    ).to_csv(
        CANDIDATE_FILE,
        index=False,
        encoding="utf-8-sig",
    )

    good = result[
        result["status"].isin(
            [
                "VERIFIED_EXISTING",
                "RECOVERED",
            ]
        )
    ]

    missing = result[
        result["status"]
        == "MISSING"
    ]

    duplicates = good[
        good["url"].duplicated(
            keep=False
        )
    ]

    print()
    print("=" * 78)
    print("RECOVERY RESULT")
    print("=" * 78)

    print(
        "TOTAL             :",
        len(result),
    )

    print(
        "VERIFIED EXISTING :",
        int(
            (
                result["status"]
                == "VERIFIED_EXISTING"
            ).sum()
        ),
    )

    print(
        "RECOVERED         :",
        int(
            (
                result["status"]
                == "RECOVERED"
            ).sum()
        ),
    )

    print(
        "MISSING           :",
        len(missing),
    )

    print(
        "GOOD UNIQUE URLS  :",
        good["url"].nunique(),
    )

    print(
        "DUPLICATE ROWS    :",
        len(duplicates),
    )

    print(
        "OUTPUT            :",
        OUTPUT_FILE,
    )

    print(
        "CANDIDATE LOG     :",
        CANDIDATE_FILE,
    )

    if not missing.empty:

        print()
        print("=== MISSING PERIODS ===")

        print(
            missing[
                ["period"]
            ].to_string(
                index=False
            )
        )

    if not duplicates.empty:

        print()
        print(
            "=== DUPLICATE GOOD URLS ==="
        )

        print(
            duplicates[
                [
                    "period",
                    "status",
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
