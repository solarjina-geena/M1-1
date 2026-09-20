from __future__ import annotations
from pathlib import Path
import hashlib
import pandas as pd

from config.schemas import INTERNAL_SALES_COLUMNS

DEFAULT_COLUMN_ALIASES = {
    "period": ["period", "년월", "판매년월", "기준월", "월"],
    "product_code": ["product_code", "품번", "PART NO", "Part No", "part_no", "모델코드"],
    "product_name": ["product_name", "품명", "제품명"],
    "model_name": ["model_name", "모델", "모델명", "당사모델"],
    "customer_name": ["customer_name", "고객사", "거래처", "납품처"],
    "oem_name": ["oem_name", "OEM", "완성차", "완성차업체"],
    "vehicle_model": ["vehicle_model", "적용차종", "차종"],
    "sales_region": ["sales_region", "판매지역", "국내수출", "구분"],
    "sales_country": ["sales_country", "판매국가", "국가"],
    "sales_qty": ["sales_qty", "판매수량", "출고수량", "수량"],
    "sales_amount": ["sales_amount", "매출액", "공급가액", "매출"],
    "currency": ["currency", "통화", "화폐"],
}


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def read_table(path: str | Path) -> pd.DataFrame:
    path = Path(path)
    suffix = path.suffix.lower()
    if suffix in {".xlsx", ".xlsm"}:
        return pd.read_excel(path)
    if suffix == ".csv":
        for enc in ("utf-8-sig", "utf-8", "cp949"):
            try:
                return pd.read_csv(path, encoding=enc)
            except UnicodeDecodeError:
                continue
        raise UnicodeDecodeError("csv", b"", 0, 1, "지원 인코딩으로 읽을 수 없습니다")
    raise ValueError(f"지원하지 않는 파일 형식: {suffix}")


def auto_mapping(columns) -> dict[str, str]:
    cols = {str(c).strip(): c for c in columns}
    mapping = {}
    for target, aliases in DEFAULT_COLUMN_ALIASES.items():
        for alias in aliases:
            if alias in cols:
                mapping[target] = cols[alias]
                break
    return mapping


def standardize_sales(df: pd.DataFrame, mapping: dict[str, str] | None = None, source_file: str = "") -> pd.DataFrame:
    mapping = mapping or auto_mapping(df.columns)
    out = pd.DataFrame(index=df.index)
    for target in INTERNAL_SALES_COLUMNS:
        source_col = mapping.get(target)
        out[target] = df[source_col] if source_col in df.columns else pd.NA

    out["source_file"] = source_file or out["source_file"]
    out["period"] = pd.to_datetime(out["period"], errors="coerce").dt.to_period("M").astype("string")
    for col in ["sales_qty", "sales_amount"]:
        out[col] = pd.to_numeric(out[col], errors="coerce")
    return out


def inspect_sales_file(path: str | Path) -> dict:
    path = Path(path)
    df = read_table(path)
    mapping = auto_mapping(df.columns)
    std = standardize_sales(df, mapping, path.name)
    return {
        "file": path.name,
        "sha256": _sha256(path),
        "rows": len(std),
        "mapping": mapping,
        "period_min": std["period"].dropna().min() if std["period"].notna().any() else None,
        "period_max": std["period"].dropna().max() if std["period"].notna().any() else None,
        "missing_product_code": int(std["product_code"].isna().sum()),
        "missing_sales_qty": int(std["sales_qty"].isna().sum()),
        "missing_sales_amount": int(std["sales_amount"].isna().sum()),
        "duplicate_rows": int(std.duplicated(["period", "product_code", "customer_name"], keep=False).sum()),
        "data": std,
    }
