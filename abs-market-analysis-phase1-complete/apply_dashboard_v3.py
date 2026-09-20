from pathlib import Path
import shutil
ROOT=Path(__file__).resolve().parent
APP=ROOT/"dashboard"/"app.py"
BACKUP=ROOT/"dashboard"/"app_before_dashboard_v3.py"
if not APP.exists(): raise FileNotFoundError(APP)
if not BACKUP.exists(): shutil.copy2(APP,BACKUP)
APP_CODE = """from pathlib import Path
import pandas as pd
import plotly.express as px
import streamlit as st

ROOT=Path(__file__).resolve().parents[1]
MART=ROOT/"data"/"mart"
META=ROOT/"data"/"metadata"
st.set_page_config(page_title="ABS 시장 분석",page_icon="🚘",layout="wide",initial_sidebar_state="collapsed")
st.markdown("<style>.block-container{padding-top:1rem;max-width:1600px}.card{border:1px solid #e8edf3;border-radius:16px;padding:14px 16px;background:white;margin-bottom:10px}.badge{display:inline-block;padding:4px 9px;border-radius:999px;background:#f1f4f8;font-size:.78rem}</style>",unsafe_allow_html=True)

@st.cache_data
def load():
    m=pd.read_parquet(MART/"market_monthly.parquet")
    m["period_dt"]=pd.to_datetime(m["period_dt"] if "period_dt" in m else m["period"],errors="coerce")
    p=pd.read_csv(MART/"patent_annual.csv") if (MART/"patent_annual.csv").exists() else pd.DataFrame()
    t=pd.read_parquet(MART/"technology_signal.parquet") if (MART/"technology_signal.parquet").exists() else pd.DataFrame()
    s=pd.read_csv(META/"source_log.csv") if (META/"source_log.csv").exists() else pd.DataFrame()
    return m,p,t,s
market,patent,tech,sources=load()
metric_map={"VEHICLE_PRODUCTION_TOTAL":"생산","VEHICLE_DOMESTIC_TOTAL":"내수","VEHICLE_EXPORT_TOTAL":"수출"}
m=market[market["metric"].isin(metric_map)].copy()
m["구분"]=m["metric"].map(metric_map); m["값"]=pd.to_numeric(m["value"],errors="coerce")
m=m.dropna(subset=["period_dt","값"]).sort_values("period_dt")
last=m.period_dt.max()

st.title("자동차 시장 변화와 제동기술 전환")
st.caption("월별 시장 흐름 → 변동성 → 기술·특허 신호를 한 흐름으로 확인합니다.")
tab1,tab2=st.tabs(["① 시장 한눈에 보기","② 상세 분석 · 기술 기회"])

with tab1:
    a,b,c,d=st.columns([1,1,1,1.2]); cur=m[m.period_dt==last]
    def v(x):
        z=cur.loc[cur["구분"]==x,"값"]; return int(z.iloc[0]) if len(z) else None
    a.metric("최근 생산",f"{v('생산'):,}대" if v("생산") is not None else "-")
    b.metric("최근 내수",f"{v('내수'):,}대" if v("내수") is not None else "-")
    c.metric("최근 수출",f"{v('수출'):,}대" if v("수출") is not None else "-")
    period=d.selectbox("조회 기간",["최근 3년","최근 5년","최근 10년","전체"],1)
    n={"최근 3년":3,"최근 5년":5,"최근 10년":10}.get(period)
    view=m if not n else m[m.period_dt>=last-pd.DateOffset(years=n)]
    f=px.line(view,x="period_dt",y="값",color="구분",markers=True,labels={"period_dt":"","값":"대수","구분":""})
    f.update_traces(connectgaps=True,hovertemplate="%{x|%Y-%m}<br>%{y:,.0f}대<extra>%{fullData.name}</extra>")
    f.update_layout(height=390,margin=dict(l=10,r=10,t=25,b=10),legend=dict(orientation="h",y=1.1),hovermode="x unified")
    st.plotly_chart(f,use_container_width=True)

    st.subheader("지금 시장 · 전년 동기간 비교")
    y=int(m.period_dt.dt.year.max()); py=y-1; mm=int(m.loc[m.period_dt.dt.year==y,"period_dt"].dt.month.max())
    comp=m[(m.period_dt.dt.year.isin([py,y]))&(m.period_dt.dt.month<=mm)].copy()
    comp["연도"]=comp.period_dt.dt.year.astype(str)
    sums=comp.groupby(["구분","연도"],as_index=False)["값"].sum()
    f2=px.bar(sums,x="구분",y="값",color="연도",barmode="group",text_auto=".3s",labels={"값":"동기간 누계","구분":""})
    f2.update_layout(height=300,margin=dict(l=10,r=10,t=20,b=10),legend=dict(orientation="h",y=1.12))
    f2.update_traces(hovertemplate="%{x}<br>%{y:,.0f}대<extra>%{fullData.name}</extra>")
    st.plotly_chart(f2,use_container_width=True)
    st.caption(f"{y}년은 {mm}월까지 실제값끼리 비교합니다. 없는 월은 0으로 채우지 않습니다.")

    st.subheader("연간 흐름")
    annual=view.assign(연도=view.period_dt.dt.year).groupby(["연도","구분"],as_index=False)["값"].sum()
    f3=px.bar(annual,x="연도",y="값",color="구분",barmode="group",labels={"값":"연간 합계","연도":""})
    f3.update_layout(height=300,margin=dict(l=10,r=10,t=10,b=10),legend=dict(orientation="h",y=1.12))
    st.plotly_chart(f3,use_container_width=True)

with tab2:
    left,right=st.columns([1.12,.88])
    with left:
        st.subheader("내수 · 수출 추이")
        det=m[(m["구분"].isin(["내수","수출"]))&(m.period_dt>=last-pd.DateOffset(years=5))]
        f4=px.line(det,x="period_dt",y="값",color="구분",markers=True,labels={"period_dt":"","값":"대수","구분":""})
        f4.update_traces(connectgaps=True,hovertemplate="%{x|%Y-%m}<br>%{y:,.0f}대<extra>%{fullData.name}</extra>")
        f4.update_layout(height=310,margin=dict(l=10,r=10,t=10,b=10),legend=dict(orientation="h",y=1.12),hovermode="x unified")
        st.plotly_chart(f4,use_container_width=True)
        if "std_12m" in det:
            vol=det[["period_dt","구분","std_12m"]].copy(); vol["std_12m"]=pd.to_numeric(vol.std_12m,errors="coerce"); vol=vol.dropna()
            if len(vol):
                f5=px.line(vol,x="period_dt",y="std_12m",color="구분",labels={"period_dt":"","std_12m":"12개월 변동성","구분":""})
                f5.update_layout(height=250,margin=dict(l=10,r=10,t=10,b=10),legend=dict(orientation="h",y=1.15))
                st.plotly_chart(f5,use_container_width=True)
    with right:
        st.subheader("특허로 본 기술 활동")
        if len(patent):
            patent["application_year"]=pd.to_numeric(patent.application_year,errors="coerce")
            p=patent[patent.application_year>=2016].copy()
            p["기술"]=p.technology.map({"ABS":"ABS","ESC":"ESC","INTEGRATED_BRAKE":"통합제동","BBW_EMB":"BBW·EMB"}).fillna(p.technology)
            f6=px.line(p,x="application_year",y="patent_count",color="기술",markers=True,labels={"application_year":"","patent_count":"특허 건수","기술":""})
            f6.update_layout(height=310,margin=dict(l=10,r=10,t=10,b=10),legend=dict(orientation="h",y=1.14))
            st.plotly_chart(f6,use_container_width=True)
            st.caption("특허 건수는 시장점유율이 아니라 기술활동 신호입니다.")
        st.subheader("주요 기술 신호")
        srcmap=dict(zip(sources.source_id.astype(str),sources.source_url.astype(str))) if {"source_id","source_url"}.issubset(sources.columns) else {}
        for _,r in tech.sort_values("signal_date",ascending=False).head(6).iterrows():
            st.markdown(f'<div class="card"><b>{r.get("company","")}</b> · <span class="badge">{r.get("signal_type","")}</span><br>{r.get("event","")}</div>',unsafe_allow_html=True)
            u=srcmap.get(str(r.get("source_id","")),"")
            if u and u!="nan": st.link_button("근거자료 보기 ↗",u)

    st.divider()
    st.subheader("그래프가 답해야 할 질문")
    x,y,z=st.columns(3)
    x.markdown('<div class="card"><b>시장</b><br>내수·수출 중 어디에서 변화가 크게 나타나는가?</div>',unsafe_allow_html=True)
    y.markdown('<div class="card"><b>기술</b><br>특허 활동이 통합제동·BBW/EMB 방향으로 이동하는 신호가 있는가?</div>',unsafe_allow_html=True)
    z.markdown('<div class="card"><b>기회</b><br>출시·수주·전망과 특허 활동이 함께 강해지는 영역은 어디인가?</div>',unsafe_allow_html=True)
    st.caption("관찰과 해석을 구분합니다. 특허 건수는 시장규모·점유율이 아니며, 미완료 연도는 완결 연도와 동일하게 해석하지 않습니다.")
"""
APP.write_text(APP_CODE,encoding="utf-8")
print("DASHBOARD V3 APPLIED")
print("BACKUP:",BACKUP)
print("RUN: python -m streamlit run dashboard/app.py")
