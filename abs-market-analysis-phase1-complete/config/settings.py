import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parents[1]

DATE_CONFIG = {
    "raw_start_year": 2010,
    "analysis_start_year": 2015,
    "recent_years": 5,
    "freq": "M",
}

API_CONFIG = {
    "dart_key": os.getenv("DART_API_KEY"),
    "trade_key": os.getenv("TRADE_API_KEY"),
    "kipris_key": os.getenv("KIPRIS_API_KEY"),
    "bok_key": os.getenv("BOK_API_KEY"),
    "kosis_key": os.getenv("KOSIS_API_KEY"),
}

PATH_CONFIG = {
    "raw": BASE_DIR / "data" / "raw",
    "processed": BASE_DIR / "data" / "processed",
    "mart": BASE_DIR / "data" / "mart",
    "cache": BASE_DIR / "data" / "cache",
    "metadata": BASE_DIR / "data" / "metadata",
    "reports": BASE_DIR / "reports" / "figures",
}

DASHBOARD_CONFIG = {
    "service_name_ko": "시장동향",
    "service_name_en": "ABS Market Intelligence",
    "default_view": "글로벌 시장",
    "views": ["글로벌 시장", "국내 시장", "한국기업 글로벌", "우리회사 비교분석"],
    "show_model_version": True,
    "show_source_date": True,
    "show_confidence_grade": True,
}
