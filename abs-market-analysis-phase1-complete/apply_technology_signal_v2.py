from pathlib import Path
from datetime import datetime
import shutil
import pandas as pd

ROOT = Path(__file__).resolve().parent
META = ROOT / "data" / "metadata"
BACKUP = META / "_backup_before_tech_v2"
BACKUP.mkdir(parents=True, exist_ok=True)

TECH_FILE = META / "technology_master.csv"
SIGNAL_FILE = META / "technology_signal_master.csv"
SOURCE_FILE = META / "source_log.csv"

for p in [TECH_FILE, SIGNAL_FILE, SOURCE_FILE]:
    if not p.exists():
        raise FileNotFoundError(f"필수 파일 없음: {p}")
    dst = BACKUP / p.name
    if not dst.exists():
        shutil.copy2(p, dst)

tech = pd.read_csv(TECH_FILE, dtype="string")
sig = pd.read_csv(SIGNAL_FILE, dtype="string")
src = pd.read_csv(SOURCE_FILE, dtype="string")

# 1) 기술분류를 실제 분석 단위로 분리
new_tech = [
    {
        "technology_id": "TECH_BBW",
        "technology_group": "BRAKE_CONTROL",
        "technology_name_ko": "Brake-by-Wire",
        "technology_name_en": "Brake-by-Wire",
        "description": "브레이크 페달과 제동 액추에이터 사이의 기계적 연결 의존도를 줄이고 전기 신호로 제동을 제어하는 차세대 제동 기술",
        "market_driver": "전동화·SDV·ADAS·자율주행 확대",
        "verification_status": "VERIFIED",
        "source_id": "TECH_BOSCH_BBW_OFFICIAL",
        "valid_from": "2025",
        "valid_to": pd.NA,
        "notes": "Bosch/Continental/ZF 공식자료 기반 기술분류. 시장규모와 수주규모는 별도 신호로 관리",
    },
    {
        "technology_id": "TECH_EMB",
        "technology_group": "BRAKE_CONTROL",
        "technology_name_ko": "전자기계식 제동(EMB)",
        "technology_name_en": "Electro-Mechanical Brake",
        "description": "휠 제동력을 전기모터 기반 액추에이터로 생성하는 전자기계식 제동 기술",
        "market_driver": "Dry Brake-by-Wire·전동화·SDV·고도 자동화",
        "verification_status": "VERIFIED",
        "source_id": "TECH_ZF_EMB_20250106",
        "valid_from": "2025",
        "valid_to": pd.NA,
        "notes": "ZF 공식 대형 OEM 계약 및 Brake-by-Wire 포트폴리오 자료 기반",
    },
]
for row in new_tech:
    if row["technology_id"] not in set(tech["technology_id"].dropna()):
        tech = pd.concat([tech, pd.DataFrame([row], columns=tech.columns)], ignore_index=True)

# 2) 기존 BBW 신호를 통합제동에서 BBW로 재분류
bbw_mask = (
    sig["event"].fillna("").str.contains("Brake-by-Wire", case=False, regex=False)
    | sig["notes"].fillna("").str.contains("brake-by-wire", case=False, regex=False)
)
sig.loc[bbw_mask, "technology_id"] = "TECH_BBW"

# 3) 공식 원문 출처 등록
new_sources = [
    {
        "source_id": "TECH_BOSCH_BBW_OFFICIAL",
        "source_key": "technical",
        "source_name": "Bosch Mobility - Brake-by-Wire",
        "basis_date": "2025",
        "collected_at": datetime.now().isoformat(timespec="seconds"),
        "source_url": "https://www.bosch-mobility.com/en/company/current-news/with-brake-by-wire-from-bosch-to-the-arctic-circle/",
        "raw_file_path": "",
        "sha256": "",
        "status": "VERIFIED",
        "notes": "공식자료: 2025년 가을 시장출시 계획, 복수 완성차 주문, 2030년 550만대 이상 전망",
    },
    {
        "source_id": "TECH_CONTINENTAL_IBBW_20250415",
        "source_key": "technical",
        "source_name": "Continental - Integrated Brake-by-Wire / Future Brake System",
        "basis_date": "2025-04-15",
        "collected_at": datetime.now().isoformat(timespec="seconds"),
        "source_url": "https://www.continental.com/en/press/press-releases/20250415-auto-shanghai-highlights/",
        "raw_file_path": "",
        "sha256": "",
        "status": "VERIFIED",
        "notes": "공식자료: Future Brake System 로드맵, 차세대 Integrated Brake-by-Wire, fully-dry electric caliper",
    },
    {
        "source_id": "TECH_ZF_EMB_20250106",
        "source_key": "technical",
        "source_name": "ZF - Brake-by-Wire / Electro-Mechanical Brake order",
        "basis_date": "2025-01-06",
        "collected_at": datetime.now().isoformat(timespec="seconds"),
        "source_url": "https://press.zf.com/press/en/releases/release_80320.html",
        "raw_file_path": "",
        "sha256": "",
        "status": "VERIFIED",
        "notes": "공식자료: 글로벌 OEM 계약, 계약기간 중 약 500만대 EMB 적용 계획 및 양산 계획",
    },
]
for row in new_sources:
    if row["source_id"] not in set(src["source_id"].dropna()):
        src = pd.concat([src, pd.DataFrame([row], columns=src.columns)], ignore_index=True)

# 기존 Bosch/Continental 신호의 source_id를 공식 URL이 있는 신규 source_id로 정규화
sig.loc[sig["company"].eq("Bosch") & bbw_mask, "source_id"] = "TECH_BOSCH_BBW_OFFICIAL"
sig.loc[sig["company"].eq("Continental") & bbw_mask, "source_id"] = "TECH_CONTINENTAL_IBBW_20250415"

# 4) ZF 사업화 신호 추가: 500만대는 '시장규모'가 아니라 계약 적용대수
zf_signal = {
    "signal_id": "SIG_ZF_EMB_ORDER_20250106",
    "signal_date": "2025-01-06",
    "technology_id": "TECH_EMB",
    "signal_type": "ORDER",
    "company": "ZF",
    "event": "Global OEM Brake-by-Wire / EMB major order",
    "vehicle_volume": "NEARLY_5000000_CONTRACT_VOLUME",
    "forecast_year": pd.NA,
    "forecast_value": pd.NA,
    "unit": "VEHICLE_CONTRACT_VOLUME",
    "region": "GLOBAL",
    "source_id": "TECH_ZF_EMB_20250106",
    "confidence_grade": "A",
    "verification_status": "VERIFIED",
    "notes": "ZF 공식자료. 계약기간 동안 약 500만대에 EMB 적용 계획. 시장규모/연간 판매량/2030 전망치로 해석 금지",
}
if zf_signal["signal_id"] not in set(sig["signal_id"].dropna()):
    sig = pd.concat([sig, pd.DataFrame([zf_signal], columns=sig.columns)], ignore_index=True)

# 5) 중복 방지 후 저장
tech = tech.drop_duplicates("technology_id", keep="last")
sig = sig.drop_duplicates("signal_id", keep="last")
src = src.drop_duplicates("source_id", keep="last")

tech.to_csv(TECH_FILE, index=False, encoding="utf-8-sig")
sig.to_csv(SIGNAL_FILE, index=False, encoding="utf-8-sig")
src.to_csv(SOURCE_FILE, index=False, encoding="utf-8-sig")

# 6) MART 재생성
from processors.technology_signal_mart import save_technology_signal_mart
result = save_technology_signal_mart()

mart = pd.read_parquet(ROOT / "data" / "mart" / "technology_signal.parquet")
merged = mart.merge(
    src[["source_id", "source_url", "status"]],
    on="source_id",
    how="left",
    suffixes=("", "_source"),
)

print("=" * 92)
print("TECHNOLOGY SIGNAL SAMPLE UPDATE - COMPLETE")
print("=" * 92)
print(f"TECHNOLOGY MASTER : {len(tech)} rows")
print(f"SIGNAL MASTER     : {len(sig)} rows")
print(f"MART              : {len(mart)} rows")
print(f"VERIFIED SIGNALS  : {(mart['verification_status'] == 'VERIFIED').sum()}")
print(f"SOURCE URL LINKED : {merged['source_url'].notna().sum()} / {len(merged)}")
print()
print("=== TECHNOLOGY COUNT ===")
print(mart.groupby("technology_id").size().to_string())
print()
print("=== SIGNALS ===")
cols = ["signal_date", "technology_id", "signal_type", "company", "event", "forecast_year", "forecast_value", "source_id"]
print(mart[cols].sort_values(["signal_date", "company"]).to_string(index=False))
print()
print("BACKUP :", BACKUP)
print("NOTE   : ZF 약 500만대는 계약 적용대수이며 시장규모/전망치로 사용하지 않음")
print("=" * 92)
