from pathlib import Path

import pandas as pd

from config.settings import PATH_CONFIG
from config.schemas import MARKET_MONTHLY_COLUMNS
from loaders.kosis_loader import load_latest_vehicle_production_processed
from loaders.master_loader import load_market_assumption_master




OUTPUT_PATH = (
    Path(__file__).resolve().parents[1]
    / "data"
    / "mart"
    / "market_monthly.parquet"
)
# ============================================================
# [MOTIE 월별 자동차 시장 데이터]
# 산업통상부 자동차산업 월별 MASTER를 시장 MART에 연결합니다.
#
# 데이터:
#   data/raw/motie/motie_monthly_master.csv
#
# 컬럼:
#   period      : YYYY-MM
#   production  : 생산량
#   domestic    : 내수 판매량
#   export      : 수출량
#
# 중요:
#   일부 월은 원자료가 없으므로 임의 보간하지 않습니다.
#   실제 확보된 월만 분석에 사용합니다.
# ============================================================

MOTIE_MONTHLY_MASTER = (
    Path(__file__).resolve().parents[1]
    / "data"
    / "raw"
    / "motie"
    / "motie_monthly_master.csv"
)

def build_market_mart() -> pd.DataFrame:
    production = load_latest_vehicle_production_processed()

    rows = []
    # ========================================================
    # [1] MOTIE 월별 자동차 시장 데이터 연결
    # ========================================================
    # 우리가 검증/정리한 월별 MASTER를 읽습니다.
    #
    # period     : 기준월 (예: 2026-08)
    # production : 국내 자동차 생산량
    # domestic   : 국내 자동차 내수 판매량
    # export     : 국내 자동차 수출량
    #
    # 결측월은 임의로 보간하지 않습니다.
    # 실제 데이터가 존재하는 월만 시장 MART에 저장합니다.
    # ========================================================

    if MOTIE_MONTHLY_MASTER.exists():
        motie = pd.read_csv(
            MOTIE_MONTHLY_MASTER,
            dtype={"period": str},
        )

        # ----------------------------------------------------
        # [1-1] 숫자 컬럼 정리
        # 문자 등이 섞여 있어도 숫자로 안전하게 변환합니다.
        # ----------------------------------------------------
        for col in ["production", "domestic", "export"]:
            motie[col] = pd.to_numeric(
                motie[col],
                errors="coerce",
            )

        # ----------------------------------------------------
        # [1-2] MASTER 컬럼을 대시보드용 지표명으로 변환
        # ----------------------------------------------------
        motie_metrics = {
            "production": "VEHICLE_PRODUCTION_TOTAL",
            "domestic": "VEHICLE_DOMESTIC_TOTAL",
            "export": "VEHICLE_EXPORT_TOTAL",
        }

        # ----------------------------------------------------
        # [1-3] 월별 데이터를 시장 MART 형식으로 저장
        # ----------------------------------------------------
        for source_col, metric_name in motie_metrics.items():

            for _, motie_row in motie.iterrows():
                value = motie_row.get(source_col)

                # 값이 없는 월은 만들어내지 않고 건너뜁니다.
                if pd.isna(value):
                    continue

                rows.append(
                    {
                        "period": motie_row["period"],
                        "market_scope": "KOREA",
                        "metric": metric_name,
                        "value": float(value),
                        "unit": "EA",
                        "source_id": motie_row.get(
                            "source_file",
                            "motie_monthly_master.csv",
                        ),
                        "source_key": "motie",
                        "estimate_flag": "ACTUAL",
                        "confidence_grade": "",
                        "model_version": "",
                    }
                )

    # KOSIS 자동차 생산량을 시장 기준 데이터로 변환
    for _, row in production.iterrows():
        year = row.get("year")
        qty = row.get("production_qty")

        if pd.isna(year):
            continue

        country_code = str(row.get("country_code", ""))
        category = str(row.get("vehicle_category", ""))

        # ====================================================
        # [2] KOSIS 기존 데이터의 사용 범위
        # ====================================================
        # GLOBAL:
        #   기존 KOSIS 연간 자동차 생산 데이터를 계속 사용합니다.
        #
        # KOREA:
        #   위에서 MOTIE 월별 MASTER를 새로 연결했으므로
        #   기존 KOSIS 한국 연간 데이터는 넣지 않습니다.
        #
        # 이유:
        #   KOSIS 한국 연간값 + MOTIE 한국 월별값이
        #   동시에 들어가는 중복을 방지하기 위해서입니다.
        # ====================================================

        if country_code == "0":
            scope = "GLOBAL"

        elif country_code == "1005":
            continue

        else:
            continue
        
        rows.append(
            {
                "period": f"{int(year)}-12",
                "market_scope": scope,
                "metric": f"VEHICLE_PRODUCTION_{category}",
                "value": (
                    float(qty)
                    if not pd.isna(qty)
                    else pd.NA
                ),
                "unit": "EA",
                "source_id": row.get("source_id"),
                "source_key": "kosis",
                "estimate_flag": row.get(
                    "estimate_flag",
                    "ACTUAL",
                ),
                "confidence_grade": "",
                "model_version": "",
            }
        )

    # 제품/당사 공급 기준은 Master를 단일 원본으로 사용
    assumptions = load_market_assumption_master()

    metric_map = {
        "coils_per_system": "COILS_PER_SYSTEM",
        "company_iv_per_system": "COMPANY_IV_PER_SYSTEM",
        "company_ov_per_system": "COMPANY_OV_PER_SYSTEM",
        "company_hsv_per_system": "COMPANY_HSV_PER_SYSTEM",
    }

    model_rows = []

    for _, row in assumptions.iterrows():
        model_id = row.get("model_id")
        parameter_name = row.get("parameter_name")

        if pd.isna(model_id) or parameter_name not in metric_map:
            continue

        value = pd.to_numeric(
            row.get("parameter_value"),
            errors="coerce",
        )

        model_rows.append(
            {
                "period": "2026-09",
                "market_scope": str(model_id),
                "metric": metric_map[parameter_name],
                "value": value if not pd.isna(value) else pd.NA,
                "unit": row.get("unit"),
                "source_id": row.get("source_id"),
                "source_key": "market_assumption_master",
                "estimate_flag": row.get("estimate_flag"),
                "confidence_grade": row.get("confidence_grade"),
                "model_version": row.get("model_version"),
            }
        )

    rows.extend(model_rows)

    mart = pd.DataFrame(rows)

    for column in MARKET_MONTHLY_COLUMNS:
        if column not in mart.columns:
            mart[column] = pd.NA

    mart = mart[MARKET_MONTHLY_COLUMNS]

    return mart


def save_market_mart() -> dict:
    mart = build_market_mart()

    OUTPUT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    mart.to_parquet(
        OUTPUT_PATH,
        index=False,
    )

    return {
        "output_file": str(OUTPUT_PATH),
        "row_count": len(mart),
        "actual_count": int(
            (mart["estimate_flag"] == "ACTUAL").sum()
        ),
        "estimated_count": int(
            (mart["estimate_flag"] == "ESTIMATED").sum()
        ),
    }


if __name__ == "__main__":
    result = save_market_mart()

    print("Market mart build completed")
    print("OUTPUT_FILE:", result["output_file"])
    print("ROW_COUNT:", result["row_count"])
    print("ACTUAL:", result["actual_count"])
    print("ESTIMATED:", result["estimated_count"])


