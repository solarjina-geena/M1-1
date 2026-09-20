"""사내 매출/판매 Excel 또는 CSV를 검사 후 표준 Parquet로 저장.

사용 예:
  python scripts/import_internal_sales.py D:/data/2026_08_sales.xlsx --preview
  python scripts/import_internal_sales.py D:/data/2026_08_sales.xlsx --commit

--commit 전에는 파일을 수정하지 않고 검사 결과만 출력한다.
"""
from __future__ import annotations
import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import pandas as pd
from loaders.internal_loader import inspect_sales_file


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("file")
    parser.add_argument("--preview", action="store_true")
    parser.add_argument("--commit", action="store_true")
    args = parser.parse_args()

    result = inspect_sales_file(args.file)
    print(f"파일: {result['file']}")
    print(f"행수: {result['rows']:,}")
    print(f"기간: {result['period_min']} ~ {result['period_max']}")
    print(f"자동매핑: {result['mapping']}")
    print(f"품번 누락: {result['missing_product_code']:,}")
    print(f"판매수량 누락: {result['missing_sales_qty']:,}")
    print(f"매출액 누락: {result['missing_sales_amount']:,}")
    print(f"중복 의심행: {result['duplicate_rows']:,}")
    print(f"SHA-256: {result['sha256']}")

    if args.preview:
        print("\n[미리보기]")
        print(result["data"].head(20).to_string(index=False))

    if args.commit:
        out_path = ROOT / "data" / "internal" / "mart" / "sales_monthly.parquet"
        out_path.parent.mkdir(parents=True, exist_ok=True)
        new = result["data"].copy()
        if out_path.exists():
            old = pd.read_parquet(out_path)
            combined = pd.concat([old, new], ignore_index=True)
        else:
            combined = new

        # 완전 동일 행 중복은 제거하지만 0/결측은 그대로 보존한다.
        combined = combined.drop_duplicates()
        combined.to_parquet(out_path, index=False)
        print(f"\n저장 완료: {out_path}")
        print(f"누적 행수: {len(combined):,}")


if __name__ == "__main__":
    main()
