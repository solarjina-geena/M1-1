from pathlib import Path
import pandas as pd
import requests
from bs4 import BeautifulSoup
import re
import time

# ============================================================
# [작업 목적]
# 2026년 공식 원문 8개의 "본문"을 실제로 읽어서 저장합니다.
#
# [입력]
# data/raw/motie/motie_2026_official_sources.csv
#
# [출력]
# ① data/raw/motie/2026_body_text/
#       2026-01.txt ~ 2026-08.txt
#
# ② data/raw/motie/motie_2026_body_check.csv
#
# [이번 단계에서 하는 일]
# - 공식 URL 접속
# - 페이지 본문 텍스트 저장
# - 대상 연/월 표현 존재 여부 확인
# - 생산/내수/수출 관련 문장 탐색
#
# [이번 단계에서 하지 않는 일]
# - 숫자를 VERIFIED 처리하지 않음
# - MASTER에 합치지 않음
#
# ★ MASTER 변경 없음
# ============================================================


# ------------------------------------------------------------
# [1단계] 경로 설정
# ------------------------------------------------------------

BASE = Path("data/raw/motie")

SOURCE_FILE = BASE / "motie_2026_official_sources.csv"

TEXT_DIR = BASE / "2026_body_text"
TEXT_DIR.mkdir(parents=True, exist_ok=True)

OUT = BASE / "motie_2026_body_check.csv"


# ------------------------------------------------------------
# [2단계] 공식 원문 목록 읽기
# ------------------------------------------------------------

df = pd.read_csv(
    SOURCE_FILE,
    encoding="utf-8-sig"
)

print("=" * 100)
print("MOTIE 2026 OFFICIAL BODY CHECK")
print("=" * 100)

print("SOURCE :", SOURCE_FILE)
print("TARGET :", len(df))
print()


# ------------------------------------------------------------
# [3단계] 웹 요청 설정
#
# 산업부 서버가 일반 브라우저 접속처럼 인식하도록
# User-Agent를 지정합니다.
# ------------------------------------------------------------

HEADERS = {
    "User-Agent":
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 Chrome/152 Safari/537.36"
}


# ------------------------------------------------------------
# [4단계] HTML → 읽을 수 있는 본문 텍스트 변환 함수
#
# script/style/menu 같은 불필요한 부분을 최대한 제거합니다.
# ------------------------------------------------------------

def html_to_text(html):

    soup = BeautifulSoup(
        html,
        "html.parser"
    )

    # 화면 동작용 태그 제거
    for tag in soup([
        "script",
        "style",
        "noscript"
    ]):
        tag.decompose()

    text = soup.get_text(
        "\n",
        strip=True
    )

    # 공백 정리
    lines = []

    for line in text.splitlines():

        line = re.sub(
            r"\s+",
            " ",
            line
        ).strip()

        if line:
            lines.append(line)

    return "\n".join(lines)


# ------------------------------------------------------------
# [5단계] 대상월 표현 확인 함수
#
# 예:
# 2026-02 →
# "2026년 2월"
# "'26년 2월"
# "'26.2월"
#
# 3월은 "1분기"
# 6월은 "상반기"
# 형태도 허용합니다.
# ------------------------------------------------------------

def period_check(period, text):

    year, month = map(
        int,
        period.split("-")
    )

    patterns = [

        rf"2026\s*년\s*0?{month}\s*월",

        rf"[’']?26\s*년\s*0?{month}\s*월",

        rf"[’']?26\s*[.\-]\s*0?{month}\s*월",
    ]

    for p in patterns:

        if re.search(p, text):

            return True, "MONTH_EXACT"

    # 3월 자료는 1분기 발표 가능
    if month == 3:

        if (
            "2026년 1분기" in text
            or "'26년 1분기" in text
            or "’26년 1분기" in text
        ):

            return True, "Q1_DOCUMENT"

    # 6월 자료는 상반기 발표 가능
    if month == 6:

        if (
            "2026년 상반기" in text
            or "'26년 상반기" in text
            or "’26년 상반기" in text
        ):

            return True, "H1_DOCUMENT"

    return False, "PERIOD_NOT_FOUND"


# ------------------------------------------------------------
# [6단계] 생산/내수/수출 관련 줄 찾기
#
# 여기서는 숫자를 확정하지 않습니다.
#
# 목적:
# "원문 어디에서 숫자가 언급되는가?"를 먼저 확인합니다.
#
# 친환경차 내수/수출이나 수출금액 등을 잘못 가져오는 것을
# 막기 위해 자동 VERIFIED는 하지 않습니다.
# ------------------------------------------------------------

def find_metric_lines(text):

    lines = text.splitlines()

    result = {
        "production_lines": [],
        "domestic_lines": [],
        "export_lines": []
    }

    for i, line in enumerate(lines):

        # 너무 긴 메뉴/페이지 문구 제외
        if len(line) > 1000:
            continue

        if "생산" in line:

            result[
                "production_lines"
            ].append(
                f"{i+1}: {line}"
            )

        if "내수" in line:

            result[
                "domestic_lines"
            ].append(
                f"{i+1}: {line}"
            )

        if "수출" in line:

            result[
                "export_lines"
            ].append(
                f"{i+1}: {line}"
            )

    # CSV가 지나치게 커지지 않도록
    # 각 항목 앞쪽 15개까지만 저장
    for key in result:

        result[key] = "\n".join(
            result[key][:15]
        )

    return result


# ------------------------------------------------------------
# [7단계] 공식 원문 8개 순차 확인
# ------------------------------------------------------------

results = []

for idx, row in df.iterrows():

    period = row["period"]
    url = row["source_url"]

    print(
        f"[{idx+1}/{len(df)}] "
        f"{period} 원문 확인 중...",
        flush=True
    )

    try:

        # --------------------------------------------
        # 공식 페이지 다운로드
        # --------------------------------------------

        r = requests.get(
            url,
            headers=HEADERS,
            timeout=20
        )

        r.raise_for_status()

        # --------------------------------------------
        # HTML → 텍스트
        # --------------------------------------------

        text = html_to_text(
            r.text
        )

        # --------------------------------------------
        # 원문 전체를 월별 TXT로 보존
        #
        # 나중에 숫자가 이상할 때
        # 다시 웹 검색하지 않고 이 파일을 볼 수 있습니다.
        # --------------------------------------------

        text_file = (
            TEXT_DIR /
            f"{period}.txt"
        )

        text_file.write_text(
            text,
            encoding="utf-8"
        )

        # --------------------------------------------
        # 대상월 확인
        # --------------------------------------------

        period_ok, period_method = (
            period_check(
                period,
                text
            )
        )

        # --------------------------------------------
        # 생산/내수/수출 관련 줄 찾기
        # --------------------------------------------

        metric = find_metric_lines(
            text
        )

        production_found = bool(
            metric["production_lines"]
        )

        domestic_found = bool(
            metric["domestic_lines"]
        )

        export_found = bool(
            metric["export_lines"]
        )

        # --------------------------------------------
        # 현재 단계 상태
        #
        # CONTENT_READY:
        # 대상월 + 생산/내수/수출 관련 본문 존재
        #
        # 주의:
        # CONTENT_READY ≠ BODY_VERIFIED
        # --------------------------------------------

        if (
            period_ok
            and production_found
            and domestic_found
            and export_found
        ):

            status = "CONTENT_READY"

        elif period_ok:

            status = "CONTENT_PARTIAL"

        else:

            status = "PERIOD_REVIEW"

        results.append({

            "period": period,

            "source_title":
                row["source_title"],

            "source_date":
                row["source_date"],

            "source_url":
                url,

            "http_status":
                r.status_code,

            "text_chars":
                len(text),

            "period_match":
                period_ok,

            "period_method":
                period_method,

            "production_found":
                production_found,

            "domestic_found":
                domestic_found,

            "export_found":
                export_found,

            "content_status":
                status,

            "production_context":
                metric["production_lines"],

            "domestic_context":
                metric["domestic_lines"],

            "export_context":
                metric["export_lines"],
        })


    except Exception as e:

        results.append({

            "period": period,

            "source_title":
                row["source_title"],

            "source_date":
                row["source_date"],

            "source_url":
                url,

            "content_status":
                "ERROR",

            "error":
                str(e)
        })

    # 산업부 서버에 과도한 요청 방지
    time.sleep(0.5)


# ------------------------------------------------------------
# [8단계] 결과 CSV 저장
# ------------------------------------------------------------

result_df = pd.DataFrame(
    results
)

result_df.to_csv(
    OUT,
    index=False,
    encoding="utf-8-sig"
)


# ------------------------------------------------------------
# [9단계] 터미널에는 핵심 결과만 출력
#
# 긴 본문은 출력하지 않습니다.
# 터미널이 멈춘 것처럼 보이는 문제를 방지합니다.
# ------------------------------------------------------------

print()
print("=" * 100)
print("RESULT")
print("=" * 100)

summary_cols = [
    "period",
    "period_match",
    "production_found",
    "domestic_found",
    "export_found",
    "content_status"
]

for c in summary_cols:
    if c not in result_df.columns:
        result_df[c] = ""

print(
    result_df[
        summary_cols
    ].to_string(
        index=False
    )
)

print()

print(
    result_df[
        "content_status"
    ].value_counts(
        dropna=False
    ).to_string()
)

print()
print(
    "TEXT   :",
    TEXT_DIR
)

print(
    "OUTPUT :",
    OUT
)

print()
print(
    "※ CONTENT_READY는 아직 BODY_VERIFIED가 아닙니다."
)

print(
    "※ MASTER 변경 없음"
)
