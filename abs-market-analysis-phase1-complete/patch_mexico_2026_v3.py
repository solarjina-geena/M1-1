from pathlib import Path
import pandas as pd

ROOT=Path(__file__).resolve().parent
G=ROOT/"data"/"global"
SRC=G/"global_market_monthly_v2.csv"
if not SRC.exists(): raise FileNotFoundError(SRC)
d=pd.read_csv(SRC,parse_dates=["period"])

# INEGI RAIAVL 공식 표 (업데이트 2026-08-07): 2026-01~07
vals=[
("2026-01",131779,314317,237481),
("2026-02",118305,311457,247945),
("2026-03",131566,343505,310205),
("2026-04",118859,329878,286317),
("2026-05",127107,342926,306288),
("2026-06",126902,354221,301009),
("2026-07",130835,302673,261534),
]
rows=[]
for per,sales,prod,exp in vals:
    for metric,value,side in [("DOMESTIC_SALES",sales,"DEMAND"),("PRODUCTION",prod,"SUPPLY"),("EXPORT",exp,"EXPORT")]:
        rows.append(dict(period=pd.Timestamp(per+"-01"),country_code="MEX",market_group="중남미",
          group_tags="OECD",market_side=side,metric=metric,vehicle_scope="LIGHT_VEHICLE",
          value=value,value_status="ACTUAL",official_status="SOURCE_PUBLISHED",
          source="INEGI RAIAVL",source_url="https://www.inegi.org.mx/app/tabulados/default.html?nc=100100090_a",
          estimate_method="",note="INEGI 공식 월별 경량차 판매·생산·수출"))
add=pd.DataFrame(rows)
for c in d.columns:
    if c not in add: add[c]=""
add=add[d.columns]
out=pd.concat([d,add],ignore_index=True)
out=out.drop_duplicates(["period","country_code","metric","vehicle_scope"],keep="last").sort_values(["country_code","metric","period"])
out.to_csv(G/"global_market_monthly_v3.csv",index=False,encoding="utf-8-sig")

# coverage
res=[]
for keys,g in out.groupby(["country_code","market_group","metric","vehicle_scope"],dropna=False):
    cc,grp,met,scope=keys; s=g.set_index("period")["value"].sort_index()
    idx=pd.date_range(s.index.min(),s.index.max(),freq="MS"); z=s.reindex(idx)
    null=z.isna().mean()*100
    recent=z[z.index>=max(idx.min(),idx.max()-pd.DateOffset(years=3))]
    rnull=recent.isna().mean()*100 if len(recent) else 100
    res.append([cc,grp,met,scope,idx.min(),idx.max(),len(idx),z.notna().sum(),round(null,2),round(rnull,2),null<=30 and rnull<=30])
cov=pd.DataFrame(res,columns=["country_code","market_group","metric","vehicle_scope","start","end","calendar_months","observed_months","null_pct","recent_3y_null_pct","include_in_aggregate"])
cov.to_csv(G/"global_market_coverage_v3.csv",index=False,encoding="utf-8-sig")

print("="*94)
print("MEXICO 2026 OFFICIAL PATCH V3 COMPLETE")
print("="*94)
print("MEXICO ROWS ADDED/UPDATED:",len(add))
print("\n=== MEXICO 2026 ===")
print(add[["period","metric","value"]].to_string(index=False))
print("\n=== COVERAGE ===")
print(cov[cov.country_code.eq("MEX")].to_string(index=False))
print("\nOUTPUT")
print(" -",G/"global_market_monthly_v3.csv")
print(" -",G/"global_market_coverage_v3.csv")
print("\n※ 2026-01~07 멕시코는 공식 월별 값으로 교체/보완했습니다.")
print("※ 추정값 사용 없음.")
print("="*94)
