from pathlib import Path
import pandas as pd

ROOT=Path(__file__).resolve().parent
G=ROOT/"data"/"global"
MASTER=G/"global_market_monthly.csv"
COV=G/"global_market_coverage.csv"
if not MASTER.exists(): raise FileNotFoundError(MASTER)

m=pd.read_csv(MASTER,parse_dates=["period"])
cov=pd.read_csv(COV) if COV.exists() else pd.DataFrame()

# 핵심 검증: 같은 국가/월에 vehicle_scope가 여러 개면 절대 합산하지 않는다.
series=(m.groupby(["country_code","market_group","metric","vehicle_scope"],dropna=False)
          .agg(start=("period","min"),end=("period","max"),months=("period","nunique"),
               rows=("value","size"),actual=("value_status",lambda s:(s=="ACTUAL").sum()))
          .reset_index())

# 대시보드용 기본 series 선정:
# 국가별로 가장 길고 결측이 적은 단일 vehicle_scope만 선택.
if len(cov):
    q=cov.copy()
    q["include_in_aggregate"]=q["include_in_aggregate"].astype(str).str.lower().isin(["true","1"])
    q=q[q.include_in_aggregate]
    q=q.sort_values(["country_code","metric","null_pct","observed_months"],
                    ascending=[True,True,True,False])
    chosen=q.drop_duplicates(["country_code","metric"])[["country_code","metric","vehicle_scope"]]
else:
    chosen=(series.sort_values(["country_code","metric","months"],ascending=[True,True,False])
                  .drop_duplicates(["country_code","metric"])[["country_code","metric","vehicle_scope"]])

dash=m.merge(chosen,on=["country_code","metric","vehicle_scope"],how="inner")
dash=dash.sort_values(["market_group","country_code","period"])
dash.to_csv(G/"global_market_dashboard_ready.csv",index=False,encoding="utf-8-sig")

# 월별 시장군 합계. 단, 동일 metric/vehicle_scope가 아니라 국가별 대표 series만 합산.
agg=(dash.groupby(["period","market_group","metric"],as_index=False)
        .agg(value=("value","sum"),
             included_countries=("country_code","nunique"),
             estimated_rows=("value_status",lambda s:(s=="ESTIMATED").sum()),
             total_rows=("value","size")))
agg["estimated_pct"]=(agg.estimated_rows/agg.total_rows*100).round(2)
agg.to_csv(G/"global_market_group_monthly.csv",index=False,encoding="utf-8-sig")

print("="*92)
print("GLOBAL MASTER V1 VALIDATION COMPLETE")
print("="*92)
print("RAW ROWS       :",len(m))
print("COUNTRIES      :",m.country_code.nunique())
print("SERIES         :",len(series))
print("DASHBOARD ROWS :",len(dash))
print("\n=== COUNTRY LIST ===")
print(m.groupby("market_group")["country_code"].apply(lambda s:", ".join(sorted(s.unique()))).to_string())
print("\n=== VEHICLE SCOPE COUNT (중요) ===")
print(series.groupby(["market_group","country_code"]).size().sort_values(ascending=False).to_string())
print("\n=== DASHBOARD SELECTED SERIES ===")
print(chosen.sort_values(["country_code","metric"]).to_string(index=False))
print("\n=== GROUP MONTHLY COVERAGE (최근 월) ===")
latest=agg.sort_values("period").groupby(["market_group","metric"],as_index=False).tail(1)
print(latest[["period","market_group","metric","value","included_countries","estimated_pct"]].to_string(index=False))
print("\nOUTPUT:")
print(" -",G/"global_market_dashboard_ready.csv")
print(" -",G/"global_market_group_monthly.csv")
print("\n※ 이번 단계는 기존 MASTER를 수정하지 않습니다.")
print("※ 여러 vehicle_scope를 합산하지 않고 국가별 대표 series 1개만 선택했습니다.")
print("="*92)
