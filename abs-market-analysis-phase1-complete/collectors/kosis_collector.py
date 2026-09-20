
import hashlib
import json
from datetime import datetime
from pathlib import Path

import pandas as pd
import requests

from config.settings import API_CONFIG, PATH_CONFIG
from config.sources import SOURCES


ORG_ID = "101"
TBL_ID = "DT_2KAA511"
API_URL = "https://kosis.kr/openapi/Param/statisticsParameterData.do"

COUNTRIES = {
    "KOREA": {
        "code": "1005",
        "name_ko": "대한민국",
    },
    "WORLD": {
        "code": "0",
        "name_ko": "세계",
    },
}

ITEMS = {
    "TOTAL": {
        "code": "T10",
        "name_ko": "전체",
    },
    "PASSENGER": {
        "code": "T11",
        "name_ko": "승용차",
    },
    "COMMERCIAL": {
        "code": "T12",
        "name_ko": "상용차",
    },
}

RAW_DIR = Path(PATH_CONFIG["raw"]) / "kosis"
SOURCE_LOG_PATH = Path(PATH_CONFIG["metadata"]) / "source_log.csv"


def _sha256(path: Path) -> str:
    h = hashlib.sha256()

    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)

    return h.hexdigest()


def _append_source_log(row: dict) -> None:
    SOURCE_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)

    if SOURCE_LOG_PATH.exists():
        existing = pd.read_csv(SOURCE_LOG_PATH, dtype=str)

        for column in existing.columns:
            if column not in row:
                row[column] = ""

        new_row = pd.DataFrame(
            [{column: row.get(column, "") for column in existing.columns}]
        )

        updated = pd.concat(
            [existing, new_row],
            ignore_index=True,
        )

        updated.to_csv(
            SOURCE_LOG_PATH,
            index=False,
            encoding="utf-8-sig",
        )

    else:
        pd.DataFrame([row]).to_csv(
            SOURCE_LOG_PATH,
            index=False,
            encoding="utf-8-sig",
        )


def collect_vehicle_production(
    start_year: int = 2010,
    end_year: int = 2024,
) -> dict:

    api_key = API_CONFIG["kosis_key"]

    if not api_key:
        raise RuntimeError("KOSIS_API_KEY가 설정되어 있지 않습니다.")

    collected_at = datetime.now()
    timestamp = collected_at.strftime("%Y%m%d%H%M%S")

    source_id = f"KOSIS_{timestamp}_VEHICLE_PRODUCTION"

    RAW_DIR.mkdir(parents=True, exist_ok=True)

    raw_path = (
        RAW_DIR
        / f"{timestamp}_KOSIS_DT_2KAA511_vehicle_production.json"
    )

    raw_snapshot = {
        "source_id": source_id,
        "source": "KOSIS",
        "org_id": ORG_ID,
        "table_id": TBL_ID,
        "table_name": "자동차 생산",
        "start_year": start_year,
        "end_year": end_year,
        "collected_at": collected_at.isoformat(),
        "requests": [],
    }

    record_count = 0

    for country_key, country in COUNTRIES.items():

        for item_key, item in ITEMS.items():

            params = {
                "method": "getList",
                "apiKey": api_key,
                "orgId": ORG_ID,
                "tblId": TBL_ID,
                "itmId": item["code"],
                "objL1": country["code"],
                "prdSe": "Y",
                "startPrdDe": str(start_year),
                "endPrdDe": str(end_year),
                "format": "json",
                "jsonVD": "Y",
            }

            response = requests.get(
                API_URL,
                params=params,
                timeout=30,
            )

            response.raise_for_status()

            try:
                data = response.json()
            except Exception as exc:
                raise RuntimeError(
                    f"KOSIS 응답 JSON 해석 실패: "
                    f"{country_key}/{item_key}"
                ) from exc

            if isinstance(data, dict) and data.get("err"):
                raise RuntimeError(
                    f"KOSIS API 오류 "
                    f"{country_key}/{item_key}: {data}"
                )

            if not isinstance(data, list):
                raise RuntimeError(
                    f"예상하지 못한 KOSIS 응답 형식: "
                    f"{country_key}/{item_key}"
                )

            record_count += len(data)

            safe_params = {
                key: value
                for key, value in params.items()
                if key != "apiKey"
            }

            raw_snapshot["requests"].append(
                {
                    "country_key": country_key,
                    "country_code": country["code"],
                    "country_name_ko": country["name_ko"],
                    "item_key": item_key,
                    "item_code": item["code"],
                    "item_name_ko": item["name_ko"],
                    "request_params": safe_params,
                    "response": data,
                }
            )

    with raw_path.open(
        "w",
        encoding="utf-8",
    ) as f:
        json.dump(
            raw_snapshot,
            f,
            ensure_ascii=False,
            indent=2,
        )

    file_hash = _sha256(raw_path)

    source = SOURCES.get(
        "kosis",
        {"name": "KOSIS 국가통계포털"},
    )

    source_log_row = {
        "source_id": source_id,
        "source_key": "kosis",
        "source_name": source.get(
            "name",
            "KOSIS 국가통계포털",
        ),
        "basis_date": str(end_year),
        "collected_at": collected_at.isoformat(),
        "source_url": (
            "https://kosis.kr/statHtml/statHtml.do"
            "?orgId=101&tblId=DT_2KAA511"
        ),
        "raw_file_path": str(raw_path),
        "sha256": file_hash,
        "status": "SUCCESS",
        "notes": (
            "KOSIS 자동차 생산 통계 "
            "대한민국/세계 × 전체/승용차/상용차 "
            f"{start_year}~{end_year}"
        ),
    }

    _append_source_log(source_log_row)

    return {
        "source_id": source_id,
        "raw_file": str(raw_path),
        "sha256": file_hash,
        "record_count": record_count,
        "start_year": start_year,
        "end_year": end_year,
    }


if __name__ == "__main__":

    result = collect_vehicle_production()

    print("KOSIS 차량 생산 데이터 수집 완료")
    print("SOURCE_ID:", result["source_id"])
    print("RAW_FILE:", result["raw_file"])
    print("RECORD_COUNT:", result["record_count"])
    print("SHA256:", result["sha256"])
