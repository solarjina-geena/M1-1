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
print("PAGE BUTTON DETAIL")
print("=" * 70)

for a in soup.find_all("a"):
    text = " ".join(a.get_text(" ", strip=True).split())

    if text in {"2", "3", "4", "5"}:
        print()
        print("BUTTON :", text)
        print("HTML   :", str(a))
        print("PARENT :", str(a.parent)[:1000])

print()
print("=" * 70)
print("FORM / CURRENT PAGE")
print("=" * 70)

for tag in soup.find_all(["input", "form"]):
    s = str(tag)

    if (
        "currentPage" in s
        or "searchForm" in s
        or "search" in s.lower()
    ):
        print(s[:1500])

print()
print("=" * 70)
print("SCRIPT HITS")
print("=" * 70)

for script in soup.find_all("script"):
    txt = script.get_text("\n", strip=True)

    if (
        "currentPage" in txt
        or "goPage" in txt
        or "fn_search" in txt
    ):
        print(txt[:4000])
        print("-" * 70)
