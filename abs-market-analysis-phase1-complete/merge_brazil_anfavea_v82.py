from pathlib import Path
import re, pandas as pd

ROOT=Path(__file__).resolve().parent
G=ROOT/"data"/"global"
SRC=G/"global_market_monthly_v3.csv"
IDX=G/"brazil_table_best_v8.csv"
if not SRC.exists() or not IDX.exists(): raise FileNotFoundError("V3 MASTER 또는 V8 후보파일 없음")

base=pd.read_csv(SRC,parse_dates=["period"])
idx=pd.read_csv(IDX)

# carta 번호가 큰 최신 자료가 과거 월의 수정치를 포함하므로 최신 호를 우선.
# 명확한 '당월/전월/누계' 첫 Total 행만 읽는다.
month_pt={"JAN":1,"FEV":2,"MAR":3,"ABR":4,"MAI":5,"JUN":6,"JUL":7,"AGO":8,"SET":9,"OUT":10,"NOV":11,"DEZ":12}
rows=[]; audit=[]

def nums(s):
    # 브라질 천단위 '.' -> integer
    return [int(x.replace(".","")) for x in re.findall(r"(?<!\d)\d{1,3}(?:\.\d{3})+(?!\d)",s)]

def parse_header_total(text, metric, pdf):
    # 예: 2026 2025 / AGO JUL JAN-AGO ... / Unidades - Total ... 271.160 254.002 1.897.518 ...
    m=re.search(r"\b(20\d{2})\s+(20\d{2})\b",text)
    if not m: return None
    year=int(m.group(1))
    # 첫 연도 뒤에서 월 약어 2개 추출
    tail=text[m.end():]
    mons=re.findall(r"\b(JAN|FEV|MAR|ABR|MAI|JUN|JUL|AGO|SET|OUT|NOV|DEZ)\b",tail)
    if len(mons)<2: return None
    cur,prev=month_pt[mons[0]],month_pt[mons[1]]
    tm=re.search(r"Unidades\s*-\s*Total\s*/\s*Units\s*/\s*Unidades\s+(.+)",text,re.I)
    if not tm: return None
    vv=nums(tm.group(1))
    if len(vv)<3: return None
    current,previous,ytd=vv[0],vv[1],vv[2]
    return year,cur,prev,current,previous,ytd

# 생산/수출: 표 구조가 명확
for metric in ["PRODUCTION","EXPORT"]:
    z=idx[idx.metric.eq(metric)].copy()
    z["issue"]=z.pdf.str.extract(r"(\d+)").astype(int)
    z=z.sort_values("issue")  # 뒤의 최신호가 overwrite
    for _,r in z.iterrows():
        f=G/Path(r["file"]).name
        if not f.exists(): continue
        t=pd.read_csv(f,header=None,dtype=str).fillna("")
        # 해당 지표의 첫 블록
        text=" ".join(t.iloc[:4].astype(str).values.flatten())
        parsed=parse_header_total(text,metric,r["pdf"])
        if not parsed:
            audit.append([r["pdf"],metric,"REVIEW","header/total parse fail"]); continue
        year,cur,prev,current,previous,ytd=parsed
        for mo,val,role in [(cur,current,"CURRENT"),(prev,previous,"PREVIOUS")]:
            rows.append([pd.Timestamp(year,mo,1),"BRA","중남미","BRICS",
                         "SUPPLY" if metric=="PRODUCTION" else "EXPORT",metric,"TOTAL_VEHICLES",
                         val,"ACTUAL","SOURCE_PUBLISHED","ANFAVEA",
                         "https://anfavea.com.br/site/conteudos/carta-da-anfavea/","",
                         f"{r['pdf']} {role}; 공식 월간 Carta Total"])
        audit.append([r["pdf"],metric,"PARSED",f"{year}-{cur:02d}={current}; prev={previous}; ytd={ytd}"])

# 내수등록은 p4가 '국산/수입' 분리라 합산 필요. 최신호별 국산 total + 수입 total.
z=idx[(idx.metric=="DOMESTIC_REGISTRATION") & (idx.page==4)].copy()
if len(z):
    z["issue"]=z.pdf.str.extract(r"(\d+)").astype(int)
    for _,r in z.sort_values("issue").iterrows():
        f=G/Path(r["file"]).name
        if not f.exists(): continue
        t=pd.read_csv(f,header=None,dtype=str).fillna("")
        text=" ".join(t.astype(str).values.flatten())
        blocks=re.split(r"Emplacamento de autoveículos novos importados",text,flags=re.I)
        if len(blocks)<2:
            audit.append([r["pdf"],"DOMESTIC_REGISTRATION","REVIEW","national/import split fail"]); continue
        a=parse_header_total(blocks[0],"DOMESTIC_REGISTRATION",r["pdf"])
        b=parse_header_total("2026 2025 "+blocks[1],"DOMESTIC_REGISTRATION",r["pdf"]) # year tokens may sit before split
        if not a or not b:
            audit.append([r["pdf"],"DOMESTIC_REGISTRATION","REVIEW","total parse fail"]); continue
        year,cur,prev,ac,ap,ay=a
        _,cur2,prev2,bc,bp,by=b
        if (cur,prev)!=(cur2,prev2):
            audit.append([r["pdf"],"DOMESTIC_REGISTRATION","REVIEW","month mismatch"]); continue
        for mo,val,role in [(cur,ac+bc,"CURRENT"),(prev,ap+bp,"PREVIOUS")]:
            rows.append([pd.Timestamp(year,mo,1),"BRA","중남미","BRICS","DEMAND","DOMESTIC_REGISTRATION",
                         "TOTAL_VEHICLES",val,"ACTUAL","SOURCE_PUBLISHED","ANFAVEA",
                         "https://anfavea.com.br/site/conteudos/carta-da-anfavea/","",
                         f"{r['pdf']} {role}; 국산+수입 공식 Total"])
        audit.append([r["pdf"],"DOMESTIC_REGISTRATION","PARSED",f"{year}-{cur:02d}={ac+bc}; ytd={ay+by}"])

cols=["period","country_code","market_group","group_tags","market_side","metric","vehicle_scope","value",
      "value_status","official_status","source","source_url","estimate_method","note"]
add=pd.DataFrame(rows,columns=cols)
# 최신 carta 값 우선
if len(add):
    add=add.drop_duplicates(["period","country_code","metric","vehicle_scope"],keep="last").sort_values(["metric","period"])
    for c in base.columns:
        if c not in add: add[c]=""
    add=add[base.columns]
    out=pd.concat([base,add],ignore_index=True)
    out=out.drop_duplicates(["period","country_code","metric","vehicle_scope"],keep="last").sort_values(["country_code","metric","period"])
    out.to_csv(G/"global_market_monthly_v4.csv",index=False,encoding="utf-8-sig")
else:
    out=base

pd.DataFrame(audit,columns=["pdf","metric","status","detail"]).to_csv(G/"brazil_merge_audit_v82.csv",index=False,encoding="utf-8-sig")
print("="*96)
print("BRAZIL ANFAVEA MERGE V8.2 COMPLETE")
print("="*96)
print("PDF RE-READ : 0")
print("BRAZIL ROWS :",len(add))
if len(add):
    print("\n=== BRAZIL MONTHLY ACTUAL ===")
    print(add[["period","metric","value","note"]].to_string(index=False))
print("\n=== AUDIT SUMMARY ===")
print(pd.DataFrame(audit,columns=["pdf","metric","status","detail"]).groupby(["metric","status"]).size().to_string())
print("\nOUTPUT")
print(" -",G/"global_market_monthly_v4.csv")
print(" -",G/"brazil_merge_audit_v82.csv")
print("="*96)
