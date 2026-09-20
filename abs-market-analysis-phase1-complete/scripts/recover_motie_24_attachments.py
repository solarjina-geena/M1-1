from pathlib import Path
import pandas as pd
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import re
import html

BASE = Path("data/raw/motie")
LOG = BASE / "motie_32_download_log.csv"
OUT = BASE / "motie_24_attachment_candidates.csv"

df = pd.read_csv(LOG, dtype=str, keep_default_na=False)
failed = df[df["status"] == "HTML_REJECTED"].copy()

session = requests.Session()
session.headers.update({
    "User-Agent":
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 Chrome/152 Safari/537.36"
})

rows = []

print("=" * 100)
print("MOTIE HTML -> ATTACHMENT RECOVERY")
print("=" * 100)

for _, row in failed.iterrows():

    period = row["period"]
    url = row["source_url"]

    print()
    print("-" * 100)
    print("PERIOD:", period)

    try:
        r = session.get(
            url,
            timeout=40,
            allow_redirects=True
        )

        text = r.text
        soup = BeautifulSoup(text, "html.parser")

        candidates = []

        # 1. 일반 <a href=""> 링크
        for a in soup.find_all("a"):

            href = a.get("href", "")
            label = " ".join(a.stripped_strings)

            if not href:
                continue

            h = html.unescape(href)

            interesting = (
                "attach/down" in h.lower()
                or ".hwp" in h.lower()
                or ".hwpx" in h.lower()
                or ".pdf" in h.lower()
                or "filedown" in h.lower()
                or "download" in h.lower()
            )

            if interesting:
                candidates.append((
                    urljoin(r.url, h),
                    label,
                    "A_TAG"
                ))

        # 2. HTML/JS 내부 attach/down 주소
        patterns = [
            r'''https?://[^"'<> ]+/attach/down/[^"'<> ]+''',
            r'''/attach/down/[^"'<> )]+''',
        ]

        for pattern in patterns:
            for m in re.findall(
                pattern,
                text,
                flags=re.I
            ):
                candidates.append((
                    urljoin(r.url, html.unescape(m)),
                    "",
                    "HTML_RAW"
                ))

        # 중복 제거
        seen = set()
        unique = []

        for u, label, source in candidates:

            u = u.replace("&amp;", "&")

            key = u.strip()

            if not key or key in seen:
                continue

            seen.add(key)

            unique.append(
                (key, label, source)
            )

        print("CANDIDATES:", len(unique))

        if not unique:
            print("  NONE")

        for n, (u, label, source) in enumerate(
            unique,
            1
        ):
            print(
                f"  [{n}] {source} | "
                f"{label[:80]} | {u[:180]}"
            )

            rows.append({
                "period": period,
                "candidate_no": n,
                "source": source,
                "label": label,
                "attachment_url": u,
                "page_url": r.url,
            })

    except Exception as e:

        print(
            "ERROR:",
            type(e).__name__,
            str(e)[:200]
        )

        rows.append({
            "period": period,
            "candidate_no": "",
            "source": "ERROR",
            "label":
                f"{type(e).__name__}: {e}",
            "attachment_url": "",
            "page_url": url,
        })


out = pd.DataFrame(rows)

out.to_csv(
    OUT,
    index=False,
    encoding="utf-8-sig"
)

found_periods = (
    out.loc[
        out["attachment_url"] != "",
        "period"
    ].nunique()
    if len(out)
    else 0
)

print()
print("=" * 100)
print("RESULT")
print("=" * 100)
print("TARGET PERIODS :", len(failed))
print("FOUND PERIODS  :", found_periods)
print("CANDIDATES     :", len(out))
print("OUTPUT         :", OUT)
