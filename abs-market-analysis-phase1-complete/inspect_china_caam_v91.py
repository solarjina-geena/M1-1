from pathlib import Path
import pandas as pd, requests, re
from bs4 import BeautifulSoup

ROOT=Path(__file__).resolve().parent
G=ROOT/"data"/"global"
AUD=G/"china_caam_audit_v9.csv"
H={"User-Agent":"Mozilla/5.0 abs-market-analysis/1.0"}

urls=[]
if AUD.exists():
    a=pd.read_csv(AUD)
    if "url" in a:
        urls=[u for u in a["url"].dropna().astype(str).unique() if u.startswith("http")]

# V9 audit가 비었거나 목록 페이지뿐이면 구조가 검증된 CAAM 공식 샘플 사용
fallback=[
"https://en.caam.org.cn/Index/show/catid/63/id/2003.html", # Production Dec 2023
"https://en.caam.org.cn/Index/show/catid/64/id/2015.html", # Sales Dec 2023
"https://en.caam.org.cn/Index/show/catid/57/id/1866.html", # Production Dec 2022
"https://en.caam.org.cn/Index/show/catid/58/id/1878.html", # Sales Dec 2022
]
for u in fallback:
    if u not in urls: urls.append(u)
urls=urls[:8]

rows=[]
print("="*96)
print("CHINA CAAM LIGHT STRUCTURE V9.1")
print("="*96)
for u in urls:
    try:
        r=requests.get(u,headers=H,timeout=30); r.raise_for_status()
        s=BeautifulSoup(r.text,"html.parser")
        title=(s.title.get_text(" ",strip=True) if s.title else "")
        text=s.get_text(" ",strip=True)
        # Cars 뒤 첫 숫자, Unit 표기, title만 검사
        unit=re.search(r"Unit\s*:\s*([^|]{1,30})",text,re.I)
        car=re.search(r"(?:^|\s)Cars\s*(?:\||｜)?\s*([0-9]+(?:\.[0-9]+)?)",text,re.I)
        rows.append([u,title,unit.group(1).strip() if unit else "",car.group(1) if car else "",
                     text[:1200]])
        print("\nTITLE:",title[:140])
        print("UNIT :",unit.group(1).strip() if unit else "NOT FOUND")
        print("CARS :",car.group(1) if car else "NOT FOUND")
    except Exception as e:
        rows.append([u,"ERROR","","",str(e)])
        print("\nERROR:",u,e)

out=pd.DataFrame(rows,columns=["url","title","unit","cars_volume","preview"])
out.to_csv(G/"china_caam_structure_v91.csv",index=False,encoding="utf-8-sig")
print("\nOUTPUT:",G/"china_caam_structure_v91.csv")
print("PAGES READ:",len(out))
print("※ 전체 CAAM 크롤링 없음. 최대 8개 샘플 페이지만 읽음.")
print("="*96)
