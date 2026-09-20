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
    / "motie_pdf_metrics_v3.csv"
)


def clean_text(text: str) -> str:
    text = text.replace("\xa0", " ")
    text = text.replace("\u200b", "")
    text = text.replace("△", "-")
    text = re.sub(r"[ \t]+", " ", text)
    return text


def to_number(value: str):
    if not value:
        return None

    try:
        return int(value.replace(",", "").strip())
    except Exception:
        return None


NUM = r"(\d{1,3}(?:,\d{3})+)"


def search_first(text: str, patterns):
    for source, pattern in patterns:
        m = re.search(
            pattern,
            text,
            flags=re.MULTILINE | re.DOTALL,
        )

        if m:
            value = to_number(m.group(1))

            if value is not None:
                return value, source

    return None, "NOT_FOUND"


def extract_industry_table(text: str):
    """
    자동차산업 실적 표를 가장 먼저 사용한다.

    예:
    생  산(대) 307,048 ...
    내  수(대) 145,464 ...
    수  출(대) 182,869 ...

    또는:
    생산(대) ... 306,738 ...
    내수(대) ... 116,565 ...
    수출(대) ... 200,825 ...

    표 구조에 따라 첫 번째 숫자가 과거값일 수 있으므로
    단순 첫 숫자 선택은 하지 않는다.
    """

    table_match = re.search(
        r"자동차\s*산업\s*실적"
        r"([\s\S]{0,1200})",
        text,
        flags=re.IGNORECASE,
    )

    if not table_match:
        return {}

    block = table_match.group(1)

    result = {}

    for key, label in [
        ("production", r"생\s*산"),
        ("domestic", r"내\s*수"),
        ("export", r"수\s*출"),
    ]:
        line_match = re.search(
            rf"^{label}\s*\(대\)\s*(.+)$",
            block,
            flags=re.MULTILINE,
        )

        if not line_match:
            continue

        line = line_match.group(1)

        values = re.findall(
            r"\d{1,3}(?:,\d{3})+",
            line,
        )

        # 월간 표에서 값이 하나뿐이면 바로 사용
        if len(values) == 1:
            result[key] = (
                to_number(values[0]),
                "industry_table",
            )

        # 값이 여러 개면 현재월 위치를 자동판정하기 어렵기 때문에
        # 여기서는 확정하지 않고 문장/참고표 검증 단계로 넘긴다.

    return result


def extract_production(text: str):

    patterns = [
        (
            "production_total_sentence",
            rf"(?:생산|생산량)"
            rf"[\s\S]{{0,180}}?"
            rf"(?:증가|감소|기록|생산)"
            rf"[\s\S]{{0,80}}?"
            rf"{NUM}\s*대"
        ),
        (
            "production_reference",
            rf"참고\s*1[\s\S]{{0,600}}?"
            rf"(?:총괄|종합)"
            rf"[\s\S]{{0,300}}?"
            rf"{NUM}\s*대\s*생산"
        ),
        (
            "production_sentence",
            rf"(?:증가한|감소한)\s*{NUM}\s*대"
            rf"[\s\S]{{0,30}}?(?:생산|플러스|마이너스)"
        ),
    ]

    return search_first(text, patterns)


def extract_domestic(text: str):

    patterns = [
        (
            "domestic_total_sentence",
            rf"□\s*\(내수\s*\)"
            rf"(?![\s\S]{{0,40}}친환경)"
            rf"[\s\S]{{0,220}}?"
            rf"{NUM}\s*대"
        ),
        (
            "domestic_reference",
            rf"참고\s*2[\s\S]{{0,700}}?"
            rf"(?:총괄|종합)"
            rf"[\s\S]{{0,300}}?"
            rf"{NUM}\s*대"
        ),
    ]

    return search_first(text, patterns)


def extract_export(text: str):

    patterns = [
        (
            "export_total_sentence",
            rf"□\s*\(수출\s*\)"
            rf"(?![\s\S]{{0,40}}친환경)"
            rf"[\s\S]{{0,220}}?"
            rf"{NUM}\s*대"
        ),
        (
            "export_reference",
            rf"참고\s*3[\s\S]{{0,700}}?"
            rf"(?:총괄|종합)"
            rf"[\s\S]{{0,350}}?"
            rf"{NUM}\s*대\s*수출"
        ),
    ]

    return search_first(text, patterns)


def plausible(value, metric):
    if value is None:
        return False

    ranges = {
        "production": (100_000, 600_000),
        "domestic": (50_000, 300_000),
        "export": (70_000, 400_000),
    }

    lo, hi = ranges[metric]

    return lo <= value <= hi


def extract_metrics(text: str):

    text = clean_text(text)

    table = extract_industry_table(text)

    results = {}

    extractors = {
        "production": extract_production,
        "domestic": extract_domestic,
        "export": extract_export,
    }

    for metric, extractor in extractors.items():

        if metric in table:
            value, source = table[metric]
        else:
            value, source = extractor(text)

        if value is None:
            status = "NOT_FOUND"

        elif plausible(value, metric):
            status = "OK"

        else:
            status = "REVIEW_RANGE"

        results[metric] = value
        results[f"{metric}_source"] = source
        results[f"{metric}_status"] = status

    return results


def main():

    rows = []

    files = sorted(TEXT_DIR.glob("*.txt"))

    print("=" * 90)
    print("MOTIE PDF METRIC EXTRACTOR V3")
    print("=" * 90)

    for path in files:

        period = path.stem

        text = path.read_text(
            encoding="utf-8",
            errors="replace",
        )

        text_chars = len(
            re.sub(r"\s+", "", text)
        )

        metrics = extract_metrics(text)

        row = {
            "period": period,
            "text_chars": text_chars,
            "usable_text": text_chars > 100,
            **metrics,
        }

        rows.append(row)

        print(
            f"{period} "
            f"P={metrics['production']} "
            f"D={metrics['domestic']} "
            f"E={metrics['export']} | "
            f"{metrics['production_status']} "
            f"{metrics['domestic_status']} "
            f"{metrics['export_status']}"
        )

    df = pd.DataFrame(rows)

    df.to_csv(
        OUTPUT_FILE,
        index=False,
        encoding="utf-8-sig",
    )

    all_three = (
        df["production"].notna()
        & df["domestic"].notna()
        & df["export"].notna()
    ).sum()

    print()
    print("=" * 90)
    print("RESULT")
    print("=" * 90)

    print("FILES   :", len(df))
    print("P FOUND :", df["production"].notna().sum())
    print("D FOUND :", df["domestic"].notna().sum())
    print("E FOUND :", df["export"].notna().sum())
    print("ALL 3   :", all_three)
    print("OUTPUT  :", OUTPUT_FILE)


if __name__ == "__main__":
    main()
