from pathlib import Path
from urllib.parse import unquote
import pandas as pd
import requests
import re
import time

BASE = Path("data/raw/motie")
CSV = BASE / "motie_24_attachment_candidates.csv"

OUT_DIR = (
    BASE
    / "monthly_pdf"
    / "verified_download_24"
)
OUT_DIR.mkdir(parents=True, exist_ok=True)

LOG = BASE / "motie_24_attachment_download_log.csv"

df = pd.read_csv(
    CSV,
    dtype=str,
    keep_default_na=False
)

session = requests.Session()
session.headers.update({
    "User-Agent":
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 Chrome/152 Safari/537.36"
})


def score_candidate(row):

    label = (
        row.get("label", "") + " " +
        row.get("attachment_url", "")
    ).lower()

    score = 0

    # 자동차 산업 자료 우선
    if "자동차" in label:
        score += 100

    if "산업" in label:
        score += 40

    if "동향" in label:
        score += 40

    if "월간" in label:
        score += 20

    # 문서 파일 우선
    if ".hwpx" in label:
        score += 30

    elif ".hwp" in label:
        score += 25

    elif ".pdf" in label:
        score += 20

    # 참고자료도 자동차산업 동향이면 허용
    if "참고자료" in label:
        score += 5

    # 일반 수출입 동향은 감점
    if "수출입" in label and "자동차" not in label:
        score -= 100

    return score


def detect_type(content, content_type, url):

    head = content[:16]

    # PDF
    if content.startswith(b"%PDF"):
        return ".pdf"

    # HWP OLE
    if head.startswith(
        bytes.fromhex("D0CF11E0A1B11AE1")
    ):
        return ".hwp"

    # HWPX/ZIP
    if content.startswith(b"PK"):
        return ".hwpx"

    ct = (content_type or "").lower()
    u = unquote(url).lower()

    if "pdf" in ct or ".pdf" in u:
        return ".pdf"

    if ".hwpx" in u:
        return ".hwpx"

    if ".hwp" in u:
        return ".hwp"

    return ""


print("=" * 100)
print("MOTIE 24 ATTACHMENT DOWNLOAD")
print("=" * 100)

rows = []

for period, group in df.groupby("period"):

    group = group.copy()

    group["score"] = group.apply(
        score_candidate,
        axis=1
    )

    group = group.sort_values(
        ["score", "candidate_no"],
        ascending=[False, True]
    )

    print()
    print("-" * 100)
    print("PERIOD:", period)

    success = False

    for _, row in group.iterrows():

        url = row["attachment_url"]

        if not url:
            continue

        try:

            r = session.get(
                url,
                timeout=50,
                allow_redirects=True
            )

            content = r.content

            ext = detect_type(
                content,
                r.headers.get(
                    "Content-Type", ""
                ),
                r.url
            )

            print(
                "TRY",
                f"SCORE={row['score']}",
                f"HTTP={r.status_code}",
                f"BYTES={len(content)}",
                f"TYPE={ext or 'UNKNOWN'}",
                row["label"][:70]
            )

            # 정상 파일 기준
            if (
                r.status_code == 200
                and len(content) > 10000
                and ext
            ):

                filename = f"{period}{ext}"

                path = OUT_DIR / filename

                path.write_bytes(content)

                rows.append({
                    "period": period,
                    "status": "SAVED",
                    "filename": filename,
                    "bytes": len(content),
                    "score": row["score"],
                    "label": row["label"],
                    "source_url": url,
                    "final_url": r.url,
                })

                print(
                    "SAVED:",
                    filename,
                    len(content)
                )

                success = True
                break

        except Exception as e:

            print(
                "ERROR:",
                type(e).__name__,
                str(e)[:150]
            )

        time.sleep(0.15)

    if not success:

        rows.append({
            "period": period,
            "status": "FAILED",
            "filename": "",
            "bytes": "",
            "score": "",
            "label": "",
            "source_url": "",
            "final_url": "",
        })

        print("FAILED:", period)


out = pd.DataFrame(rows)

out.to_csv(
    LOG,
    index=False,
    encoding="utf-8-sig"
)

saved = (
    out["status"] == "SAVED"
).sum()

failed = (
    out["status"] == "FAILED"
).sum()

print()
print("=" * 100)
print("RESULT")
print("=" * 100)

print("TARGET :", len(out))
print("SAVED  :", saved)
print("FAILED :", failed)

print()
print("=== FILE TYPES ===")

if saved:
    print(
        out.loc[
            out["status"] == "SAVED",
            "filename"
        ]
        .map(lambda x: Path(x).suffix)
        .value_counts()
        .to_string()
    )

if failed:

    print()
    print("=== FAILED ===")

    print(
        " ".join(
            out.loc[
                out["status"] == "FAILED",
                "period"
            ]
        )
    )

print()
print("OUTPUT :", OUT_DIR)
print("LOG    :", LOG)
