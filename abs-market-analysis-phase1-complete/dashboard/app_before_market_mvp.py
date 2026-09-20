from pathlib import Path
import pandas as pd
import streamlit as st

from processors.time_series import aggregate_timeseries

BASE_DIR = Path(__file__).resolve().parents[1]
INTERNAL_MART = BASE_DIR / "data" / "internal" / "mart" / "sales_monthly.parquet"
MARKET_MART = BASE_DIR / "data" / "mart" / "market_monthly.parquet"

st.set_page_config(
    page_title="시장동향 | ABS Market Intelligence",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
.block-container {padding-top: 1.1rem; padding-bottom: 2rem; max-width: 1500px;}
div[data-testid="stMetric"] {border:1px solid rgba(49,51,63,.12);padding:12px 14px;border-radius:14px;background:white;}
.small-note {font-size:.82rem;color:#667085;}
@media (max-width: 768px) {
 .block-container {padding-left:.75rem;padding-right:.75rem;}
 h1 {font-size:1.65rem !important;}
 h2,h3 {font-size:1.15rem !important;}
 div[data-testid="stHorizontalBlock"] {gap:.55rem;}
}
</style>
""", unsafe_allow_html=True)


def load_parquet(path: Path) -> pd.DataFrame:
    try:
        return pd.read_parquet(path) if path.exists() else pd.DataFrame()
    except Exception:
        return pd.DataFrame()


def options(df: pd.DataFrame, col: str):
    if df.empty or col not in df.columns:
        return []
    return sorted(df[col].dropna().astype(str).unique().tolist())

market_df = load_parquet(MARKET_MART)
company_df = load_parquet(INTERNAL_MART)

st.title("시장동향")
st.caption("ABS Coil Assy Market Intelligence")

page = st.segmented_control(
    "분석 화면",
    ["글로벌 시장", "국내 시장", "한국기업 글로벌", "우리회사 비교분석"],
    default="글로벌 시장",
)

with st.sidebar:
    st.header("공통 필터")
    freq = st.radio("시계열", ["월", "분기", "연"], horizontal=True)
    model_sel = st.multiselect("모델", options(company_df, "model_name"))
    customer_sel = st.multiselect("고객사", options(company_df, "customer_name"))
    region_sel = st.multiselect("판매지역", options(company_df, "sales_region"))
    st.divider()
    st.caption("필터는 데이터가 있는 항목부터 자동 활성화됩니다.")
    st.caption("빈 값은 0으로 대체하지 않습니다.")

filters = {}
if model_sel:
    filters["model_name"] = model_sel
if customer_sel:
    filters["customer_name"] = customer_sel
if region_sel:
    filters["sales_region"] = region_sel

if page != "우리회사 비교분석":
    st.info("외부시장 실제 데이터 연결 전입니다. 연결되지 않은 수치는 예시값을 넣지 않고 '데이터 없음'으로 유지합니다.")
    c1,c2,c3,c4 = st.columns(4)
    c1.metric("시장규모", "데이터 없음")
    c2.metric("전년 대비", "산출불가")
    c3.metric("5년 CAGR", "산출불가")
    c4.metric("데이터 기준", "데이터 없음")
    st.subheader(f"{page} 시계열")
    st.caption("KAMA 공개 월보 및 기타 무료 공개데이터 연결 후 표시됩니다.")
else:
    st.subheader("우리회사 경쟁력 비교")
    st.caption("시장과 같은 시간축으로 당사 매출·판매량·점유율(추정)·성장 Gap을 비교합니다.")

    if company_df.empty:
        st.warning("사내자료가 아직 등록되지 않았습니다. 사내자료가 없어도 외부시장 화면은 정상 동작합니다.")
        c1,c2,c3,c4 = st.columns(4)
        c1.metric("당사 매출", "데이터 없음")
        c2.metric("당사 판매량", "데이터 없음")
        c3.metric("시장점유율(추정)", "산출불가")
        c4.metric("성장 Gap", "산출불가")
    else:
        sales_ts = aggregate_timeseries(company_df, "sales_amount", freq, filters)
        qty_ts = aggregate_timeseries(company_df, "sales_qty", freq, filters)
        total_sales = company_df["sales_amount"].sum(min_count=1) if "sales_amount" in company_df else pd.NA
        total_qty = company_df["sales_qty"].sum(min_count=1) if "sales_qty" in company_df else pd.NA
        c1,c2,c3,c4 = st.columns(4)
        c1.metric("당사 매출", "데이터 없음" if pd.isna(total_sales) else f"{total_sales:,.0f}")
        c2.metric("당사 판매량", "데이터 없음" if pd.isna(total_qty) else f"{total_qty:,.0f}")
        c3.metric("시장점유율(추정)", "산출불가")
        c4.metric("성장 Gap", "산출불가")

        left,right = st.columns(2)
        with left:
            st.markdown("#### 매출 시계열")
            if not sales_ts.empty:
                st.line_chart(sales_ts.set_index("period_label"))
        with right:
            st.markdown("#### 판매량 시계열")
            if not qty_ts.empty:
                st.line_chart(qty_ts.set_index("period_label"))

st.divider()
st.markdown("<span class='small-note'>원칙: 실제값/추정값 분리 · 결측≠0 · 공통기간 비교 · 출처/기준일/모델버전 추적</span>", unsafe_allow_html=True)
