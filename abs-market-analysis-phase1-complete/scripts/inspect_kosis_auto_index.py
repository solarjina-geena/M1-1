import os
import requests
from config.settings import API_CONFIG

ORG_ID = "101"
TBL_ID = "DT_1F02001"

api_key = API_CONFIG.get("kosis_api_key") or os.getenv("KOSIS_API_KEY")

if not api_key:
    raise RuntimeError("KOSIS API key not found")

url = "https://kosis.kr/openapi/statisticsData.do"

params = {
    "method": "getList",
    "apiKey": api_key,
    "format": "json",
    "jsonVD": "Y",
    "userStatsId": "tester/101/DT_1F02001/2/1/20260919",
    "prdSe": "M",
    "newEstPrdCnt": "3",
    "orgId": ORG_ID,
    "tblId": TBL_ID,
}

print("=" * 80)
print("KOSIS TABLE INSPECTION")
print("ORG_ID:", ORG_ID)
print("TBL_ID:", TBL_ID)
print("=" * 80)

response = requests.get(
    url,
    params=params,
    timeout=30,
)

print("STATUS:", response.status_code)
print("CONTENT-TYPE:", response.headers.get("Content-Type"))
print("RESPONSE LENGTH:", len(response.text))

response.raise_for_status()

text = response.text

print()
print("=== KEYWORD CHECK ===")

keywords = [
    "자동차",
    "트레일러",
    "자동차 및 트레일러",
    "생산지수",
]

for keyword in keywords:
    print(
        f"{keyword}:",
        "FOUND" if keyword in text else "NOT FOUND",
    )

print()
print("=== AUTOMOBILE CONTEXT ===")

positions = []

start = 0
while True:
    pos = text.find("자동차", start)

    if pos == -1:
        break

    positions.append(pos)
    start = pos + 1

if not positions:
    print("No automobile keyword found in response.")

else:
    print("MATCH COUNT:", len(positions))

    for i, pos in enumerate(positions[:20], start=1):
        left = max(0, pos - 250)
        right = min(len(text), pos + 500)

        print()
        print("-" * 80)
        print("MATCH", i)
        print("-" * 80)
        print(text[left:right])

print()
print("=== RESPONSE PREVIEW ===")
print(text[:3000])
