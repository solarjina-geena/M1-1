from pathlib import Path
import pandas as pd

ROOT=Path(__file__).resolve().parent
G=ROOT/"data"/"global"
SRC=G/"global_market_dashboard_ready.csv"
if not SRC.exists():
    raise FileNotFoundError(f"{SRC}\n먼저 validate_global_market_v1.py를 실행하세요.")

d=pd.read_csv(SRC,parse_dates=["period"])
d["value"]=pd.to_numeric(d["value"],errors="coerce")

# 각 시장군/지표의 전체 대표국가 수
base=(d.groupby(["market_group","metric"])["country_code"].nunique()
        .rename("base_countries").reset_index())

# 월별 실제 포함국가 수와 합계
a=(d.dropna(subset=["value"])
     .groupby(["period","market_group","metric"],as_index=False)
     .agg(value=("value","sum"),
          included_countries=("country_code","nunique"),
          actual_rows=("value_status",lambda s:(s=="ACTUAL").sum()),
          estimated_rows=("value_status",lambda s:(s=="ESTIMATED").sum())))

a=a.merge(base,on=["market_group","metric"],how="left")
a["coverage_pct"]=(a["included_countries"]/a["base_countries"]*100).round(1)
a["estimated_pct"]=((a["estimated_rows"]/(a["actual_rows"]+a["estimated_rows"]).replace(0,pd.NA))*100).round(1)

# 핵심 보완: 70% 미만이면 시장군 합계를 대시보드에서 사용 금지.
a["aggregate_status"]=a["coverage_pct"].apply(lambda x:"USE" if x>=70 else "HIDE")
a["display_value"]=a["value"].where(a["aggregate_status"].eq("USE"))
a["coverage_note"]=a.apply(
    lambda r:f"{int(r.included_countries)}/{int(r.base_countries)}개국 집계 · 커버리지 {r.coverage_pct:.1f}%"
             +("" if r.aggregate_status=="USE" else " · 합계 숨김"),
    axis=1)

a.to_csv(G/"global_market_group_monthly_v2.csv",index=False,encoding="utf-8-sig")

# 고정 비교군: 최신 공통월을 찾고 그 월에 값이 있는 국가만 선정
fixed=[]
for (grp,met),g in d.groupby(["market_group","metric"]):
    countries=sorted(g.country_code.unique())
    pivot=g.pivot_table(index="period",columns="country_code",values="value",aggfunc="first")
    counts=pivot.notna().sum(axis=1)
    threshold=max(1,int((len(countries)*0.7)+0.999999))
    eligible=counts[counts>=threshold]
    if len(eligible):
        common_month=eligible.index.max()
        keep=sorted(pivot.columns[pivot.loc[common_month].notna()])
        fixed.append([grp,met,common_month,len(countries),len(keep),",".join(keep)])
fixed=pd.DataFrame(fixed,columns=["market_group","metric","reference_month","base_countries","fixed_countries","country_list"])
fixed.to_csv(G/"global_fixed_comparison_group.csv",index=False,encoding="utf-8-sig")

print("="*94)
print("GLOBAL COVERAGE V2 COMPLETE")
print("="*94)
print("RULE : 시장군 월별 커버리지 70% 이상만 합계 표시")
print("\n=== LATEST STATUS ===")
latest=a.sort_values("period").groupby(["market_group","metric"],as_index=False).tail(1)
print(latest[["period","market_group","metric","included_countries","base_countries","coverage_pct","aggregate_status","coverage_note"]].to_string(index=False))
print("\n=== FIXED COMPARISON GROUP ===")
print(fixed.to_string(index=False))
print("\nOUTPUT")
print(" -",G/"global_market_group_monthly_v2.csv")
print(" -",G/"global_fixed_comparison_group.csv")
print("\n※ 기존 MASTER와 dashboard_ready 파일은 수정하지 않았습니다.")
print("※ display_value가 NULL이면 대시보드에서 합계선을 그리지 않습니다.")
print("="*94)
