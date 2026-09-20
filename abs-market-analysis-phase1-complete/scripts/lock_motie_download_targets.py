from pathlib import Path
import pandas as pd

SRC = Path("data/raw/motie/motie_33_download_targets.csv")
OUT = Path("data/raw/motie/motie_32_download_targets_verified.csv")

df = pd.read_csv(SRC, dtype=str, keep_default_na=False)

# 자동차산업 월간동향으로 강하게 검증된 후보만 사용
out = (
    df[df["validation"] == "STRONG"]
    .copy()
    .sort_values("period")
)

out.to_csv(
    OUT,
    index=False,
    encoding="utf-8-sig"
)

print("=" * 90)
print("VERIFIED DOWNLOAD TARGETS")
print("=" * 90)
print("TARGETS :", len(out))
print("FIRST   :", out["period"].min())
print("LAST    :", out["period"].max())
print()
print("PERIODS:")
print(" ".join(out["period"].tolist()))
print()
print("EXCLUDED:")
print(
    df[df["validation"] != "STRONG"]
    [["period", "validation", "title"]]
    .to_string(index=False)
)
print()
print("OUTPUT :", OUT)
