import os
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
    "method": "getList",
    "apiKey": api_key,
    "format": "json",
    "jsonVD": "Y",
    "prdSe": "M",
    "newEstPrdCnt": "3",
    "orgId": ORG_ID,
    "tblId": TBL_ID,
}

response = requests.get(
    url,
    params=params,
    timeout=30,
)

print("STATUS =", response.status_code)
print("URL =", response.url)
print("LENGTH =", len(response.text))
print("CONTENT-TYPE =", response.headers.get("Content-Type"))

response.raise_for_status()

text = response.text

print()
print("=== KEYWORD CHECK ===")

keywords = [
    "자동차",
    "승용차",
    "승합차",
    "화물차",
    "트레일러",
    "생산",
    "출하",
    "재고",
]

for keyword in keywords:
    print(
        f"{keyword}:",
        "FOUND" if keyword in text else "NOT FOUND",
    )

print()
print("=== RESPONSE PREVIEW ===")
print(text[:5000])

print()
print("=== AUTOMOBILE CONTEXT ===")

found = False

for keyword in ["자동차", "승용차", "승합차", "화물차"]:
    start = 0

    while True:
        pos = text.find(keyword, start)

        if pos == -1:
            break

        found = True

        left = max(0, pos - 300)
        right = min(len(text), pos + 700)

        print()
        print("-" * 80)
        print("KEYWORD:", keyword)
        print(text[left:right])

        start = pos + len(keyword)

if not found:
    print("No automobile-related item found.")
