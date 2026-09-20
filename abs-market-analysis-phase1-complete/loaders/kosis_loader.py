import json
from pathlib import Path

import pandas as pd

from config.settings import PATH_CONFIG


PROCESSED_COLUMNS = [
    "source_id",
    "source_key",
    "org_id",
    "table_id",
    "table_name",
    "period_type",
    "period",
    "year",
    "country_code",
    "country_name",
    "country_name_en",
    "item_code",
    "item_name",
    "item_name_en",
    "vehicle_category",
    "production_qty",
    "unit",
    "last_changed_date",
    "estimate_flag",
    "raw_file_path",
]


ITEM_CATEGORY_MAP = {
    "T10": "TOTAL",
    "T11": "PASSENGER",
    "T12": "COMMERCIAL",
}


def _to_nullable_int(value):
    if value is None:
        return pd.NA

    text = str(value).strip()

    if text == "":
        return pd.NA

    try:
        return int(text)
    except ValueError:
        return pd.NA


def load_vehicle_production_raw(raw_file: str | Path) -> pd.DataFrame:
    raw_path = Path(raw_file)

    if not raw_path.exists():
        raise FileNotFoundError(f"RAW file not found: {raw_path}")

    with raw_path.open("r", encoding="utf-8") as f:
        snapshot = json.load(f)

    source_id = snapshot.get("source_id")
    org_id = snapshot.get("org_id")
    table_id = snapshot.get("table_id")
    table_name = snapshot.get("table_name")

    records = []

    for request_block in snapshot.get("requests", []):
        for row in request_block.get("response", []):
            item_code = row.get("ITM_ID")

            records.append(
                {
                    "source_id": source_id,
                    "source_key": "kosis",
                    "org_id": row.get("ORG_ID", org_id),
                    "table_id": row.get("TBL_ID", table_id),
                    "table_name": row.get("TBL_NM", table_name),
                    "period_type": row.get("PRD_SE"),
                    "period": row.get("PRD_DE"),
                    "year": _to_nullable_int(row.get("PRD_DE")),
                    "country_code": row.get("C1"),
                    "country_name": row.get("C1_NM"),
                    "country_name_en": row.get("C1_NM_ENG"),
                    "item_code": item_code,
                    "item_name": row.get("ITM_NM"),
                    "item_name_en": row.get("ITM_NM_ENG"),
                    "vehicle_category": ITEM_CATEGORY_MAP.get(
                        item_code,
                        "UNKNOWN",
                    ),
                    "production_qty": _to_nullable_int(row.get("DT")),
                    "unit": row.get("UNIT_NM"),
                    "last_changed_date": row.get("LST_CHN_DE"),
                    "estimate_flag": "ACTUAL",
                    "raw_file_path": str(raw_path),
                }
            )

    df = pd.DataFrame(records)

    if df.empty:
        return pd.DataFrame(columns=PROCESSED_COLUMNS)

    for column in PROCESSED_COLUMNS:
        if column not in df.columns:
            df[column] = pd.NA

    df = df[PROCESSED_COLUMNS]

    df["year"] = pd.array(
        df["year"],
        dtype="Int64",
    )

    df["production_qty"] = pd.array(
        df["production_qty"],
        dtype="Int64",
    )

    df = df.sort_values(
        [
            "country_code",
            "item_code",
            "year",
        ],
        kind="stable",
    ).reset_index(drop=True)

    return df


def save_vehicle_production_processed(
    raw_file: str | Path,
) -> dict:
    raw_path = Path(raw_file)

    df = load_vehicle_production_raw(raw_path)

    processed_dir = Path(PATH_CONFIG["processed"])
    processed_dir.mkdir(parents=True, exist_ok=True)

    output_name = (
        raw_path.stem
        + "_processed.csv"
    )

    output_path = processed_dir / output_name

    df.to_csv(
        output_path,
        index=False,
        encoding="utf-8-sig",
    )

    return {
        "processed_file": str(output_path),
        "row_count": len(df),
        "null_production_qty": int(
            df["production_qty"].isna().sum()
        ),
        "year_min": (
            int(df["year"].min())
            if not df.empty
            else None
        ),
        "year_max": (
            int(df["year"].max())
            if not df.empty
            else None
        ),
    }
def load_latest_vehicle_production_processed() -> pd.DataFrame:
    processed_dir = Path(PATH_CONFIG["processed"])

    processed_files = sorted(
        processed_dir.glob(
            "*_KOSIS_DT_2KAA511_vehicle_production_processed.csv"
        )
    )

    if not processed_files:
        raise FileNotFoundError(
            "No processed KOSIS vehicle production file found."
        )

    latest_file = processed_files[-1]

    df = pd.read_csv(
        latest_file,
        dtype={
            "source_id": "string",
            "country_code": "string",
            "item_code": "string",
            "vehicle_category": "string",
        },
    )

    df["year"] = pd.to_numeric(
        df["year"],
        errors="coerce",
    ).astype("Int64")

    df["production_qty"] = pd.to_numeric(
        df["production_qty"],
        errors="coerce",
    ).astype("Int64")

    return df


def get_vehicle_production(
    year: int,
    country_code: str,
    vehicle_category: str = "TOTAL",
) -> dict:
    df = load_latest_vehicle_production_processed()

    matched = df[
        (df["year"] == year)
        & (df["country_code"] == str(country_code))
        & (df["vehicle_category"] == vehicle_category)
    ]

    if matched.empty:
        return {
            "value": None,
            "unit": "EA",
            "estimate_flag": "MISSING",
            "source_id": None,
            "year": year,
            "country_code": str(country_code),
            "vehicle_category": vehicle_category,
        }

    if len(matched) > 1:
        raise RuntimeError(
            "Duplicate KOSIS vehicle production rows found."
        )

    row = matched.iloc[0]

    production_qty = row["production_qty"]

    return {
        "value": (
            int(production_qty)
            if not pd.isna(production_qty)
            else None
        ),
        "unit": row.get("unit", "EA"),
        "estimate_flag": row.get(
            "estimate_flag",
            "ACTUAL",
        ),
        "source_id": row.get("source_id"),
        "year": year,
        "country_code": str(country_code),
        "vehicle_category": vehicle_category,
    }

if __name__ == "__main__":
    raw_dir = Path(PATH_CONFIG["raw"]) / "kosis"

    raw_files = sorted(
        raw_dir.glob(
            "*_KOSIS_DT_2KAA511_vehicle_production.json"
        )
    )

    if not raw_files:
        raise FileNotFoundError(
            "No KOSIS vehicle production RAW file found."
        )

    latest_raw = raw_files[-1]

    result = save_vehicle_production_processed(
        latest_raw
    )

    print("KOSIS vehicle production load completed")
    print("PROCESSED_FILE:", result["processed_file"])
    print("ROW_COUNT:", result["row_count"])
    print(
        "NULL_PRODUCTION_QTY:",
        result["null_production_qty"],
    )
    print(
        "YEAR_RANGE:",
        result["year_min"],
        "-",
        result["year_max"],
    )
