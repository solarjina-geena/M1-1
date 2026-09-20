from pathlib import Path
import html
import altair as alt
import numpy as np
import pandas as pd
import streamlit as st

BASE_DIR = Path(__file__).resolve().parents[1]
MARKET_MART = BASE_DIR / "data" / "mart" / "market_monthly.parquet"
SIGNAL_MART = BASE_DIR / "data" / "mart" / "technology_signal.parquet"
GLOBAL_CANDIDATES = [
    BASE_DIR / "data" / "global" / f"global_market_monthly_v{i}.csv"
    for i in range(9, 3, -1)
]
PATENT_CANDIDATES = [
    BASE_DIR / "data" / "processed" / "patent_technology_yearly.csv",
    BASE_DIR / "data" / "mart" / "patent_technology_yearly.csv",
    BASE_DIR / "data" / "metadata" / "patent_technology_yearly.csv",
]

st.set_page_config(page_title="ABS Market Intelligence", page_icon="◈",
                   layout="wide", initial_sidebar_state="collapsed")

NAVY="#0B2B59"; BLUE="#1769D2"; GREEN="#229A8A"; ORANGE="#E48A3A"
RED="#E14B4B"; MUTED="#6B7C93"; BORDER="#DDE6F0"

st.markdown("""
<style>
:root { --navy:#0B2B59; --blue:#1769D2; --muted:#6B7C93; --border:#DDE6F0; }
html,body,[class*="css"] {font-family: Pretendard,"Noto Sans KR","Malgun Gothic",sans-serif;}
.stApp {background:#F4F8FD;}
.block-container {max-width:1580px;padding:0 1.55rem 1.5rem;}
header[data-testid="stHeader"] {background:transparent;}
#MainMenu, footer {visibility:hidden;}
.hero {background:#0B2B59;margin:0 -1.55rem 1.05rem;padding:1.05rem 1.7rem .95rem;color:white;}
.hero-row {display:flex;justify-content:space-between;align-items:flex-end;gap:20px;}
.hero-title {font-size:1.65rem;font-weight:850;letter-spacing:-.04em;}
.hero-sub {font-size:.82rem;color:#D9E9FF;margin-top:.18rem;}
.hero-rule {font-size:.72rem;color:#D9E9FF;text-align:right;}
.section-title {font-size:1.42rem;font-weight:850;color:#102A4C;letter-spacing:-.035em;margin:.15rem 0 .08rem;}
.section-sub {font-size:.78rem;color:#6B7C93;margin-bottom:.55rem;}
.card {background:white;border:1px solid #DDE6F0;border-radius:14px;padding:.9rem 1rem;box-shadow:0 1px 2px rgba(16,42,76,.03);}
.kpi-label {font-size:.73rem;font-weight:750;color:#6B7C93;}
.kpi-value {font-size:1.55rem;font-weight:850;color:#102A4C;line-height:1.2;margin:.24rem 0 .12rem;}
.kpi-sub {font-size:.69rem;color:#6B7C93;}
.fact {border-left:4px solid #1769D2;background:#F8FBFF;padding:.72rem .82rem;border-radius:0 10px 10px 0;margin:.42rem 0;}
.why {border-left:4px solid #E48A3A;background:#FFFBF5;padding:.72rem .82rem;border-radius:0 10px 10px 0;margin:.42rem 0;}
.action {border-left:4px solid #229A8A;background:#F5FBFA;padding:.72rem .82rem;border-radius:0 10px 10px 0;margin:.42rem 0;}
.box-head {font-size:.75rem;font-weight:850;margin-bottom:.2rem;}
.box-body {font-size:.78rem;color:#31455F;line-height:1.52;}
.flow {display:grid;grid-template-columns:1fr auto 1fr auto 1fr auto 1.35fr;gap:8px;align-items:center;margin:.45rem 0;}
.node {background:#EEF5FD;border:1px solid #CFE0F3;border-radius:11px;padding:.65rem .5rem;text-align:center;color:#0B2B59;font-weight:800;font-size:.78rem;}
.arrow {color:#1769D2;font-weight:900;text-align:center;}
.signal {background:#FAFCFF;border:1px solid #E2EAF3;border-radius:10px;padding:.6rem .7rem;margin:.35rem 0;}
.signal strong {color:#1769D2;font-size:.78rem;}
.signal span {font-size:.73rem;color:#31455F;}
[data-testid="stMetric"] {background:white;border:1px solid #DDE6F0;border-radius:14px;padding:.72rem .85rem;}
[data-testid="stMetricLabel"] {font-size:.72rem;color:#6B7C93;}
[data-testid="stMetricValue"] {font-size:1.35rem;font-weight:850;color:#102A4C;}
.stTabs [data-baseweb="tab-list"] {gap:7px;background:#EAF2FB;padding:5px;border-radius:11px;width:max-content;}
.stTabs [data-baseweb="tab"] {height:34px;border-radius:8px;padding:0 18px;font-size:.78rem;font-weight:800;}
.stTabs [aria-selected="true"] {background:#0B2B59;color:white;}
@media(max-width:900px){.block-container{padding:0 .7rem 1rem}.hero{margin:0 -.7rem 1rem}.hero-row{display:block}.hero-rule{text-align:left;margin-top:.5rem}.flow{grid-template-columns:1fr}.arrow{transform:rotate(90deg)}}
</style>
""", unsafe_allow_html=True)

@st.cache_data
def load_market():
    if not MARKET_MART.exists(): return pd.DataFrame()
    return pd.read_parquet(MARKET_MART)

@st.cache_data
def load_signals():
    if not SIGNAL_MART.exists(): return pd.DataFrame()
    return pd.read_parquet(SIGNAL_MART)

@st.cache_data
def load_first_csv(paths):
    for p in paths:
        if p.exists():
            try:
                x=pd.read_csv(p)
                x["_source_file"]=p.name
                return x
            except Exception:
                pass
    return pd.DataFrame()

market=load_market()
signals=load_signals()
global_market=load_first_csv(GLOBAL_CANDIDATES)
patent_yearly=load_first_csv(PATENT_CANDIDATES)

METRICS={
    "생산":["VEHICLE_PRODUCTION_TOTAL"],
    "내수":["VEHICLE_DOMESTIC_TOTAL","VEHICLE_DOMESTIC_SALES_TOTAL","DOMESTIC_SALES_TOTAL"],
    "수출":["VEHICLE_EXPORT_TOTAL","EXPORT_TOTAL","VEHICLE_SALES_EXPORT_TOTAL"],
}

def metric_name(label, scope="KOREA"):
    if market.empty: return None
    x=market
    if "market_scope" in x: x=x[x["market_scope"].astype(str).str.upper()==scope.upper()]
    avail=set(x["metric"].astype(str))
    return next((m for m in METRICS[label] if m in avail),None)

def series(label):
    m=metric_name(label)
    if not m: return pd.DataFrame(columns=["date","value"])
    x=market[(market["market_scope"].astype(str).str.upper()=="KOREA") & (market["metric"].astype(str)==m)].copy()
    x["date"]=pd.to_datetime(x["period"],format="%Y-%m",errors="coerce")
    x["value"]=pd.to_numeric(x["value"],errors="coerce")
    x=x.dropna(subset=["date","value"]).sort_values("date")
    # 동일 월 중복은 최신 행 하나만 사용. 결측월 생성/0 대체 금지.
    return x.drop_duplicates("date",keep="last")

def latest(label):
    x=series(label)
    return None if x.empty else x.iloc[-1]

def fmt(v):
    return "-" if v is None or pd.isna(v) else f"{v:,.0f}"

def features(x):
    if x.empty:return x
    y=x[["date","value"]].copy().sort_values("date")
    # 달력 기준 재색인: missing은 NaN 유지한다. 절대 0으로 채우지 않는다.
    idx=pd.date_range(y.date.min(),y.date.max(),freq="MS")
    y=y.set_index("date").reindex(idx).rename_axis("date").reset_index()
    y["ma3"]=y["value"].rolling(3,min_periods=2).mean()
    y["ma12"]=y["value"].rolling(12,min_periods=6).mean()
    y["std12"]=y["value"].rolling(12,min_periods=6).std()
    y["yoy_pct"]=y["value"].pct_change(12,fill_method=None)*100
    return y

def kpi_card(label, value, unit="대", sub="실제 관측값"):
    st.markdown(f"""<div class="card"><div class="kpi-label">{label}</div>
    <div class="kpi-value">{value} <span style="font-size:.8rem">{unit}</span></div>
    <div class="kpi-sub">{sub}</div></div>""",unsafe_allow_html=True)

def line_chart():
    parts=[]
    for label,color in [("생산",BLUE),("내수",GREEN),("수출",ORANGE)]:
        x=series(label)
        if not x.empty:
            q=x[["date","value"]].copy();q["구분"]=label;q["색"]=color;parts.append(q)
    if not parts:
        st.info("국내 월별 시장 데이터가 없습니다.");return
    d=pd.concat(parts,ignore_index=True)
    c=alt.Chart(d).mark_line(strokeWidth=2.2,point=False).encode(
        x=alt.X("date:T",title=None,axis=alt.Axis(format="%Y-%m",labelAngle=0,tickCount=8)),
        y=alt.Y("value:Q",title="대",scale=alt.Scale(zero=False)),
        color=alt.Color("구분:N",scale=alt.Scale(domain=["생산","내수","수출"],range=[BLUE,GREEN,ORANGE]),legend=alt.Legend(orient="top")),
        tooltip=[alt.Tooltip("date:T",title="월",format="%Y-%m"),"구분:N",alt.Tooltip("value:Q",title="대수",format=",")]
    ).properties(height=300).interactive()
    st.altair_chart(c,use_container_width=True)

def annual_chart():
    rows=[]
    for label in ["생산","내수","수출"]:
        x=series(label)
        if x.empty:continue
        x=x.assign(year=x.date.dt.year,month=x.date.dt.month)
        latest_year=int(x.year.max())
        latest_month=int(x.loc[x.year==latest_year,"month"].max())
        # 모든 연도를 최신연도와 동일 월수로 비교. 완결연도 합계를 최신 부분연도와 직접 비교하지 않음.
        y=x[x.month<=latest_month].groupby("year",as_index=False)["value"].sum()
        y["구분"]=label;y["기준월"]=latest_month;rows.append(y)
    if not rows:
        st.info("연간 비교 데이터가 없습니다.");return
    d=pd.concat(rows)
    c=alt.Chart(d).mark_line(point=True,strokeWidth=2.1).encode(
        x=alt.X("year:O",title="연도"),
        y=alt.Y("value:Q",title="동일기간 누적 대수",scale=alt.Scale(zero=False)),
        color=alt.Color("구분:N",scale=alt.Scale(domain=["생산","내수","수출"],range=[BLUE,GREEN,ORANGE])),
        tooltip=["year:O","구분:N",alt.Tooltip("value:Q",format=",")]
    ).properties(height=245)
    st.altair_chart(c,use_container_width=True)
    m=int(d["기준월"].max())
    st.caption(f"※ 최신연도 기준 1~{m}월 동일기간 누적 비교입니다. 부분연도를 완결연도처럼 표시하지 않습니다.")

def normalize_global():
    if global_market.empty or "period" not in global_market or "value" not in global_market:return pd.DataFrame()
    g=global_market.copy()
    g["date"]=pd.to_datetime(g["period"],errors="coerce")
    g["value"]=pd.to_numeric(g["value"],errors="coerce")
    return g.dropna(subset=["date","value"])

def global_view():
    g=normalize_global()
    if g.empty:
        st.info("글로벌 시장 CSV가 연결되면 이 영역에 실제 관측 시계열이 표시됩니다.");return
    label_col="country_code" if "country_code" in g else ("country" if "country" in g else None)
    if not label_col:
        st.dataframe(g.tail(12),use_container_width=True,hide_index=True);return
    countries=sorted(g[label_col].dropna().astype(str).unique())
    selected=st.multiselect("비교 국가",countries,default=countries[:min(6,len(countries))],key="global_country")
    v=g[g[label_col].astype(str).isin(selected)]
    if "metric" in v:
        metrics=sorted(v["metric"].dropna().astype(str).unique())
        metric=st.selectbox("글로벌 지표",metrics,key="global_metric")
        v=v[v["metric"].astype(str)==metric]
    c=alt.Chart(v).mark_line(point=True).encode(
        x=alt.X("date:T",title=None),y=alt.Y("value:Q",title="실제 관측값",scale=alt.Scale(zero=False)),
        color=alt.Color(f"{label_col}:N",title="국가"),
        tooltip=[alt.Tooltip("date:T",format="%Y-%m"),f"{label_col}:N",alt.Tooltip("value:Q",format=",")]
    ).properties(height=250).interactive()
    st.altair_chart(c,use_container_width=True)

def volatility_chart(label):
    f=features(series(label))
    if f.empty:
        st.info("계산 가능한 시계열이 없습니다.");return
    base=f.melt("date",["value","ma3"],var_name="계열",value_name="값")
    base["계열"]=base["계열"].map({"value":"실제값","ma3":"3개월 이동평균"})
    c1=alt.Chart(base.dropna()).mark_line(strokeWidth=2).encode(
        x=alt.X("date:T",title=None),y=alt.Y("값:Q",title="대",scale=alt.Scale(zero=False)),
        color=alt.Color("계열:N",scale=alt.Scale(domain=["실제값","3개월 이동평균"],range=[GREEN,BLUE])),
        tooltip=[alt.Tooltip("date:T",format="%Y-%m"),"계열:N",alt.Tooltip("값:Q",format=",")]
    )
    c2=alt.Chart(f.dropna(subset=["std12"])).mark_area(opacity=.16,color=ORANGE).encode(
        x="date:T",y=alt.Y("std12:Q",title="12개월 표준편차")
    )
    st.altair_chart(alt.layer(c1,c2).resolve_scale(y="independent").properties(height=275),use_container_width=True)

QUESTIONS=["최근 내수 흐름은 어떻게 변했나?","수출 변동성이 커진 시점은 언제인가?","최근 생산 흐름에서 확인할 변화는 무엇인가?"]

def answer(q):
    label="내수" if "내수" in q else ("수출" if "수출" in q else "생산")
    f=features(series(label)); actual=f.dropna(subset=["value"]) if not f.empty else f
    if actual is None or actual.empty:
        return "계산 가능한 실제 관측값이 없습니다.","원인 해석도 보류합니다.","데이터 연결 상태를 먼저 확인합니다."
    r=actual.iloc[-1]; yoy=r.get("yoy_pct",np.nan)
    if "변동성" in q:
        v=f.dropna(subset=["std12"])
        if v.empty: fact="연속 관측 구간이 부족해 12개월 변동성 최대시점을 계산하지 않습니다."
        else:
            p=v.loc[v.std12.idxmax()]
            fact=f"{p.date:%Y-%m}의 12개월 표준편차가 {p.std12:,.0f}대로 관측 구간 중 가장 컸습니다."
        why="변동성 확대는 월별 움직임이 커졌다는 관찰입니다. 수출지역·조업일수·외부 사건은 별도 근거 확인 전 원인으로 단정하지 않습니다."
    else:
        yy="비교 기준월 부족" if pd.isna(yoy) else f"{yoy:+.1f}%"
        fact=f"최근 {label} 관측값은 {r.date:%Y-%m} {r.value:,.0f}대이며 전년 동월 대비 {yy}입니다."
        why="방향성은 실제값과 이동평균으로 확인합니다. 계절성·수요·생산차질 등 원인은 현재 시계열만으로 단정하지 않습니다."
    action="시장 변화와 ABS → ESC → 통합제동 → Brake-by-Wire 기술신호를 함께 보고 Coil Ass'y 접근 가능 시장을 추가 검증합니다."
    return fact,why,action

def patent_chart():
    p=patent_yearly.copy()
    if p.empty:
        st.warning("patent_technology_yearly.csv가 아직 연결되지 않았습니다. 특허 건수를 임의 생성하거나 0으로 표시하지 않습니다.");return
    year=next((c for c in ["year","출원연도","publication_year"] if c in p),None)
    count=next((c for c in ["count","건수","patent_count"] if c in p),None)
    tech=next((c for c in ["technology","기술","technology_group","tech_group"] if c in p),None)
    if not all([year,count,tech]):
        st.warning("특허 CSV 컬럼 구조를 확인해야 합니다.");st.dataframe(p.head(),hide_index=True,use_container_width=True);return
    p[count]=pd.to_numeric(p[count],errors="coerce");p=p.dropna(subset=[count])
    c=alt.Chart(p).mark_line(point=True,strokeWidth=2).encode(
        x=alt.X(f"{year}:O",title="연도"),y=alt.Y(f"{count}:Q",title="특허 건수"),
        color=alt.Color(f"{tech}:N",title="기술"),
        tooltip=[f"{year}:O",f"{tech}:N",alt.Tooltip(f"{count}:Q",format=",")]
    ).properties(height=240).interactive()
    st.altair_chart(c,use_container_width=True)

def signal_cards():
    if signals.empty:
        st.info("등록된 기술 신호가 없습니다.");return
    x=signals.copy()
    if "signal_year" in x:x=x.sort_values("signal_year",ascending=False)
    for _,r in x.head(4).iterrows():
        company=html.escape(str(r.get("company","기술자료")))
        year=html.escape(str(r.get("signal_year","")))
        event=html.escape(str(r.get("event","")))
        status=" · 검증완료" if str(r.get("verification_status",""))=="VERIFIED" else ""
        st.markdown(f'<div class="signal"><strong>{company} · {year}{status}</strong><br><span>{event}</span></div>',unsafe_allow_html=True)

latest_dates=[latest(x)["date"] for x in ["생산","내수","수출"] if latest(x) is not None]
basis=max(latest_dates).strftime("%Y-%m") if latest_dates else "데이터 미연결"

st.markdown(f"""<div class="hero"><div class="hero-row"><div>
<div class="hero-title">ABS Market Intelligence</div>
<div class="hero-sub">자동차 시장 흐름과 제동기술 전환을 데이터로 읽는 1차 분석</div></div>
<div class="hero-rule">데이터 기준 {basis}<br>NULL/미수집 월은 0으로 대체하지 않음</div>
</div></div>""",unsafe_allow_html=True)

tab1,tab2=st.tabs(["01  시장동향","02  변동분석 · 기술동향"])

with tab1:
    st.markdown('<div class="section-title">01. 시장동향</div><div class="section-sub">국내 · 글로벌 자동차 시장을 실제 관측 데이터로 비교합니다.</div>',unsafe_allow_html=True)
    cols=st.columns(4)
    for c,label,color in zip(cols,["생산","내수","수출"],[BLUE,GREEN,ORANGE]):
        r=latest(label)
        with c:kpi_card(f"최근 {label}",fmt(None if r is None else r["value"]),"대","실제 관측값" if r is not None else "데이터 없음")
    # 공백월: 생산/내수/수출의 공통 전체 월 범위에서 값이 없는 셀 수
    with cols[3]:
        all_s=[features(series(x)) for x in ["생산","내수","수출"]]
        missing=sum(int(x["value"].isna().sum()) for x in all_s if not x.empty)
        kpi_card("미수집/공백",f"{missing:,}","셀","0으로 채우지 않음")

    left,right=st.columns([1.9,1])
    with left:
        with st.container(border=True):
            st.markdown("#### 국내 생산 · 내수 · 수출 월별 추이")
            st.caption("실제 관측값만 사용하며 미수집 월은 0으로 연결하지 않습니다.")
            line_chart()
    with right:
        with st.container(border=True):
            st.markdown("#### 연간 흐름 · 동일기간 비교")
            annual_chart()

    with st.container(border=True):
        st.markdown("#### 글로벌 주요 시장")
        st.caption("국가별 정의와 스케일이 다른 지표는 임의 합산하지 않습니다.")
        global_view()

with tab2:
    st.markdown('<div class="section-title">02. 변동분석 · 기술동향</div><div class="section-sub">시계열 변화 → 질문 → Fact/Why → 기술 근거를 한 화면에서 연결합니다.</div>',unsafe_allow_html=True)
    left,right=st.columns([1.25,1])
    with left:
        with st.container(border=True):
            st.markdown("#### 변동성 분석")
            vol_label=st.radio("분석 지표",["내수","수출","생산"],horizontal=True,label_visibility="collapsed")
            volatility_chart(vol_label)
            st.caption("12개월 표준편차는 값이 존재하는 관측구간으로 계산하며, 미수집 월을 0으로 만들지 않습니다.")
    with right:
        with st.container(border=True):
            st.markdown("#### 질문으로 보는 시장 분석")
            q=st.selectbox("분석 질문",QUESTIONS,label_visibility="collapsed")
            fact,why,action=answer(q)
            st.markdown(f'<div class="fact"><div class="box-head">관찰 (Fact)</div><div class="box-body">{fact}</div></div>',unsafe_allow_html=True)
            st.markdown(f'<div class="why"><div class="box-head">해석 (Why)</div><div class="box-body">{why}</div></div>',unsafe_allow_html=True)
            st.markdown(f'<div class="action"><div class="box-head">사업적 의미 · 다음 확인</div><div class="box-body">{action}</div></div>',unsafe_allow_html=True)

    with st.container(border=True):
        st.markdown("#### 기술동향")
        st.markdown("""<div class="flow"><div class="node">ABS<br><small>기본 제동 제어</small></div><div class="arrow">→</div>
        <div class="node">ESC<br><small>차량 자세 제어</small></div><div class="arrow">→</div>
        <div class="node">통합제동<br><small>전자식 통합 제어</small></div><div class="arrow">→</div>
        <div class="node">Brake-by-Wire / EMB<br><small>차세대 전자식 제동</small></div></div>""",unsafe_allow_html=True)
        a,b=st.columns([1.1,1])
        with a:
            st.markdown("##### 제동 관련 특허 활동 추이")
            st.caption("특허 건수는 시장점유율이 아니라 기술활동 신호로 해석합니다.")
            patent_chart()
        with b:
            st.markdown("##### 주요 기술 신호 · 공식자료 기반")
            signal_cards()

    st.caption("분석 원칙 | 관찰(Fact)과 해석(Why) 분리 · NULL/미수집은 0 대체 금지 · 점유율/장착률은 근거 확보 전 계산 금지")
