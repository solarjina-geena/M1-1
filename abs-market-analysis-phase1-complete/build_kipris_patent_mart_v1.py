from pathlib import Path
import os, re, time, hashlib
import xml.etree.ElementTree as ET
from urllib.parse import urlencode
from urllib.request import Request, urlopen
import pandas as pd
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent
load_dotenv(ROOT / ".env")
KEY = (os.getenv("KIPRIS_API_KEY") or "").strip()
if not KEY:
    raise RuntimeError("KIPRIS_API_KEY가 없습니다.")

RAW = ROOT / "data" / "raw" / "kipris" / "full_v1"
MART = ROOT / "data" / "mart"
RAW.mkdir(parents=True, exist_ok=True)
MART.mkdir(parents=True, exist_ok=True)

BASE = "https://plus.kipris.or.kr/kipo-api/kipi/patUtiModInfoSearchSevice/getAdvancedSearch"
ROWS = 100
MAX_PAGES = 100  # 안전상한. 검색별 최대 10,000건.

SEARCHES = {
    "ABS": [
        ("잠김 방지 브레이크", "브레이크"),
        ("ABS 브레이크", "잠김"),
        ("안티록 브레이크", "브레이크"),
    ],
    "ESC": [
        ("차체 자세 제어", "제동"),
        ("전자 안정성 제어", "차량"),
        ("주행 안정 제어", "브레이크"),
    ],
    "INTEGRATED_BRAKE": [
        ("통합 제동", "제동"),
        ("통합 브레이크", "제동"),
        ("통합형 브레이크", "차량"),
    ],
    "BBW_EMB": [
        ("브레이크 바이 와이어", "제동"),
        ("Brake-by-Wire", "brake"),
        ("전자기계식 브레이크", "제동"),
        ("전기기계식 브레이크", "제동"),
    ],
}

POS = {
    "ABS": [r"안티.?록", r"anti.?lock", r"\bABS\b.{0,40}(브레이크|제동)",
            r"(브레이크|제동).{0,40}\bABS\b", r"잠김.?방지.{0,20}(브레이크|제동)"],
    "ESC": [r"전자.{0,12}안정성.{0,12}제어", r"electronic stability",
            r"차체.{0,12}자세.{0,12}제어", r"주행.{0,12}안정.{0,12}제어"],
    "INTEGRATED_BRAKE": [r"통합.{0,12}(제동|브레이크)", r"(제동|브레이크).{0,12}통합",
                         r"integrated.{0,16}(brake|braking)"],
    "BBW_EMB": [r"브레이크.?바이.?와이어", r"brake.?by.?wire",
                r"(전자|전기)기계식.{0,12}(브레이크|제동)",
                r"electro.?mechanical.{0,16}brake", r"electromechanical.{0,16}brake"],
}
NEG = {
    # V2에서 확인된 오분류 차단: parking brake의 '잠김 방지'는 ABS로 세지 않음.
    "ABS": [r"주차.?브레이크.{0,15}잠김.?방지", r"파킹.?브레이크.{0,15}잠김.?방지"],
    "ESC": [],
    "INTEGRATED_BRAKE": [],
    "BBW_EMB": [],
}

def tag(e): return e.tag.split("}",1)[-1] if "}" in e.tag else e.tag
def text_of(parent, name):
    for e in parent.iter():
        if tag(e) == name:
            return (e.text or "").strip()
    return ""

def fetch(title, abstract_word, page):
    params = {
        "inventionTitle": title, "astrtCont": abstract_word,
        "patent": "true", "utility": "false",
        "pageNo": page, "numOfRows": ROWS,
        "sortSpec": "AD", "descSort": "true",
        "ServiceKey": KEY,
    }
    req = Request(BASE + "?" + urlencode(params), headers={"User-Agent":"Mozilla/5.0"})
    with urlopen(req, timeout=40) as r:
        return r.read()

def parse(xml):
    root = ET.fromstring(xml)
    total = next((int((e.text or "0").strip() or 0) for e in root.iter() if tag(e)=="totalCount"), 0)
    out=[]
    for item in [e for e in root.iter() if tag(e)=="item"]:
        out.append({
            "title": text_of(item,"inventionTitle"),
            "ipc": text_of(item,"ipcNumber"),
            "application_number": text_of(item,"applicationNumber"),
            "application_date": text_of(item,"applicationDate"),
            "open_number": text_of(item,"openNumber"),
            "open_date": text_of(item,"openDate"),
            "register_number": text_of(item,"registerNumber"),
            "register_date": text_of(item,"registerDate"),
            "register_status": text_of(item,"registerStatus"),
            "abstract": text_of(item,"astrtCont"),
            "applicant": text_of(item,"applicantName"),
        })
    return total,out

records=[]; logs=[]
for tech,pairs in SEARCHES.items():
    for title,abst in pairs:
        first=fetch(title,abst,1)
        total,rows=parse(first)
        pages=min(MAX_PAGES, max(1,(total+ROWS-1)//ROWS))
        safe=re.sub(r"[^0-9A-Za-z가-힣_-]+","_",title)
        (RAW/f"{tech}_{safe}_p001.xml").write_bytes(first)
        for r in rows:
            r.update({"query_technology":tech,"title_query":title,"abstract_query":abst})
            records.append(r)
        for page in range(2,pages+1):
            xml=fetch(title,abst,page)
            (RAW/f"{tech}_{safe}_p{page:03d}.xml").write_bytes(xml)
            _,rows=parse(xml)
            for r in rows:
                r.update({"query_technology":tech,"title_query":title,"abstract_query":abst})
                records.append(r)
            time.sleep(.12)
        logs.append({"technology":tech,"title_query":title,"abstract_query":abst,
                     "total_count":total,"pages":pages})
        time.sleep(.15)

raw=pd.DataFrame(records)
log=pd.DataFrame(logs)
log.to_csv(RAW/"kipris_full_query_log.csv",index=False,encoding="utf-8-sig")

if raw.empty:
    raise RuntimeError("KIPRIS 전체 검색 결과가 0건입니다.")

# 동일 출원번호는 검색어가 달라도 하나의 특허로 취급.
raw=raw.drop_duplicates(["application_number","title"],keep="first").copy()
combined=(raw["title"].fillna("")+" "+raw["abstract"].fillna("")).str.replace(r"\s+"," ",regex=True)

def strict_match(tech, txt, ipc):
    pos=any(re.search(p,txt,re.I) for p in POS[tech])
    neg=any(re.search(p,txt,re.I) for p in NEG[tech])
    ipc_ok=bool(re.search(r"\bB60T",ipc or "",re.I))
    if tech=="ESC":
        ipc_ok=bool(re.search(r"\bB60[WT]",ipc or "",re.I))
    return pos and ipc_ok and not neg

raw["strict_pass"]=[strict_match(t,x,i) for t,x,i in zip(raw.query_technology,combined,raw.ipc.fillna(""))]
raw["application_year"]=pd.to_numeric(raw["application_date"].astype(str).str[:4],errors="coerce").astype("Int64")
raw["required_fields"]=(
    raw["application_date"].fillna("").ne("") &
    raw["title"].fillna("").ne("") &
    raw["ipc"].fillna("").ne("") &
    raw["applicant"].fillna("").ne("")
)
raw["strict_pass"] = raw["strict_pass"] & raw["required_fields"]
raw.to_csv(RAW/"kipris_patents_full_review.csv",index=False,encoding="utf-8-sig")

valid=raw[raw["strict_pass"] & raw["application_year"].notna()].copy()
valid["technology"]=valid["query_technology"]
valid["source"]="KIPRIS_PLUS"
valid["verification_status"]="RULE_VERIFIED"

# 한 특허가 여러 기술 검색에 잡힌 경우 기술별 신호는 유지하되 같은 기술 내 중복은 제거.
valid=valid.drop_duplicates(["technology","application_number"],keep="first")
valid.to_csv(MART/"patent_signals.csv",index=False,encoding="utf-8-sig")

annual=(valid.groupby(["application_year","technology"],as_index=False)
        .agg(patent_count=("application_number","nunique")))
annual["application_year"]=annual["application_year"].astype(int)
annual=annual.sort_values(["application_year","technology"])
annual.to_csv(MART/"patent_annual.csv",index=False,encoding="utf-8-sig")

app=(valid.assign(applicant=valid["applicant"].fillna("").str.split("|"))
     .explode("applicant"))
app["applicant"]=app["applicant"].str.strip()
app=app[app["applicant"].ne("")]
top=(app.groupby(["technology","applicant"],as_index=False)
     .agg(patent_count=("application_number","nunique"))
     .sort_values(["technology","patent_count"],ascending=[True,False]))
top["rank"]=top.groupby("technology")["patent_count"].rank(method="first",ascending=False).astype(int)
top=top[top["rank"]<=10]
top.to_csv(MART/"patent_top_applicants.csv",index=False,encoding="utf-8-sig")

print("="*100)
print("KIPRIS FULL EXTRACTION + STRICT CLASSIFICATION COMPLETE")
print("="*100)
print("RAW UNIQUE      :",len(raw))
print("STRICT PASS     :",len(valid))
print("REVIEW/EXCLUDED :",len(raw)-int(raw["strict_pass"].sum()))
print("YEAR RANGE      :",f"{valid.application_year.min()} ~ {valid.application_year.max()}" if len(valid) else "NONE")
print("\n=== STRICT PASS BY TECHNOLOGY ===")
print(valid.groupby("technology").size().to_string() if len(valid) else "NONE")
print("\n=== RECENT 10 YEARS ===")
recent=annual[annual.application_year >= max(annual.application_year.max()-9,0)] if len(annual) else annual
print(recent.pivot(index="application_year",columns="technology",values="patent_count").fillna(0).astype(int).to_string() if len(recent) else "NONE")
print("\nOUTPUT:")
print(" -",MART/"patent_signals.csv")
print(" -",MART/"patent_annual.csv")
print(" -",MART/"patent_top_applicants.csv")
print("※ market_monthly / technology_signal / 기존 MASTER 변경 없음")
print("="*100)
