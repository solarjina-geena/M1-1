import requests
from bs4 import BeautifulSoup

url = "https://www.motie.go.kr/search/search.do"

params = {
    "site": "main",
    "kwd": "자동차산업동향",
    "category": "c1",
    "currentPage": "1",
    "rowPerPage": "10",
    "sort": "r",
    "searchRange": "fdTot",
}

r = requests.get(
    url,
    params=params,
    headers={"User-Agent": "Mozilla/5.0"},
    timeout=30,
)

r.raise_for_status()

soup = BeautifulSoup(r.text, "html.parser")

print("=" * 70)
print("PAGINATION CHECK")
print("=" * 70)
print("FINAL URL :", r.url)
print()

for a in soup.find_all("a", href=True):
    text = " ".join(a.get_text(" ", strip=True).split())
    href = a.get("href", "")

    if (
        "currentPage" in href
        or "fn_search" in href
        or "goPage" in href
        or text in {"1","2","3","4","5","6","7","8","9","10","다음","마지막"}
    ):
        print("TEXT :", repr(text))
        print("HREF :", repr(href))
        print("-" * 50)
