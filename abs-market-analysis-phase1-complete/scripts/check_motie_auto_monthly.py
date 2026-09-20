from __future__ import annotations

import re
import time
from pathlib import Path

import pandas as pd
import requests


BASE_DIR = Path(__file__).resolve().parents[1]

OUTPUT_DIR = BASE_DIR / "data" / "raw" / "motie"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

OUTPUT_FILE = OUTPUT_DIR / "motie_auto_monthly_index.csv"


SEARCH_URL = "https://www.motir.go.kr/search/search.do"


def search_month(year: int, month: int) -> dict:
    """
    산업통상부 통합검색에서 특정 연월의 자동차산업 동향을 찾는다.
    이 단계에서는 숫자를 수집하지 않고 공식 페이지 존재 여부만 검사한다.
    """

    keyword = f"{year}년 {month}월 자동차산업 동향"

    params = {
        "kwd": keyword,
        "category": "c1",
        "currentPage": 1,
        "rowPerPage": 20,
    }

    headers = {
        "User-Agent": (
            "Mozilla/5.0 "
            "(Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 "
            "Chrome/120 Safari/537.36"
        )
    }

    try:
        response = requests.get(
            SEARCH_URL,
            params=params,
            headers=headers,
            timeout=30,
        )

        response.raise_for_status()

        text = response.text

    except Exception as exc:
        return {
            "period": f"{year}-{month:02d}",
            "keyword": keyword,
            "found": False,
            "url": "",
            "status": f"ERROR: {exc!r}",
        }

    # 산업통상부 보도자료 URL 후보
    patterns = [
        r'href="([^"]*ATCL3f49a5a8c[^"]*/view[^"]*)"',
        r'href="([^"]*/kor/article/[^"]*/view[^"]*)"',
    ]

    urls = []

    for pattern in patterns:
        urls.extend(
            re.findall(
                pattern,
                text,
                flags=re.IGNORECASE,
            )
        )

    normalized = []

    for url in urls:
        url = url.replace("&amp;", "&")

        if url.startswith("/"):
            url = "https://www.motir.go.kr" + url

        if url not in normalized:
            normalized.append(url)

    found_url = normalized[0] if normalized else ""

    return {
        "period": f"{year}-{month:02d}",
        "keyword": keyword,
        "found": bool(found_url),
        "url": found_url,
        "status": "OK" if found_url else "NOT_FOUND",
    }


def main():
    rows = []

    total = 0

    for year in range(2015, 2026):
        for month in range(1, 13):
            total += 1

            result = search_month(
                year,
                month,
            )

            rows.append(result)

            mark = "OK" if result["found"] else "--"

            print(
                f"{total:03d}/132 "
                f"{result['period']} "
                f"{mark}"
            )

            # 정부 사이트에 과도한 요청을 보내지 않도록 대기
            time.sleep(0.25)

    df = pd.DataFrame(rows)

    df.to_csv(
        OUTPUT_FILE,
        index=False,
        encoding="utf-8-sig",
    )

    found_count = int(df["found"].sum())
    missing_count = len(df) - found_count

    print()
    print("=" * 70)
    print("MOTIE MONTHLY INDEX CHECK")
    print("=" * 70)

    print("TOTAL   :", len(df))
    print("FOUND   :", found_count)
    print("MISSING :", missing_count)
    print("OUTPUT  :", OUTPUT_FILE)

    if missing_count:
        print()
        print("=== MISSING PERIODS ===")

        print(
            df.loc[
                ~df["found"],
                ["period", "status"],
            ].to_string(index=False)
        )


if __name__ == "__main__":
    main()
