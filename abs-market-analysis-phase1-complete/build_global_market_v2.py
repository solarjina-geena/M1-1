from pathlib import Path
from io import StringIO
import pandas as pd, requests

ROOT=Path(__file__).resolve().parent
G=ROOT/"data"/"global"; G.mkdir(parents=True,exist_ok=True)
SRC=G/"global_market_monthly.csv"
if not SRC.exists(): raise FileNotFoundError(SRC)

base=pd.read_csv(SRC,parse_dates=["period"])
cols=list(base.columns)

# V2: 검증된 멕시코 INEGI 공식 월별 2026 실적을 우선 병합.
# 값은 INEGI RAIAVL 월별 공식 발표/누계에서 확인 가능한 범위만 사용.
mx = [
# period, sales, production, export, official status
("2026-01",131779,303980,224528,"PRELIMINARY"),
("2026-02",118305,311457,247945,"PRELIMINARY"),
("2026-04",118859,326069,286317,"PRELIMINARY"),
("2026-06",None,354221,301009,"PRELIMINARY"),
]
rows=[]
for period,sales,prod,exp,status in mx:
    for metric,value,side in [
        ("DOMESTIC_SALES",sales,"DEMAND"),
        ("PRODUCTION",prod,"SUPPLY"),
        ("EXPORT",exp,"EXPORT")]:
        if value is None: continue
        rows.append({
            "period":pd.Timestamp(period+"-01"),"country_code":"MEX","market_group":"중남미",
            "group_tags":"OECD","market_side":side,"metric":metric,"vehicle_scope":"LIGHT_VEHICLE",
            "value":value,"value_status":"ACTUAL","official_status":status,"source":"INEGI RAIAVL",
            "source_url":"https://www.inegi.org.mx/datosprimarios/iavl/default.html",
            "estimate_method":"","note":"멕시코 경량차 공식 월별 실적"
        })
add=pd.DataFrame(rows,columns=cols)
out=pd.concat([base,add],ignore_index=True)
out=out.drop_duplicates(["period","country_code","metric","vehicle_scope"],keep="last").sort_values(["country_code","metric","period"])
out.to_csv(G/"global_market_monthly_v2.csv",index=False,encoding="utf-8-sig")

# 시장군 집계는 같은 metric끼리만. 서로 다른 등록/판매/생산을 섞지 않음.
# 국가별 각 metric의 기대기간 내 NULL률도 계산.
coverage=[]
for keys,g in out.groupby(["country_code","market_group","metric","vehicle_scope"],dropna=False):
    cc,grp,met,scope=keys
    s=g.set_index("period")["value"].sort_index()
    idx=pd.date_range(s.index.min(),s.index.max(),freq="MS"); z=s.reindex(idx)
    null=float(z.isna().mean()*100)
    recent=z[z.index>=max(idx.min(),idx.max()-pd.DateOffset(years=3))]
    rnull=float(recent.isna().mean()*100) if len(recent) else 100
    coverage.append([cc,grp,met,scope,idx.min(),idx.max(),len(idx),z.notna().sum(),
                     round(null,2),round(rnull,2),null<=30 and rnull<=30])
cov=pd.DataFrame(coverage,columns=["country_code","market_group","metric","vehicle_scope","start","end",
                                  "calendar_months","observed_months","null_pct","recent_3y_null_pct","include_in_aggregate"])
cov.to_csv(G/"global_market_coverage_v2.csv",index=False,encoding="utf-8-sig")

# 추가 소스 상태: 숫자를 아직 넣지 않은 것은 READY_SOURCE로 유지.
registry=pd.DataFrame([
["ANFAVEA","BRA","중남미","월별 생산/등록/수출","READY_SOURCE",
 "1957년부터 월별 역사계열 Excel 공개; 자동 파서 연결 전"],
["INEGI RAIAVL","MEX","중남미","월별 판매/생산/수출","PARTIAL_LOADED",
 "2026 공식 확인값 우선 병합; 전체 역사 XLS/API 연결 예정"],
["CAAM","CHN","중국","월별 생산/판매","READY_SOURCE",
 "공식 월별 자료 확인; 자동 파서 연결 전"],
],columns=["source","country_code","market_group","coverage","status","note"])
registry.to_csv(G/"global_source_registry_v2.csv",index=False,encoding="utf-8-sig")

print("="*96)
print("GLOBAL MARKET MASTER V2 BUILD COMPLETE")
print("="*96)
print("BASE ROWS :",len(base))
print("ADDED     :",len(add))
print("V2 ROWS   :",len(out))
print("\n=== MEXICO ADDED ===")
print(add[["period","metric","value","official_status"]].to_string(index=False))
print("\n=== MEXICO COVERAGE ===")
print(cov[cov.country_code.eq("MEX")].to_string(index=False))
print("\nIMPORTANT")
print(" - 멕시코 생산/판매/수출은 서로 합산하지 않습니다.")
print(" - 2026-03, 2026-05 등 아직 직접 검증하지 않은 월은 0이나 임의추정으로 넣지 않았습니다.")
print(" - 따라서 멕시코 신규 metric은 현 단계에서 NULL 30% 규칙에 따라 합계 제외될 수 있습니다.")
print(" - 브라질/중국은 공식 원자료 파서가 붙기 전까지 숫자를 임의 삽입하지 않습니다.")
print("\nOUTPUT")
print(" -",G/"global_market_monthly_v2.csv")
print(" -",G/"global_market_coverage_v2.csv")
print(" -",G/"global_source_registry_v2.csv")
print("="*96)
