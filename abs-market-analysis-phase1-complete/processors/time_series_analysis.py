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
        .drop_duplicates(subset=["date"], keep="last")
        .reset_index(drop=True)
    )

    ts["year"] = ts["date"].dt.year
    ts["month"] = ts["date"].dt.month
    ts["period_label"] = ts["date"].dt.strftime("%Y-%m")

    return ts


def detect_frequency(df: pd.DataFrame) -> str:
    """
    실제 데이터의 시간 주기를 판별한다.

    같은 연도에 2개 이상의 월 데이터가 있으면 MONTHLY,
    연도별 1개 데이터만 있으면 ANNUAL로 판단한다.
    """

    if df.empty:
        return "UNKNOWN"

    temp = df.copy()

    if "date" not in temp.columns:
        return "UNKNOWN"

    counts = (
        temp.groupby(temp["date"].dt.year)
        ["date"]
        .count()
    )

    if not counts.empty and counts.max() >= 2:
        return "MONTHLY"

    return "ANNUAL"


def add_timeseries_features(
    df: pd.DataFrame,
) -> pd.DataFrame:
    """
    데이터 주기에 맞는 시계열 분석 변수를 추가한다.

    ANNUAL:
        YoY
        3년 이동평균
        3년 이동표준편차

    MONTHLY:
        MoM
        YoY
        3개월 이동평균
        12개월 이동평균
        12개월 이동표준편차
    """

    if df.empty:
        return df.copy()

    result = (
        df.sort_values("date")
        .reset_index(drop=True)
        .copy()
    )

    frequency = detect_frequency(result)
    result["frequency"] = frequency

    result["change_abs"] = result["value"].diff()

    if frequency == "MONTHLY":
        # ====================================================
        # [월별 시계열 분석]
        # ====================================================
        # 중요:
        # 데이터가 없는 월을 앞/뒤 월 값으로 채우지 않습니다.
        #
        # 예:
        # 2025-10 다음 데이터가 2026-01이라면
        # 2026-01의 전월은 2025-12이므로
        # 2025-10과 비교하여 MoM을 만들지 않습니다.
        #
        # 계산 기준
        # - MoM    : 실제 1개월 전과 비교
        # - YoY    : 실제 12개월 전과 비교
        # - MA3    : 달력 기준 최근 3개월
        # - MA12   : 달력 기준 최근 12개월
        # - STD12  : 달력 기준 최근 12개월 변동성
        # ====================================================

        # ----------------------------------------------------
        # [1] 월을 실제 날짜 인덱스로 변환
        # ----------------------------------------------------
        monthly = (
            result[["period_dt", "value"]]
            .drop_duplicates(subset=["period_dt"], keep="last")
            .set_index("period_dt")
            .sort_index()
        )

        # ----------------------------------------------------
        # [2] 빠진 달을 포함한 월별 달력 생성
        # ----------------------------------------------------
        # 없는 달은 NaN으로 남겨둡니다.
        # 값을 추정하거나 보간하지 않습니다.
        # ----------------------------------------------------
        full_month_index = pd.date_range(
            start=monthly.index.min(),
            end=monthly.index.max(),
            freq="MS",
        )

        monthly = monthly.reindex(full_month_index)

        # ----------------------------------------------------
        # [3] 전월 대비 변화율 (MoM)
        # ----------------------------------------------------
        # 바로 전 달 값이 없으면 NaN
        # ----------------------------------------------------
        monthly["mom_pct"] = (
            monthly["value"]
            .pct_change(periods=1, fill_method=None)
            * 100
        )

        # ----------------------------------------------------
        # [4] 전년 동월 대비 변화율 (YoY)
        # ----------------------------------------------------
        # 정확히 12개월 전 값과 비교합니다.
        # 12개월 전 데이터가 없으면 NaN
        # ----------------------------------------------------
        monthly["yoy_pct"] = (
            monthly["value"]
            .pct_change(periods=12, fill_method=None)
            * 100
        )

        # ----------------------------------------------------
        # [5] 3개월 이동평균
        # ----------------------------------------------------
        # 3개월 중 하나라도 데이터가 없으면 계산하지 않습니다.
        # ----------------------------------------------------
        monthly["ma_3m"] = (
            monthly["value"]
            .rolling(
                window=3,
                min_periods=3,
            )
            .mean()
        )

        # ----------------------------------------------------
        # [6] 12개월 이동평균
        # ----------------------------------------------------
        # 완전한 12개월 데이터가 있을 때만 계산합니다.
        # ----------------------------------------------------
        monthly["ma_12m"] = (
            monthly["value"]
            .rolling(
                window=12,
                min_periods=12,
            )
            .mean()
        )

        # ----------------------------------------------------
        # [7] 최근 12개월 변동성
        # ----------------------------------------------------
        # 표준편차가 클수록 월별 움직임이 컸다는 의미입니다.
        # 완전한 12개월 데이터가 있을 때만 계산합니다.
        # ----------------------------------------------------
        monthly["std_12m"] = (
            monthly["value"]
            .rolling(
                window=12,
                min_periods=12,
            )
            .std()
        )

        # ----------------------------------------------------
        # [8] 계산 결과를 원래 데이터에 다시 연결
        # ----------------------------------------------------
        # 달력 생성을 위해 추가했던 결측월 자체를
        # 실제 데이터 행으로 새로 만들지는 않습니다.
        # ----------------------------------------------------
        monthly_features = (
            monthly[
                [
                    "mom_pct",
                    "yoy_pct",
                    "ma_3m",
                    "ma_12m",
                    "std_12m",
                ]
            ]
            .reset_index()
            .rename(columns={"index": "period_dt"})
        )

        result = result.merge(
            monthly_features,
            on="period_dt",
            how="left",
        )
        
    else:

        result["mom_pct"] = pd.NA

        result["yoy_pct"] = (
            result["value"]
            .pct_change(
                periods=1,
                fill_method=None,
            )
            * 100
        )

        result["ma_3y"] = (
            result["value"]
            .rolling(
                window=3,
                min_periods=1,
            )
            .mean()
        )

        result["std_3y"] = (
            result["value"]
            .rolling(
                window=3,
                min_periods=2,
            )
            .std()
        )

    return result


def calculate_cagr(df: pd.DataFrame):
    """실제 날짜 간격을 사용하여 연환산 CAGR을 계산한다."""

    if df.empty or len(df) < 2:
        return None

    data = (
        df.sort_values("date")
        .dropna(subset=["date", "value"])
    )

    if len(data) < 2:
        return None

    first = float(data.iloc[0]["value"])
    last = float(data.iloc[-1]["value"])

    days = (
        data.iloc[-1]["date"]
        - data.iloc[0]["date"]
    ).days

    years = days / 365.2425

    if first <= 0 or last < 0 or years <= 0:
        return None

    return float(
        (
            (last / first) ** (1 / years)
            - 1
        )
        * 100
    )


def calculate_period_change(df: pd.DataFrame):
    """선택 기간 시작 대비 종료 변화율."""

    if df.empty or len(df) < 2:
        return None

    first = float(df.iloc[0]["value"])
    last = float(df.iloc[-1]["value"])

    if first == 0:
        return None

    return float(
        ((last / first) - 1) * 100
    )


def summarize_timeseries(df: pd.DataFrame) -> dict:
    """시계열 핵심 지표와 변곡점을 요약한다."""

    if df.empty:
        return {}

    analyzed = add_timeseries_features(df)
    frequency = detect_frequency(analyzed)

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
            "period": growth_row["period_label"],
            "yoy_pct": float(
                growth_row["yoy_pct"]
            ),
        }

        max_decline = {
            "period": decline_row["period_label"],
            "yoy_pct": float(
                decline_row["yoy_pct"]
            ),
        }

    result = {
        "frequency": frequency,
        "start_period": analyzed.iloc[0]["period_label"],
        "end_period": analyzed.iloc[-1]["period_label"],
        "start_value": float(
            analyzed.iloc[0]["value"]
        ),
        "end_value": float(
            analyzed.iloc[-1]["value"]
        ),
        "cagr_pct": calculate_cagr(analyzed),
        "period_change_pct": calculate_period_change(
            analyzed
        ),
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

    if frequency == "MONTHLY":

        valid_mom = analyzed.dropna(
            subset=["mom_pct"]
        )

        result["mean_mom_pct"] = (
            float(valid_mom["mom_pct"].mean())
            if not valid_mom.empty
            else None
        )

        result["mom_volatility"] = (
            float(valid_mom["mom_pct"].std())
            if len(valid_mom) > 1
            else None
        )

    return result


def compare_recent_vs_longterm(
    df: pd.DataFrame,
    recent_years: int = 5,
) -> dict:
    """전체기간과 최근기간의 연환산 성장률을 비교한다."""

    if df.empty:
        return {}

    full = (
        df.sort_values("date")
        .reset_index(drop=True)
        .copy()
    )

    latest_date = full["date"].max()

    recent_start_date = (
        latest_date
        - pd.DateOffset(years=recent_years)
    )

    recent = full[
        full["date"] >= recent_start_date
    ].copy()

    return {
        "longterm_cagr_pct": calculate_cagr(full),
        "recent_cagr_pct": calculate_cagr(recent),
        "recent_start_period": (
            recent.iloc[0]["period_label"]
            if not recent.empty
            else None
        ),
        "recent_end_period": (
            recent.iloc[-1]["period_label"]
            if not recent.empty
            else None
        ),
    }


def analyze_market(
    scope: str,
    metric: str = "VEHICLE_PRODUCTION_TOTAL",
) -> dict:

    ts = load_vehicle_timeseries(
        scope=scope,
        metric=metric,
    )

    return {
        "frequency": detect_frequency(ts),
        "data": add_timeseries_features(ts),
        "summary": summarize_timeseries(ts),
        "trend_compare": compare_recent_vs_longterm(ts),
    }


if __name__ == "__main__":

    for scope in ["GLOBAL", "KOREA"]:

        result = analyze_market(scope)

        print()
        print("=" * 70)
        print(scope)
        print("=" * 70)

        print("FREQUENCY")
        print(result["frequency"])

        print()
        print("SUMMARY")
        print(result["summary"])

        print()
        print("RECENT VS LONG TERM")
        print(result["trend_compare"])

        print()
        print("TIME SERIES")

        data = result["data"]

        if result["frequency"] == "MONTHLY":

            columns = [
                "period_label",
                "value",
                "mom_pct",
                "yoy_pct",
                "ma_3m",
                "ma_12m",
                "std_12m",
            ]

        else:

            columns = [
                "period_label",
                "value",
                "yoy_pct",
                "ma_3y",
                "std_3y",
            ]

        print(
            data[columns].to_string(
                index=False
            )
        )
