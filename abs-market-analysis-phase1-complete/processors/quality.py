from __future__ import annotations
import pandas as pd

REQUIRED_AUDIT_COLUMNS = [
    "source_id", "source_key", "basis_date", "collected_at",
    "estimate_flag", "confidence_grade", "model_version"
]

def validate_audit_columns(df: pd.DataFrame) -> list[str]:
    return [c for c in REQUIRED_AUDIT_COLUMNS if c not in df.columns]

def detect_duplicates(df: pd.DataFrame, keys: list[str]) -> pd.DataFrame:
    return df[df.duplicated(keys, keep=False)].sort_values(keys)

def detect_spikes(
    df: pd.DataFrame,
    value_col: str,
    group_cols: list[str],
    threshold: float = 0.5,
) -> pd.DataFrame:
    x = df.copy().sort_values(group_cols + ["period"])
    x["pct_change"] = x.groupby(group_cols)[value_col].pct_change()
    return x[x["pct_change"].abs() >= threshold]
