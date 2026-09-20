HS_CODES = {
    "brake_parts": {
        "code": "8708.30",
        "name": "자동차용 브레이크 및 부품",
        "note": "ABS Coil Assy 전용 코드가 아니므로 관측치로만 사용. 최종 시장규모는 반드시 '추정' 처리.",
    },
    "solenoid_valve": {
        "code": "8481.20",
        "name": "공압/유압용 밸브",
        "note": "ABS 관련성이 있을 수 있으나 품목 범위 검증 필요.",
    },
    "electro_magnet": {
        "code": "8505.20",
        "name": "전자석/전자기 관련 품목",
        "note": "ABS Coil Assy와의 직접 대응 여부를 별도 검증.",
    },
}

CLASSIFICATION_RULES = {
    "domestic_market": "생산지역(plant_country) 기준: 대한민국 내 생산·공급 활동",
    "korean_company_global": "기업 지배관계(parent_hq_country) 기준: 한국계 기업의 국내+해외 생산",
    "global_market": "전 세계 생산/수요를 지역·국가 기준으로 집계",
}
MARKET_ASSUMPTION_PARAMETERS = {
    "vehicle_production_qty": {
        "name_ko": "차량 생산량",
        "unit": "EA",
    },
    "fitment_rate": {
        "name_ko": "장착률",
        "unit": "RATIO",
    },
    "systems_per_vehicle": {
        "name_ko": "차량당 시스템 수",
        "unit": "EA/VEHICLE",
    },
    "coils_per_system": {
        "name_ko": "시스템당 Coil 수",
        "unit": "EA/SYSTEM",
    },
    "applicable_system_qty": {
        "name_ko": "적용 대상 시스템 수량",
        "unit": "EA",
    },
    "units_per_system": {
        "name_ko": "시스템당 적용 수량",
        "unit": "EA/SYSTEM",
    },
    "calculation_status": {
        "name_ko": "계산 상태",
        "unit": "TEXT",
    },
}