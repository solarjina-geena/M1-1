from pathlib import Path
import pandas as pd

ROOT=Path(__file__).resolve().parent
G=ROOT/"data"/"global"
SRC=G/"global_market_monthly_v6.csv"
if not SRC.exists(): raise FileNotFoundError(SRC)

# SIAM 공식 무료 Press Release에서 직접 공개된 월별 값.
# Production은 PV만이 아니라 PV+3W+2W+Quadricycle 총생산이므로 별도 scope로 명시.
data=[
("2025-12-01",2633506,399216,"https://www.siam.in/pressrelease-details.aspx?mpgid=53&pgidtrail=50&pid=595"),
("2026-01-01",2927394,449616,"https://www.siam.in/pressrelease-details.aspx?mpgid=48&pgidtrail=50&pid=597"),
("2026-02-01",2864612,417705,"https://www.siam.in/pressrelease-details.aspx?mpgid=53&pgidtrail=50&pid=603"),
("2026-03-01",2978173,442460,"https://www.siam.in/pressrelease-details.aspx?pid=605"),
("2026-04-01",2922427,437312,"https://www.siam.in/pressrelease-details.aspx?mpgid=53&pgidtrail=50&pid=607"),
("2026-05-01",2927711,438854,"https://www.siam.in/pressrelease-details.aspx?mpgid=53&pgidtrail=50&pid=609"),
("2026-06-01",3015528,388144,"https://www.siam.in/pressrelease-details.aspx?pid=610"),
("2026-07-01",3370958,457810,"https://www.siam.in/news-%26-updates/press-releases/auto-industry-performance-of-july-2026/612"),
("2026-08-01",3157822,439309,"https://www.siam.in/pressrelease-details.aspx?mpgid=53&pgidtrail=50&pid=620"),
]
rows=[]
for dt,prod,pv_sales,url in data:
    rows += [
      [pd.Timestamp(dt),"IND","인도","BRICS|성장아시아","SUPPLY","PRODUCTION",
       "PV_3W_2W_QUAD_TOTAL",prod,"ACTUAL","SOURCE_PUBLISHED","SIAM",url,"",
       "SIAM 무료 월간 보도자료 총생산; PV+3W+2W+Quadricycle"],
      [pd.Timestamp(dt),"IND","인도","BRICS|성장아시아","DEMAND","DOMESTIC_SALES",
       "PASSENGER_VEHICLES",pv_sales,"ACTUAL","SOURCE_PUBLISHED","SIAM",url,"",
       "SIAM 무료 월간 보도자료 Passenger Vehicles 국내판매"],
    ]
cols=["period","country_code","market_group","group_tags","market_side","metric","vehicle_scope","value",
"value_status","official_status","source","source_url","estimate_method","note"]
add=pd.DataFrame(rows,columns=cols)

base=pd.read_csv(SRC,parse_dates=["period"])
for c in base.columns:
    if c not in add: add[c]=""
add=add[base.columns]
out=pd.concat([base,add],ignore_index=True)
out=out.drop_duplicates(["period","country_code","metric","vehicle_scope"],keep="last")
out=out.sort_values(["country_code","metric","vehicle_scope","period"])
out.to_csv(G/"global_market_monthly_v7.csv",index=False,encoding="utf-8-sig")

cv=[]
for (met,scope),g in add.groupby(["metric","vehicle_scope"]):
    s=g.groupby("period")["value"].last().sort_index()
    idx=pd.date_range(s.index.min(),s.index.max(),freq="MS")
    z=s.reindex(idx)
    cv.append([met,scope,idx.min(),idx.max(),len(idx),z.notna().sum(),round(z.isna().mean()*100,2)])
cov=pd.DataFrame(cv,columns=["metric","vehicle_scope","start","end","calendar_months","observed_months","null_pct"])
cov.to_csv(G/"india_siam_coverage_v10.csv",index=False,encoding="utf-8-sig")

print("="*100)
print("INDIA SIAM OFFICIAL PATCH V10 COMPLETE")
print("="*100)
print("WEB CRAWL REQUESTS : 0")
print("ROWS ADDED         :",len(add))
print("\n=== INDIA COVERAGE ===")
print(cov.to_string(index=False))
print("\nIMPORTANT")
print(" - DOMESTIC_SALES = Passenger Vehicles만")
print(" - PRODUCTION = PV+3W+2W+Quadricycle 총생산 (판매와 scope 다름)")
print(" - 두 값을 서로 합산하거나 같은 절대규모 축으로 비교하지 않음")
print(" - SIAM 상세 월간 Production & Sales 데이터셋은 유료이므로 사용하지 않음")
print(" - 추정값 없음")
print("\nOUTPUT")
print(" -",G/"global_market_monthly_v7.csv")
print(" -",G/"india_siam_coverage_v10.csv")
print("="*100)
