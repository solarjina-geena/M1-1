from pathlib import Path
import re, requests, pandas as pd
from bs4 import BeautifulSoup
from urllib.parse import urljoin

ROOT=Path(__file__).resolve().parent
G=ROOT/"data"/"global"; RAW=G/"raw"/"china"; RAW.mkdir(parents=True,exist_ok=True)
SRC=G/"global_market_monthly_v4.csv"
if not SRC.exists(): raise FileNotFoundError(SRC)

# CAAM 영문 공식 사이트의 Production/Sales 월별 표 페이지를 가볍게 탐색.
# 전체 사이트 크롤링 대신 검색엔진 없이 CAAM 목록/알려진 카테고리만 제한 호출.
H={"User-Agent":"Mozilla/5.0 abs-market-analysis/1.0"}
starts=[
 "https://en.caam.org.cn/Index/lists/catid/76.html", # recent sales
 "https://en.caam.org.cn/Index/lists/catid/75.html", # recent production 후보
 "https://en.caam.org.cn/Index/lists/catid/63.html",
]
links=[]
for u in starts:
    try:
        r=requests.get(u,headers=H,timeout=30)
        if r.status_code!=200: continue
        s=BeautifulSoup(r.text,"html.parser")
        for a in s.find_all("a",href=True):
            txt=" ".join(a.stripped_strings)
            href=urljoin(u,a["href"])
            if re.search(r"(Sales|Production) of Automobiles in",txt,re.I):
                links.append((href,txt))
    except: pass

# 중복 제거, 최대 80페이지만
seen=set(); uniq=[]
for x in links:
    if x[0] not in seen:
        seen.add(x[0]); uniq.append(x)
uniq=uniq[:80]

rows=[]; audit=[]
months={m:i for i,m in enumerate(["January","February","March","April","May","June","July","August","September","October","November","December"],1)}
for url,title in uniq:
    mt=re.search(r"(Sales|Production) of Automobiles in ([A-Za-z]+) (20\d{2})",title,re.I)
    if not mt: continue
    kind,mon,year=mt.group(1).upper(),mt.group(2).title(),int(mt.group(3))
    if mon not in months: continue
    try:
        r=requests.get(url,headers=H,timeout=30); r.raise_for_status()
        text=BeautifulSoup(r.text,"html.parser").get_text(" ",strip=True)
        # 공식 표에서 Cars 행: Volume | Jan—...; 첫 숫자가 당월 총 자동차.
        # Unit: 10000이므로 10,000대 단위 -> 대 단위 변환.
        m=re.search(r"Cars\s*[|｜]?\s*([0-9]+(?:\.[0-9]+)?)",text,re.I)
        if not m:
            audit.append([title,url,"REVIEW","Cars Volume parse fail"]); continue
        val=round(float(m.group(1))*10000)
        metric="DOMESTIC_SALES" if kind=="SALES" else "PRODUCTION"
        side="DEMAND" if kind=="SALES" else "SUPPLY"
        rows.append(dict(period=pd.Timestamp(year,months[mon],1),country_code="CHN",market_group="중국",
            group_tags="BRICS",market_side=side,metric=metric,vehicle_scope="TOTAL_VEHICLES",
            value=val,value_status="ACTUAL",official_status="SOURCE_PUBLISHED",source="CAAM",
            source_url=url,estimate_method="",note=f"CAAM {title}; unit 10,000 vehicles"))
        audit.append([title,url,"PARSED",val])
    except Exception as e:
        audit.append([title,url,"ERROR",str(e)])

add=pd.DataFrame(rows)
pd.DataFrame(audit,columns=["title","url","status","detail"]).to_csv(G/"china_caam_audit_v9.csv",index=False,encoding="utf-8-sig")
if add.empty:
    print("="*94); print("CHINA CAAM V9 - NO SAFE AUTO PARSE"); print("="*94)
    print("CAAM 페이지는 확인됐지만 현재 HTML에서 안전한 표 자동추출에 실패했습니다.")
    print("MASTER 변경 없음.")
    print("AUDIT:",G/"china_caam_audit_v9.csv")
    raise SystemExit(2)

add=add.drop_duplicates(["period","country_code","metric","vehicle_scope"],keep="last")
base=pd.read_csv(SRC,parse_dates=["period"])
for c in base.columns:
    if c not in add: add[c]=""
add=add[base.columns]
out=pd.concat([base,add],ignore_index=True)
out=out.drop_duplicates(["period","country_code","metric","vehicle_scope"],keep="last").sort_values(["country_code","metric","period"])
out.to_csv(G/"global_market_monthly_v5.csv",index=False,encoding="utf-8-sig")

print("="*94)
print("CHINA CAAM MONTHLY V9 COMPLETE")
print("="*94)
print("PAGES FOUND :",len(uniq))
print("ROWS ADDED  :",len(add))
print("\n=== CHINA RANGE ===")
print(add.groupby("metric").agg(start=("period","min"),end=("period","max"),months=("period","nunique")).to_string())
print("\nOUTPUT")
print(" -",G/"global_market_monthly_v5.csv")
print(" -",G/"china_caam_audit_v9.csv")
print("\n※ CAAM 공식 페이지의 Total Cars Volume만 사용")
print("※ 단위 10,000대를 실제 대수로 환산")
print("※ 판매와 생산은 별도 지표, 추정값 없음")
print("="*94)
