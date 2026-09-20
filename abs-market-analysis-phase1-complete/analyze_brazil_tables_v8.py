from pathlib import Path
import pandas as pd, re, sys

ROOT=Path(__file__).resolve().parent
G=ROOT/"data"/"global"
IDX=G/"brazil_table_index_v7.csv"
if not IDX.exists(): raise FileNotFoundError(IDX)

idx=pd.read_csv(IDX)
out=[]
def clean(x):
    if pd.isna(x): return ""
    return re.sub(r"\s+"," ",str(x)).strip()

for _,r in idx.iterrows():
    f=Path(str(r["table_file"]))
    # PC 경로가 그대로 저장돼 있으므로 현재 프로젝트 기준 파일명으로 재탐색
    if not f.exists():
        f=G/f.name
    if not f.exists(): continue
    t=pd.read_csv(f,header=None,dtype=str).fillna("")
    text=" | ".join(clean(x) for x in t.values.flatten())
    low=text.lower()
    # V8은 작은 CSV만 읽고 구조 점수만 계산한다.
    score=0
    for k in ["2026","2025","jan","fev","mar","abr","mai","jun","jul","ago","set","out","nov","dez",
              "janeiro","fevereiro","março","abril","maio","junho","julho","agosto"]:
        if k in low: score+=1
    if any(k in low for k in ["total","acumul","jan/","até","ate"]): score+=3
    nums=re.findall(r"(?<!\d)\d{1,3}(?:[.\s]\d{3})+(?!\d)|(?<!\d)\d{4,7}(?!\d)",text)
    out.append([r["pdf"],r["page"],r["table"],r["metric"],f.name,t.shape[0],t.shape[1],score,len(nums),text[:1800]])

a=pd.DataFrame(out,columns=["pdf","page","table","metric","file","rows","cols","structure_score","numeric_tokens","preview"])
a=a.sort_values(["metric","structure_score","numeric_tokens"],ascending=[True,False,False])
a.to_csv(G/"brazil_table_rank_v8.csv",index=False,encoding="utf-8-sig")

best=(a.groupby("metric",group_keys=False).head(8) if len(a) else a)
best.to_csv(G/"brazil_table_best_v8.csv",index=False,encoding="utf-8-sig")

print("="*94)
print("BRAZIL TABLE LIGHT ANALYSIS V8 COMPLETE")
print("="*94)
print("TABLES READ :",len(a))
print("PDF RE-READ : 0")
print("\n=== BEST CANDIDATES ===")
if len(best):
    print(best[["metric","pdf","page","table","rows","cols","structure_score","numeric_tokens","file"]].to_string(index=False))
else:
    print("NONE")
print("\nOUTPUT")
print(" -",G/"brazil_table_rank_v8.csv")
print(" -",G/"brazil_table_best_v8.csv")
print("\n※ PDF를 다시 열지 않았습니다. V7이 만든 작은 CSV 표만 분석했습니다.")
print("※ 아직 숫자를 MASTER에 넣지 않았습니다.")
print("="*94)
