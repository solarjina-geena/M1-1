from pathlib import Path
import pandas as pd

ROOT=Path(__file__).resolve().parent
G=ROOT/"data"/"global"
SRC=G/"global_market_monthly_v5.csv"
if not SRC.exists(): raise FileNotFoundError(SRC)

# CAAM 공식 월별/산업운영 페이지에서 직접 확인한 2023 월값.
# 1~8월은 생산/판매 모두 확보. 9~12월 판매는 월별 상세표 확보.
data=[
("2023-01-01",1594000,1649000,"https://en.caam.org.cn/Index/show/catid/44/id/2088.html"),
("2023-02-01",2032000,1976000,"https://en.caam.org.cn/Index/show/catid/44/id/2089.html"),
("2023-03-01",2584000,2451000,"https://en.caam.org.cn/Index/show/catid/44/id/2090.html"),
("2023-04-01",2133000,2159000,"https://en.caam.org.cn/Index/show/catid/44/id/2091.html"),
("2023-05-01",2333000,2382000,"https://en.caam.org.cn/Index/show/catid/63/id/2010.html"),
("2023-06-01",2561000,2622000,"https://en.caam.org.cn/Index/show/catid/44/id/2092.html"),
("2023-07-01",2401000,2387000,"https://en.caam.org.cn/Index/show/catid/63/id/2008.html"),
("2023-08-01",2575000,2582000,"https://en.caam.org.cn/Index/show/catid/63/id/2007.html"),
]
sales_extra=[
("2023-09-01",2858000,"https://en.caam.org.cn/Index/show/catid/64/id/2018.html"),
("2023-10-01",2853000,"https://en.caam.org.cn/Index/show/catid/64/id/2017.html"),
("2023-11-01",2970000,"https://en.caam.org.cn/Index/show/catid/64/id/2016.html"),
("2023-12-01",3156000,"https://en.caam.org.cn/Index/show/catid/64/id/2015.html"),
]
rows=[]
for dt,prod,sales,url in data:
    for metric,val,side in [("PRODUCTION",prod,"SUPPLY"),("DOMESTIC_SALES",sales,"DEMAND")]:
        rows.append([pd.Timestamp(dt),"CHN","중국","BRICS",side,metric,"TOTAL_VEHICLES",val,
                     "ACTUAL","SOURCE_PUBLISHED","CAAM",url,"","CAAM 공식 월별/산업운영 자료"])
for dt,val,url in sales_extra:
    rows.append([pd.Timestamp(dt),"CHN","중국","BRICS","DEMAND","DOMESTIC_SALES","TOTAL_VEHICLES",val,
                 "ACTUAL","SOURCE_PUBLISHED","CAAM",url,"","CAAM 공식 월별 Total Cars"])

cols=["period","country_code","market_group","group_tags","market_side","metric","vehicle_scope","value",
"value_status","official_status","source","source_url","estimate_method","note"]
add=pd.DataFrame(rows,columns=cols)
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
    # 2023만 별도 판정: 2022-12 한 점 때문에 결측률을 왜곡하지 않음
    s23=s[(s.index>=pd.Timestamp("2023-01-01"))&(s.index<=pd.Timestamp("2023-12-01"))]
    idx=pd.date_range("2023-01-01","2023-12-01",freq="MS"); z=s23.reindex(idx)
    cv.append([met,"2023",12,z.notna().sum(),round(z.isna().mean()*100,2),
               ",".join(x.strftime("%Y-%m") for x in z[z.isna()].index)])
cov=pd.DataFrame(cv,columns=["metric","period_scope","calendar_months","observed_months","null_pct","missing_months"])
cov.to_csv(G/"china_caam_coverage_v95.csv",index=False,encoding="utf-8-sig")

print("="*96)
print("CHINA CAAM FAST MERGE V9.5 COMPLETE")
print("="*96)
print("WEB CRAWL REQUESTS : 0")
print("ROWS PATCHED       :",len(add))
print("\n=== 2023 COVERAGE ===")
print(cov.to_string(index=False))
print("\nOUTPUT")
print(" -",G/"global_market_monthly_v6.csv")
print(" -",G/"china_caam_coverage_v95.csv")
print("\n※ 2023 판매는 12/12개월 확보")
print("※ 생산은 현재 8/12개월 확보; 30% 기준 판정 후 필요한 경우 누락월만 보완")
print("※ 추정값 없음")
print("="*96)
