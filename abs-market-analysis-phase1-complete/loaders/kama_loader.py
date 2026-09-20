"""KAMA 공개 월보 로더.

KAMA의 로그인 기반 통계 DB를 사용하지 않고, 공개 게시물의 월보 첨부파일을
원본(raw)으로 보관한 뒤 읽는 방식이다. 월보 양식은 시점에 따라 달라질 수 있으므로
시트 자동 추정 결과를 검증한 뒤 표준화한다.
"""
from __future__ import annotations
from pathlib import Path
import pandas as pd


def list_sheets(path: str | Path) -> list[str]:
    return pd.ExcelFile(path).sheet_names


def preview_sheet(path: str | Path, sheet_name=0, rows: int = 20) -> pd.DataFrame:
    return pd.read_excel(path, sheet_name=sheet_name, header=None, nrows=rows)


def find_candidate_sheets(path: str | Path, keywords=("생산", "내수", "수출")) -> dict[str, list[str]]:
    xls = pd.ExcelFile(path)
    result = {k: [] for k in keywords}
    for sheet in xls.sheet_names:
        compact = str(sheet).replace(" ", "")
        for k in keywords:
            if k in compact:
                result[k].append(sheet)
    return result
