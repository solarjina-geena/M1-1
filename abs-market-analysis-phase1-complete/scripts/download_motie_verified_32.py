from pathlib import Path
import pandas as pd
import requests
import time

BASE = Path("data/raw/motie")
SRC = BASE / "motie_32_download_targets_verified.csv"
OUT = BASE / "monthly_pdf" / "verified_download_32"
LOG = BASE / "motie_32_download_log.csv"

OUT.mkdir(parents=True, exist_ok=True)

df = pd.read_csv(SRC, dtype=str, keep_default_na=False)

session = requests.Session()
session.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 Chrome/152 Safari/537.36"
})

def detect_ext(data):
    # PDF
    if data.startswith(b"%PDF"):
        return ".pdf"

    # HWP 구형 OLE
    if data.startswith(bytes.fromhex("D0CF11E0A1B11AE1")):
        return ".hwp"

    # ZIP 기반: HWPX 등
    if data.startswith(b"PK\x03\x04"):
        return ".hwpx"

    return None


rows = []

print("=" * 100)
print("MOTIE VERIFIED 32 DOWNLOAD")
print("=" * 100)

for i, row in df.iterrows():

    period = row["period"]
    url = row["url"]

    print(f"[{i+1:02d}/{len(df)}] {period}", end=" ... ", flush=True)

    try:
        r = session.get(
            url,
            timeout=40,
            allow_redirects=True
        )

        data = r.content
        ext = detect_ext(data)

        # HTML 오류페이지 차단
        html_like = (
            data.lstrip().lower().startswith(b"<!doctype html")
            or data.lstrip().lower().startswith(b"<html")
        )

        if r.status_code != 200:
            status = f"HTTP_{r.status_code}"
            filename = ""

        elif html_like:
            status = "HTML_REJECTED"
            filename = ""

        elif ext is None:
            status = "UNKNOWN_FORMAT"
            filename = ""

        elif len(data) < 10000:
            status = "TOO_SMALL"
            filename = ""

        else:
            path = OUT / f"{period}{ext}"
            path.write_bytes(data)

            status = "SAVED"
            filename = path.name

        print(
            f"{status} | "
            f"{len(data):,} bytes"
            + (f" | {filename}" if filename else "")
        )

        rows.append({
            "period": period,
            "status": status,
            "http_status": r.status_code,
            "bytes": len(data),
            "content_type": r.headers.get("Content-Type", ""),
            "final_url": r.url,
            "filename": filename,
            "title": row.get("title", ""),
            "source_url": url,
        })

    except Exception as e:

        print(f"ERROR | {type(e).__name__}: {e}")

        rows.append({
            "period": period,
            "status": "ERROR",
            "http_status": "",
            "bytes": 0,
            "content_type": "",
            "final_url": "",
            "filename": "",
            "title": row.get("title", ""),
            "source_url": url,
            "error": f"{type(e).__name__}: {e}",
        })

    time.sleep(0.25)


log = pd.DataFrame(rows)

log.to_csv(
    LOG,
    index=False,
    encoding="utf-8-sig"
)

saved = log[log["status"] == "SAVED"]

print()
print("=" * 100)
print("RESULT")
print("=" * 100)
print("TARGET :", len(df))
print("SAVED  :", len(saved))
print("FAILED :", len(df) - len(saved))

print()
print("=== FILE TYPES ===")

if len(saved):
    print(
        saved["filename"]
        .map(lambda x: Path(x).suffix.lower())
        .value_counts()
        .to_string()
    )
else:
    print("NONE")

failed = log[log["status"] != "SAVED"]

if len(failed):
    print()
    print("=== FAILED ===")
    print(
        failed[
            ["period", "status", "http_status", "bytes"]
        ].to_string(index=False)
    )

print()
print("OUTPUT :", OUT)
print("LOG    :", LOG)
