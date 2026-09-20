from pathlib import Path
import pandas as pd

ROOT=Path(__file__).resolve().parent
G=ROOT/"data"/"global"
SRC=G/"global_market_monthly_v4.csv"
if not SRC.exists(): raise FileNotFoundError(SRC)

d=pd.read_csv(SRC,parse_dates=["period"])
d["value"]=pd.to_numeric(d["value"],errors="coerce")

# 1) 브라질 월 연속성/결측 검증
res=[]
for (cc,grp,met,scope),g in d[d.country_code.eq("BRA")].groupby(
    ["country_code","market_group","metric","vehicle_scope"],dropna=False):
    s=g.groupby("period")["value"].last().sort_index()
    idx=pd.date_range(s.index.min(),s.index.max(),freq="MS")
    z=s.reindex(idx)
    res.append([cc,grp,met,scope,idx.min(),idx.max(),len(idx),z.notna().sum(),
                round(z.isna().mean()*100,2),",".join(x.strftime("%Y-%m") for x in z[z.isna()].index)])
cov=pd.DataFrame(res,columns=["country_code","market_group","metric","vehicle_scope","start","end",
                              "calendar_months","observed_months","null_pct","missing_months"])
cov["include_in_aggregate"]=cov["null_pct"]<=30
cov.to_csv(G/"brazil_coverage_v83.csv",index=False,encoding="utf-8-sig")

# 2) 중남미 국가/지표 현황. 서로 다른 metric은 합산하지 않는다.
lat=d[d.market_group.eq("중남미")].copy()
status=(lat.groupby(["country_code","metric","vehicle_scope"],dropna=False)
       .agg(start=("period","min"),end=("period","max"),rows=("value","count"))
       .reset_index())
status.to_csv(G/"latam_series_status_v83.csv",index=False,encoding="utf-8-sig")

# 3) 수요계열 비교용 매핑: CHL FIRST_REGISTRATION, MEX DOMESTIC_SALES, BRA DOMESTIC_REGISTRATION
demand_map={"CHL":"FIRST_REGISTRATION","MEX":"DOMESTIC_SALES","BRA":"DOMESTIC_REGISTRATION"}
q=[]
for cc,met in demand_map.items():
    g=lat[(lat.country_code.eq(cc)) & (lat.metric.eq(met))].copy()
    if len(g):
        q.append(g.assign(comparable_axis="VEHICLE_DEMAND"))
q=pd.concat(q,ignore_index=True) if q else pd.DataFrame()
if len(q):
    q.to_csv(G/"latam_demand_comparable_v83.csv",index=False,encoding="utf-8-sig")

print("="*96)
print("BRAZIL + LATAM VALIDATION V8.3 COMPLETE")
print("="*96)
print("\n=== BRAZIL COVERAGE ===")
print(cov.to_string(index=False))
print("\n=== LATAM SERIES ===")
print(status.to_string(index=False))
print("\nRULE")
print(" - 브라질 NULL <=30%인 지표만 집계 후보")
print(" - 칠레 등록 / 멕시코 판매 / 브라질 등록은 '수요 추세 비교축'으로만 묶음")
print(" - 세 지표를 절대수량 하나로 단순 합산하지 않음")
print(" - 생산/수출은 별도 축 유지")
print("\nOUTPUT")
print(" -",G/"brazil_coverage_v83.csv")
print(" -",G/"latam_series_status_v83.csv")
if len(q): print(" -",G/"latam_demand_comparable_v83.csv")
print("="*96)
