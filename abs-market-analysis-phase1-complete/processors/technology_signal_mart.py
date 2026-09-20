from pathlib import Path

import pandas as pd


BASE_DIR = Path(__file__).resolve().parents[1]

SOURCE_PATH = (
    BASE_DIR
    / "data"
    / "metadata"
    / "technology_signal_master.csv"
)

OUTPUT_PATH = (
    BASE_DIR
    / "data"
    / "mart"
    / "technology_signal.parquet"
)


COLUMNS = [
    "signal_id",
    "signal_date",
    "technology_id",
    "signal_type",
    "company",
    "event",
    "vehicle_volume",
    "forecast_year",
    "forecast_value",
    "unit",
    "region",
    "source_id",
    "confidence_grade",
    "verification_status",
    "notes",
]


def build_technology_signal_mart() -> pd.DataFrame:
    if not SOURCE_PATH.exists():
        return pd.DataFrame(columns=COLUMNS)

    df = pd.read_csv(
        SOURCE_PATH,
        dtype="string",
    )

    for column in COLUMNS:
        if column not in df.columns:
            df[column] = pd.NA

    df = df[COLUMNS].copy()

    df["forecast_value"] = pd.to_numeric(
        df["forecast_value"],
        errors="coerce",
    )

    df["forecast_year"] = pd.to_numeric(
        df["forecast_year"],
        errors="coerce",
    ).astype("Int64")

    # signal_date가 YYYY 형식이어도 정렬 가능하도록 보조 연도 생성
    df["signal_year"] = pd.to_numeric(
        df["signal_date"].str[:4],
        errors="coerce",
    ).astype("Int64")

    df = df.sort_values(
        ["signal_year", "company", "signal_type"],
        ascending=[False, True, True],
        kind="stable",
    ).reset_index(drop=True)

    return df


def save_technology_signal_mart() -> dict:
    df = build_technology_signal_mart()

    OUTPUT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    df.to_parquet(
        OUTPUT_PATH,
        index=False,
    )

    return {
        "output_file": str(OUTPUT_PATH),
        "row_count": len(df),
        "verified_count": int(
            (df["verification_status"] == "VERIFIED").sum()
        ),
        "forecast_count": int(
            (df["signal_type"] == "FORECAST").sum()
        ),
    }


if __name__ == "__main__":
    result = save_technology_signal_mart()

    print("Technology signal mart build completed")
    print("OUTPUT_FILE:", result["output_file"])
    print("ROW_COUNT:", result["row_count"])
    print("VERIFIED:", result["verified_count"])
    print("FORECAST:", result["forecast_count"])
