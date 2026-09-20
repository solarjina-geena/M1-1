from pathlib import Path
import re, requests, urllib3, pandas as pd
from bs4 import BeautifulSoup

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
ROOT=Path(__file__).resolve().parent
G=ROOT/"data"/"global"
SRC=G/"global_market_monthly_v5.csv"
if not SRC.exists(): raise FileNotFoundError(SRC)

H={"User-Agent":"Mozilla/5.0 abs-market-analysis/1.0"}
# CAAM 상세 페이지 ID는 연속성이 높으므로 검증된 페이지 주변만 제한 탐색.
# 전체 사이트 크롤링이 아니라 2022/2023 검증 ID 주변의 소수 범위.
ranges=[(1840,2035)]
rows=[]; audit=[]
months={m:i for i,m in enumerate(
["January","February","March","April","May","June","July","August","September","October","November","December"],1)}

for ident in range(ranges[0][0],ranges[0][1]+1):
    # catid는 실제 검증된 월별 production/sales 카테고리들만 시도
    for cat in [57,58,63,64]:
        u=f"https://en.caam.org.cn/Index/show/catid/{cat}/id/{ident}.html"
        try:
            r=requests.get(u,headers=H,timeout=10,verify=False)
            if r.status_code!=200: continue
            s=BeautifulSoup(r.text,"html.parser")
            title=s.title.get_text(" ",strip=True) if s.title else ""
            mt=re.search(r"(Production|Sales) of Automobiles in ([A-Za-z]+) (20\d{2})",title,re.I)
            if not mt: continue
            kind,mon,year=mt.group(1).lower(),mt.group(2).title(),int(mt.group(3))
            if mon not in months or year not in [2022,2023]: continue
            text=s.get_text(" ",strip=True)
            m=re.search(r"\bCars\s+([0-9]+(?:\.[0-9]+)?)\s+([0-9]+(?:\.[0-9]+)?)\s+[-+]?[0-9.]+\s+[-+]?[0-9.]+\s+[-+]?[0-9.]+",text,re.I)
            if not m: continue
            current,ytd=float(m.group(1)),float(m.group(2))
            metric="PRODUCTION" if kind=="production" else "DOMESTIC_SALES"
            side="SUPPLY" if kind=="production" else "DEMAND"
            rows.append(dict(period=pd.Timestamp(year,months[mon],1),country_code="CHN",market_group="중국",
                group_tags="BRICS",market_side=side,metric=metric,vehicle_scope="TOTAL_VEHICLES",
                value=round(current*10000),value_status="ACTUAL",official_status="SOURCE_PUBLISHED",
                source="CAAM",source_url=u,estimate_method="",
                note=f"CAAM Total Cars; 당월 {current}만대; 누계 {ytd}만대"))
            audit.append([ident,cat,title,"PARSED",current,ytd,u])
        except Exception:
            pass

add=pd.DataFrame(rows)
if add.empty:
    print("CHINA CAAM V9.4: 추가 월 발견 실패 / MASTER 변경 없음")
    raise SystemExit(2)

add=add.drop_duplicates(["period","metric"],keep="last").sort_values(["metric","period"])
pd.DataFrame(audit,columns=["id","catid","title","status","current_10k","ytd_10k","url"]).to_csv(
    G/"china_caam_audit_v94.csv",index=False,encoding="utf-8-sig")

base=pd.read_csv(SRC,parse_dates=["period"])
for c in base.columns:
    if c not in add: add[c]=""
add=add[base.columns]
out=pd.concat([base,add],ignore_index=True)
out=out.drop_duplicates(["period","country_code","metric","vehicle_scope"],keep="last").sort_values(["country_code","metric","period"])
out.to_csv(G/"global_market_monthly_v6.csv",index=False,encoding="utf-8-sig")

cv=[]
for met,g in out[out.country_code.eq("CHN")].groupby("metric"):
    s=g.groupby("period")["value"].last().sort_index()
    idx=pd.date_range(s.index.min(),s.index.max(),freq="MS"); z=s.reindex(idx)
    cv.append([met,idx.min(),idx.max(),len(idx),z.notna().sum(),round(z.isna().mean()*100,2),
               ",".join(x.strftime("%Y-%m") for x in z[z.isna()].index)])
cov=pd.DataFrame(cv,columns=["metric","start","end","calendar_months","observed_months","null_pct","missing_months"])
cov.to_csv(G/"china_caam_coverage_v94.csv",index=False,encoding="utf-8-sig")

print("="*96)
print("CHINA CAAM HISTORY V9.4 COMPLETE")
print("="*96)
print("UNIQUE MONTHLY ROWS FOUND:",len(add))
print("\n=== COVERAGE ===")
print(cov.to_string(index=False))
print("\nOUTPUT")
print(" -",G/"global_market_monthly_v6.csv")
print(" -",G/"china_caam_audit_v94.csv")
print(" -",G/"china_caam_coverage_v94.csv")
print("※ 2022~2023 CAAM 공식 상세페이지 주변만 제한 탐색")
print("※ 추정값 없음 / Total Cars만 사용")
print("="*96)
