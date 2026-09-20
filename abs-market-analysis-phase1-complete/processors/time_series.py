from __future__ import annotations
import pandas as pd


def normalize_period(series: pd.Series) -> pd.Series:
    """다양한 날짜 표현을 월 단위 Period[M]으로 표준화한다."""
    parsed = pd.to_datetime(series, errors="coerce")
    return parsed.dt.to_period("M")


def add_time_fields(df: pd.DataFrame, period_col: str = "period") -> pd.DataFrame:
    out = df.copy()
    p = normalize_period(out[period_col].astype(str))
    out["period_m"] = p
    out["year"] = p.dt.year.astype("Int64")
    out["quarter"] = p.dt.quarter.astype("Int64")
    out["year_quarter"] = p.astype(str).where(p.isna(), p.dt.year.astype(str) + "-Q" + p.dt.quarter.astype(str))
    return out


def aggregate_timeseries(
    df: pd.DataFrame,
    value_col: str,
    frequency: str = "월",
    filters: dict | None = None,
) -> pd.DataFrame:
    """기간·모델·고객사 등 공통 필터 적용 후 시계열 집계."""
    if df.empty or value_col not in df.columns:
        return pd.DataFrame(columns=["period_label", value_col])

    x = add_time_fields(df)
    filters = filters or {}
    for col, selected in filters.items():
        if col not in x.columns or selected is None:
            continue
        if isinstance(selected, (list, tuple, set)):
            selected = list(selected)
            if selected:
                x = x[x[col].isin(selected)]
        else:
            x = x[x[col].eq(selected)]

    # 결측값은 0으로 치환하지 않음. min_count=1로 전부 결측이면 결과도 NaN 유지.
    if frequency == "연":
        grouped = x.groupby("year", dropna=False)[value_col].sum(min_count=1).reset_index()
        grouped["period_label"] = grouped["year"].astype("Int64").astype(str)
    elif frequency == "분기":
        grouped = x.groupby(["year", "quarter"], dropna=False)[value_col].sum(min_count=1).reset_index()
        grouped["period_label"] = grouped["year"].astype("Int64").astype(str) + " Q" + grouped["quarter"].astype("Int64").astype(str)
    else:
        grouped = x.groupby("period_m", dropna=False)[value_col].sum(min_count=1).reset_index()
        grouped["period_label"] = grouped["period_m"].astype(str)

    return grouped[["period_label", value_col]]


def common_period_end(*frames: pd.DataFrame, period_col: str = "period"):
    """비교 데이터셋 간 공통 최신월을 반환한다."""
    ends = []
    for df in frames:
        if df is None or df.empty or period_col not in df.columns:
            return None
        p = normalize_period(df[period_col].astype(str)).dropna()
        if p.empty:
            return None
        ends.append(p.max())
    return min(ends) if ends else None
