from __future__ import annotations
import math
import pandas as pd


def is_missing(value) -> bool:
    """None/NaN/빈 문자열을 결측으로 판단하되 숫자 0은 결측이 아니다."""
    if value is None:
        return True
    if isinstance(value, str):
        return value.strip() == ""
    try:
        return bool(pd.isna(value))
    except Exception:
        return False


def safe_divide(numerator, denominator):
    """분자/분모가 없거나 분모가 0이면 계산하지 않는다."""
    if is_missing(numerator) or is_missing(denominator):
        return None
    if denominator == 0:
        return None
    return numerator / denominator


def display_value(value, number_format=",.0f", missing_text="데이터 없음") -> str:
    if is_missing(value):
        return missing_text
    if isinstance(value, (int, float)):
        return format(value, number_format)
    return str(value)
