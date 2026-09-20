from pathlib import Path
import re, sys, subprocess
import pandas as pd

ROOT=Path(__file__).resolve().parent
G=ROOT/"data"/"global"; RAW=G/"raw"/"brazil"
SRC=G/"global_market_monthly_v3.csv"
if not SRC.exists(): raise FileNotFoundError(SRC)
pdfs=sorted(RAW.glob("carta*.pdf"))
if not pdfs: raise FileNotFoundError("ANFAVEA PDF 없음: "+str(RAW))

try:
    import pdfplumber
except ImportError:
    print("pdfplumber 설치 중...")
    subprocess.check_call([sys.executable,"-m","pip","install","pdfplumber","-q"])
    import pdfplumber

# 1) PDF 텍스트/표를 전부 보존. 먼저 구조를 판독하고, 확실한 값만 자동 추출.
audit=[]; candidates=[]
keywords={
 "PRODUCTION":["produção","producao"],
 "EXPORT":["exportações","exportacoes"],
 "DOMESTIC_REGISTRATION":["licenciamento","emplacamento"]
}
for pdf in pdfs:
    m=re.search(r"carta(\d+)",pdf.name,re.I); issue=int(m.group(1)) if m else None
    try:
        with pdfplumber.open(pdf) as doc:
            pages_text=[]
            for pi,page in enumerate(doc.pages,1):
                txt=page.extract_text(x_tolerance=2,y_tolerance=3) or ""
                pages_text.append(txt)
                low=txt.lower()
                for metric,ks in keywords.items():
                    if any(k in low for k in ks):
                        # 숫자 토큰과 주변 텍스트를 감사용으로 보존
                        nums=re.findall(r"(?<!\d)(\d{1,3}(?:[.\s]\d{3})+|\d{4,7})(?!\d)",txt)
                        candidates.append([pdf.name,issue,pi,metric,txt[:1200].replace("\n"," | "),";".join(nums[:80])])
            (RAW/(pdf.stem+".txt")).write_text("\n\n---PAGE---\n\n".join(pages_text),encoding="utf-8")
            audit.append([pdf.name,len(doc.pages),"OK"])
    except Exception as e:
        audit.append([pdf.name,0,"ERROR: "+str(e)])

pd.DataFrame(audit,columns=["pdf","pages","status"]).to_csv(G/"brazil_pdf_audit_v7.csv",index=False,encoding="utf-8-sig")
cand=pd.DataFrame(candidates,columns=["pdf","issue","page","metric","context","number_tokens"])
cand.to_csv(G/"brazil_pdf_candidates_v7.csv",index=False,encoding="utf-8-sig")

# 2) 월간 Carta는 레이아웃이 호수별로 달라질 수 있으므로
#    단순 regex로 숫자를 MASTER에 넣지 않는다.
#    대신 표 추출 결과가 '월 + 당월 + 누계' 구조로 명확한 경우만 후보 생성.
rows=[]
for pdf in pdfs:
    try:
        with pdfplumber.open(pdf) as doc:
            for pi,page in enumerate(doc.pages,1):
                tables=page.extract_tables() or []
                for ti,t in enumerate(tables):
                    if not t or len(t)<2: continue
                    flat=" ".join("" if v is None else str(v) for row in t for v in row).lower()
                    met=None; side=None
                    if "produção" in flat or "producao" in flat: met,side="PRODUCTION","SUPPLY"
                    elif "exporta" in flat: met,side="EXPORT","EXPORT"
                    elif "licenciamento" in flat or "emplacamento" in flat: met,side="DOMESTIC_REGISTRATION","DEMAND"
                    if not met: continue
                    # 감사용 원시표 저장
                    tf=G/f"brazil_table_{pdf.stem}_p{pi}_t{ti}.csv"
                    pd.DataFrame(t).to_csv(tf,index=False,header=False,encoding="utf-8-sig")
                    rows.append([pdf.name,pi,ti,met,str(tf)])
    except: pass
tables=pd.DataFrame(rows,columns=["pdf","page","table","metric","table_file"])
tables.to_csv(G/"brazil_table_index_v7.csv",index=False,encoding="utf-8-sig")

print("="*96)
print("BRAZIL ANFAVEA PDF EXTRACTION V7 COMPLETE")
print("="*96)
print("PDF FILES       :",len(pdfs))
print("PDF READ OK     :",sum(x[2]=="OK" for x in audit))
print("KEYWORD PAGES   :",len(cand))
print("EXTRACTED TABLES:",len(tables))
print("\nOUTPUT")
print(" -",G/"brazil_pdf_audit_v7.csv")
print(" -",G/"brazil_pdf_candidates_v7.csv")
print(" -",G/"brazil_table_index_v7.csv")
print(" -",RAW/"cartaXXX.txt")
print("\nSAFETY")
print(" - 이번 단계에서는 regex 숫자를 MASTER에 자동 삽입하지 않았습니다.")
print(" - 표 구조와 월/누계 관계를 확인한 다음에만 ACTUAL로 병합합니다.")
print(" - 기존 global_market_monthly_v3.csv는 변경하지 않았습니다.")
print("="*96)
