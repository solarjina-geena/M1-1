import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

URL = "https://www.motie.go.kr/search/search.do"

params = {
    "site": "main",
    "kwd": "자동차산업동향",
    "category": "c1",
    "currentPage": "1",
    "rowPerPage": "100",
    "sort": "r",
    "searchRange": "fdTot",
}

r = requests.get(
    URL,
    params=params,
    timeout=30,
    headers={
        "User-Agent": "Mozilla/5.0"
    },
)

print("STATUS :", r.status_code)
print("URL    :", r.url)
print("CHARS  :", len(r.text))

soup = BeautifulSoup(r.text, "html.parser")

found = []

for a in soup.find_all("a", href=True):
    title = " ".join(a.get_text(" ", strip=True).split())
    href = urljoin(r.url, a["href"])

    text = title.replace(" ", "")

    if "자동차산업" in text or "자동차산업동향" in text:
        found.append((title, href))

print("MATCHES:", len(found))
print()

for i, (title, href) in enumerate(found[:30], 1):
    print(f"[{i}] {title}")
    print(href)
    print()
