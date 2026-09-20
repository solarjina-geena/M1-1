from pathlib import Path
import sys
import pandas as pd

# ============================================================
# 경로
# ============================================================
BASE = Path(__file__).resolve().parent

SCRIPTS = BASE / "scripts"
RECOVERED_TEXT = (
    BASE
    / "data"
    / "raw"
    / "motie"
    / "monthly_pdf"
    / "recovered_text"
)

OUTPUT = (
    BASE
    / "data"
    / "raw"
    / "motie"
    / "motie_recovered_metrics_verified.csv"
)

# ============================================================
# V2 LOCKED 로직만 사용
# ============================================================
sys.path.insert(0, str(SCRIPTS))

import build_motie_pdf_master_v2_locked as v2


# 현재 살아남은 검증 대상 월
TARGET_PERIODS = {
    "2015-04",
    "2015-06",
    "2015-07",
    "2015-08",
    "2015-09",
    "2015-10",
    "2015-11",
    "2016-03",
    "2016-04",
    "2016-08",
    "2016-09",
    "2016-10",
    "2017-02",
    "2017-05",
    "2017-09",
    "2017-12",
    "2018-05",
    "2022-12",
    "2023-03",
    "2023-04",
    "2023-05",
    "2024-03",
    "2024-12",
}


def main():

    print("=" * 100)
    print("RECOVERED METRIC CHECK - V2 LOCKED")
    print("=" * 100)

    print("V2 MODULE :", Path(v2.__file__).name)
    print("TEXT DIR  :", RECOVERED_TEXT)
    print()

    rows = []

    for period in sorted(TARGET_PERIODS):

        path = RECOVERED_TEXT / f"{period}.txt"

        if not path.exists():

            rows.append({
                "period": period,
                "production": None,
                "domestic": None,
                "export": None,
                "production_status": "TEXT_MISSING",
                "domestic_status": "TEXT_MISSING",
                "export_status": "TEXT_MISSING",
            })

            print(
                f"{period} | "
                f"P=None D=None E=None | TEXT_MISSING"
            )

            continue

        text = path.read_text(
            encoding="utf-8",
            errors="replace",
        )

        metrics = v2.extract_metrics(text)

        row = {
            "period": period,
            **metrics,
        }

        rows.append(row)

        print(
            f"{period} | "
            f"P={metrics.get('production')} "
            f"D={metrics.get('domestic')} "
            f"E={metrics.get('export')} | "
            f"{metrics.get('production_status')} "
            f"{metrics.get('domestic_status')} "
            f"{metrics.get('export_status')}"
        )

    df = pd.DataFrame(rows)

    # --------------------------------------------------------
    # 완전성
    # --------------------------------------------------------
    metric_cols = [
        "production",
        "domestic",
        "export",
    ]

    df["complete"] = (
        df[metric_cols]
        .notna()
        .all(axis=1)
    )

    # 같은 3개 값이 여러 월에 존재하는지 검사
    df["duplicate_metrics"] = False

    complete_df = df[df["complete"]].copy()

    if not complete_df.empty:

        dup_mask = complete_df.duplicated(
            subset=metric_cols,
            keep=False,
        )

        dup_periods = set(
            complete_df.loc[
                dup_mask,
                "period"
            ]
        )

        df.loc[
            df["period"].isin(dup_periods),
            "duplicate_metrics"
        ] = True

    # --------------------------------------------------------
    # 저장
    # --------------------------------------------------------
    OUTPUT.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    df.to_csv(
        OUTPUT,
        index=False,
        encoding="utf-8-sig",
    )

    print()
    print("=" * 100)
    print("RESULT")
    print("=" * 100)

    print("TARGET     :", len(df))
    print("COMPLETE   :", int(df["complete"].sum()))
    print(
        "INCOMPLETE :",
        int((~df["complete"]).sum())
    )
    print(
        "DUPLICATE  :",
        int(df["duplicate_metrics"].sum())
    )

    print()

    review = df[
        (~df["complete"])
        | (df["duplicate_metrics"])
    ]

    if len(review):

        print("=== REVIEW ===")

        cols = [
            "period",
            "production",
            "domestic",
            "export",
            "production_status",
            "domestic_status",
            "export_status",
            "duplicate_metrics",
        ]

        print(
            review[cols]
            .to_string(index=False)
        )

    else:

        print("REVIEW : NONE")

    print()
    print("OUTPUT :", OUTPUT)


if __name__ == "__main__":
    main()