import os
import json
import requests

from config.settings import API_CONFIG


ORG_ID = "101"
TBL_ID = "DT_1F02012"

api_key = (
    API_CONFIG.get("kosis_api_key")
    or os.getenv("KOSIS_API_KEY")
)

if not api_key:
    raise RuntimeError("KOSIS API key not found")


BASE_URL = "https://kosis.kr/openapi/statisticsData.do"


def request_meta(meta_type):
    params = {
        "method": "getMeta",
        "type": meta_type,
        "apiKey": api_key,
        "orgId": ORG_ID,
        "tblId": TBL_ID,
        "format": "json",
    }

    response = requests.get(
        BASE_URL,
        params=params,
        timeout=30,
    )

    print()
    print("=" * 90)
    print("META TYPE:", meta_type)
    print("STATUS:", response.status_code)
    print("LENGTH:", len(response.text))
    print("=" * 90)

    response.raise_for_status()

    try:
        return response.json()

    except Exception:
        print("RAW RESPONSE:")
        print(response.text[:5000])
        return None


# --------------------------------------------------
# 1. PERIOD
# --------------------------------------------------

prd = request_meta("PRD")

print()
print("=== PERIOD META ===")

if isinstance(prd, list):

    for row in prd[:30]:
        print(
            "PRD_SE =",
            row.get("PRD_SE"),
            "| PRD_DE =",
            row.get("PRD_DE"),
        )

else:
    print(prd)


# --------------------------------------------------
# 2. ITEM / CLASSIFICATION
# --------------------------------------------------

items = request_meta("ITM")

print()
print("=== ITEM / CLASSIFICATION META ===")

if not isinstance(items, list):

    print(items)

else:

    print("ROWS =", len(items))

    keywords = [
        "자동차",
        "승용",
        "승합",
        "화물",
        "트레일러",
        "생산",
        "출하",
        "재고",
        "내수",
        "수출",
    ]

    matched = []

    for row in items:

        text = " ".join(
            str(row.get(key, ""))
            for key in [
                "OBJ_ID",
                "OBJ_NM",
                "ITM_ID",
                "ITM_NM",
                "UP_ITM_ID",
                "UNIT_NM",
            ]
        )

        if any(
            keyword in text
            for keyword in keywords
        ):
            matched.append(row)

    print()
    print("MATCHED ROWS =", len(matched))

    for i, row in enumerate(
        matched[:200],
        start=1,
    ):

        print()
        print("-" * 90)
        print("MATCH", i)
        print("-" * 90)

        for key in [
            "OBJ_ID",
            "OBJ_NM",
            "ITM_ID",
            "ITM_NM",
            "UP_ITM_ID",
            "OBJ_ID_SN",
            "UNIT_ID",
            "UNIT_NM",
        ]:
            print(
                f"{key:12} =",
                row.get(key),
            )


    print()
    print("=== FIRST 30 META ROWS ===")

    for row in items[:30]:

        print(
            "OBJ_ID=",
            row.get("OBJ_ID"),
            "| OBJ_NM=",
            row.get("OBJ_NM"),
            "| ITM_ID=",
            row.get("ITM_ID"),
            "| ITM_NM=",
            row.get("ITM_NM"),
            "| UP=",
            row.get("UP_ITM_ID"),
            "| UNIT=",
            row.get("UNIT_NM"),
        )


# --------------------------------------------------
# SAVE RAW META
# --------------------------------------------------

output_dir = (
    os.path.join(
        "data",
        "raw",
        "kosis",
        "metadata",
    )
)

os.makedirs(
    output_dir,
    exist_ok=True,
)

if prd is not None:

    with open(
        os.path.join(
            output_dir,
            "DT_1F02012_period_meta.json",
        ),
        "w",
        encoding="utf-8",
    ) as f:

        json.dump(
            prd,
            f,
            ensure_ascii=False,
            indent=2,
        )


if items is not None:

    with open(
        os.path.join(
            output_dir,
            "DT_1F02012_item_meta.json",
        ),
        "w",
        encoding="utf-8",
    ) as f:

        json.dump(
            items,
            f,
            ensure_ascii=False,
            indent=2,
        )


print()
print("=== META INSPECTION COMPLETED ===")
print(
    "RAW META SAVED:",
    output_dir,
)
