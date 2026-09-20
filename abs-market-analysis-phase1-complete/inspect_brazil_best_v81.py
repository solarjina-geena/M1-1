from pathlib import Path
import pandas as pd

ROOT=Path(__file__).resolve().parent
G=ROOT/"data"/"global"
BEST=G/"brazil_table_best_v8.csv"
if not BEST.exists(): raise FileNotFoundError(BEST)
b=pd.read_csv(BEST)

# 지표별 최신/대표 표 2개씩만 읽어 실제 셀 구조를 출력한다. PDF 재독 없음.
sel=(b.sort_values(["metric","pdf"],ascending=[True,False])
       .groupby("metric",group_keys=False).head(2))
rows=[]
print("="*100)
print("BRAZIL TABLE STRUCTURE INSPECTION V8.1")
print("="*100)
for _,r in sel.iterrows():
    f=G/Path(str(r["file"])).name
    if not f.exists(): continue
    t=pd.read_csv(f,header=None,dtype=str).fillna("")
    print(f"\n--- {r['metric']} | {r['pdf']} | page {r['page']} | {f.name} ---")
    # 셀이 매우 길어도 화면 폭주하지 않게 500자 제한
    for i,row in t.iterrows():
        vals=[str(x).replace("\n"," / ")[:500] for x in row.tolist()]
        print(f"R{i}: " + " || ".join(vals))
        rows.append([r["metric"],r["pdf"],r["page"],f.name,i," || ".join(vals)])
pd.DataFrame(rows,columns=["metric","pdf","page","file","row","content"]).to_csv(
    G/"brazil_structure_v81.csv",index=False,encoding="utf-8-sig")
print("\nOUTPUT:",G/"brazil_structure_v81.csv")
print("PDF RE-READ: 0")
print("="*100)
