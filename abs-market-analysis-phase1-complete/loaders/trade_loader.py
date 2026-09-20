"""관세청 수출입무역통계 RAW XML 로더.

RAW XML은 수정하지 않고 그대로 보존한다.
분석용 데이터에서는 API가 반환하는 '총계' 행을 제외하여
세부 HS 코드와 총계가 중복 집계되지 않도록 한다.
"""

from __future__ import annotations

import csv
import xml.etree.ElementTree as ET
from pathlib import Path

import pandas as pd

from config.schemas import STATUS, TRADE_PROCESSED_COLUMNS
from config.settings import PATH_CONFIG


def _to_nullable_int(value: str | None):
    """숫자 결측을 0으로 바꾸지 않고 NA로 유지한다."""
    if value is None:
        return pd.NA

    value = value.strip()

    if value in {"", "-"}:
        return pd.NA

    try:
        return int(value)
    except ValueError:
        return pd.NA


def _find_source_metadata(raw_file_path: Path) -> dict:
    """source_log.csv에서 RAW 파일의 수집 메타데이터를 찾는다."""
    log_path = PATH_CONFIG["metadata"] / "source_log.csv"

    if not log_path.exists():
        raise FileNotFoundError(
            f"source_log.csv를 찾을 수 없습니다: {log_path}"
        )

    target = raw_file_path.resolve()

    with log_path.open(
        "r",
        encoding="utf-8-sig",
        newline="",
    ) as f:
        reader = csv.DictReader(f)

        for row in reader:
            logged_path = Path(row["raw_file_path"])

            try:
                if logged_path.resolve() == target:
                    return row
            except OSError:
                continue

    raise ValueError(
        "해당 RAW 파일의 source_log 기록을 찾을 수 없습니다: "
        f"{raw_file_path}"
    )


def load_trade_raw(
    raw_file_path: str | Path,
) -> pd.DataFrame:
    raw_file_path = Path(raw_file_path)

    tree = ET.parse(raw_file_path)
    root = tree.getroot()

    result_code = root.findtext("./header/resultCode")
    result_msg = root.findtext("./header/resultMsg")

    if result_code != "00":
        raise RuntimeError(
            f"관세청 API 오류: {result_code} / {result_msg}"
        )

    metadata = _find_source_metadata(raw_file_path)

    rows = []

    for item in root.findall("./body/items/item"):
        period_raw = item.findtext("year")
        hs_code = item.findtext("hsCd")

        # API가 함께 반환하는 총계 행은 제외한다.
        if period_raw == "총계":
            continue

        if hs_code in {None, "", "-"}:
            continue

        period = (
            period_raw.replace(".", "-")
            if period_raw
            else pd.NA
        )

        rows.append(
            {
                "period": period,
                "hs_code": hs_code,
                "item_name": item.findtext("statKor"),
                "country_code": item.findtext("statCd"),
                "country_name": item.findtext("statCdCntnKor1"),
                "export_usd": _to_nullable_int(
                    item.findtext("expDlr")
                ),
                "export_kg": _to_nullable_int(
                    item.findtext("expWgt")
                ),
                "import_usd": _to_nullable_int(
                    item.findtext("impDlr")
                ),
                "import_kg": _to_nullable_int(
                    item.findtext("impWgt")
                ),
                "trade_balance_usd": _to_nullable_int(
                    item.findtext("balPayments")
                ),
                "source_id": metadata["source_id"],
                "source_key": metadata["source_key"],
                "basis_date": metadata["basis_date"],
                "collected_at": metadata["collected_at"],
                "estimate_flag": STATUS["actual"],

                # 평가 규칙이 확정되기 전까지 임의 값 입력 금지
                "confidence_grade": pd.NA,
                "model_version": pd.NA,
            }
        )

    df = pd.DataFrame(
        rows,
        columns=TRADE_PROCESSED_COLUMNS,
    )

    numeric_columns = [
        "export_usd",
        "export_kg",
        "import_usd",
        "import_kg",
        "trade_balance_usd",
    ]

    for column in numeric_columns:
        if column in df.columns:
            df[column] = df[column].astype("Int64")

    return df
def save_trade_processed(
    df: pd.DataFrame,
    raw_file_path: str | Path,
) -> Path:
    """표준화된 관세청 데이터를 processed 영역에 저장한다."""
    raw_file_path = Path(raw_file_path)

    processed_dir = PATH_CONFIG["processed"]
    processed_dir.mkdir(parents=True, exist_ok=True)

    output_name = f"{raw_file_path.stem}_processed.csv"
    output_path = processed_dir / output_name

    df.to_csv(
        output_path,
        index=False,
        encoding="utf-8-sig",
    )

    return output_path