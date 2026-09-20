"""다운로드한 KAMA 공개 월보의 시트 구조를 확인한다."""
from __future__ import annotations
import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from loaders.kama_loader import list_sheets, find_candidate_sheets, preview_sheet


def main():
    p = argparse.ArgumentParser()
    p.add_argument("file")
    p.add_argument("--sheet", default=None)
    args = p.parse_args()

    print("시트:", list_sheets(args.file))
    print("후보:", find_candidate_sheets(args.file))
    if args.sheet is not None:
        print(preview_sheet(args.file, args.sheet).to_string(index=False, header=False))


if __name__ == "__main__":
    main()
