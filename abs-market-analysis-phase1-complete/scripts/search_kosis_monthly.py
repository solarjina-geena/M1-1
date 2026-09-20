import re
import requests

from config.settings import API_CONFIG


API_URL = "https://kosis.kr/openapi/statisticsSearch.do"

SEARCH_WORDS = [
    "자동차 생산지수",
    "자동차 제조업",
    "자동차 및 트레일러",
    "광공업생산지수 자동차",
    "제조업 생산지수 자동차",
]


def search_kosis(keyword):

    params = {
        "method": "getList",
        "apiKey": API_CONFIG["kosis_key"],
        "searchNm": keyword,
        "sort": "RANK",
        "startCount": 1,
        "resultCount": 100,
        "format": "json",
        "jsonVD": "Y",
    }

    response = requests.get(
        API_URL,
        params=params,
        timeout=30,
    )

    response.raise_for_status()

    return response.text


def extract_results(text):

    pattern = re.compile(
        r'ORG_ID:"(?P<org_id>[^"]*)".*?'
        r'ORG_NM:"(?P<org_name>[^"]*)".*?'
        r'TBL_ID:"(?P<tbl_id>[^"]*)".*?'
        r'TBL_NM:"(?P<tbl_name>[^"]*)".*?'
        r'STAT_ID:"(?P<stat_id>[^"]*)".*?'
        r'STAT_NM:"(?P<stat_name>[^"]*)".*?'
        r'STRT_PRD_DE:"(?P<start_period>[^"]*)".*?'
        r'END_PRD_DE:"(?P<end_period>[^"]*)"',
        re.DOTALL,
    )

    return [
        match.groupdict()
        for match in pattern.finditer(text)
    ]


if __name__ == "__main__":

    seen = set()

    for keyword in SEARCH_WORDS:

        print()
        print("=" * 90)
        print("SEARCH:", keyword)
        print("=" * 90)

        try:
            text = search_kosis(keyword)
            rows = extract_results(text)

            print("PARSED RESULTS:", len(rows))

            shown = 0

            for row in rows:

                key = (
                    row["org_id"],
                    row["tbl_id"],
                )

                if key in seen:
                    continue

                seen.add(key)

                print()
                print("ORG :", row["org_id"], row["org_name"])
                print("TBL :", row["tbl_id"])
                print("NAME:", row["tbl_name"])
                print("STAT:", row["stat_name"])
                print(
                    "PERIOD:",
                    row["start_period"],
                    "~",
                    row["end_period"],
                )

                shown += 1

                if shown >= 20:
                    break

        except Exception as exc:
            print("ERROR:", repr(exc))
