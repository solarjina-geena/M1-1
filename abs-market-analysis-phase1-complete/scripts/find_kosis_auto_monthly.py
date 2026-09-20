import re
import requests

from config.settings import API_CONFIG


URL = "https://kosis.kr/openapi/statisticsSearch.do"

KEYWORDS = [
    "광공업생산지수",
    "광업제조업동향조사",
    "자동차 및 트레일러",
    "자동차부품",
]


def search(keyword):

    params = {
        "method": "getList",
        "apiKey": API_CONFIG["kosis_key"],
        "searchNm": keyword,
        "sort": "RANK",
        "startCount": 1,
        "resultCount": 100,
        "format": "json",
    }

    r = requests.get(
        URL,
        params=params,
        timeout=30,
    )

    r.raise_for_status()

    return r.text


def field(block, name):
    m = re.search(
        rf'{name}:"((?:\\.|[^"])*)"',
        block,
        flags=re.DOTALL,
    )

    return m.group(1) if m else ""


for keyword in KEYWORDS:

    print()
    print("=" * 90)
    print("SEARCH:", keyword)
    print("=" * 90)

    text = search(keyword)

    blocks = re.split(
        r'(?=\{ORG_ID:")',
        text,
    )

    count = 0

    for block in blocks:

        org_id = field(block, "ORG_ID")
        tbl_id = field(block, "TBL_ID")
        tbl_name = field(block, "TBL_NM")
        stat_name = field(block, "STAT_NM")
        start = field(block, "STRT_PRD_DE")
        end = field(block, "END_PRD_DE")

        if not org_id or not tbl_id:
            continue

        # 자동차/광공업 관련 후보만 표시
        combined = (
            tbl_name
            + " "
            + stat_name
            + " "
            + field(block, "CONTENTS")
        )

        if not any(
            x in combined
            for x in [
                "자동차",
                "광공업",
                "제조업",
                "생산지수",
            ]
        ):
            continue

        print()
        print("ORG_ID :", org_id)
        print("TBL_ID :", tbl_id)
        print("TBL_NM :", tbl_name)
        print("STAT_NM:", stat_name)
        print("PERIOD :", start, "~", end)

        count += 1

        if count >= 20:
            break

    print()
    print("CANDIDATES:", count)
