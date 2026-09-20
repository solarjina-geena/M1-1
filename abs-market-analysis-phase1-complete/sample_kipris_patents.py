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

OUTDIR = ROOT / "data" / "raw" / "kipris" / "sample"
OUTDIR.mkdir(parents=True, exist_ok=True)

BASE = "https://plus.kipris.or.kr/kipo-api/kipi/patUtiModInfoSearchSevice/getAdvancedSearch"

# 'ABS'처럼 약어만 검색하면 전혀 관계없는 특허가 많이 섞일 수 있으므로
# 기술명/관련 표현을 여러 쿼리로 소량 수집한 뒤 본문 규칙으로 1차 분류합니다.
QUERIES = {
    "ABS": ["안티록 브레이크", "잠김 방지 브레이크", "ABS 브레이크"],
    "ESC": ["전자식 주행 안정", "차체 자세 제어", "전자 안정성 제어"],
    "INTEGRATED_BRAKE": ["통합 제동", "통합형 제동", "통합 브레이크"],
    "BBW_EMB": ["브레이크 바이 와이어", "Brake-by-Wire", "전자기계식 브레이크", "electromechanical brake"],
}

RULES = {
    "ABS": [
        r"안티.?록", r"잠김.?방지", r"anti.?lock", r"\bABS\b.{0,30}(브레이크|제동)",
    ],
    "ESC": [
        r"전자.{0,8}(주행|차체).{0,8}(안정|자세)", r"전자.{0,8}안정성.{0,8}제어",
        r"electronic stability", r"\bESC\b.{0,30}(차량|제동|안정)",
    ],
    "INTEGRATED_BRAKE": [
        r"통합.{0,8}(제동|브레이크)", r"(제동|브레이크).{0,8}통합",
        r"integrated.{0,12}brake", r"integrated.{0,12}braking",
    ],
    "BBW_EMB": [
        r"브레이크.?바이.?와이어", r"brake.?by.?wire",
        r"전자기계식.{0,8}(브레이크|제동)", r"electro.?mechanical.{0,12}brake",
        r"electromechanical.{0,12}brake",
    ],
}

def strip_ns(tag):
    return tag.split("}", 1)[-1] if "}" in tag else tag

def children_by_name(root, name):
    return [e for e in root.iter() if strip_ns(e.tag) == name]

def text_of(parent, name):
    for e in parent.iter():
        if strip_ns(e.tag) == name:
            return (e.text or "").strip()
    return ""

def request_xml(word, rows=8):
    params = {
        "word": word,
        "patent": "true",
        "utility": "false",
        "pageNo": 1,
        "numOfRows": rows,
        "sortSpec": "AD",
        "descSort": "true",
        "ServiceKey": KEY,
    }
    url = BASE + "?" + urlencode(params)
    req = Request(url, headers={"User-Agent": "Mozilla/5.0"})
    try:
        with urlopen(req, timeout=30) as r:
            data = r.read()
    except HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")[:1000]
        raise RuntimeError(f"HTTP {e.code}: {body}") from e
    except URLError as e:
        raise RuntimeError(f"NETWORK ERROR: {e}") from e
    return data

def parse_items(data):
    root = ET.fromstring(data)
    total = ""
    for e in root.iter():
        if strip_ns(e.tag) == "totalCount":
            total = (e.text or "").strip()
            break
    rows = []
    for item in children_by_name(root, "item"):
        rows.append({
            "register_status": text_of(item, "registerStatus"),
            "title": text_of(item, "inventionTitle"),
            "ipc": text_of(item, "ipcNumber"),
            "register_number": text_of(item, "registerNumber"),
            "register_date": text_of(item, "registerDate"),
            "application_number": text_of(item, "applicationNumber"),
            "application_date": text_of(item, "applicationDate"),
            "open_number": text_of(item, "openNumber"),
            "open_date": text_of(item, "openDate"),
            "abstract": text_of(item, "astrtCont"),
            "applicant": text_of(item, "applicantName"),
        })
    return total, rows

all_rows = []
query_log = []

for tech, words in QUERIES.items():
    for word in words:
        try:
            xml = request_xml(word)
            safe = re.sub(r"[^0-9A-Za-z가-힣_-]+", "_", word)
            (OUTDIR / f"{tech}_{safe}.xml").write_bytes(xml)
            total, rows = parse_items(xml)
            query_log.append({"technology": tech, "query": word, "total_count": total, "returned": len(rows), "status": "OK"})
            for r in rows:
                r["query_technology"] = tech
                r["query"] = word
                all_rows.append(r)
            time.sleep(0.15)
        except Exception as e:
            query_log.append({"technology": tech, "query": word, "total_count": "", "returned": 0, "status": f"ERROR: {e}"})

df = pd.DataFrame(all_rows)
log = pd.DataFrame(query_log)

if not df.empty:
    df = df.drop_duplicates(subset=["application_number", "title"], keep="first").copy()
    text = (df["title"].fillna("") + " " + df["abstract"].fillna("")).str.replace(r"\s+", " ", regex=True)
    def classify(txt):
        hits = []
        for tech, patterns in RULES.items():
            if any(re.search(p, txt, flags=re.I) for p in patterns):
                hits.append(tech)
        return "|".join(hits)
    df["rule_hits"] = text.map(classify)
    df["sample_pass"] = df.apply(
        lambda r: r["query_technology"] in (r["rule_hits"] or "").split("|")
                  and bool(str(r["application_date"]).strip())
                  and bool(str(r["title"]).strip())
                  and bool(str(r["abstract"]).strip())
                  and bool(str(r["ipc"]).strip())
                  and bool(str(r["applicant"]).strip()),
        axis=1
    )
    df["application_year"] = df["application_date"].astype(str).str[:4]
    cols = [
        "query_technology","query","sample_pass","rule_hits","application_year",
        "application_date","title","applicant","ipc","application_number",
        "open_number","register_status","abstract"
    ]
    df = df[cols]
    df.to_csv(OUTDIR / "kipris_patent_sample.csv", index=False, encoding="utf-8-sig")

log.to_csv(OUTDIR / "kipris_query_log.csv", index=False, encoding="utf-8-sig")

print("=" * 96)
print("KIPRIS PATENT SAMPLE CHECK")
print("=" * 96)
print(log.to_string(index=False))
print()
if df.empty:
    print("SAMPLE ROWS : 0")
    print("RESULT      : REVIEW REQUIRED - 응답/검색어 확인 필요")
else:
    print("UNIQUE SAMPLE :", len(df))
    print("PASS          :", int(df["sample_pass"].sum()))
    print("REVIEW        :", int((~df["sample_pass"]).sum()))
    print()
    print("=== PASS BY TECHNOLOGY ===")
    print(df.groupby("query_technology")["sample_pass"].agg(["count","sum"]).to_string())
    print()
    print("=== PASS SAMPLE (최대 기술별 3건) ===")
    passed = df[df["sample_pass"]].groupby("query_technology", group_keys=False).head(3)
    show = ["query_technology","application_date","title","applicant","ipc","application_number"]
    print(passed[show].to_string(index=False))
    print()
    print("OUTPUT :", OUTDIR / "kipris_patent_sample.csv")
    print("LOG    :", OUTDIR / "kipris_query_log.csv")
    print("※ 전체수집/MASTER/MART 변경 없음")
print("=" * 96)
