from dataclasses import dataclass
from typing import Optional
from pathlib import Path

@dataclass
class EstimateResult:
    value: Optional[float]
    unit: str
    calculation_status: str
    estimate_flag: str = "ESTIMATED"
    confidence_grade: Optional[str] = None
    model_version: str = "EST_MODEL_V1.0"


def estimate_coil_market_qty(
    vehicle_production: Optional[float],
    fitment_rate: Optional[float],
    systems_per_vehicle: Optional[float],
    coils_per_system: Optional[float],
    confidence_grade: Optional[str] = None,
) -> EstimateResult:

    required_values = [
        vehicle_production,
        fitment_rate,
        systems_per_vehicle,
        coils_per_system,
    ]

    if any(value is None for value in required_values):
        return EstimateResult(
            value=None,
            unit="EA",
            calculation_status="CALCULATION_UNAVAILABLE",
            confidence_grade=confidence_grade,
        )

    value = (
        vehicle_production
        * fitment_rate
        * systems_per_vehicle
        * coils_per_system
    )

    return EstimateResult(
        value=value,
        unit="EA",
        calculation_status="CALCULATED",
        confidence_grade=confidence_grade,
    )


def estimate_market_value(
    market_qty: Optional[float],
    avg_unit_price: Optional[float],
    confidence_grade: Optional[str] = None,
) -> EstimateResult:

    if market_qty is None or avg_unit_price is None:
        return EstimateResult(
            value=None,
            unit="KRW",
            calculation_status="CALCULATION_UNAVAILABLE",
            confidence_grade=confidence_grade,
        )

    value = market_qty * avg_unit_price

    return EstimateResult(
        value=value,
        unit="KRW",
        calculation_status="CALCULATED",
        confidence_grade=confidence_grade,
    )

import pandas as pd

from loaders.master_loader import load_market_assumption_master


def _to_optional_float(value) -> Optional[float]:
    if value is None or pd.isna(value):
        return None

    text = str(value).strip()

    if text == "":
        return None

    try:
        return float(text)
    except ValueError:
        return None


def get_assumption_value(
    technology_id: str,
    parameter_name: str,
    model_id: Optional[str] = None,
    region: Optional[str] = None,
    year: Optional[int] = None,
    vehicle_category: Optional[str] = None,
) -> dict:

    assumptions = load_market_assumption_master()

    filtered = assumptions[
        (assumptions["technology_id"] == technology_id)
        & (assumptions["parameter_name"] == parameter_name)
    ].copy()

    # 1. 모델 전용 가정이 있으면 우선 사용
    if model_id is not None:
        model_specific = filtered[
            filtered["model_id"] == model_id
        ]

        if not model_specific.empty:
            filtered = model_specific

    # 2. 지역 전용 가정이 있으면 우선 사용
    #    없으면 GLOBAL 공통 가정 사용
    if region is not None:
        region_specific = filtered[
            filtered["region"] == region
        ]

        if not region_specific.empty:
            filtered = region_specific
        else:
            filtered = filtered[
                filtered["region"] == "GLOBAL"
            ]

    # 3. 해당 연도의 가정이 있으면 우선 사용
    if year is not None:
        year_specific = filtered[
            filtered["year"] == str(year)
        ]

        if not year_specific.empty:
            filtered = year_specific

    # 4. 해당 차종의 가정이 있으면 우선 사용
    if vehicle_category is not None:
        category_specific = filtered[
            filtered["vehicle_category"] == vehicle_category
        ]

        if not category_specific.empty:
            filtered = category_specific

    if filtered.empty:
        return {
            "value": None,
            "estimate_flag": "MISSING",
            "confidence_grade": None,
            "source_id": None,
            "assumption_id": None,
        }

    row = filtered.iloc[0]

    return {
        "value": _to_optional_float(
            row.get("parameter_value")
        ),
        "estimate_flag": row.get("estimate_flag"),
        "confidence_grade": row.get("confidence_grade"),
        "source_id": row.get("source_id"),
        "assumption_id": row.get("assumption_id"),
    }


def estimate_brake_coil_market_from_assumptions(
    vehicle_production: Optional[float],
    technology_id: str,
    model_id: Optional[str] = None,
    region: Optional[str] = None,
    year: Optional[int] = None,
    vehicle_category: Optional[str] = None,
) -> dict:

    fitment = get_assumption_value(
        technology_id=technology_id,
        parameter_name="fitment_rate",
        model_id=model_id,
        region=region,
        year=year,
        vehicle_category=vehicle_category,
    )

    systems = get_assumption_value(
        technology_id=technology_id,
        parameter_name="systems_per_vehicle",
        model_id=model_id,
        region=region,
        year=year,
        vehicle_category=vehicle_category,
    )

    coils = get_assumption_value(
        technology_id=technology_id,
        parameter_name="coils_per_system",
        model_id=model_id,
        region=region,
        year=year,
        vehicle_category=vehicle_category,
    )

    result = estimate_coil_market_qty(
        vehicle_production=vehicle_production,
        fitment_rate=fitment["value"],
        systems_per_vehicle=systems["value"],
        coils_per_system=coils["value"],
        confidence_grade=coils["confidence_grade"],
    )

    return {
        "result": result,
        "inputs": {
            "vehicle_production": vehicle_production,
            "fitment_rate": fitment,
            "systems_per_vehicle": systems,
            "coils_per_system": coils,
        },
    }


from loaders.kosis_loader import get_vehicle_production


def estimate_brake_coil_market_from_kosis(
    year: int,
    country_code: str,
    technology_id: str,
    model_id: Optional[str] = None,
    vehicle_category: str = "TOTAL",
) -> dict:

    production = get_vehicle_production(
        year=year,
        country_code=country_code,
        vehicle_category=vehicle_category,
    )

    region_map = {
        "1005": "KOREA",
    }

    region = region_map.get(str(country_code))

    estimation = estimate_brake_coil_market_from_assumptions(
        vehicle_production=production["value"],
        technology_id=technology_id,
        model_id=model_id,
        region=region,
        year=year,
        vehicle_category=vehicle_category,
    )

    return {
        "production": production,
        "result": estimation["result"],
        "inputs": estimation["inputs"],
    }
from datetime import datetime

from config.settings import PATH_CONFIG


def _clean_log_value(value):
    if value is None:
        return ""
    if pd.isna(value):
        return ""
    return value


def append_calculation_log(
    metric_name: str,
    result: EstimateResult,
    formula: str,
    source_ids: list[str] | None = None,
    notes: str = "",
) -> dict:

    calculated_at = datetime.now()
    timestamp = calculated_at.strftime("%Y%m%d%H%M%S%f")

    estimate_id = f"EST_{timestamp}"

    log_path = Path(PATH_CONFIG["metadata"]) / "calculation_log.csv"

    source_ids = source_ids or []

    row = {
        "estimate_id": estimate_id,
        "metric_name": metric_name,
        "result_value": _clean_log_value(result.value),
        "result_unit": result.unit,
        "calculation_status": result.calculation_status,
        "estimate_flag": result.estimate_flag,
        "confidence_grade": _clean_log_value(
            result.confidence_grade
        ),
        "formula": formula,
        "source_ids": "|".join(
            str(x)
            for x in source_ids
            if x is not None and not pd.isna(x)
        ),
        "model_version": result.model_version,
        "calculated_at": calculated_at.isoformat(),
        "notes": notes,
    }

    existing = pd.read_csv(
        log_path,
        dtype="string",
    )

    new_row = pd.DataFrame([row])

    updated = pd.concat(
        [existing, new_row],
        ignore_index=True,
    )

    updated.to_csv(
        log_path,
        index=False,
        encoding="utf-8-sig",
    )

    return row


def estimate_and_log_brake_coil_market_from_kosis(
    year: int,
    country_code: str,
    technology_id: str,
    model_id: Optional[str] = None,
    vehicle_category: str = "TOTAL",
) -> dict:

    estimation = estimate_brake_coil_market_from_kosis(
        year=year,
        country_code=country_code,
        technology_id=technology_id,
        model_id=model_id,
        vehicle_category=vehicle_category,
    )

    production = estimation["production"]
    result = estimation["result"]
    inputs = estimation["inputs"]

    source_ids = [
        production.get("source_id"),
        inputs["fitment_rate"].get("source_id"),
        inputs["systems_per_vehicle"].get("source_id"),
        inputs["coils_per_system"].get("source_id"),
    ]

    metric_name = (
        f"{technology_id}"
        + (
            f"_{model_id}"
            if model_id
            else ""
        )
        + "_COIL_MARKET_QTY"
    )

    formula = (
        "vehicle_production"
        " * fitment_rate"
        " * systems_per_vehicle"
        " * coils_per_system"
    )

    notes = (
        f"year={year}; "
        f"country_code={country_code}; "
        f"vehicle_category={vehicle_category}"
    )

    log_row = append_calculation_log(
        metric_name=metric_name,
        result=result,
        formula=formula,
        source_ids=source_ids,
        notes=notes,
    )

    return {
        **estimation,
        "calculation_log": log_row,
    }
def get_coil_component_qty(
    technology_id: str,
    model_id: str,
    coil_type: str,
    company_scope: bool = False,
) -> dict:
    """
    모델별 IV / OV / HSV 시스템당 수량 조회.

    company_scope=False:
        전체 시스템의 해당 Coil 구성 수량 조회

    company_scope=True:
        당사 공급대상으로 등록된 수량 조회
        실제 당사 공급량/점유율을 의미하지 않음
    """

    coil_type = coil_type.strip().upper()

    valid_types = {"IV", "OV", "HSV"}

    if coil_type not in valid_types:
        return {
            "value": None,
            "estimate_flag": "MISSING",
            "confidence_grade": None,
            "source_id": None,
            "assumption_id": None,
        }

    if company_scope:
        parameter_name = f"company_{coil_type.lower()}_per_system"
    else:
        parameter_name = f"{coil_type.lower()}_per_system"

    return get_assumption_value(
        technology_id=technology_id,
        parameter_name=parameter_name,
        model_id=model_id,
    )
def get_company_supply_scope_per_system(
    technology_id: str,
    model_id: str,
) -> dict:
    """
    시스템 1대 기준 당사 공급대상 Coil 수량을 계산한다.

    주의:
    이 값은 실제 당사 공급량이나 시장점유율이 아니다.
    비독점 품목의 경쟁사 공급분을 포함할 수 있다.
    """

    components = {}

    total = 0.0
    found = False

    source_ids = []
    assumption_ids = []

    for coil_type in ("IV", "OV", "HSV"):
        item = get_coil_component_qty(
            technology_id=technology_id,
            model_id=model_id,
            coil_type=coil_type,
            company_scope=True,
        )

        components[coil_type] = item

        if item["value"] is not None:
            total += item["value"]
            found = True

        source_id = item.get("source_id")
        if source_id is not None and not pd.isna(source_id):
            source_ids.append(source_id)

        assumption_id = item.get("assumption_id")
        if assumption_id is not None and not pd.isna(assumption_id):
            assumption_ids.append(assumption_id)

    if not found:
        return {
            "value": None,
            "unit": "EA/SYSTEM",
            "calculation_status": "CALCULATION_UNAVAILABLE",
            "components": components,
            "source_ids": source_ids,
            "assumption_ids": assumption_ids,
        }

    return {
        "value": total,
        "unit": "EA/SYSTEM",
        "calculation_status": "CALCULATED",
        "components": components,
        "source_ids": source_ids,
        "assumption_ids": assumption_ids,
    }
