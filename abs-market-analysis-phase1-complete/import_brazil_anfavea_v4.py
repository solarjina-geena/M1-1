from pathlib import Path
import sys, re
import pandas as pd

ROOT=Path(__file__).resolve().parent
G=ROOT/"data"/"global"
SRC=G/"global_market_monthly_v3.csv"
RAW=G/"raw"/"brazil"
RAW.mkdir(parents=True,exist_ok=True)
if not SRC.exists(): raise FileNotFoundError(SRC)

# 안전 원칙:
# ANFAVEA 원본 Excel/CSV를 RAW 폴더에 넣으면 자동 탐색/파싱한다.
# 원본 파일이 없으면 숫자를 임의 생성하지 않고 정확한 저장 위치를 안내한다.
files=list(RAW.glob("*.xlsx"))+list(RAW.glob("*.xls"))+list(RAW.glob("*.csv"))
if not files:
    print("="*94)
    print("BRAZIL ANFAVEA IMPORTER V4 - RAW FILE REQUIRED")
    print("="*94)
    print("ANFAVEA 원본 Excel/CSV를 아래 폴더에 저장한 뒤 다시 실행하세요:")
    print(" ",RAW)
    print("\n권장: ANFAVEA 'Edições em Excel'에서 월간 통계 Excel을 내려받아 원본 그대로 저장")
    print("※ 임의 수치/보도자료 몇 개로 MASTER를 채우지 않습니다.")
    sys.exit(2)

base=pd.read_csv(SRC,parse_dates=["period"])
allrows=[]; audit=[]

month_map={"jan":1,"fev":2,"mar":3,"abr":4,"mai":5,"jun":6,"jul":7,"ago":8,"set":9,"out":10,"nov":11,"dez":12,
           "janeiro":1,"fevereiro":2,"março":3,"marco":3,"abril":4,"maio":5,"junho":6,"julho":7,"agosto":8,
           "setembro":9,"outubro":10,"novembro":11,"dezembro":12}

def norm(x):
    return re.sub(r"\s+"," ",str(x).strip().lower())

for f in files:
    try:
        sheets={"CSV":pd.read_csv(f,header=None)} if f.suffix.lower()==".csv" else pd.read_excel(f,sheet_name=None,header=None)
        for sname,df in sheets.items():
            text=" ".join(df.astype(str).fillna("").values.flatten()).lower()
            # 관련 시트만 후보로 남김
            if not any(k in text for k in ["produção","producao","export","licenciamento","emplacamento"]):
                continue
            # 범용 자동파서는 표 구조가 다양하므로 'long-format' 명확한 경우만 자동 적재
            hdr=None
            for i in range(min(30,len(df))):
                row=[norm(v) for v in df.iloc[i].tolist()]
                joined="|".join(row)
                if any(k in joined for k in ["mês","mes","month"]) and any(k in joined for k in ["produção","producao","export","licenciamento","emplacamento"]):
                    hdr=i; break
            if hdr is None:
                audit.append([f.name,sname,"REVIEW","관련 시트이나 long-format 헤더 자동판독 불가"])
                continue
            t=df.iloc[hdr:].copy(); t.columns=[norm(x) for x in t.iloc[0]]; t=t.iloc[1:].reset_index(drop=True)
            # year/month columns
            yc=next((c for c in t.columns if c in ["ano","year"]),None)
            mc=next((c for c in t.columns if c in ["mês","mes","month"]),None)
            if not yc or not mc:
                audit.append([f.name,sname,"REVIEW","연/월 컬럼 불명확"]); continue
            metric_cols={}
            for c in t.columns:
                n=norm(c)
                if "produ" in n: metric_cols[c]=("PRODUCTION","SUPPLY")
                elif "export" in n: metric_cols[c]=("EXPORT","EXPORT")
                elif "licenc" in n or "emplac" in n: metric_cols[c]=("DOMESTIC_REGISTRATION","DEMAND")
            if not metric_cols:
                audit.append([f.name,sname,"REVIEW","지표 컬럼 불명확"]); continue
            nadd=0
            for _,r in t.iterrows():
                try: year=int(float(r[yc]))
                except: continue
                mv=norm(r[mc])
                try: month=int(float(mv))
                except: month=month_map.get(mv)
                if not month or not (1<=month<=12): continue
                for c,(metric,side) in metric_cols.items():
                    val=pd.to_numeric(str(r[c]).replace(".","").replace(",", "."),errors="coerce")
                    if pd.isna(val): continue
                    allrows.append(dict(period=pd.Timestamp(year,month,1),country_code="BRA",market_group="중남미",
                      group_tags="BRICS",market_side=side,metric=metric,vehicle_scope="SOURCE_DEFINED",
                      value=float(val),value_status="ACTUAL",official_status="SOURCE_PUBLISHED",
                      source="ANFAVEA",source_url="https://anfavea.com.br/site/edicoes-em-excel/",
                      estimate_method="",note=f"ANFAVEA 원본 {f.name} / {sname}"))
                    nadd+=1
            audit.append([f.name,sname,"PARSED",nadd])
    except Exception as e:
        audit.append([f.name,"","ERROR",str(e)])

add=pd.DataFrame(allrows)
pd.DataFrame(audit,columns=["file","sheet","status","detail"]).to_csv(G/"brazil_import_audit_v4.csv",index=False,encoding="utf-8-sig")

if add.empty:
    print("="*94); print("BRAZIL ANFAVEA V4 - REVIEW REQUIRED"); print("="*94)
    print(pd.DataFrame(audit,columns=["file","sheet","status","detail"]).to_string(index=False))
    print("\n자동으로 확실히 판독되는 long-format 표가 없어 MASTER는 변경하지 않았습니다.")
    print("AUDIT:",G/"brazil_import_audit_v4.csv")
    sys.exit(3)

for c in base.columns:
    if c not in add: add[c]=""
add=add[base.columns]
out=pd.concat([base,add],ignore_index=True)
out=out.drop_duplicates(["period","country_code","metric","vehicle_scope"],keep="last").sort_values(["country_code","metric","period"])
out.to_csv(G/"global_market_monthly_v4.csv",index=False,encoding="utf-8-sig")

print("="*94); print("BRAZIL ANFAVEA V4 IMPORT COMPLETE"); print("="*94)
print("BRAZIL ROWS:",len(add))
print("PERIOD:",add.period.min().strftime("%Y-%m"),"~",add.period.max().strftime("%Y-%m"))
print("\nBY METRIC"); print(add.groupby("metric").agg(rows=("value","size"),months=("period","nunique")).to_string())
print("\nOUTPUT:",G/"global_market_monthly_v4.csv")
print("AUDIT :",G/"brazil_import_audit_v4.csv")
print("="*94)
