import os
import re
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


url = "https://kosis.kr/openapi/statisticsData.do"

params = {
    "method": "getMeta",
    "type": "ITM",
    "apiKey": api_key,
    "orgId": ORG_ID,
    "tblId": TBL_ID,
    "format": "json",
}

response = requests.get(
    url,
    params=params,
    timeout=30,
)

response.raise_for_status()

text = response.text


# --------------------------------------------------
# RAW 응답 그대로 저장
# --------------------------------------------------

output_dir = os.path.join(
    "data",
    "raw",
    "kosis",
    "metadata",
)

os.makedirs(
    output_dir,
    exist_ok=True,
)

output_path = os.path.join(
    output_dir,
    "DT_1F02012_item_meta_raw.txt",
)

with open(
    output_path,
    "w",
    encoding="utf-8",
) as f:
    f.write(text)


print("=" * 90)
print("KOSIS ITEM META")
print("=" * 90)

print("STATUS =", response.status_code)
print("LENGTH =", len(text))
print("SAVED =", output_path)


# --------------------------------------------------
# 객체 단위로 분리
# --------------------------------------------------

objects = re.findall(
    r"\{[^{}]*\}",
    text,
)


print()
print("OBJECT COUNT =", len(objects))


# --------------------------------------------------
# 자동차 관련 품목 검색
# --------------------------------------------------

keywords = [
    "자동차",
    "승용",
    "승합",
    "화물",
    "버스",
    "트럭",
    "트레일러",
]

matched = []

for obj in objects:

    if any(
        keyword in obj
        for keyword in keywords
    ):
        matched.append(obj)


print()
print("=" * 90)
print("AUTOMOBILE MATCHES =", len(matched))
print("=" * 90)


for i, obj in enumerate(
    matched,
    start=1,
):

    item_id = re.search(
        r'ITM_ID:"([^"]*)"',
        obj,
    )

    item_name = re.search(
        r'ITM_NM:"([^"]*)"',
        obj,
    )

    unit_name = re.search(
        r'UNIT_NM:"([^"]*)"',
        obj,
    )

    obj_id = re.search(
        r'OBJ_ID:"([^"]*)"',
        obj,
    )

    print()
    print(
        f"[{i}]",
        "OBJ_ID =",
        obj_id.group(1)
        if obj_id else "",
    )

    print(
        "    ITM_ID =",
        item_id.group(1)
        if item_id else "",
    )

    print(
        "    ITM_NM =",
        item_name.group(1)
        if item_name else "",
    )

    print(
        "    UNIT    =",
        unit_name.group(1)
        if unit_name else "",
    )


print()
print("=" * 90)
print("KNOWN DATA ITEMS")
print("=" * 90)
print("T40 = 품목별생산량")
print("T41 = 품목별출하량")
print("T42 = 품목별재고량")
print("T43 = 품목별내수량")
print("T44 = 품목별수출량")

print()
print("=== INSPECTION COMPLETED ===")
