from pathlib import Path
import json
import pandas as pd

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "dashboard_data_audit.txt"

def section(title):
    return "\n" + "=" * 100 + f"\n{title}\n" + "=" * 100 + "\n"

def inspect_parquet(relpath):
    p = ROOT / relpath
    lines = [f"FILE: {relpath}", f"EXISTS: {p.exists()}"]
    if not p.exists():
        return "\n".join(lines)
    try:
        df = pd.read_parquet(p)
        lines += [
            f"ROWS: {len(df):,}",
            f"COLUMNS ({len(df.columns)}): {list(df.columns)}",
            "\nDTYPES:",
            df.dtypes.to_string(),
            "\nNULL COUNT:",
            df.isna().sum().to_string(),
        ]
        for col in ["period", "period_dt", "date", "year", "metric", "technology", "technology_code",
                    "source", "source_type", "company", "status", "is_estimated"]:
            if col in df.columns:
                vals = df[col].dropna()
                lines.append(f"\n[{col}] UNIQUE={vals.nunique()}")
                lines.append(str(vals.astype(str).drop_duplicates().head(30).tolist()))
        lines.append("\nHEAD(12):")
        lines.append(df.head(12).to_string(index=False))
        lines.append("\nTAIL(12):")
        lines.append(df.tail(12).to_string(index=False))
    except Exception as e:
        lines.append(f"ERROR: {type(e).__name__}: {e}")
    return "\n".join(lines)

def inspect_csv(relpath):
    p = ROOT / relpath
    lines = [f"FILE: {relpath}", f"EXISTS: {p.exists()}"]
    if not p.exists():
        return "\n".join(lines)
    try:
        df = pd.read_csv(p, encoding="utf-8-sig")
        lines += [
            f"ROWS: {len(df):,}",
            f"COLUMNS ({len(df.columns)}): {list(df.columns)}",
            "\nHEAD(10):",
            df.head(10).to_string(index=False),
        ]
    except Exception:
        try:
            df = pd.read_csv(p)
            lines += [
                f"ROWS: {len(df):,}",
                f"COLUMNS ({len(df.columns)}): {list(df.columns)}",
                "\nHEAD(10):",
                df.head(10).to_string(index=False),
            ]
        except Exception as e:
            lines.append(f"ERROR: {type(e).__name__}: {e}")
    return "\n".join(lines)

def inspect_code(relpath):
    p = ROOT / relpath
    lines = [f"FILE: {relpath}", f"EXISTS: {p.exists()}"]
    if not p.exists():
        return "\n".join(lines)
    try:
        text = p.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        text = p.read_text(encoding="cp949", errors="replace")
    lines.append(f"LINES: {len(text.splitlines())}")
    lines.append(text)
    return "\n".join(lines)

parts = []
parts.append(section("1. MARKET MART") + inspect_parquet("data/mart/market_monthly.parquet"))
parts.append(section("2. TECHNOLOGY SIGNAL MART") + inspect_parquet("data/mart/technology_signal.parquet"))

for rel in [
    "data/metadata/technology_master.csv",
    "data/metadata/technology_signal_master.csv",
    "data/metadata/market_assumption_master.csv",
    "data/metadata/source_log.csv",
    "data/metadata/model_technology_map.csv",
    "data/metadata/company_master.csv",
]:
    parts.append(section("METADATA") + inspect_csv(rel))

for rel in [
    "processors/market_mart.py",
    "processors/technology_signal_mart.py",
    "collectors/technical_source_collector.py",
    "config/sources.py",
    "config/settings.py",
    "dashboard/app.py",
]:
    parts.append(section("CODE") + inspect_code(rel))

OUT.write_text("\n".join(parts), encoding="utf-8")
print("=" * 72)
print("DASHBOARD DATA AUDIT COMPLETE")
print(f"OUTPUT : {OUT}")
print("NEXT   : dashboard_data_audit.txt 파일만 ChatGPT에 업로드")
print("=" * 72)
