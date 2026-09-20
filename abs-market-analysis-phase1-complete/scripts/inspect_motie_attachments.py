from pathlib import Path
import pandas as pd
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

BASE_DIR = Path(__file__).resolve().parents[1]

INDEX_FILE = (
    BASE_DIR / "data" / "raw" / "motie"
    / "motie_auto_monthly_index_recovered.csv"
)

df = pd.read_csv(INDEX_FILE, dtype=str).fillna("")

row = df[df["period"] == "2025-01"]

if row.empty:
    raise RuntimeError("2025-01 not found")

url = row.iloc[0]["url"]

headers = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 Chrome/120 Safari/537.36"
    )
}

r = requests.get(url, headers=headers, timeout=30)
r.raise_for_status()

soup = BeautifulSoup(r.text, "html.parser")

print("=" * 90)
print("PAGE URL")
print("=" * 90)
print(url)

print()
print("=" * 90)
print("PAGE TITLE")
print("=" * 90)

title = soup.title.get_text(" ", strip=True) if soup.title else ""
print(title)

print()
print("=" * 90)
print("ATTACHMENT CANDIDATES")
print("=" * 90)

count = 0

for a in soup.find_all("a", href=True):

    href = a.get("href", "").strip()
    text = a.get_text(" ", strip=True)

    combined = (text + " " + href).lower()

    if any(
        key in combined
        for key in [
            ".pdf",
            ".hwp",
            ".hwpx",
            "download",
            "file",
            "attach",
        ]
    ):
        count += 1

        print()
        print(f"[{count}]")
        print("TEXT :", text)
        print("HREF :", href)
        print("FULL :", urljoin(url, href))

if count == 0:
    print("NO ATTACHMENT CANDIDATES FOUND")

print()
print("=" * 90)
print("TOTAL =", count)
print("=" * 90)
