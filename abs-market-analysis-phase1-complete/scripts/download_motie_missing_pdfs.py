from __future__ import annotations

import re
import time
from pathlib import Path
from urllib.parse import urljoin

import pandas as pd
import requests
from bs4 import BeautifulSoup


BASE_DIR = Path(__file__).resolve().parents[1]

INPUT_FILE = (
    BASE_DIR
    / "data"
    / "raw"
    / "motie"
    / "motie_missing_match_best.csv"
)

OUTPUT_DIR = (
    BASE_DIR
    / "data"
    / "raw"
    / "motie"
    / "monthly_pdf"
    / "recovered_pdf"
)

LOG_FILE = (
    BASE_DIR
    / "data"
    / "raw"
    / "motie"
    / "motie_missing_pdf_download_log.csv"
)

OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True,
)

session = requests.Session()

session.headers.update(
    {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/152.0.0.0 Safari/537.36"
        )
    }
)


def clean(value) -> str:
    if pd.isna(value):
        return ""

    return " ".join(
        str(value).split()
    )


def is_pdf_response(response) -> bool:

    content_type = (
        response.headers
        .get("Content-Type", "")
        .lower()
    )

    if "pdf" in content_type:
        return True

    content = response.content[:20]

    if content.startswith(b"%PDF"):
        return True

    return False


def extract_pdf_links(
    article_url: str,
):

    response = session.get(
        article_url,
        timeout=30,
    )

    response.raise_for_status()

    soup = BeautifulSoup(
        response.text,
        "html.parser",
    )

    links = []

    for a in soup.find_all(
        "a",
        href=True,
    ):

        href = clean(
            a.get("href")
        )

        title = clean(
            a.get_text(
                " ",
                strip=True,
            )
        )

        full_url = urljoin(
            article_url,
            href,
        )

        combined = (
            title + " " + href
        ).lower()

        if (
            ".pdf" in combined
            or (
                "/attach/down/" in full_url
                and "pdf" in title.lower()
            )
        ):
            links.append(
                {
                    "title": title,
                    "url": full_url,
                }
            )

    # 중복 제거
    unique = []
    seen = set()

    for item in links:

        if item["url"] in seen:
            continue

        seen.add(
            item["url"]
        )

        unique.append(
            item
        )

    return unique


def download_pdf(
    url: str,
    output_path: Path,
):

    response = session.get(
        url,
        timeout=60,
        allow_redirects=True,
    )

    response.raise_for_status()

    if not is_pdf_response(
        response
    ):
        return False, len(response.content)

    output_path.write_bytes(
        response.content
    )

    return True, len(response.content)


df = pd.read_csv(
    INPUT_FILE
)

df = df[
    df["match_status"] == "CANDIDATE"
].copy()

print("=" * 90)
print("MOTIE MISSING PDF DOWNLOADER")
print("=" * 90)
print("TARGET :", len(df))
print()

logs = []


for _, row in df.iterrows():

    period = clean(
        row["period"]
    )

    source_type = clean(
        row.get("type", "")
    ).upper()

    source_url = clean(
        row.get("url", "")
    )

    score = row.get(
        "score"
    )

    print("-" * 90)
    print(
        period,
        "TYPE=" + source_type,
        "SCORE=" + str(score),
    )

    candidates = []

    # --------------------------------------------------------
    # ARTICLE이면 게시물 안에서 PDF 첨부 찾기
    # --------------------------------------------------------

    if source_type == "ARTICLE":

        try:

            candidates = extract_pdf_links(
                source_url
            )

        except Exception as exc:

            print(
                "ARTICLE ERROR:",
                exc,
            )

            logs.append(
                {
                    "period": period,
                    "score": score,
                    "source_type": source_type,
                    "source_url": source_url,
                    "pdf_url": "",
                    "pdf_title": "",
                    "file": "",
                    "bytes": 0,
                    "status": "ARTICLE_ERROR",
                    "error": str(exc),
                }
            )

            continue

    # --------------------------------------------------------
    # ATTACHMENT 후보는 직접 다운로드 시도
    # --------------------------------------------------------

    elif source_type == "ATTACHMENT":

        candidates = [
            {
                "title": clean(
                    row.get(
                        "title",
                        ""
                    )
                ),
                "url": source_url,
            }
        ]

    else:

        logs.append(
            {
                "period": period,
                "score": score,
                "source_type": source_type,
                "source_url": source_url,
                "pdf_url": "",
                "pdf_title": "",
                "file": "",
                "bytes": 0,
                "status": "UNKNOWN_TYPE",
                "error": "",
            }
        )

        print("UNKNOWN TYPE")

        continue

    # --------------------------------------------------------
    # PDF 후보 없음
    # --------------------------------------------------------

    if not candidates:

        print("PDF LINK NOT FOUND")

        logs.append(
            {
                "period": period,
                "score": score,
                "source_type": source_type,
                "source_url": source_url,
                "pdf_url": "",
                "pdf_title": "",
                "file": "",
                "bytes": 0,
                "status": "PDF_LINK_NOT_FOUND",
                "error": "",
            }
        )

        continue

    # --------------------------------------------------------
    # 여러 첨부 중 실제 PDF 확인
    # --------------------------------------------------------

    success = False

    for n, candidate in enumerate(
        candidates,
        start=1,
    ):

        pdf_url = candidate["url"]
        pdf_title = candidate["title"]

        if len(candidates) == 1:
            filename = f"{period}.pdf"
        else:
            filename = (
                f"{period}_{n:02d}.pdf"
            )

        output_path = (
            OUTPUT_DIR
            / filename
        )

        try:

            ok, size = download_pdf(
                pdf_url,
                output_path,
            )

            if ok:

                print(
                    "PDF OK :",
                    filename,
                    f"{size:,} bytes",
                )

                logs.append(
                    {
                        "period": period,
                        "score": score,
                        "source_type": source_type,
                        "source_url": source_url,
                        "pdf_url": pdf_url,
                        "pdf_title": pdf_title,
                        "file": str(output_path),
                        "bytes": size,
                        "status": "DOWNLOADED",
                        "error": "",
                    }
                )

                success = True

            else:

                print(
                    "NOT PDF:",
                    pdf_title[:80],
                )

                logs.append(
                    {
                        "period": period,
                        "score": score,
                        "source_type": source_type,
                        "source_url": source_url,
                        "pdf_url": pdf_url,
                        "pdf_title": pdf_title,
                        "file": "",
                        "bytes": size,
                        "status": "NOT_PDF",
                        "error": "",
                    }
                )

        except Exception as exc:

            print(
                "DOWNLOAD ERROR:",
                exc,
            )

            logs.append(
                {
                    "period": period,
                    "score": score,
                    "source_type": source_type,
                    "source_url": source_url,
                    "pdf_url": pdf_url,
                    "pdf_title": pdf_title,
                    "file": "",
                    "bytes": 0,
                    "status": "DOWNLOAD_ERROR",
                    "error": str(exc),
                }
            )

        time.sleep(0.15)

    if not success:

        print(
            "NO VALID PDF FOR",
            period,
        )


log_df = pd.DataFrame(
    logs
)

log_df.to_csv(
    LOG_FILE,
    index=False,
    encoding="utf-8-sig",
)

print()
print("=" * 90)
print("RESULT")
print("=" * 90)

if len(log_df):

    print(
        log_df["status"]
        .value_counts()
        .to_string()
    )

    downloaded = log_df[
        log_df["status"] == "DOWNLOADED"
    ]

    print()
    print(
        "DOWNLOADED FILES  :",
        len(downloaded),
    )

    print(
        "DOWNLOADED PERIODS:",
        downloaded["period"]
        .nunique(),
    )

    failed_periods = sorted(
        set(df["period"])
        - set(downloaded["period"])
    )

    print(
        "FAILED PERIODS     :",
        len(failed_periods),
    )

    if failed_periods:

        print()
        print("=== FAILED ===")

        for period in failed_periods:
            print(period)

print()
print(
    "PDF DIR:",
    OUTPUT_DIR,
)

print(
    "LOG    :",
    LOG_FILE,
)