from pathlib import Path
import pandas as pd
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import re
import time

# ============================================================
# [작업 목적]
# 2026-01 ~ 2026-08 산업부 공식 게시글에서
# 실제 보도자료 첨부파일(PDF/HWP/HWPX)을 찾아 다운로드합니다.
#
# [왜 이 단계가 필요한가?]
# 앞 단계에서 확인한 결과,
# 게시글 HTML에는 실제 생산/내수/수출 숫자가 없었습니다.
#
# 따라서 숫자가 들어 있는 "첨부 원문"을 직접 확보합니다.
#
# ------------------------------------------------------------
# [입력]
# data/raw/motie/motie_2026_official_sources.csv
#
# [출력]
# data/raw/motie/2026_attachments/
#     2026-01_xxx.pdf
#     2026-02_xxx.hwpx
#     ...
#
# data/raw/motie/motie_2026_attachment_index.csv
#
# ------------------------------------------------------------
# [중요]
# - 아직 숫자 추출 안 함
# - BODY_VERIFIED 처리 안 함
# - MASTER 변경 없음
# ============================================================


# ------------------------------------------------------------
# [1단계] 기본 경로
# ------------------------------------------------------------

BASE = Path("data/raw/motie")

SOURCE_FILE = (
    BASE /
    "motie_2026_official_sources.csv"
)

DOWNLOAD_DIR = (
    BASE /
    "2026_attachments"
)

DOWNLOAD_DIR.mkdir(
    parents=True,
    exist_ok=True
)

OUT = (
    BASE /
    "motie_2026_attachment_index.csv"
)


# ------------------------------------------------------------
# [2단계] 공식 원문 목록 읽기
# ------------------------------------------------------------

sources = pd.read_csv(
    SOURCE_FILE,
    encoding="utf-8-sig"
)


# ------------------------------------------------------------
# [3단계] 웹 요청 설정
# ------------------------------------------------------------

HEADERS = {
    "User-Agent":
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 Chrome/152 Safari/537.36"
}


# ------------------------------------------------------------
# [4단계] 첨부파일 종류 판별
#
# 산업부 게시글에는
# PDF / HWP / HWPX가 같이 있는 경우가 있습니다.
#
# 이번에는 모두 보존합니다.
# 나중에 가장 잘 읽히는 파일을 선택합니다.
# ------------------------------------------------------------

def detect_extension(text, url):

    combined = (
        str(text) + " " + str(url)
    ).lower()

    if ".hwpx" in combined:
        return ".hwpx"

    if ".hwp" in combined:
        return ".hwp"

    if ".pdf" in combined:
        return ".pdf"

    return ""


# ------------------------------------------------------------
# [5단계] 실제 파일인지 확인
#
# 과거 작업에서 HTTP 200인데 실제로는
# HTML 오류페이지였던 경우가 있었습니다.
#
# 그래서 다운로드 후 파일 앞부분을 검사합니다.
# ------------------------------------------------------------

def check_file_type(content):

    # PDF
    if content.startswith(b"%PDF"):
        return "PDF"

    # HWP 구버전은 OLE Compound File
    if content.startswith(
        bytes.fromhex("D0CF11E0A1B11AE1")
    ):
        return "HWP"

    # HWPX는 ZIP 기반
    if content.startswith(b"PK"):
        return "ZIP_OR_HWPX"

    # HTML 오류페이지 차단
    head = content[:500].lower()

    if (
        b"<html" in head
        or b"<!doctype html" in head
    ):
        return "HTML"

    return "UNKNOWN"


# ------------------------------------------------------------
# [6단계] 월별 공식 게시글에서 첨부파일 찾기
# ------------------------------------------------------------

records = []

print("=" * 100)
print("MOTIE 2026 ATTACHMENT DOWNLOAD")
print("=" * 100)
print()

for idx, row in sources.iterrows():

    period = row["period"]
    page_url = row["source_url"]

    print(
        f"[{idx+1}/8] {period} 첨부파일 확인...",
        flush=True
    )

    try:

        # --------------------------------------------
        # 공식 게시글 열기
        # --------------------------------------------

        r = requests.get(
            page_url,
            headers=HEADERS,
            timeout=20
        )

        r.raise_for_status()

        soup = BeautifulSoup(
            r.text,
            "html.parser"
        )

        candidates = []

        # --------------------------------------------
        # 게시글의 모든 링크 검사
        # --------------------------------------------

        for a in soup.find_all(
            "a",
            href=True
        ):

            href = a.get(
                "href",
                ""
            )

            label = " ".join(
                a.get_text(
                    " ",
                    strip=True
                ).split()
            )

            ext = detect_extension(
                label,
                href
            )

            if not ext:
                continue

            full_url = urljoin(
                page_url,
                href
            )

            candidates.append({
                "label": label,
                "url": full_url,
                "extension": ext
            })


        # --------------------------------------------
        # 같은 URL 중복 제거
        # --------------------------------------------

        unique = {}

        for c in candidates:
            unique[c["url"]] = c

        candidates = list(
            unique.values()
        )


        # --------------------------------------------
        # 첨부파일이 하나도 없으면 기록
        # --------------------------------------------

        if not candidates:

            records.append({
                "period": period,
                "page_url": page_url,
                "status": "NO_ATTACHMENT"
            })

            print(
                "   → 첨부파일 없음"
            )

            continue


        # --------------------------------------------
        # 발견한 첨부파일 모두 다운로드
        # --------------------------------------------

        saved_count = 0

        for n, c in enumerate(
            candidates,
            1
        ):

            try:

                fr = requests.get(
                    c["url"],
                    headers=HEADERS,
                    timeout=30
                )

                content = fr.content

                real_type = check_file_type(
                    content
                )

                # ------------------------------------
                # HTML이면 파일로 저장하지 않음
                # ------------------------------------

                if real_type == "HTML":

                    records.append({
                        "period": period,
                        "page_url": page_url,
                        "attachment_label":
                            c["label"],
                        "attachment_url":
                            c["url"],
                        "extension":
                            c["extension"],
                        "http_status":
                            fr.status_code,
                        "bytes":
                            len(content),
                        "real_type":
                            real_type,
                        "status":
                            "HTML_REJECTED"
                    })

                    continue


                # ------------------------------------
                # 파일명 안전하게 생성
                #
                # 예:
                # 2026-07_01.pdf
                # 2026-07_02.hwpx
                # ------------------------------------

                filename = (
                    f"{period}_"
                    f"{n:02d}"
                    f"{c['extension']}"
                )

                save_path = (
                    DOWNLOAD_DIR /
                    filename
                )

                save_path.write_bytes(
                    content
                )

                saved_count += 1


                # ------------------------------------
                # 다운로드 기록 저장
                # ------------------------------------

                records.append({
                    "period": period,
                    "page_url": page_url,
                    "attachment_label":
                        c["label"],
                    "attachment_url":
                        c["url"],
                    "extension":
                        c["extension"],
                    "http_status":
                        fr.status_code,
                    "bytes":
                        len(content),
                    "real_type":
                        real_type,
                    "saved_file":
                        str(save_path),
                    "status":
                        "SAVED"
                })


            except Exception as e:

                records.append({
                    "period": period,
                    "page_url": page_url,
                    "attachment_label":
                        c["label"],
                    "attachment_url":
                        c["url"],
                    "status":
                        "DOWNLOAD_ERROR",
                    "error":
                        str(e)
                })


        print(
            f"   → 후보 {len(candidates)}개 / "
            f"저장 {saved_count}개"
        )

        # 서버 부담 방지
        time.sleep(0.5)


    except Exception as e:

        records.append({
            "period": period,
            "page_url": page_url,
            "status": "PAGE_ERROR",
            "error": str(e)
        })

        print(
            "   → PAGE ERROR:",
            e
        )


# ------------------------------------------------------------
# [7단계] 전체 결과 저장
# ------------------------------------------------------------

result = pd.DataFrame(
    records
)

result.to_csv(
    OUT,
    index=False,
    encoding="utf-8-sig"
)


# ------------------------------------------------------------
# [8단계] 결과 요약
#
# 터미널에는 긴 URL이나 파일명을 전부 출력하지 않습니다.
# 월별로 몇 개가 저장됐는지만 확인합니다.
# ------------------------------------------------------------

print()
print("=" * 100)
print("RESULT")
print("=" * 100)

for period in sources["period"]:

    g = result[
        result["period"] == period
    ]

    saved = (
        (g["status"] == "SAVED").sum()
        if "status" in g.columns
        else 0
    )

    rejected = (
        (g["status"] == "HTML_REJECTED").sum()
        if "status" in g.columns
        else 0
    )

    errors = (
        g["status"].isin([
            "DOWNLOAD_ERROR",
            "PAGE_ERROR"
        ]).sum()
        if "status" in g.columns
        else 0
    )

    print(
        f"{period} | "
        f"SAVED={saved} | "
        f"HTML_REJECTED={rejected} | "
        f"ERROR={errors}"
    )


# ------------------------------------------------------------
# [9단계] 파일 형식별 개수
# ------------------------------------------------------------

saved_rows = result[
    result["status"] == "SAVED"
].copy()

print()
print("=== SAVED FILE TYPES ===")

if saved_rows.empty:

    print("NONE")

else:

    print(
        saved_rows[
            "real_type"
        ].value_counts().to_string()
    )


print()
print(
    "FILES  :",
    DOWNLOAD_DIR
)

print(
    "INDEX  :",
    OUT
)

print()
print(
    "※ 아직 숫자 추출 안 함"
)

print(
    "※ BODY_VERIFIED 처리 안 함"
)

print(
    "※ MASTER 변경 없음"
)
