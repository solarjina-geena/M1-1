from pathlib import Path
import re, requests, urllib3, pandas as pd
from bs4 import BeautifulSoup
from urllib.parse import urljoin

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
ROOT=Path(__file__).resolve().parent
G=ROOT/"data"/"global"; RAW=G/"raw"/"china"; RAW.mkdir(parents=True,exist_ok=True)
SRC=G/"global_market_monthly_v4.csv"
if not SRC.exists(): raise FileNotFoundError(SRC)

H={"User-Agent":"Mozilla/5.0 abs-market-analysis/1.0"}
# CAAM 공식 상세자료가 있는 카테고리 주변 목록만 제한 탐색
starts=[
"https://en.caam.org.cn/Index/lists/catid/63.html",
"https://en.caam.org.cn/Index/lists/catid/64.html",
"https://en.caam.org.cn/Index/lists/catid/57.html",
"https://en.caam.org.cn/Index/lists/catid/58.html",
]
links=[]
for u in starts:
    try:
        r=requests.get(u,headers=H,timeout=30,verify=False)
        if r.status_code!=200: continue
        s=BeautifulSoup(r.text,"html.parser")
        for a in s.find_all("a",href=True):
            title=" ".join(a.stripped_strings)
            href=urljoin(u,a["href"])
            if re.search(r"(Production|Sales) of Automobiles in [A-Za-z]+ 20\d{2}",title,re.I):
                links.append((href,title))
    except Exception:
        pass

# 이미 검증된 상세페이지도 반드시 포함
links += [
("https://en.caam.org.cn/Index/show/catid/63/id/2003.html","Production of Automobiles in December 2023"),
("https://en.caam.org.cn/Index/show/catid/64/id/2015.html","Sales of Automobiles in December 2023"),
("https://en.caam.org.cn/Index/show/catid/57/id/1866.html","Production of Automobiles in December 2022"),
("https://en.caam.org.cn/Index/show/catid/58/id/1878.html","Sales of Automobiles in December 2022"),
]
seen=set(); uniq=[]
for u,t in links:
    if u not in seen: seen.add(u); uniq.append((u,t))

months={m:i for i,m in enumerate(
["January","February","March","April","May","June","July","August","September","October","November","December"],1)}
rows=[]; audit=[]
for u,hint in uniq:
    try:
        r=requests.get(u,headers=H,timeout=30,verify=False); r.raise_for_status()
        s=BeautifulSoup(r.text,"html.parser")
        title=s.title.get_text(" ",strip=True) if s.title else hint
        mt=re.search(r"(Production|Sales) of Automobiles in ([A-Za-z]+) (20\d{2})",title,re.I)
        if not mt:
            mt=re.search(r"(Production|Sales) of Automobiles in ([A-Za-z]+) (20\d{2})",hint,re.I)
        if not mt or mt.group(2).title() not in months:
            audit.append([u,title,"REVIEW","date/title parse fail"]); continue
        kind,mon,year=mt.group(1).lower(),mt.group(2).title(),int(mt.group(3))
        text=s.get_text(" ",strip=True)
        # 검증된 구조: "Cars 당월 누계 MoM YoY 누계YoY"
        m=re.search(r"\bCars\s+([0-9]+(?:\.[0-9]+)?)\s+([0-9]+(?:\.[0-9]+)?)\s+[-+]?[0-9.]+\s+[-+]?[0-9.]+\s+[-+]?[0-9.]+",text,re.I)
        if not m:
            audit.append([u,title,"REVIEW","Cars row parse fail"]); continue
        current=float(m.group(1)); ytd=float(m.group(2))
        metric="PRODUCTION" if kind=="production" else "DOMESTIC_SALES"
        side="SUPPLY" if kind=="production" else "DEMAND"
        rows.append(dict(period=pd.Timestamp(year,months[mon],1),country_code="CHN",market_group="중국",
            group_tags="BRICS",market_side=side,metric=metric,vehicle_scope="TOTAL_VEHICLES",
            value=round(current*10000),value_status="ACTUAL",official_status="SOURCE_PUBLISHED",
            source="CAAM",source_url=u,estimate_method="",
            note=f"CAAM 공식 Total Cars; 당월 {current}만대; 누계 {ytd}만대"))
        audit.append([u,title,"PARSED",f"current={current}; ytd={ytd}"])
    except Exception as e:
        audit.append([u,hint,"ERROR",str(e)])

aud=pd.DataFrame(audit,columns=["url","title","status","detail"])
aud.to_csv(G/"china_caam_audit_v93.csv",index=False,encoding="utf-8-sig")
add=pd.DataFrame(rows)
if add.empty:
    print("CHINA CAAM V9.3: 안전하게 추출된 값 없음 / MASTER 변경 없음")
    print("AUDIT:",G/"china_caam_audit_v93.csv"); raise SystemExit(2)

add=add.drop_duplicates(["period","country_code","metric","vehicle_scope"],keep="last").sort_values(["metric","period"])
base=pd.read_csv(SRC,parse_dates=["period"])
for c in base.columns:
    if c not in add: add[c]=""
add=add[base.columns]
out=pd.concat([base,add],ignore_index=True)
out=out.drop_duplicates(["period","country_code","metric","vehicle_scope"],keep="last").sort_values(["country_code","metric","period"])
out.to_csv(G/"global_market_monthly_v5.csv",index=False,encoding="utf-8-sig")

# 실제 관측 구간 내 결측률
cv=[]
for met,g in add.groupby("metric"):
    s=g.groupby("period")["value"].last().sort_index()
    idx=pd.date_range(s.index.min(),s.index.max(),freq="MS"); z=s.reindex(idx)
    cv.append([met,idx.min(),idx.max(),len(idx),z.notna().sum(),round(z.isna().mean()*100,2)])
cov=pd.DataFrame(cv,columns=["metric","start","end","calendar_months","observed_months","null_pct"])
cov.to_csv(G/"china_caam_coverage_v93.csv",index=False,encoding="utf-8-sig")

print("="*96)
print("CHINA CAAM MONTHLY V9.3 COMPLETE")
print("="*96)
print("DETAIL PAGES :",len(uniq))
print("ROWS ADDED   :",len(add))
print("\n=== CHINA COVERAGE ===")
print(cov.to_string(index=False))
print("\n=== SAMPLE ===")
print(add[["period","metric","value","note"]].tail(12).to_string(index=False))
print("\nOUTPUT")
print(" -",G/"global_market_monthly_v5.csv")
print(" -",G/"china_caam_audit_v93.csv")
print(" -",G/"china_caam_coverage_v93.csv")
print("※ SSL 우회는 CAAM 공식 도메인에만 적용 / 추정값 없음")
print("="*96)
