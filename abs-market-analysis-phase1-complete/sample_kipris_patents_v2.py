from pathlib import Path
import os, re, time
import xml.etree.ElementTree as ET
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError
import pandas as pd
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent
load_dotenv(ROOT / ".env")
KEY = (os.getenv("KIPRIS_API_KEY") or "").strip()
if not KEY:
    raise RuntimeError("KIPRIS_API_KEY가 없습니다.")

OUTDIR = ROOT / "data" / "raw" / "kipris" / "sample_v2"
OUTDIR.mkdir(parents=True, exist_ok=True)
BASE = "https://plus.kipris.or.kr/kipo-api/kipi/patUtiModInfoSearchSevice/getAdvancedSearch"

# V1의 word 자유검색은 검색범위가 지나치게 넓었음.
# V2는 공식 항목별 검색의 inventionTitle / astrtCont를 사용하고,
# 자동차 제동 IPC B60T를 결과 필터로 결합한다.
SEARCHES = {
    "ABS": [
        ("안티록 브레이크", "잠김 방지"),
        ("잠김 방지 브레이크", "브레이크"),
        ("ABS 브레이크", "잠김"),
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

RULES = {
    "ABS": [r"안티.?록", r"잠김.?방지", r"anti.?lock", r"\bABS\b.{0,40}(브레이크|제동)"],
    "ESC": [r"차체.{0,12}자세.{0,12}제어", r"전자.{0,12}안정성.{0,12}제어",
            r"주행.{0,12}안정.{0,12}제어", r"electronic stability"],
    "INTEGRATED_BRAKE": [r"통합.{0,12}(제동|브레이크)", r"(제동|브레이크).{0,12}통합",
                         r"integrated.{0,16}(brake|braking)"],
    "BBW_EMB": [r"브레이크.?바이.?와이어", r"brake.?by.?wire",
                r"(전자|전기)기계식.{0,12}(브레이크|제동)",
                r"electro.?mechanical.{0,16}brake", r"electromechanical.{0,16}brake"],
}

def strip_ns(tag): return tag.split("}",1)[-1] if "}" in tag else tag
def text_of(parent, name):
    for e in parent.iter():
        if strip_ns(e.tag) == name:
            return (e.text or "").strip()
    return ""
def request_xml(title, abstract_word, rows=12):
    params = {
        "inventionTitle": title,
        "astrtCont": abstract_word,
        "patent": "true", "utility": "false",
        "pageNo": 1, "numOfRows": rows,
        "sortSpec": "AD", "descSort": "true",
        "ServiceKey": KEY,
    }
    url = BASE + "?" + urlencode(params)
    req = Request(url, headers={"User-Agent":"Mozilla/5.0"})
    with urlopen(req, timeout=30) as r:
        return r.read()

def parse(data):
    root = ET.fromstring(data)
    total = next(((e.text or "").strip() for e in root.iter() if strip_ns(e.tag)=="totalCount"), "")
    rows=[]
    for item in [e for e in root.iter() if strip_ns(e.tag)=="item"]:
        rows.append({
            "title": text_of(item,"inventionTitle"),
            "ipc": text_of(item,"ipcNumber"),
            "application_number": text_of(item,"applicationNumber"),
            "application_date": text_of(item,"applicationDate"),
            "open_number": text_of(item,"openNumber"),
            "abstract": text_of(item,"astrtCont"),
            "applicant": text_of(item,"applicantName"),
            "register_status": text_of(item,"registerStatus"),
        })
    return total, rows

records=[]; logs=[]
for tech, pairs in SEARCHES.items():
    for title, abst in pairs:
        try:
            xml=request_xml(title,abst)
            safe=re.sub(r"[^0-9A-Za-z가-힣_-]+","_",title)
            (OUTDIR/f"{tech}_{safe}.xml").write_bytes(xml)
            total, rows=parse(xml)
            logs.append({"technology":tech,"title_query":title,"abstract_query":abst,
                         "total_count":total,"returned":len(rows),"status":"OK"})
            for r in rows:
                r.update({"query_technology":tech,"title_query":title,"abstract_query":abst})
                records.append(r)
            time.sleep(.15)
        except Exception as e:
            logs.append({"technology":tech,"title_query":title,"abstract_query":abst,
                         "total_count":"","returned":0,"status":f"ERROR: {e}"})

log=pd.DataFrame(logs)
df=pd.DataFrame(records)
if not df.empty:
    df=df.drop_duplicates(["application_number","title"],keep="first").copy()
    combined=(df["title"].fillna("")+" "+df["abstract"].fillna("")).str.replace(r"\s+"," ",regex=True)
    def hit(tech, txt):
        return any(re.search(p,txt,re.I) for p in RULES[tech])
    df["text_match"]=[hit(t,x) for t,x in zip(df["query_technology"],combined)]
    # B60T = vehicle brake control systems; allow B60W only for stability-control candidates
    df["brake_ipc"]=df["ipc"].fillna("").str.contains(r"\bB60T",case=False,regex=True)
    df["vehicle_control_ipc"]=df["ipc"].fillna("").str.contains(r"\bB60[WT]",case=False,regex=True)
    df["required_fields"]=(
        df["application_date"].fillna("").ne("") &
        df["title"].fillna("").ne("") &
        df["abstract"].fillna("").ne("") &
        df["ipc"].fillna("").ne("") &
        df["applicant"].fillna("").ne("")
    )
    df["sample_pass"]=df["text_match"] & df["required_fields"] & (
        df["brake_ipc"] | ((df["query_technology"]=="ESC") & df["vehicle_control_ipc"])
    )
    df["application_year"]=df["application_date"].astype(str).str[:4]
    df.to_csv(OUTDIR/"kipris_patent_sample_v2.csv",index=False,encoding="utf-8-sig")
log.to_csv(OUTDIR/"kipris_query_log_v2.csv",index=False,encoding="utf-8-sig")

print("="*100)
print("KIPRIS PATENT SAMPLE V2 - FIELD SEARCH + IPC FILTER")
print("="*100)
print(log.to_string(index=False))
print()
if df.empty:
    print("UNIQUE SAMPLE : 0")
    print("RESULT        : REVIEW REQUIRED")
else:
    print("UNIQUE SAMPLE :",len(df))
    print("PASS          :",int(df["sample_pass"].sum()))
    print("REVIEW        :",int((~df["sample_pass"]).sum()))
    print("\n=== PASS BY TECHNOLOGY ===")
    print(df.groupby("query_technology")["sample_pass"].agg(["count","sum"]).to_string())
    print("\n=== PASS SAMPLE ===")
    passed=df[df["sample_pass"]].groupby("query_technology",group_keys=False).head(4)
    show=["query_technology","application_date","title","applicant","ipc","application_number"]
    print(passed[show].to_string(index=False))
    print("\nOUTPUT :",OUTDIR/"kipris_patent_sample_v2.csv")
    print("※ 기존 sample/MART/MASTER 변경 없음")
print("="*100)
