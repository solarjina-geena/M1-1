from pathlib import Path
import pandas as pd, requests, re, urllib3
from bs4 import BeautifulSoup

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
ROOT=Path(__file__).resolve().parent
G=ROOT/"data"/"global"
OUT=G/"china_caam_structure_v92.csv"
H={"User-Agent":"Mozilla/5.0 abs-market-analysis/1.0"}

urls=[
"https://en.caam.org.cn/Index/show/catid/63/id/2003.html",
"https://en.caam.org.cn/Index/show/catid/64/id/2015.html",
"https://en.caam.org.cn/Index/show/catid/57/id/1866.html",
"https://en.caam.org.cn/Index/show/catid/58/id/1878.html",
]
rows=[]
print("="*96)
print("CHINA CAAM V9.2 - SSL WORKAROUND + STRUCTURE CHECK")
print("="*96)
print("NOTE: CAAM 서버 인증서 만료 때문에 해당 공식 도메인에 한해 verify=False 사용\n")
for u in urls:
    try:
        r=requests.get(u,headers=H,timeout=30,verify=False); r.raise_for_status()
        s=BeautifulSoup(r.text,"html.parser")
        title=s.title.get_text(" ",strip=True) if s.title else ""
        text=s.get_text(" ",strip=True)
        unit=re.search(r"Unit\s*:\s*([^|]{1,40})",text,re.I)
        # Cars 주변 문맥을 별도로 보존하여 다음 파서에서 정확한 위치를 고정
        m=re.search(r"(.{0,180}\bCars\b.{0,500})",text,re.I)
        ctx=m.group(1) if m else ""
        numbers=re.findall(r"\d+(?:\.\d+)?",ctx)
        rows.append([u,r.status_code,title,unit.group(1).strip() if unit else "",ctx,numbers[:12]])
        print("OK   :",r.status_code,title[:100])
        print("UNIT :",unit.group(1).strip() if unit else "NOT FOUND")
        print("CARS :",ctx[:300] if ctx else "NOT FOUND")
        print()
    except Exception as e:
        rows.append([u,"ERROR","","","",str(e)])
        print("ERROR:",u,e)

pd.DataFrame(rows,columns=["url","http_status","title","unit","cars_context","numbers"]).to_csv(
    OUT,index=False,encoding="utf-8-sig")
print("OUTPUT:",OUT)
print("MASTER 변경: 없음")
print("="*96)
