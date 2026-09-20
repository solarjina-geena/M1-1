from __future__ import annotations

import csv
import hashlib
import urllib.parse
from datetime import datetime
from pathlib import Path

import requests

from config.settings import API_CONFIG, PATH_CONFIG
from config.sources import SOURCES
from config.targets import HS_CODES


TRADE_API_URL = (
    "https://apis.data.go.kr/1220000/"
    "nitemtrade/getNitemtradeList"
)


def get_trade_api_key() -> str:
    key = API_CONFIG.get("trade_key")

    if not key:
        raise RuntimeError("TRADE_API_KEY가 설정되어 있지 않습니다.")

    return urllib.parse.unquote(key.strip())


def normalize_hs_code(code: str) -> str:
    """
    targets.py의 '8708.30' 같은 표기에서 점을 제거한다.
    현재는 후보코드 확인용이므로 코드 의미를 임의 확장하지 않는다.
    """
    return str(code).replace(".", "").strip()


def fetch_trade_xml(
    start_yymm: str,
    end_yymm: str,
    hs_code: str,
    country_code: str = "",
) -> str:
    params = {
        "strtYymm": start_yymm,
        "endYymm": end_yymm,
        "hsSgn": normalize_hs_code(hs_code),
        "serviceKey": get_trade_api_key(),
    }

    if country_code:
        params["cntyCd"] = country_code

    response = requests.get(
        TRADE_API_URL,
        params=params,
        timeout=30,
    )
    response.raise_for_status()

    return response.text


def save_raw_xml(
    xml_text: str,
    hs_code: str,
    start_yymm: str,
    end_yymm: str,
    country_code: str = "ALL",
) -> Path:
    raw_dir = PATH_CONFIG["raw"] / "trade"
    raw_dir.mkdir(parents=True, exist_ok=True)

    collected_at = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    hs_clean = normalize_hs_code(hs_code)

    filename = (
        f"{collected_at}_HS{hs_clean}_"
        f"{start_yymm}-{end_yymm}_{country_code}.xml"
    )

    output_path = raw_dir / filename

    output_path.write_text(
        xml_text,
        encoding="utf-8",
    )

    return output_path


def calculate_sha256(file_path: Path) -> str:
    sha256 = hashlib.sha256()

    with file_path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256.update(chunk)

    return sha256.hexdigest()


def append_source_log(
    raw_file_path: Path,
    start_yymm: str,
    end_yymm: str,
    hs_code: str,
    country_code: str,
) -> str:
    log_path = PATH_CONFIG["metadata"] / "source_log.csv"

    collected_at = datetime.now()
    source_id = (
        f"TRADE_"
        f"{collected_at.strftime('%Y%m%d%H%M%S')}_"
        f"HS{normalize_hs_code(hs_code)}_"
        f"{country_code or 'ALL'}"
    )

    source = SOURCES["trade"]

    row = {
        "source_id": source_id,
        "source_key": "trade",
        "source_name": source["name"],
        "basis_date": f"{start_yymm}-{end_yymm}",
        "collected_at": collected_at.isoformat(timespec="seconds"),
        "source_url": TRADE_API_URL,
        "raw_file_path": str(raw_file_path),
        "sha256": calculate_sha256(raw_file_path),
        "status": "SUCCESS",
        "notes": (
            f"HS={normalize_hs_code(hs_code)}; "
            f"country={country_code or 'ALL'}"
        ),
    }

    fieldnames = [
        "source_id",
        "source_key",
        "source_name",
        "basis_date",
        "collected_at",
        "source_url",
        "raw_file_path",
        "sha256",
        "status",
        "notes",
    ]

    with log_path.open(
        "a",
        encoding="utf-8-sig",
        newline="",
    ) as f:
        writer = csv.DictWriter(
            f,
            fieldnames=fieldnames,
        )
        writer.writerow(row)

    return source_id


def collect_one(
    start_yymm: str,
    end_yymm: str,
    hs_code: str,
    country_code: str = "",
) -> Path:
    xml_text = fetch_trade_xml(
        start_yymm=start_yymm,
        end_yymm=end_yymm,
        hs_code=hs_code,
        country_code=country_code,
    )

    output_path = save_raw_xml(
        xml_text=xml_text,
        hs_code=hs_code,
        start_yymm=start_yymm,
        end_yymm=end_yymm,
        country_code=country_code or "ALL",
    )

    source_id = append_source_log(
        raw_file_path=output_path,
        start_yymm=start_yymm,
        end_yymm=end_yymm,
        hs_code=hs_code,
        country_code=country_code,
    )

    print(f"Source ID: {source_id}")

    return output_path


if __name__ == "__main__":
    print("관세청 수집기 연결 테스트")

    target = HS_CODES["brake_parts"]

    path = collect_one(
        start_yymm="202501",
        end_yymm="202501",
        hs_code=target["code"],
        country_code="US",
    )

    print(f"저장 완료: {path}")