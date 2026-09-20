from pathlib import Path
import pandas as pd


BASE_DIR = Path(__file__).resolve().parents[1]
MARKET_MART = BASE_DIR / "data" / "mart" / "market_monthly.parquet"


def load_vehicle_timeseries(
    scope: str = "GLOBAL",
    metric: str = "VEHICLE_PRODUCTION_TOTAL",
) -> pd.DataFrame:
    """시장 mart에서 자동차 생산 시계열을 불러온다."""

    df = pd.read_parquet(MARKET_MART)

    ts = df[
        (df["market_scope"] == scope)
        & (df["metric"] == metric)
    ].copy()

    if ts.empty:
        return pd.DataFrame()

    ts["date"] = pd.to_datetime(
        ts["period"],
        format="%Y-%m",
        errors="coerce",
    )

    ts["value"] = pd.to_numeric(
        ts["value"],
        errors="coerce",
    )

    ts = (
        ts.dropna(subset=["date", "value"])
        .sort_values("date")
        .reset_index(drop=True)
    )

    ts["year"] = ts["date"].dt.year

    return ts


def add_timeseries_features(
    df: pd.DataFrame,
    moving_window: int = 3,
) -> pd.DataFrame:
    """YoY, 이동평균, 이동표준편차 등 분석 변수를 추가한다."""

    if df.empty:
        return df.copy()

    result = df.copy()

    result["yoy_pct"] = (
        result["value"].pct_change(fill_method=None) * 100
    )

    result[f"ma_{moving_window}y"] = (
        result["value"]
        .rolling(
            window=moving_window,
            min_periods=1,
        )
        .mean()
    )

    result[f"std_{moving_window}y"] = (
        result["value"]
        .rolling(
            window=moving_window,
            min_periods=2,
        )
        .std()
    )

    result["change_abs"] = result["value"].diff()

    return result


def calculate_cagr(df: pd.DataFrame):
    """선택 구간의 CAGR을 계산한다."""

    if df.empty or len(df) < 2:
        return None

    first = float(df.iloc[0]["value"])
    last = float(df.iloc[-1]["value"])

    years = int(
        df.iloc[-1]["year"]
        - df.iloc[0]["year"]
    )

    if first <= 0 or years <= 0:
        return None

    return (
        (last / first) ** (1 / years) - 1
    ) * 100


def summarize_timeseries(df: pd.DataFrame) -> dict:
    """시계열의 핵심 지표와 변곡점을 요약한다."""

    if df.empty:
        return {}

    analyzed = add_timeseries_features(df)

    valid_yoy = analyzed.dropna(
        subset=["yoy_pct"]
    )

    max_growth = None
    max_decline = None

    if not valid_yoy.empty:
        growth_row = valid_yoy.loc[
            valid_yoy["yoy_pct"].idxmax()
        ]

        decline_row = valid_yoy.loc[
            valid_yoy["yoy_pct"].idxmin()
        ]

        max_growth = {
            "year": int(growth_row["year"]),
            "yoy_pct": float(growth_row["yoy_pct"]),
        }

        max_decline = {
            "year": int(decline_row["year"]),
            "yoy_pct": float(decline_row["yoy_pct"]),
        }

    return {
        "start_year": int(analyzed.iloc[0]["year"]),
        "end_year": int(analyzed.iloc[-1]["year"]),
        "start_value": float(analyzed.iloc[0]["value"]),
        "end_value": float(analyzed.iloc[-1]["value"]),
        "cagr_pct": calculate_cagr(analyzed),
        "period_change_pct": (
            (
                analyzed.iloc[-1]["value"]
                / analyzed.iloc[0]["value"]
            )
            - 1
        )
        * 100,
        "mean_yoy_pct": (
            float(valid_yoy["yoy_pct"].mean())
            if not valid_yoy.empty
            else None
        ),
        "yoy_volatility": (
            float(valid_yoy["yoy_pct"].std())
            if len(valid_yoy) > 1
            else None
        ),
        "max_growth": max_growth,
        "max_decline": max_decline,
    }


def compare_recent_vs_longterm(
    df: pd.DataFrame,
    recent_years: int = 5,
) -> dict:
    """전체기간과 최근기간 CAGR을 비교한다."""

    if df.empty:
        return {}

    full = df.sort_values("year").copy()

    recent_start = (
        int(full["year"].max())
        - recent_years
    )

    recent = full[
        full["year"] >= recent_start
    ].copy()

    return {
        "longterm_cagr_pct": calculate_cagr(full),
        "recent_cagr_pct": calculate_cagr(recent),
        "recent_start_year": (
            int(recent.iloc[0]["year"])
            if not recent.empty
            else None
        ),
        "recent_end_year": (
            int(recent.iloc[-1]["year"])
            if not recent.empty
            else None
        ),
    }


def analyze_market(scope: str) -> dict:
    ts = load_vehicle_timeseries(scope=scope)

    return {
        "data": add_timeseries_features(ts),
        "summary": summarize_timeseries(ts),
        "trend_compare": compare_recent_vs_longterm(ts),
    }


if __name__ == "__main__":

    for scope in ["GLOBAL", "KOREA"]:

        result = analyze_market(scope)

        print()
        print("=" * 60)
        print(scope)
        print("=" * 60)

        print("SUMMARY")
        print(result["summary"])

        print()
        print("RECENT VS LONG TERM")
        print(result["trend_compare"])

        print()
        print("TIME SERIES")
        print(
            result["data"][
                [
                    "year",
                    "value",
                    "yoy_pct",
                    "ma_3y",
                    "std_3y",
                ]
            ].to_string(index=False)
        )
