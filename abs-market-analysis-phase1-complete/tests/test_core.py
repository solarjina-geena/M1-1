import pandas as pd
from processors.missing import safe_divide, is_missing
from processors.time_series import aggregate_timeseries, common_period_end
from analyzers.competitiveness import estimated_market_share


def test_zero_is_not_missing():
    assert is_missing(0) is False
    assert is_missing(None) is True


def test_safe_divide_missing_or_zero_denominator():
    assert safe_divide(None, 10) is None
    assert safe_divide(10, None) is None
    assert safe_divide(10, 0) is None
    assert safe_divide(10, 2) == 5


def test_sum_all_missing_stays_missing():
    df = pd.DataFrame({
        "period": ["2026-01", "2026-01"],
        "model_name": ["A", "B"],
        "sales_qty": [pd.NA, pd.NA],
    })
    out = aggregate_timeseries(df, "sales_qty", "월")
    assert pd.isna(out.loc[0, "sales_qty"])


def test_filters():
    df = pd.DataFrame({
        "period": ["2026-01", "2026-01", "2026-02"],
        "model_name": ["A", "B", "A"],
        "sales_qty": [10, 20, 30],
    })
    out = aggregate_timeseries(df, "sales_qty", "월", {"model_name": ["A"]})
    assert out["sales_qty"].tolist() == [10, 30]


def test_common_period():
    a = pd.DataFrame({"period": ["2026-07", "2026-08"]})
    b = pd.DataFrame({"period": ["2026-06", "2026-07"]})
    assert str(common_period_end(a, b)) == "2026-07"


def test_market_share_is_estimated():
    result = estimated_market_share(10, 100)
    assert result["value"] == 0.1
    assert result["estimate_flag"] == "ESTIMATED"
