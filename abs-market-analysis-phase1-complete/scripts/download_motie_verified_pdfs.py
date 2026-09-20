from __future__ import annotations

import time
from pathlib import Path
from urllib.parse import urljoin

import pandas as pd
import requests
from bs4 import BeautifulSoup
from pypdf import PdfReader


BASE_DIR = Path(__file__).resolve().parents[1]

INDEX_FILE = (
    BASE_DIR
    / "data"
    / "raw"
    / "motie"
    / "motie_auto_monthly_index_recovered.csv"
)

OUTPUT_DIR = (
    BASE_DIR
    / "data"
    / "raw"
    / "motie"
    / "monthly_pdf"
)

PDF_DIR = OUTPUT_DIR / "pdf"
TEXT_DIR = OUTPUT_DIR / "text"

PDF_DIR.mkdir(parents=True, exist_ok=True)
TEXT_DIR.mkdir(parents=True, exist_ok=True)

LOG_FILE = OUTPUT_DIR / "download_log.csv"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 "
        "(Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 "
        "Chrome/120 Safari/537.36"
    )
}


def get_pdf_url(page_url: str) -> tuple[str | None, str | None]:

    response = requests.get(
        page_url,
        headers=HEADERS,
        timeout=30,
    )
    response.raise_for_status()

    soup = BeautifulSoup(
        response.text,
        "html.parser",
    )

    candidates = []

    for a in soup.find_all(
        "a",
        href=True,
    ):
        label = a.get_text(
            " ",
            strip=True,
        )

        href = a["href"]

        if ".pdf" not in label.lower():
            continue

        if "/attach/down/" not in href:
            continue

        candidates.append(
            (
                label,
                urljoin(page_url, href),
            )
        )

    if not candidates:
        return None, None

    # 자동차 산업 동향 PDF를 우선
    for label, url in candidates:

        compact = label.replace(" ", "")

        if (
            "자동차" in compact
            and "동향" in compact
        ):
            return label, url

    return candidates[0]


def download_pdf(
    url: str,
    target: Path,
):

    response = requests.get(
        url,
        headers=HEADERS,
        timeout=60,
    )
    response.raise_for_status()

    target.write_bytes(
        response.content
    )


def extract_pdf_text(
    pdf_path: Path,
) -> tuple[str, int]:

    reader = PdfReader(
        str(pdf_path)
    )

    parts = []

    for page_no, page in enumerate(
        reader.pages,
        start=1,
    ):
        try:
            text = (
                page.extract_text()
                or ""
            )
        except Exception:
            text = ""

        parts.append(
            f"\n===== PAGE {page_no} =====\n"
        )

        parts.append(text)

    return (
        "\n".join(parts),
        len(reader.pages),
    )


def main():

    df = pd.read_csv(
        INDEX_FILE,
        dtype=str,
    )

    rows = []

    total = len(df)

    print("=" * 78)
    print("MOTIE VERIFIED PDF DOWNLOAD")
    print("=" * 78)

    for idx, row in df.iterrows():

        period = row["period"]

        url = str(
            row.get("url", "")
        ).strip()

        if (
            not url
            or url.lower() == "nan"
        ):
            rows.append(
                {
                    "period": period,
                    "page_url": "",
                    "pdf_url": "",
                    "pdf_label": "",
                    "pdf_pages": None,
                    "text_chars": 0,
                    "status": "NO_VERIFIED_URL",
                }
            )

            print(
                f"{idx + 1:03d}/{total} "
                f"{period} NO_URL"
            )

            continue

        pdf_path = (
            PDF_DIR
            / f"{period}.pdf"
        )

        text_path = (
            TEXT_DIR
            / f"{period}.txt"
        )

        try:

            label, pdf_url = get_pdf_url(
                url
            )

            if not pdf_url:
                raise RuntimeError(
                    "PDF attachment not found"
                )

            if not pdf_path.exists():
                download_pdf(
                    pdf_url,
                    pdf_path,
                )

            text, pages = extract_pdf_text(
                pdf_path
            )

            text_path.write_text(
                text,
                encoding="utf-8",
            )

            chars = len(
                "".join(
                    text.split()
                )
            )

            status = (
                "TEXT_OK"
                if chars >= 300
                else "TEXT_WEAK"
            )

            rows.append(
                {
                    "period": period,
                    "page_url": url,
                    "pdf_url": pdf_url,
                    "pdf_label": label,
                    "pdf_pages": pages,
                    "text_chars": chars,
                    "status": status,
                }
            )

            print(
                f"{idx + 1:03d}/{total} "
                f"{period} "
                f"{status} "
                f"PAGES={pages} "
                f"CHARS={chars}"
            )

        except Exception as exc:

            rows.append(
                {
                    "period": period,
                    "page_url": url,
                    "pdf_url": "",
                    "pdf_label": "",
                    "pdf_pages": None,
                    "text_chars": 0,
                    "status": (
                        f"ERROR: {exc!r}"
                    ),
                }
            )

            print(
                f"{idx + 1:03d}/{total} "
                f"{period} ERROR "
                f"{exc!r}"
            )

        time.sleep(0.25)

    result = pd.DataFrame(rows)

    result.to_csv(
        LOG_FILE,
        index=False,
        encoding="utf-8-sig",
    )

    print()
    print("=" * 78)
    print("DOWNLOAD RESULT")
    print("=" * 78)

    print(
        result["status"]
        .value_counts()
        .to_string()
    )

    print()
    print("LOG:", LOG_FILE)


if __name__ == "__main__":
    main()
