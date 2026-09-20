from __future__ import annotations

import hashlib
import mimetypes
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

import pandas as pd
import requests

from config.settings import PATH_CONFIG
from config.sources import SOURCES


RAW_DIR = Path(PATH_CONFIG["raw"]) / "technical"
SOURCE_LOG_PATH = Path(PATH_CONFIG["metadata"]) / "source_log.csv"


def _safe_filename(text: str) -> str:
    allowed = (
        "-_.() "
        "abcdefghijklmnopqrstuvwxyz"
        "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        "0123456789"
    )
    cleaned = "".join(
        c if c in allowed else "_" for c in text
    )
    cleaned = "_".join(cleaned.split())
    return cleaned.strip("_") or "technical_source"


def _guess_extension(
    url: str,
    content_type: str | None,
) -> str:
    suffix = Path(urlparse(url).path).suffix.lower()

    if suffix and len(suffix) <= 6:
        return suffix

    if content_type:
        mime = content_type.split(";")[0].strip()
        guessed = mimetypes.guess_extension(mime)
        if guessed:
            return guessed

    return ".html"


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def collect_technical_source(
    url: str,
    title: str,
    notes: str = "",
) -> dict:
    RAW_DIR.mkdir(parents=True, exist_ok=True)

    response = requests.get(
        url,
        timeout=60,
        headers={
            "User-Agent": (
                "Mozilla/5.0 ABS-Market-Intelligence "
                "technical-source-collector"
            )
        },
    )
    response.raise_for_status()

    collected_at = datetime.now()
    timestamp = collected_at.strftime("%Y%m%d%H%M%S")

    extension = _guess_extension(
        url,
        response.headers.get("Content-Type"),
    )

    filename = (
        f"{timestamp}_{_safe_filename(title)}"
        f"{extension}"
    )

    raw_path = RAW_DIR / filename
    raw_path.write_bytes(response.content)

    digest = _sha256(response.content)
    source_id = f"TECH_{timestamp}"

    source_info = SOURCES.get(
        "technical",
        {
            "name": "공개 기술자료 / 제조사 공식자료",
        },
    )

    log_row = {
        "source_id": source_id,
        "source_key": "technical",
        "source_name": source_info["name"],
        "basis_date": "",
        "collected_at": collected_at.isoformat(
            timespec="seconds"
        ),
        "source_url": url,
        "raw_file_path": str(raw_path),
        "sha256": digest,
        "status": "SUCCESS",
        "notes": notes or title,
    }

    if SOURCE_LOG_PATH.exists():
        log_df = pd.read_csv(
            SOURCE_LOG_PATH,
            dtype="string",
        )
    else:
        log_df = pd.DataFrame(
            columns=list(log_row.keys())
        )

    log_df = pd.concat(
        [
            log_df,
            pd.DataFrame([log_row]),
        ],
        ignore_index=True,
    )

    log_df.to_csv(
        SOURCE_LOG_PATH,
        index=False,
        encoding="utf-8-sig",
    )

    return {
        "source_id": source_id,
        "raw_file": str(raw_path),
        "sha256": digest,
        "bytes": len(response.content),
        "content_type": response.headers.get(
            "Content-Type"
        ),
    }


if __name__ == "__main__":
    print("technical_source_collector 준비 완료")
