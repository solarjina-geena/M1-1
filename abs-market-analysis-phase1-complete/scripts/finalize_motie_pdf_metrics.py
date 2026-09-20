from pathlib import Path

import pandas as pd


BASE_DIR = Path(__file__).resolve().parents[1]

INPUT_FILE = (
    BASE_DIR
    / "data"
    / "raw"
    / "motie"
    / "motie_pdf_metrics_v2.csv"
)

OUTPUT_FILE = (
    BASE_DIR
    / "data"
    / "raw"
    / "motie"
    / "motie_pdf_metrics_final.csv"
)


# 공식 PDF 원문을 직접 확인하여 확정한 값
CORRECTIONS = {
    "2021-10": {
        "production": 263723,
        "domestic": 125296,
        "export": 159520,
    },
    "2022-01": {
        "production": 271054,
        "domestic": 111294,
        "export": 179709,
    },
    "2022-02": {
        "production": 263959,
        "domestic": 122929,
        "export": 167682,
    },
    "2022-05": {
        "production": 307048,
        "domestic": 145464,
        "export": 182869,
    },
    "2023-01": {
        "production": 306738,
        "domestic": 116565,
        "export": 200825,
    },
    "2023-02": {
        "production": 343575,
        "domestic": 147031,
        "export": 222934,
    },
}


def main():

    df = pd.read_csv(
        INPUT_FILE,
        dtype={"period": str},
    )

    # 추적용 컬럼
    df["final_status"] = "AUTO_EXTRACTED"
    df["final_note"] = ""

    # 직접 확인한 6개월 보정
    for period, values in CORRECTIONS.items():

        mask = df["period"] == period

        if not mask.any():
            print(f"WARNING: period not found: {period}")
            continue

        for metric, value in values.items():

            df.loc[mask, metric] = value

            source_col = f"{metric}_source"
            status_col = f"{metric}_status"

            if source_col in df.columns:
                df.loc[mask, source_col] = "manual_pdf_verified"

            if status_col in df.columns:
                df.loc[mask, status_col] = "VERIFIED_PDF"

        df.loc[mask, "final_status"] = "VERIFIED_PDF"
        df.loc[mask, "final_note"] = (
            "Official MOTIE PDF text manually verified"
        )

    # 2015-02:
    # PDF는 존재하지만 텍스트 레이어가 없어 자동 추출 불가
    mask = df["period"] == "2015-02"

    if mask.any():
        df.loc[mask, "final_status"] = "REVIEW_SCAN_PDF"
        df.loc[mask, "final_note"] = (
            "PDF exists but text extraction unavailable"
        )

    # 최종 완전성
    df["complete"] = (
        df["production"].notna()
        & df["domestic"].notna()
        & df["export"].notna()
    )

    # 범위 검사용
    df["range_check"] = "OK"

    checks = {
        "production": (100000, 600000),
        "domestic": (50000, 300000),
        "export": (70000, 400000),
    }

    for metric, (low, high) in checks.items():

        bad = (
            df[metric].notna()
            & ~df[metric].between(low, high)
        )

        df.loc[bad, "range_check"] = "REVIEW"

    df.to_csv(
        OUTPUT_FILE,
        index=False,
        encoding="utf-8-sig",
    )

    print("=" * 80)
    print("MOTIE FINAL METRICS")
    print("=" * 80)

    print("TOTAL       :", len(df))
    print("COMPLETE    :", int(df["complete"].sum()))
    print(
        "INCOMPLETE  :",
        int((~df["complete"]).sum()),
    )
    print(
        "RANGE REVIEW:",
        int((df["range_check"] == "REVIEW").sum()),
    )

    print()
    print("=== CORRECTED / REVIEW ROWS ===")

    target = list(CORRECTIONS.keys()) + ["2015-02"]

    cols = [
        "period",
        "production",
        "domestic",
        "export",
        "final_status",
        "range_check",
    ]

    print(
        df.loc[
            df["period"].isin(target),
            cols,
        ].to_string(index=False)
    )

    print()
    print("=== ALL INCOMPLETE ===")

    incomplete = df.loc[
        ~df["complete"],
        cols,
    ]

    if incomplete.empty:
        print("NONE")
    else:
        print(incomplete.to_string(index=False))

    print()
    print("OUTPUT:", OUTPUT_FILE)


if __name__ == "__main__":
    main()