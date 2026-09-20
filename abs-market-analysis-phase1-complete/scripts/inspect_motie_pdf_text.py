from __future__ import annotations

import io
import re
import sys
from pathlib import Path
from urllib.parse import urljoin

import pandas as pd
import requests
from bs4 import BeautifulSoup
from pypdf import PdfReader


BASE_DIR = Path(__file__).resolve().parents[1]

INDEX_CANDIDATES = [
    BASE_DIR / "data" / "raw" / "motie" / "motie_auto_monthly_index_recovered.csv",
    BASE_DIR / "data" / "raw" / "motie" / "motie_auto_monthly_index_verified.csv",
    BASE_DIR / "data" / "raw" / "motie" / "motie_auto_monthly_index.csv",
]

TEST_PERIODS = [
    "2015-02",
    "2020-02",
    "2025-01",
]

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 "
        "(Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 "
        "Chrome/120 Safari/537.36"
    )
}

OUTPUT_DIR = (
    BASE_DIR
    / "data"
    / "raw"
    / "motie"
    / "pdf_text_test"
)

OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True,
)


def safe_print(*args, **kwargs):
    text = " ".join(str(x) for x in args)

    encoding = (
        getattr(sys.stdout, "encoding", None)
        or "utf-8"
    )

    text = text.encode(
        encoding,
        errors="replace",
    ).decode(
        encoding,
        errors="replace",
    )

    print(
        text,
        **kwargs,
    )


def load_index() -> tuple[pd.DataFrame, Path]:

    for path in INDEX_CANDIDATES:

        if not path.exists():
            continue

        df = pd.read_csv(
            path,
            dtype=str,
        )

        if "period" not in df.columns:
            continue

        if "url" not in df.columns:
            continue

        return df, path

    raise FileNotFoundError(
        "사용 가능한 MOTIE index CSV를 찾지 못했습니다."
    )


def get_page(url: str) -> str:

    response = requests.get(
        url,
        headers=HEADERS,
        timeout=30,
    )

    response.raise_for_status()

    return response.text


def find_pdf_url(
    page_url: str,
    html: str,
) -> tuple[str | None, str | None]:

    soup = BeautifulSoup(
        html,
        "html.parser",
    )

    candidates = []

    for a in soup.find_all(
        "a",
        href=True,
    ):
        href = a.get(
            "href",
            "",
        ).strip()

        label = " ".join(
            a.stripped_strings
        )

        label_lower = label.lower()
        href_lower = href.lower()

        is_pdf = (
            ".pdf" in label_lower
            or ".pdf" in href_lower
        )

        is_download = (
            "/attach/down/" in href_lower
        )

        if is_pdf and is_download:
            candidates.append(
                (
                    urljoin(
                        page_url,
                        href,
                    ),
                    label,
                )
            )

    if not candidates:
        return None, None

    return candidates[0]


def download_pdf(
    pdf_url: str,
) -> bytes:

    response = requests.get(
        pdf_url,
        headers=HEADERS,
        timeout=60,
    )

    response.raise_for_status()

    data = response.content

    if not data.startswith(
        b"%PDF"
    ):
        raise ValueError(
            "다운로드 결과가 PDF 형식이 아닙니다."
        )

    return data


def extract_pdf_text(
    pdf_data: bytes,
) -> tuple[str, int]:

    reader = PdfReader(
        io.BytesIO(
            pdf_data
        )
    )

    pages = []

    for page_no, page in enumerate(
        reader.pages,
        start=1,
    ):

        try:
            text = (
                page.extract_text()
                or ""
            )

        except Exception as exc:
            text = (
                f"\n"
                f"[PAGE {page_no} "
                f"EXTRACTION ERROR: "
                f"{exc!r}]"
                f"\n"
            )

        pages.append(
            f"\n\n"
            f"===== PAGE {page_no} ====="
            f"\n\n"
            f"{text}"
        )

    return (
        "\n".join(pages),
        len(reader.pages),
    )


def normalize_for_search(
    text: str,
) -> str:

    text = text.replace(
        "\xa0",
        " ",
    )

    text = re.sub(
        r"[ \t]+",
        " ",
        text,
    )

    text = re.sub(
        r"\n{3,}",
        "\n\n",
        text,
    )

    return text


def show_context(
    text: str,
    keyword: str,
    width: int = 900,
):

    positions = [
        m.start()
        for m in re.finditer(
            re.escape(keyword),
            text,
            flags=re.IGNORECASE,
        )
    ]

    safe_print()
    safe_print(
        f"--- KEYWORD: {keyword} "
        f"/ MATCHES: {len(positions)} ---"
    )

    if not positions:
        safe_print(
            "NOT FOUND"
        )
        return

    for no, pos in enumerate(
        positions[:3],
        start=1,
    ):

        start = max(
            0,
            pos - width,
        )

        end = min(
            len(text),
            pos + width,
        )

        safe_print()
        safe_print(
            f"[CONTEXT {no}]"
        )

        safe_print(
            text[start:end]
        )


def main():

    df, index_file = load_index()

    safe_print(
        "=" * 90
    )
    safe_print(
        "MOTIE PDF TEXT INSPECTION"
    )
    safe_print(
        "=" * 90
    )
    safe_print(
        "INDEX:",
        index_file,
    )

    for period in TEST_PERIODS:

        safe_print()
        safe_print(
            "=" * 90
        )
        safe_print(
            "PERIOD :",
            period,
        )
        safe_print(
            "=" * 90
        )

        matched = df[
            df["period"] == period
        ].copy()

        if matched.empty:
            safe_print(
                "INDEX ROW NOT FOUND"
            )
            continue

        matched = matched[
            matched["url"].notna()
        ]

        matched = matched[
            matched["url"].str.strip()
            != ""
        ]

        if matched.empty:
            safe_print(
                "URL NOT FOUND"
            )
            continue

        page_url = (
            matched.iloc[0]["url"]
            .strip()
        )

        safe_print(
            "PAGE URL:",
            page_url,
        )

        try:
            html = get_page(
                page_url
            )

            pdf_url, pdf_label = find_pdf_url(
                page_url,
                html,
            )

            if not pdf_url:
                safe_print(
                    "PDF ATTACHMENT NOT FOUND"
                )
                continue

            safe_print(
                "PDF LABEL:",
                pdf_label,
            )

            safe_print(
                "PDF URL:",
                pdf_url,
            )

            pdf_data = download_pdf(
                pdf_url
            )

            pdf_file = (
                OUTPUT_DIR
                / f"{period}.pdf"
            )

            pdf_file.write_bytes(
                pdf_data
            )

            text, page_count = extract_pdf_text(
                pdf_data
            )

            text_file = (
                OUTPUT_DIR
                / f"{period}.txt"
            )

            text_file.write_text(
                text,
                encoding="utf-8",
            )

            safe_print(
                "PDF SIZE:",
                len(pdf_data),
            )

            safe_print(
                "PAGE COUNT:",
                page_count,
            )

            safe_print(
                "TEXT LENGTH:",
                len(text),
            )

            safe_print(
                "PDF SAVED:",
                pdf_file,
            )

            safe_print(
                "TEXT SAVED:",
                text_file,
            )

            searchable = normalize_for_search(
                text
            )

            for keyword in [
                "생산",
                "생산량",
                "내수",
                "수출",
                "자동차",
            ]:
                show_context(
                    searchable,
                    keyword,
                )

        except Exception as exc:

            safe_print(
                "ERROR:",
                repr(exc),
            )

    safe_print()
    safe_print(
        "=" * 90
    )
    safe_print(
        "INSPECTION COMPLETED"
    )
    safe_print(
        "=" * 90
    )


if __name__ == "__main__":
    main()
