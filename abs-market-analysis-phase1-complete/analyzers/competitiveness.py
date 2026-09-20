from __future__ import annotations
import pandas as pd
from processors.missing import safe_divide


def yoy_growth(current, previous):
    ratio = safe_divide(current, previous)
    return None if ratio is None else ratio - 1


def estimated_market_share(company_sales_qty, estimated_market_demand):
    """시장 분모가 추정이면 결과도 반드시 '추정'으로 취급한다."""
    ratio = safe_divide(company_sales_qty, estimated_market_demand)
    return {
        "value": ratio,
        "estimate_flag": "ESTIMATED" if ratio is not None else "CALCULATION_UNAVAILABLE",
    }


def growth_gap(company_growth, market_growth):
    if company_growth is None or market_growth is None:
        return None
    return company_growth - market_growth


def data_completeness(record: dict, required_fields: list[str]) -> float | None:
    if not required_fields:
        return None
    available = sum(pd.notna(record.get(k)) for k in required_fields)
    return available / len(required_fields)
