from pathlib import Path
import re, sys, requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

ROOT=Path(__file__).resolve().parent
RAW=ROOT/"data"/"global"/"raw"/"brazil"
RAW.mkdir(parents=True,exist_ok=True)
BASE="https://anfavea.com.br/site/conteudos/carta-da-anfavea/"
H={"User-Agent":"Mozilla/5.0 abs-market-analysis/1.0"}

r=requests.get(BASE,headers=H,timeout=60); r.raise_for_status()
s=BeautifulSoup(r.text,"html.parser")
links=[]
for a in s.find_all("a",href=True):
    u=urljoin(BASE,a["href"])
    txt=" ".join(a.stripped_strings)
    if ".pdf" in u.lower() or "pdf" in txt.lower():
        links.append((u,txt))
# Search fallback: current known Carta numbering around 2026.
for n in range(476,486):
    links.append((f"https://www.anfavea.com.br/cartas/carta{n}.pdf",f"carta{n}"))

seen=set(); ok=[]
for u,txt in links:
    if u in seen: continue
    seen.add(u)
    try:
        q=requests.get(u,headers=H,timeout=60)
        if q.status_code!=200 or len(q.content)<20000 or not q.content.startswith(b"%PDF"): continue
        m=re.search(r"carta(\d+)",u,re.I)
        name=(f"carta{m.group(1)}.pdf" if m else f"anfavea_{len(ok)+1:02d}.pdf")
        fp=RAW/name; fp.write_bytes(q.content)
        ok.append((name,len(q.content),u))
        print("DOWNLOADED",name,f"{len(q.content):,} bytes")
    except Exception as e:
        pass
print("="*92)
print("ANFAVEA PDF DOWNLOAD V6 COMPLETE")
print("PDF FILES:",len(ok))
print("RAW DIR  :",RAW)
if not ok:
    print("공식 PDF 자동 다운로드 실패. 숫자 생성 없이 종료.")
    sys.exit(2)
print("\nNEXT: PDF 원문을 기준으로 월별/누계 표 추출 및 교차검증")
print("="*92)
