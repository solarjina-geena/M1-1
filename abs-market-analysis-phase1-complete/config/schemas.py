"""표준 데이터 스키마.

원본 컬럼명이 달라도 이 스키마로 매핑한 뒤 분석한다.
모르는 값은 None/NA로 유지하며 0으로 대체하지 않는다.
"""

INTERNAL_SALES_COLUMNS = [
    "period",              # YYYY-MM
    "product_code",        # 사내 품번/고유키
    "product_name",
    "model_name",
    "customer_name",
    "oem_name",
    "vehicle_model",
    "sales_region",
    "sales_country",
    "sales_qty",
    "sales_amount",
    "currency",
    "source_file",
]

INTERNAL_PRODUCTION_COLUMNS = [
    "period",
    "product_code",
    "product_name",
    "model_name",
    "plant_name",
    "plant_country",
    "production_qty",
    "source_file",
]

MARKET_MONTHLY_COLUMNS = [
    "period",
    "market_scope",
    "metric",
    "value",
    "unit",
    "source_id",
    "source_key",
    "estimate_flag",
    "confidence_grade",
    "model_version",
]

STATUS = {
    "actual": "ACTUAL",
    "estimated": "ESTIMATED",
    "missing": "MISSING",
    "unavailable": "CALCULATION_UNAVAILABLE",
}
TRADE_PROCESSED_COLUMNS = [
    # 관세청 원자료 표준화
    "period",
    "hs_code",
    "item_name",
    "country_code",
    "country_name",
    "export_usd",
    "export_kg",
    "import_usd",
    "import_kg",
    "trade_balance_usd",

    # 원본 추적 / 감사
    "source_id",
    "source_key",
    "basis_date",
    "collected_at",
    "estimate_flag",
    "confidence_grade",
    "model_version",
]