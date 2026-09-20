from pathlib import Path
import pandas as pd

OUT = Path("data/raw/motie/motie_manual_body_verified.csv")

row = {
    "period": "2015-02",
    "production": 317746,
    "domestic": 120812,
    "export": 211596,
    "verification_status": "BODY_VERIFIED",
    "verification_method": "MOTIE_WEB_BODY_AND_ATTACHMENT_PREVIEW",
    "source_title": "'15년 2월 자동차 산업 동향",
    "source_date": "2015-03-09",
    "source_url": "https://www.motie.go.kr/kor/article/ATCL3f49a5a8c/157048/view",
    "note": "본문 및 자동차산업 총괄표에서 생산/내수/수출 확인"
}

if OUT.exists():
    df = pd.read_csv(OUT, dtype={"period": str})
    df = df[df["period"] != row["period"]]
    df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)
else:
    df = pd.DataFrame([row])

df = df.sort_values("period")
df.to_csv(OUT, index=False, encoding="utf-8-sig")

print("=" * 80)
print("BODY VERIFIED DATA")
print("=" * 80)
print(df.to_string(index=False))
print()
print("TOTAL :", len(df))
print("OUTPUT:", OUT)
print()
print("2015-02 >>> BODY_VERIFIED <<<")
print("MASTER >>> NOT YET MERGED <<<")
