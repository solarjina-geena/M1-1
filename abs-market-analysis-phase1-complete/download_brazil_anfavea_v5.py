from pathlib import Path
import re, sys, requests
from urllib.parse import urljoin
from bs4 import BeautifulSoup

ROOT=Path(__file__).resolve().parent
RAW=ROOT/"data"/"global"/"raw"/"brazil"
RAW.mkdir(parents=True,exist_ok=True)

PAGES=[
 "https://anfavea.com.br/site/page/3/",
 "https://anfavea.com.br/site/conteudos/carta-da-anfavea/",
 "https://anfavea.com.br/site/edicoes-em-excel/",
]
H={"User-Agent":"Mozilla/5.0 abs-market-analysis/1.0"}
candidates=[]
for page in PAGES:
    try:
        r=requests.get(page,headers=H,timeout=60); r.raise_for_status()
        soup=BeautifulSoup(r.text,"html.parser")
        for a in soup.find_all("a",href=True):
            href=urljoin(page,a["href"])
            text=" ".join(a.stripped_strings)
            if re.search(r"\.(xlsx?|csv)(\?|$)",href,re.I) or ("excel" in text.lower() and href):
                candidates.append((href,text,page))
    except Exception as e:
        print("PAGE WARN:",page,e)

# 중복 제거
seen=set(); uniq=[]
for x in candidates:
    if x[0] not in seen: seen.add(x[0]); uniq.append(x)

print("="*94)
print("ANFAVEA AUTO DOWNLOAD V5")
print("="*94)
print("EXCEL/CSV CANDIDATES:",len(uniq))
downloaded=[]
for i,(url,text,page) in enumerate(uniq,1):
    try:
        rr=requests.get(url,headers=H,timeout=90,allow_redirects=True); rr.raise_for_status()
        ctype=rr.headers.get("content-type","").lower()
        final=rr.url
        ext=".xlsx"
        m=re.search(r"\.(xlsx?|csv)(?:\?|$)",final,re.I)
        if m: ext="."+m.group(1).lower()
        # HTML 응답은 파일로 저장하지 않음
        if "text/html" in ctype and not re.search(r"\.(xlsx?|csv)",final,re.I):
            continue
        name=f"anfavea_auto_{i:02d}{ext}"
        fp=RAW/name; fp.write_bytes(rr.content)
        if fp.stat().st_size<5000:
            fp.unlink(missing_ok=True); continue
        downloaded.append((name,fp.stat().st_size,url,text))
        print("DOWNLOADED:",name,f"{fp.stat().st_size:,} bytes",text[:80])
    except Exception as e:
        print("DOWNLOAD WARN:",url,e)

print("\nRAW DIR:",RAW)
if not downloaded:
    print("\n자동 다운로드 가능한 Excel/CSV 직접 링크를 찾지 못했습니다.")
    print("ANFAVEA 사이트는 Excel 링크를 스크립트/버튼으로 제공할 수 있습니다.")
    print("이 경우 숫자를 만들지 않고 종료합니다.")
    sys.exit(2)

print("\nNEXT:")
print("python .\\import_brazil_anfavea_v4.py")
print("="*94)
