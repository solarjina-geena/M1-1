from pathlib import Path
from io import StringIO
import pandas as pd, requests

ROOT=Path(__file__).resolve().parent
OUT=ROOT/"data"/"global"; RAW=OUT/"raw"
OUT.mkdir(parents=True,exist_ok=True); RAW.mkdir(parents=True,exist_ok=True)
START="2016-01"; LIMIT=30.0
GROUPS={"USA":"선진시장","CAN":"선진시장","DEU":"선진시장","FRA":"선진시장","GBR":"선진시장","ITA":"선진시장","ESP":"선진시장","JPN":"선진시장","KOR":"선진시장","AUS":"선진시장","NLD":"선진시장","BEL":"선진시장","SWE":"선진시장","NOR":"선진시장","CHE":"선진시장","CHN":"중국","IND":"성장아시아","IDN":"성장아시아","THA":"성장아시아","VNM":"성장아시아","BRA":"중남미","MEX":"중남미","ARG":"중남미","CHL":"중남미","COL":"중남미","SAU":"중동","ARE":"중동","KAZ":"중앙아시아/CIS","UZB":"중앙아시아/CIS","ZAF":"아프리카","EGY":"아프리카","MAR":"아프리카"}
OECD=set("AUS AUT BEL CAN CHL COL CRI CZE DNK EST FIN FRA DEU GRC HUN ISL IRL ISR ITA JPN KOR LVA LTU LUX MEX NLD NZL NOR POL PRT SVK SVN ESP SWE CHE TUR GBR USA".split())
BRICS=set("BRA RUS IND CHN ZAF EGY ETH IDN IRN ARE SAU".split())
def tags(c):
    return "|".join((["OECD"] if c in OECD else [])+(["BRICS"] if c in BRICS else []))
frames=[]; audit=[]
url="https://sdmx.oecd.org/public/rest/data/OECD.ITF,DSD_ST@DF_STREG,1.0/.M......?startPeriod="+START+"&dimensionAtObservation=AllDimensions&format=csvfilewithlabels"
try:
    r=requests.get(url,timeout=90,headers={"User-Agent":"abs-market-analysis/1.0"}); r.raise_for_status()
    (RAW/"oecd_first_registrations.csv").write_text(r.text,encoding="utf-8")
    d=pd.read_csv(StringIO(r.text))
    def pick(exact,contains):
        for c in d.columns:
            if str(c).upper()==exact: return c
        for c in d.columns:
            if contains in str(c).lower(): return c
    ca=pick("REF_AREA","reference area"); ct=pick("TIME_PERIOD","time period"); cv=pick("OBS_VALUE","observation value"); cf=pick("FREQ","frequency"); cveh=pick("VEHICLE_TYPE","vehicle type")
    if not ca or not ct or not cv: raise RuntimeError("필수 컬럼 탐색 실패: "+",".join(map(str,d.columns)))
    x=d.copy()
    if cf: x=x[x[cf].astype(str).str.upper().isin(["M","MONTHLY"])]
    x["country_code"]=x[ca].astype(str).str.upper().str.strip()
    x=x[x.country_code.isin(GROUPS)]
    x["period"]=pd.to_datetime(x[ct].astype(str),errors="coerce").dt.to_period("M").dt.to_timestamp()
    x["value"]=pd.to_numeric(x[cv],errors="coerce"); x=x.dropna(subset=["period","value"])
    x["market_group"]=x.country_code.map(GROUPS); x["group_tags"]=x.country_code.map(tags)
    x["market_side"]="DEMAND"; x["metric"]="FIRST_REGISTRATION"
    x["vehicle_scope"]=x[cveh].astype(str) if cveh else "SOURCE_DEFINED"
    x["value_status"]="ACTUAL"; x["official_status"]="SOURCE_PUBLISHED"; x["source"]="OECD/ITF"
    x["source_url"]="https://data-explorer.oecd.org/"; x["estimate_method"]=""
    x["note"]="국가기관 최초등록 신차; 원자료 차량범위 유지"
    cols=["period","country_code","market_group","group_tags","market_side","metric","vehicle_scope","value","value_status","official_status","source","source_url","estimate_method","note"]
    frames.append(x[cols]); audit.append(["OECD","OK",len(x),"월별 신차 최초등록"])
except Exception as e:
    audit.append(["OECD","ERROR",0,str(e)])

cols=["period","country_code","market_group","group_tags","market_side","metric","vehicle_scope","value","value_status","official_status","source","source_url","estimate_method","note"]
master=pd.concat(frames,ignore_index=True) if frames else pd.DataFrame(columns=cols)
if len(master): master=master.drop_duplicates(["period","country_code","metric","vehicle_scope"],keep="last").sort_values(["country_code","period"])
master.to_csv(OUT/"global_market_monthly.csv",index=False,encoding="utf-8-sig")

coverage=[]; missing=[]
if len(master):
    for keys,g in master.groupby(["country_code","market_group","metric","vehicle_scope"],dropna=False):
        cc,grp,met,scope=keys; s=g.set_index("period")["value"].sort_index()
        idx=pd.date_range(s.index.min(),s.index.max(),freq="MS"); z=s.reindex(idx)
        null=float(z.isna().mean()*100); recent=z[z.index>=max(idx.min(),idx.max()-pd.DateOffset(years=3))]
        rnull=float(recent.isna().mean()*100) if len(recent) else 100
        coverage.append([cc,grp,met,scope,idx.min(),idx.max(),len(idx),z.notna().sum(),round(null,2),round(rnull,2),null<=LIMIT and rnull<=LIMIT])
        for dt in z[z.isna()].index: missing.append([dt,cc,met,scope,"NULL","공식 월별 값 미확보; 0으로 대체하지 않음",""])
cov=pd.DataFrame(coverage,columns=["country_code","market_group","metric","vehicle_scope","start","end","calendar_months","observed_months","null_pct","recent_3y_null_pct","include_in_aggregate"])
cov.to_csv(OUT/"global_market_coverage.csv",index=False,encoding="utf-8-sig")
pd.DataFrame(missing,columns=["period","country_code","metric","vehicle_scope","status","note","estimate_basis"]).to_csv(OUT/"global_market_notes.csv",index=False,encoding="utf-8-sig")
pd.DataFrame([{"country_code":c,"market_group":g,"group_tags":tags(c)} for c,g in GROUPS.items()]).to_csv(OUT/"market_group_master.csv",index=False,encoding="utf-8-sig")
pd.DataFrame([
["OECD/ITF","선진시장","DEMAND","FIRST_REGISTRATION","API","ACTIVE","https://data-explorer.oecd.org/"],
["ANFAVEA","중남미","MULTI","PRODUCTION/REGISTRATION/EXPORT","MONTHLY","READY","https://anfavea.com.br/site/conteudos/carta-da-anfavea/"],
["INEGI","중남미","MULTI","PRODUCTION/SALES/EXPORT","MONTHLY","READY","https://www.inegi.org.mx/datosprimarios/iavl/default.html"],
["CAAM","중국","MULTI","PRODUCTION/SALES","MONTHLY","READY","https://www.caam.org.cn/chn/4/cate_31/list_1.html"]
],columns=["source","market_group","market_side","metric","access","status","source_url"]).to_csv(OUT/"global_source_registry.csv",index=False,encoding="utf-8-sig")
pd.DataFrame(audit,columns=["source","status","rows","message"]).to_csv(OUT/"global_build_audit.csv",index=False,encoding="utf-8-sig")
print("="*88); print("GLOBAL MARKET MASTER V1 BUILD COMPLETE"); print("="*88)
print("MASTER ROWS:",len(master)); print("COUNTRIES:",master.country_code.nunique() if len(master) else 0)
print(pd.DataFrame(audit,columns=["source","status","rows","message"]).to_string(index=False))
if len(cov):
    print("\nCOVERAGE")
    print(cov.groupby("market_group").agg(series=("country_code","size"),passed=("include_in_aggregate","sum"),avg_null_pct=("null_pct","mean")).round(2).to_string())
print("\nNULL은 0으로 채우지 않음 / 30% 초과 series는 합계 제외 / 추정값은 근거 확보 후에만 추가")
