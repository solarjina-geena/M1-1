from __future__ import annotations

import re
from pathlib import Path

import pandas as pd


BASE_DIR = Path(__file__).resolve().parents[1]

TEXT_DIR = (
    BASE_DIR
    / "data"
    / "raw"
    / "motie"
    / "monthly_pdf"
    / "text"
)

OUTPUT_FILE = (
    BASE_DIR
    / "data"
    / "raw"
    / "motie"
    / "motie_pdf_metrics_v2.csv"
)


def clean_text(text: str) -> str:
    text = text.replace("\xa0", " ")
    text = text.replace("\u200b", "")
    text = text.replace("△", "-")
    text = text.replace("’", "'")
    text = text.replace("‘", "'")

    text = re.sub(r"[ \t]+", " ", text)

    return text


def number(value: str) -> int:
    return int(value.replace(",", ""))


def valid_vehicle_count(value: int | None) -> bool:
    """
    월간 국내 자동차 전체 실적에 대한 기본 안전 범위.
    너무 작은 친환경차/업체별 수치나
    누계값이 들어오는 것을 1차 방어한다.
    """
    if value is None:
        return False

    return 50_000 <= value <= 800_000


def collect_candidates(
    text: str,
    patterns: list[tuple[str, str]],
) -> list[dict]:

    candidates = []

    for priority, (source, pattern) in enumerate(
        patterns,
        start=1,
    ):
        for match in re.finditer(
            pattern,
            text,
            flags=re.MULTILINE | re.IGNORECASE,
        ):
            try:
                value = number(match.group(1))
            except Exception:
                continue

            candidates.append(
                {
                    "value": value,
                    "source": source,
                    "priority": priority,
                    "valid_range": valid_vehicle_count(value),
                }
            )

    return candidates


def choose_candidate(
    candidates: list[dict],
) -> tuple[int | None, str, str]:

    if not candidates:
        return None, "", "NOT_FOUND"

    valid = [
        c
        for c in candidates
        if c["valid_range"]
    ]

    pool = valid if valid else candidates

    pool = sorted(
        pool,
        key=lambda x: x["priority"],
    )

    selected = pool[0]

    same_value_count = sum(
        1
        for c in candidates
        if c["value"] == selected["value"]
    )

    if same_value_count >= 2:
        status = "VERIFIED_MULTI"
    elif selected["valid_range"]:
        status = "FOUND_SINGLE"
    else:
        status = "REVIEW_RANGE"

    return (
        selected["value"],
        selected["source"],
        status,
    )


def extract_metrics(text: str) -> dict:

    text = clean_text(text)

    # ---------------------------------------------------------
    # 생산
    # ---------------------------------------------------------

    production_patterns = [

        (
            "production_quantity_table",
            r"생산량\s+(\d{1,3}(?:,\d{3})+)",
        ),

        (
            "production_summary",
            r"\(생산\)[\s\S]{0,250}?"
            r"(?:감소|증가)[\s\S]{0,80}?"
            r"(\d{1,3}(?:,\d{3})+)\s*대"
            r"(?:\s*생산)?",
        ),

        (
            "production_sentence",
            r"(\d{1,3}(?:,\d{3})+)\s*대\s*생산",
        ),

        (
            "production_table",
            r"생\s*산\s+(\d{1,3}(?:,\d{3})+)",
        ),
    ]

    # ---------------------------------------------------------
    # 내수
    # ---------------------------------------------------------

    domestic_patterns = [

        (
            "domestic_quantity_table",
            r"내수\s*판매량\s+"
            r"(\d{1,3}(?:,\d{3})+)",
        ),

        (
            "domestic_summary",
            r"\(내수\)[\s\S]{0,250}?"
            r"(?:감소|증가)[\s\S]{0,100}?"
            r"(\d{1,3}(?:,\d{3})+)\s*대"
            r"(?:\s*판매)?",
        ),

        (
            "domestic_table",
            r"내\s*수(?:\s*판매)?\s+"
            r"(\d{1,3}(?:,\d{3})+)",
        ),
    ]

    # ---------------------------------------------------------
    # 수출
    # ---------------------------------------------------------

    export_patterns = [

        (
            "export_quantity_table",
            r"수출량\s+"
            r"(\d{1,3}(?:,\d{3})+)",
        ),

        (
            "export_summary",
            r"\(수출\)[\s\S]{0,300}?"
            r"(?:감소|증가)[\s\S]{0,120}?"
            r"(\d{1,3}(?:,\d{3})+)\s*대",
        ),

        (
            "export_total_table",
            r"업체별\s*수출\s*현황"
            r"[\s\S]{0,600}?"
            r"합\s*계\s+"
            r"(\d{1,3}(?:,\d{3})+)",
        ),

        (
            "export_sentence",
            r"(\d{1,3}(?:,\d{3})+)\s*대\s*"
            r"(?:수출|판매)",
        ),
    ]

    production_candidates = collect_candidates(
        text,
        production_patterns,
    )

    domestic_candidates = collect_candidates(
        text,
        domestic_patterns,
    )

    export_candidates = collect_candidates(
        text,
        export_patterns,
    )

    production, production_source, production_status = (
        choose_candidate(production_candidates)
    )

    domestic, domestic_source, domestic_status = (
        choose_candidate(domestic_candidates)
    )

    export, export_source, export_status = (
        choose_candidate(export_candidates)
    )

    return {
        "production": production,
        "domestic": domestic,
        "export": export,

        "production_source": production_source,
        "domestic_source": domestic_source,
        "export_source": export_source,

        "production_status": production_status,
        "domestic_status": domestic_status,
        "export_status": export_status,
    }


def main():

    rows = []

    files = sorted(TEXT_DIR.glob("*.txt"))

    print("=" * 90)
    print("MOTIE PDF METRIC EXTRACTOR V2")
    print("=" * 90)

    for path in files:

        period = path.stem

        text = path.read_text(
            encoding="utf-8",
            errors="replace",
        )

        metrics = extract_metrics(text)

        text_chars = len(
            re.sub(r"\s+", "", text)
        )

        usable = text_chars > 100

        row = {
            "period": period,
            "text_chars": text_chars,
            "usable_text": usable,
            **metrics,
        }

        rows.append(row)

        print(
            period,
            f"P={metrics['production']}",
            f"D={metrics['domestic']}",
            f"E={metrics['export']}",
            "|",
            metrics["production_status"],
            metrics["domestic_status"],
            metrics["export_status"],
        )

    df = pd.DataFrame(rows)

    df.to_csv(
        OUTPUT_FILE,
        index=False,
        encoding="utf-8-sig",
    )

    all_three = (
        df[
            [
                "production",
                "domestic",
                "export",
            ]
        ]
        .notna()
        .all(axis=1)
        .sum()
    )

    print()
    print("=" * 90)
    print("RESULT")
    print("=" * 90)

    print("FILES       :", len(df))
    print(
        "P FOUND     :",
        int(df["production"].notna().sum()),
    )
    print(
        "D FOUND     :",
        int(df["domestic"].notna().sum()),
    )
    print(
        "E FOUND     :",
        int(df["export"].notna().sum()),
    )
    print(
        "ALL 3       :",
        int(all_three),
    )
    print("OUTPUT      :", OUTPUT_FILE)


if __name__ == "__main__":
    main()