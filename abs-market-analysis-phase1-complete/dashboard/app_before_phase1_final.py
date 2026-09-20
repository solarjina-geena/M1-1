from pathlib import Path
from datetime import datetime

import altair as alt
import pandas as pd
import streamlit as st


# ============================================================
# [기본 경로]
# - 기존 데이터 수집/검증 로직은 건드리지 않습니다.
# - 이미 만들어진 MART만 읽어서 화면에 표시합니다.
# ============================================================

BASE_DIR = Path(__file__).resolve().parents[1]
MARKET_MART = BASE_DIR / "data" / "mart" / "market_monthly.parquet"
SIGNAL_MART = BASE_DIR / "data" / "mart" / "technology_signal.parquet"
SOURCE_LOG = BASE_DIR / "data" / "metadata" / "source_log.csv"


# ============================================================
# [페이지 설정]
# ============================================================

st.set_page_config(
    page_title="자동차 시장 변화 분석",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="collapsed",
)


# ============================================================
# [화면 디자인]
# - 한 화면에 정보가 들어오도록 여백/글자/카드를 작게 조정합니다.
# - 불필요한 큰 박스와 긴 설명은 줄였습니다.
# ============================================================

st.markdown(
    """
    <style>
    .block-container {
        padding-top: 0.8rem;
        padding-bottom: 1.2rem;
        max-width: 1600px;
    }

    header[data-testid="stHeader"] {
        background: rgba(255,255,255,0);
    }

    .main-title {
        font-size: 1.72rem;
        font-weight: 800;
        letter-spacing: -0.045em;
        color: #172033;
        margin-bottom: 0.08rem;
    }

    .main-sub {
        color: #6b7280;
        font-size: 0.88rem;
        margin-bottom: 0.35rem;
    }

    .section-title {
        font-size: 1.02rem;
        font-weight: 800;
        letter-spacing: -0.025em;
        color: #172033;
        margin: 0 0 0.1rem 0;
    }

    .section-sub {
        color: #7b8495;
        font-size: 0.77rem;
        margin-bottom: 0.25rem;
    }

    .mini-note {
        color: #7b8495;
        font-size: 0.72rem;
        line-height: 1.45;
    }

    [data-testid="stMetric"] {
        background: #ffffff;
        border: 1px solid #edf0f4;
        border-radius: 12px;
        padding: 0.58rem 0.72rem;
        box-shadow: 0 1px 3px rgba(16,24,40,.025);
    }

    [data-testid="stMetricLabel"] {
        font-size: 0.72rem;
        color: #697386;
    }

    [data-testid="stMetricValue"] {
        font-size: 1.18rem;
        font-weight: 750;
    }

    [data-testid="stMetricDelta"] {
        font-size: 0.70rem;
    }

    div[data-testid="stVerticalBlockBorderWrapper"] {
        border-color: #edf0f4;
        border-radius: 14px;
        background: #ffffff;
    }

    .insight-box {
        border-left: 3px solid #5b6f95;
        background: #f8fafc;
        padding: 0.58rem 0.72rem;
        border-radius: 0 10px 10px 0;
        font-size: 0.80rem;
        line-height: 1.48;
        margin-bottom: 0.35rem;
    }

    .tech-flow {
        display: grid;
        grid-template-columns: 1fr auto 1fr auto 1fr auto 1fr;
        gap: 7px;
        align-items: center;
        margin: 0.35rem 0 0.45rem 0;
    }

    .tech-node {
        background: #f8fafc;
        border: 1px solid #e7ebf0;
        border-radius: 11px;
        padding: 0.62rem 0.45rem;
        text-align: center;
        min-height: 66px;
    }

    .tech-node strong {
        display: block;
        color: #172033;
        font-size: 0.86rem;
    }

    .tech-node span {
        color: #7b8495;
        font-size: 0.69rem;
    }

    .tech-arrow {
        color: #a1a8b5;
        font-weight: 800;
    }

    .source-card {
        background: #fbfcfe;
        border: 1px solid #edf0f4;
        border-radius: 10px;
        padding: 0.55rem 0.65rem;
        min-height: 78px;
        font-size: 0.76rem;
    }

    .stTabs [data-baseweb="tab-list"] {
        gap: 6px;
    }

    .stTabs [data-baseweb="tab"] {
        height: 38px;
        padding-left: 18px;
        padding-right: 18px;
        font-size: 0.86rem;
        font-weight: 700;
    }

    div[data-testid="stRadio"] label {
        font-size: 0.76rem;
    }

    @media (max-width: 900px) {
        .block-container {
            padding-left: 0.7rem;
            padding-right: 0.7rem;
        }
        .tech-flow {
            grid-template-columns: 1fr;
        }
        .tech-arrow {
            text-align: center;
            transform: rotate(90deg);
        }
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# [데이터 불러오기]
# ============================================================

@st.cache_data
def load_market():
    if not MARKET_MART.exists():
        return pd.DataFrame()
    return pd.read_parquet(MARKET_MART)


@st.cache_data
def load_signals():
    if not SIGNAL_MART.exists():
        return pd.DataFrame()
    return pd.read_parquet(SIGNAL_MART)


@st.cache_data
def load_source_log():
    if not SOURCE_LOG.exists():
        return pd.DataFrame()
    try:
        return pd.read_csv(SOURCE_LOG, dtype="string")
    except Exception:
        return pd.DataFrame()


market = load_market()
signals = load_signals()
source_log = load_source_log()


# ============================================================
# [시장 데이터 공통 함수]
# ============================================================

METRIC_CANDIDATES = {
    "생산": [
        "VEHICLE_PRODUCTION_TOTAL",
    ],
    "내수": [
        "VEHICLE_DOMESTIC_TOTAL",
        "VEHICLE_DOMESTIC_SALES_TOTAL",
        "DOMESTIC_SALES_TOTAL",
        "VEHICLE_SALES_DOMESTIC_TOTAL",
    ],
    "수출": [
        "VEHICLE_EXPORT_TOTAL",
        "EXPORT_TOTAL",
        "VEHICLE_SALES_EXPORT_TOTAL",
    ],
}


def find_metric(label, scope="KOREA"):
    """현재 MART에 실제로 존재하는 metric 이름을 자동으로 찾습니다."""
    if market.empty or "metric" not in market.columns:
        return None

    view = market.copy()

    if "market_scope" in view.columns:
        view = view[
            view["market_scope"].astype(str).str.upper()
            == str(scope).upper()
        ]

    available = set(view["metric"].astype(str))

    for candidate in METRIC_CANDIDATES[label]:
        if candidate in available:
            return candidate

    keyword = {
        "생산": "PRODUCTION",
        "내수": "DOMESTIC",
        "수출": "EXPORT",
    }[label]

    matches = [
        x for x in available
        if keyword in x.upper() and "TOTAL" in x.upper()
    ]

    return sorted(matches)[0] if matches else None


def monthly_series(label, scope="KOREA"):
    """생산/내수/수출 월별 실제값을 반환합니다."""
    metric = find_metric(label, scope)

    if metric is None or market.empty:
        return pd.DataFrame()

    df = market[
        (market["market_scope"].astype(str).str.upper() == scope.upper())
        & (market["metric"].astype(str) == metric)
    ].copy()

    if df.empty:
        return df

    df["date"] = pd.to_datetime(
        df["period"].astype(str),
        format="%Y-%m",
        errors="coerce",
    )
    df["value"] = pd.to_numeric(df["value"], errors="coerce")

    df = (
        df.dropna(subset=["date", "value"])
        .sort_values("date")
        .drop_duplicates(subset=["date"], keep="last")
        .reset_index(drop=True)
    )

    # 중요: NULL/미수집 월은 0으로 만들지 않는다.
    # 실제 원자료 값이 0인 경우만 0으로 인정한다.
    df["series"] = label
    return df[["date", "value", "series"]]


def calendar_features(df):
    """
    달력 기준 시계열 분석.
    없는 월은 임의로 채우지 않습니다.
    """
    if df.empty:
        return pd.DataFrame()

    x = (
        df[["date", "value"]]
        .drop_duplicates("date", keep="last")
        .set_index("date")
        .sort_index()
    )

    full = pd.date_range(x.index.min(), x.index.max(), freq="MS")
    x = x.reindex(full)
    x.index.name = "date"

    x["mom_pct"] = x["value"].pct_change(1, fill_method=None) * 100
    x["yoy_pct"] = x["value"].pct_change(12, fill_method=None) * 100
    x["ma3"] = x["value"].rolling(3, min_periods=3).mean()
    x["std12"] = x["value"].rolling(12, min_periods=12).std()
    x["missing"] = x["value"].isna()

    return x.reset_index()


def latest_actual(df):
    if df.empty:
        return None
    x = df.dropna(subset=["value"]).sort_values("date")
    return None if x.empty else x.iloc[-1]


def period_start_date(mode, latest_date):
    if mode == "최근 3년":
        return latest_date - pd.DateOffset(years=3) + pd.DateOffset(months=1)
    if mode == "최근 5년":
        return latest_date - pd.DateOffset(years=5) + pd.DateOffset(months=1)
    if mode == "최근 10년":
        return latest_date - pd.DateOffset(years=10) + pd.DateOffset(months=1)
    return pd.Timestamp("1900-01-01")


def fmt_count(v):
    if v is None or pd.isna(v):
        return "-"
    return f"{v:,.0f}대"


def fmt_pct(v):
    if v is None or pd.isna(v):
        return "-"
    return f"{v:+.1f}%"


def safe_yoy(df):
    """최신월과 정확히 12개월 전을 비교합니다."""
    f = calendar_features(df)
    if f.empty:
        return None
    actual = f.dropna(subset=["value"])
    if actual.empty:
        return None
    return actual.iloc[-1]["yoy_pct"]


def annual_total(df, year):
    if df.empty:
        return None
    x = df[df["date"].dt.year == year]["value"]
    if x.empty:
        return None
    return float(x.sum())


def annual_change(df, year):
    now = annual_total(df, year)
    prev = annual_total(df, year - 1)
    if now is None or prev in (None, 0):
        return None
    return (now / prev - 1) * 100


# ============================================================
# [차트 1] 생산·내수·수출을 한 그래프에 표시
# ============================================================

def market_change_chart(period_mode):
    frames = [
        monthly_series("생산"),
        monthly_series("내수"),
        monthly_series("수출"),
    ]
    frames = [x for x in frames if not x.empty]

    if not frames:
        st.warning("월별 생산·내수·수출 데이터를 찾지 못했습니다.")
        return

    df = pd.concat(frames, ignore_index=True)
    latest_date = df["date"].max()
    start = period_start_date(period_mode, latest_date)
    df = df[df["date"] >= start].copy()

    # 월별 점에 접근하면 세 지표의 숫자를 한 번에 보기 위한 피벗
    pivot = (
        df.pivot_table(
            index="date",
            columns="series",
            values="value",
            aggfunc="last",
        )
        .reset_index()
    )

    # 실제 관측값 범위로 Y축을 잡아 0축 때문에 변화가 눌리지 않게 한다.
    ymin = float(df["value"].min())
    ymax = float(df["value"].max())
    pad = max((ymax - ymin) * 0.06, abs(ymax) * 0.015, 1.0)
    y_domain = [ymin - pad, ymax + pad]

    # 선은 3개를 한 그래프에 겹쳐서 표현
    line = (
        alt.Chart(df)
        .mark_line(point=alt.OverlayMarkDef(size=22, filled=True))
        .encode(
            x=alt.X(
                "date:T",
                title=None,
                axis=alt.Axis(format="%Y", labelAngle=0, tickCount="year"),
            ),
            y=alt.Y(
                "value:Q",
                title="대수",
                axis=alt.Axis(format="~s"),
                scale=alt.Scale(domain=y_domain, zero=False, nice=False),
            ),
            color=alt.Color(
                "series:N",
                title=None,
                scale=alt.Scale(
                    domain=["생산", "내수", "수출"],
                    range=["#355C9A", "#2F8F83", "#D48645"],
                ),
            ),
            tooltip=[
                alt.Tooltip("date:T", title="월", format="%Y-%m"),
                alt.Tooltip("series:N", title="구분"),
                alt.Tooltip("value:Q", title="대수", format=",.0f"),
            ],
        )
        .properties(height=315)
        .interactive()
    )

    st.altair_chart(line, use_container_width=True)

    # 최근 12개월 숫자는 그래프를 가리지 않도록 접어서 제공
    with st.expander("최근 월별 숫자 보기", expanded=False):
        table = pivot.sort_values("date", ascending=False).head(12).copy()
        table["월"] = table["date"].dt.strftime("%Y-%m")
        cols = ["월"] + [x for x in ["생산", "내수", "수출"] if x in table.columns]
        st.dataframe(
            table[cols],
            hide_index=True,
            use_container_width=True,
            height=245,
            column_config={
                "생산": st.column_config.NumberColumn(format="%,.0f"),
                "내수": st.column_config.NumberColumn(format="%,.0f"),
                "수출": st.column_config.NumberColumn(format="%,.0f"),
            },
        )


# ============================================================
# [차트 2] 지금 시장은?
# ============================================================

def current_market_chart(compare_mode, selected_year):
    rows = []

    for label in ["생산", "내수", "수출"]:
        df = monthly_series(label)
        if df.empty:
            continue

        if compare_mode == "전년 대비":
            # 선택 연도의 월별 합계와 전년 같은 기간을 비교
            current = df[df["date"].dt.year == selected_year].copy()
            previous = df[df["date"].dt.year == selected_year - 1].copy()

            if current.empty:
                continue

            max_month = int(current["date"].dt.month.max())
            previous = previous[previous["date"].dt.month <= max_month]

            current_value = float(current["value"].sum())
            previous_value = (
                float(previous["value"].sum())
                if not previous.empty
                else None
            )

            change = (
                (current_value / previous_value - 1) * 100
                if previous_value not in (None, 0)
                else None
            )

            rows.append({
                "구분": label,
                "값": current_value,
                "증감률": change,
                "비교": f"{selected_year}년 1~{max_month}월",
            })

        else:
            value = annual_total(df, selected_year)
            if value is None:
                continue
            rows.append({
                "구분": label,
                "값": value,
                "증감률": annual_change(df, selected_year),
                "비교": f"{selected_year}년",
            })

    chart_df = pd.DataFrame(rows)

    if chart_df.empty:
        st.info("선택한 기간의 시장 데이터가 없습니다.")
        return

    bars = (
        alt.Chart(chart_df)
        .mark_bar(cornerRadiusTopLeft=5, cornerRadiusTopRight=5)
        .encode(
            x=alt.X("구분:N", title=None, sort=["생산", "내수", "수출"]),
            y=alt.Y("값:Q", title="대수", axis=alt.Axis(format="~s")),
            color=alt.Color(
                "구분:N",
                legend=None,
                scale=alt.Scale(
                    domain=["생산", "내수", "수출"],
                    range=["#355C9A", "#2F8F83", "#D48645"],
                ),
            ),
            tooltip=[
                alt.Tooltip("구분:N", title="구분"),
                alt.Tooltip("비교:N", title="기간"),
                alt.Tooltip("값:Q", title="대수", format=",.0f"),
                alt.Tooltip("증감률:Q", title="증감률", format="+.1f"),
            ],
        )
        .properties(height=245)
    )

    st.altair_chart(bars, use_container_width=True)


# ============================================================
# [시장 구조]
# - 회사 실제 점유율 근거가 아직 없으면 임의 숫자를 만들지 않습니다.
# - 대신 기술 전환 구조를 시각화합니다.
# ============================================================

def render_market_structure(market_type):
    st.markdown(
        f'<div class="section-title">{market_type} 시장 구조</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class="tech-flow">
            <div class="tech-node"><strong>ABS</strong><span>성숙 기술</span></div>
            <div class="tech-arrow">→</div>
            <div class="tech-node"><strong>ESC</strong><span>주류 제어</span></div>
            <div class="tech-arrow">→</div>
            <div class="tech-node"><strong>통합제동</strong><span>성장·전환</span></div>
            <div class="tech-arrow">→</div>
            <div class="tech-node"><strong>신기술</strong><span>Brake-by-Wire</span></div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.caption(
        "※ 당사 실제 시장점유율은 내부 매출/출하와 시장모수의 동일 기준 연결 후 표시합니다. "
        "근거 없는 점유율은 만들지 않습니다."
    )


# ============================================================
# [상세 분석 차트]
# ============================================================

def detailed_trend_chart(selected_series, period_mode):
    df = monthly_series(selected_series)

    if df.empty:
        st.info(f"{selected_series} 월별 데이터가 없습니다.")
        return

    f = calendar_features(df)
    latest_date = f["date"].max()
    start = period_start_date(period_mode, latest_date)
    f = f[f["date"] >= start].copy()

    plot = f[["date", "value", "ma3"]].rename(
        columns={"value": "실제값", "ma3": "3개월 이동평균"}
    )
    plot = plot.melt(
        id_vars=["date"],
        var_name="구분",
        value_name="값",
    ).dropna(subset=["값"])

    chart = (
        alt.Chart(plot)
        .mark_line()
        .encode(
            x=alt.X(
                "date:T",
                title=None,
                axis=alt.Axis(format="%Y-%m", tickCount=7),
            ),
            y=alt.Y("값:Q", title="대수", scale=alt.Scale(zero=False)),
            color=alt.Color(
                "구분:N",
                title=None,
                scale=alt.Scale(
                    domain=["실제값", "3개월 이동평균"],
                    range=["#355C9A", "#D48645"],
                ),
            ),
            strokeWidth=alt.condition(
                alt.datum["구분"] == "실제값",
                alt.value(2.4),
                alt.value(2.0),
            ),
            tooltip=[
                alt.Tooltip("date:T", title="월", format="%Y-%m"),
                alt.Tooltip("구분:N", title="구분"),
                alt.Tooltip("값:Q", title="대수", format=",.0f"),
            ],
        )
        .properties(height=270)
        .interactive()
    )

    st.altair_chart(chart, use_container_width=True)


def volatility_chart(series_list, period_mode):
    frames = []

    for label in series_list:
        df = monthly_series(label)
        if df.empty:
            continue

        f = calendar_features(df)
        f["구분"] = label
        frames.append(f[["date", "std12", "구분"]])

    if not frames:
        st.info("변동성 데이터를 계산할 수 없습니다.")
        return

    x = pd.concat(frames, ignore_index=True)
    latest_date = x["date"].max()
    start = period_start_date(period_mode, latest_date)
    x = x[(x["date"] >= start) & x["std12"].notna()].copy()

    if x.empty:
        st.info("선택 기간에는 12개월 변동성 계산값이 없습니다.")
        return

    chart = (
        alt.Chart(x)
        .mark_line()
        .encode(
            x=alt.X(
                "date:T",
                title=None,
                axis=alt.Axis(format="%Y-%m", tickCount=7),
            ),
            y=alt.Y(
                "std12:Q",
                title="12개월 표준편차",
                scale=alt.Scale(zero=False),
            ),
            color=alt.Color(
                "구분:N",
                title=None,
                scale=alt.Scale(
                    domain=["내수", "수출"],
                    range=["#2F8F83", "#D48645"],
                ),
            ),
            tooltip=[
                alt.Tooltip("date:T", title="월", format="%Y-%m"),
                alt.Tooltip("구분:N", title="구분"),
                alt.Tooltip("std12:Q", title="변동성", format=",.0f"),
            ],
        )
        .properties(height=270)
        .interactive()
    )

    st.altair_chart(chart, use_container_width=True)


# ============================================================
# [질문 → 관찰 → 해석 → 기회]
# ============================================================

def insight_for_question(question):
    domestic = monthly_series("내수")
    export = monthly_series("수출")

    if question == "최근 내수 흐름은 어떻게 변했나?":
        df = domestic
        subject = "내수"
    elif question == "수출 변동성이 커진 시점은 언제인가?":
        df = export
        subject = "수출"
    else:
        df = export if not export.empty else domestic
        subject = "시장"

    if df.empty:
        return (
            "계산 가능한 데이터가 없습니다.",
            "현재 자료만으로 해석하기 어렵습니다.",
            "시장 데이터 연결 상태를 먼저 확인합니다.",
        )

    f = calendar_features(df)
    actual = f.dropna(subset=["value"]).sort_values("date")

    latest = actual.iloc[-1]
    yoy_value = latest["yoy_pct"]

    if question == "수출 변동성이 커진 시점은 언제인가?":
        vol = f.dropna(subset=["std12"])
        if not vol.empty:
            peak = vol.loc[vol["std12"].idxmax()]
            fact = (
                f"{peak['date']:%Y-%m}에 12개월 변동성이 "
                f"{peak['std12']:,.0f}대로 가장 크게 나타났습니다."
            )
        else:
            fact = "연속 12개월 자료가 부족해 변동성 최대시점을 계산할 수 없습니다."

        why = (
            "변동성 확대는 시장 방향 자체보다 월별 충격이 커졌다는 신호입니다. "
            "당시 수출지역·생산차질·외부 사건과 함께 확인해야 합니다."
        )
        action = (
            "수출 변동이 큰 구간과 기술전환 신호를 겹쳐 보고 "
            "통합제동·신기술 적용시장 확대 여부를 추가 확인합니다."
        )
        return fact, why, action

    fact = (
        f"최근 {subject}은 {latest['date']:%Y-%m} "
        f"{latest['value']:,.0f}대이며, "
        f"전년 동월 대비 {fmt_pct(yoy_value)}입니다."
    )

    if pd.isna(yoy_value):
        why = "비교 기준월 데이터가 없어 전년 동월 변화만으로 방향을 단정하지 않습니다."
    elif yoy_value >= 0:
        why = "최근 값은 전년 동월보다 높습니다. 회복이 일시적인지 추세적인지는 이동평균과 함께 봐야 합니다."
    else:
        why = "최근 값은 전년 동월보다 낮습니다. 계절성·조업일수·수요 변화 등 외부 요인 확인이 필요합니다."

    action = (
        "전체 자동차 수량만 보지 않고 ABS → ESC → 통합제동 → "
        "Brake-by-Wire 전환과 연결해 당사 접근 가능 시장을 확인합니다."
    )

    return fact, why, action


# ============================================================
# [기술 신호 / 근거]
# ============================================================

def render_technology_evidence():
    if signals.empty:
        st.info("등록된 기술 신호가 없습니다.")
        return

    view = signals.copy()

    sort_cols = [
        c for c in ["signal_year", "company"]
        if c in view.columns
    ]
    if sort_cols:
        view = view.sort_values(
            sort_cols,
            ascending=[False] * len(sort_cols),
        )

    view = view.head(4)

    cols = st.columns(2)

    for i, (_, row) in enumerate(view.iterrows()):
        with cols[i % 2]:
            company = str(row.get("company", "기술자료"))
            year = row.get("signal_year", "")
            event = str(row.get("event", "")).strip()
            status = str(row.get("verification_status", "")).strip()
            source_url = row.get("source_url", None)

            st.markdown(
                f"""
                <div class="source-card">
                    <strong>{company}</strong>
                    <span style="color:#8a93a3;"> · {year}</span><br>
                    {event}
                </div>
                """,
                unsafe_allow_html=True,
            )

            if status == "VERIFIED":
                st.caption("공식자료 · 검증 완료")

            if source_url is not None and str(source_url).startswith("http"):
                st.link_button(
                    "근거자료 보기 ↗",
                    str(source_url),
                    use_container_width=True,
                )



# ============================================================
# [글로벌 시장 + 특허 데이터]
# ============================================================

GLOBAL_CANDIDATES = [
    BASE_DIR / "data" / "global" / "global_market_monthly_v7.csv",
    BASE_DIR / "data" / "global" / "global_market_monthly_v6.csv",
    BASE_DIR / "data" / "global" / "global_market_monthly_v5.csv",
    BASE_DIR / "data" / "global" / "global_market_monthly_v4.csv",
]
PATENT_CANDIDATES = [
    BASE_DIR / "data" / "processed" / "patent_technology_yearly.csv",
    BASE_DIR / "data" / "mart" / "patent_technology_yearly.csv",
    BASE_DIR / "data" / "metadata" / "patent_technology_yearly.csv",
]

@st.cache_data
def load_global_market():
    for p in GLOBAL_CANDIDATES:
        if p.exists():
            try:
                g = pd.read_csv(p)
                g["_source_file"] = p.name
                return g
            except Exception:
                pass
    return pd.DataFrame()

@st.cache_data
def load_patent_yearly():
    for p in PATENT_CANDIDATES:
        if p.exists():
            try:
                x = pd.read_csv(p)
                x["_source_file"] = p.name
                return x
            except Exception:
                pass
    return pd.DataFrame()

global_market = load_global_market()
patent_yearly = load_patent_yearly()

def normalize_global():
    if global_market.empty:
        return pd.DataFrame()
    g = global_market.copy()
    if "period" not in g.columns or "value" not in g.columns:
        return pd.DataFrame()
    g["date"] = pd.to_datetime(g["period"], errors="coerce")
    g["value"] = pd.to_numeric(g["value"], errors="coerce")
    g = g.dropna(subset=["date", "value"])
    # 결측은 삭제할 뿐 0으로 대체하지 않는다.
    if "country_code" not in g.columns:
        g["country_code"] = "UNKNOWN"
    if "metric" not in g.columns:
        g["metric"] = "UNKNOWN"
    if "market_group" not in g.columns:
        g["market_group"] = "기타"
    return g

def render_global_market():
    g = normalize_global()
    if g.empty:
        st.info("글로벌 V7 파일을 찾지 못했습니다. data/global/global_market_monthly_v7.csv를 그대로 두면 자동 연결됩니다.")
        return

    st.markdown('<div class="section-title">글로벌 자동차 시장</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="section-sub">국가별 정의와 스케일이 다른 지표는 임의 합산하지 않고, 실제 관측 series를 비교합니다.</div>',
        unsafe_allow_html=True,
    )

    demand_metrics = ["FIRST_REGISTRATION", "DOMESTIC_SALES", "DOMESTIC_REGISTRATION"]
    demand = g[g["metric"].isin(demand_metrics)].copy()
    if demand.empty:
        demand = g.copy()

    groups = sorted(demand["market_group"].dropna().astype(str).unique().tolist())
    selected_groups = st.multiselect("시장군", groups, default=groups, key="global_groups")
    view = demand[demand["market_group"].astype(str).isin(selected_groups)].copy()

    countries = sorted(view["country_code"].dropna().astype(str).unique().tolist())
    default_countries = countries[:8]
    selected = st.multiselect("국가", countries, default=default_countries, key="global_countries")
    view = view[view["country_code"].astype(str).isin(selected)].copy()

    if view.empty:
        st.info("선택한 조건에 표시할 실제 데이터가 없습니다.")
        return

    view["series"] = view["country_code"].astype(str) + " · " + view["metric"].astype(str)
    chart = (
        alt.Chart(view)
        .mark_line()
        .encode(
            x=alt.X("date:T", title=None, axis=alt.Axis(format="%Y", tickCount="year")),
            y=alt.Y("value:Q", title="대수", scale=alt.Scale(zero=False)),
            color=alt.Color("series:N", title=None),
            tooltip=[
                alt.Tooltip("date:T", title="월", format="%Y-%m"),
                alt.Tooltip("series:N", title="국가·지표"),
                alt.Tooltip("value:Q", title="값", format=",.0f"),
            ],
        )
        .properties(height=390)
        .interactive()
    )
    st.altair_chart(chart, use_container_width=True)
    st.caption("※ NULL/미수집 월은 0으로 만들지 않습니다. 국가별 실제 관측점만 사용합니다.")

def normalize_patent():
    if patent_yearly.empty:
        return pd.DataFrame()
    p = patent_yearly.copy()
    rename = {}
    for c in p.columns:
        cl = c.lower()
        if cl in ["year", "application_year", "연도"]:
            rename[c] = "year"
        elif cl in ["technology", "technology_group", "tech", "기술", "기술군"]:
            rename[c] = "technology"
        elif cl in ["count", "patent_count", "건수", "value"]:
            rename[c] = "count"
    p = p.rename(columns=rename)
    if not {"year","technology","count"}.issubset(p.columns):
        return pd.DataFrame()
    p["year"] = pd.to_numeric(p["year"], errors="coerce")
    p["count"] = pd.to_numeric(p["count"], errors="coerce")
    return p.dropna(subset=["year","technology","count"]).copy()

def render_technology_tab():
    st.markdown('<div class="section-title">특허로 본 기술 활동</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="section-sub">특허 건수는 시장점유율이 아니라 기술활동 신호입니다. 통합제동·BBW/EMB와 ABS·ESC는 스케일을 분리해 읽습니다.</div>',
        unsafe_allow_html=True,
    )

    p = normalize_patent()
    if not p.empty:
        # 명칭 정규화
        tech_map = {
            "INTEGRATED_BRAKE":"통합제동", "통합형 전자제동":"통합제동",
            "BBW_EMB":"BBW·EMB", "BBW/EMB":"BBW·EMB", "Brake-by-Wire / EMB":"BBW·EMB",
            "ABS":"ABS", "ESC":"ESC",
        }
        p["기술"] = p["technology"].astype(str).map(lambda x: tech_map.get(x, x))
        left = p[p["기술"].isin(["통합제동","BBW·EMB"])].copy()
        right = p[p["기술"].isin(["ABS","ESC"])].copy()

        left_chart = alt.Chart(left).mark_line(point=True).encode(
            x=alt.X("year:O", title="연도"),
            y=alt.Y("count:Q", title="통합제동 · BBW/EMB 특허 건수", scale=alt.Scale(zero=True)),
            color=alt.Color("기술:N", title=None),
            tooltip=["year:O","기술:N",alt.Tooltip("count:Q",format=",.0f")],
        )
        right_chart = alt.Chart(right).mark_line(point=True).encode(
            x=alt.X("year:O", title="연도"),
            y=alt.Y("count:Q", title="ABS · ESC 특허 건수", scale=alt.Scale(zero=True)),
            color=alt.Color("기술:N", title=None),
            tooltip=["year:O","기술:N",alt.Tooltip("count:Q",format=",.0f")],
        )
        st.altair_chart((left_chart | right_chart).resolve_scale(y="independent"), use_container_width=True)

        totals = p.groupby("기술", as_index=False)["count"].sum()
        cols = st.columns(4)
        for col, tech in zip(cols, ["통합제동","BBW·EMB","ABS","ESC"]):
            row = totals[totals["기술"] == tech]
            with col:
                st.metric(f"{tech} 특허", f"{int(row['count'].iloc[0]):,}건" if not row.empty else "-")
    else:
        st.warning(
            "특허 연도별 원본 CSV가 현재 연결되지 않았습니다. "
            "기존 특허 데이터를 0으로 만들거나 임의 복원하지 않습니다. "
            "patent_technology_yearly.csv가 있으면 이 화면에 자동 연결됩니다."
        )

    st.markdown("### 주요 기술 신호 (공식 자료 기반)")
    render_technology_evidence()

    st.markdown("### 기술 질문 · 해석")
    tq = st.selectbox(
        "기술 분석 질문",
        [
            "제동기술은 ABS/ESC에서 통합제동·Brake-by-Wire 방향으로 이동하는 신호가 있는가?",
            "최근 공식 기술 신호가 Coil Ass'y 접근가능 시장에 주는 의미는 무엇인가?",
            "특허 활동과 시장규모를 같은 의미로 봐도 되는가?",
        ],
        key="tech_question",
    )
    if tq.startswith("제동기술"):
        fact = "공식 기술 신호 데이터에는 Bosch의 Brake-by-Wire 시장진입·2030 전망과 Continental의 차세대 Integrated Brake-by-Wire 기술 신호가 등록되어 있습니다."
        why = "이는 기술 전환 방향을 확인하는 근거이지만, 실제 장착률이나 시장점유율을 직접 의미하지는 않습니다."
        action = "2차 과제에서 국가·OEM별 적용차종, 장착률, 시장점유율 근거를 연결해 접근가능 시장으로 확장합니다."
    elif tq.startswith("최근 공식"):
        fact = "현재 검증된 기술 신호는 통합제동/Brake-by-Wire 쪽에 집중되어 있습니다."
        why = "시장 총량이 정체되더라도 제동 아키텍처 전환이 Coil 구성과 적용 범위를 바꿀 수 있다는 가설을 검토할 수 있습니다."
        action = "시장규모 × 기술 장착률 × 시스템당 Coil 수를 같은 기준연도·차종으로 연결한 뒤 Opportunity를 계산합니다."
    else:
        fact = "특허 건수는 기술활동의 빈도이고 자동차 판매·생산량은 시장규모 지표입니다."
        why = "두 지표는 단위와 의미가 달라 절대값을 합산하거나 점유율로 해석하면 안 됩니다."
        action = "동일 시간축에서 방향과 변곡점만 비교하고, 인과관계는 뉴스·양산·수주 근거로 별도 검증합니다."

    st.info(f"**관찰(Fact)** · {fact}")
    st.info(f"**해석(Why)** · {why}")
    st.info(f"**다음 확인(Action)** · {action}")


# ============================================================
# HEADER
# ============================================================

all_monthly = [
    monthly_series("생산"),
    monthly_series("내수"),
    monthly_series("수출"),
]
all_monthly = [x for x in all_monthly if not x.empty]

if all_monthly:
    latest_market_date = max(x["date"].max() for x in all_monthly)
    first_market_date = min(x["date"].min() for x in all_monthly)
else:
    latest_market_date = pd.NaT
    first_market_date = pd.NaT

st.markdown(
    '<div class="main-title">ABS Market Intelligence</div>',
    unsafe_allow_html=True,
)

if pd.notna(latest_market_date):
    subtitle = (
        f"{first_market_date:%Y-%m} ~ {latest_market_date:%Y-%m} · "
        "월별 생산·내수·수출 흐름에서 시장 변화와 사업기회를 찾습니다."
    )
else:
    subtitle = "월별 생산·내수·수출 흐름에서 시장 변화와 사업기회를 찾습니다."

st.markdown(
    f'<div class="main-sub">{subtitle}</div>',
    unsafe_allow_html=True,
)


# ============================================================
# 2개 화면
# ============================================================

page1, page2, page3 = st.tabs(
    ["① 시장동향", "② 변동분석 · 질문", "③ 기술·특허"]
)


# ============================================================
# PAGE 1
# 1. 자동차시장 변화
# 2. 지금 시장은?
# ============================================================

with page1:

    market_scope_view = st.segmented_control(
        "시장 선택",
        ["국내 (한국)", "해외 (글로벌)"],
        default="국내 (한국)",
        key="market_scope_view",
    )

    if market_scope_view == "해외 (글로벌)":
        render_global_market()
        st.caption("국내 화면은 위 선택을 '국내 (한국)'으로 바꾸면 같은 탭에서 전환됩니다.")

    if market_scope_view == "국내 (한국)":
        left, right = st.columns([1.65, 1.0], gap="medium")

        # --------------------------------------------------------
        # ① 자동차시장 변화
        # --------------------------------------------------------
        with left:
            with st.container(border=True):
                title_col, period_col = st.columns([4.2, 1.35])

                with title_col:
                    st.markdown(
                        '<div class="section-title">국내 자동차시장 변화</div>',
                        unsafe_allow_html=True,
                    )
                    st.markdown(
                        '<div class="section-sub">'
                        '생산 · 내수 · 수출을 월별로 함께 비교합니다.'
                        '</div>',
                        unsafe_allow_html=True,
                    )

                with period_col:
                    trend_period = st.selectbox(
                        "기간",
                        ["최근 3년", "최근 5년", "최근 10년", "전체"],
                        index=2,
                        key="trend_period",
                        label_visibility="collapsed",
                    )

                market_change_chart(trend_period)

        # --------------------------------------------------------
        # ② 지금 시장은?
        # --------------------------------------------------------
        with right:
            with st.container(border=True):
                st.markdown(
                    '<div class="section-title">지금 시장은?</div>',
                    unsafe_allow_html=True,
                )
                st.markdown(
                    '<div class="section-sub">'
                    '선택 기간의 생산 · 내수 · 수출 규모와 전년 변화를 봅니다.'
                    '</div>',
                    unsafe_allow_html=True,
                )

                c_mode, c_year = st.columns([1.1, 1.0])

                with c_mode:
                    compare_mode = st.radio(
                        "비교 방식",
                        ["전년 대비", "연간"],
                        horizontal=True,
                        key="compare_mode",
                        label_visibility="collapsed",
                    )

                years = []
                for x in all_monthly:
                    years.extend(x["date"].dt.year.tolist())

                years = sorted(set(years), reverse=True)

                with c_year:
                    selected_year = st.selectbox(
                        "연도",
                        years if years else [datetime.now().year],
                        index=0,
                        key="current_year",
                        label_visibility="collapsed",
                    )

                current_market_chart(compare_mode, selected_year)

                # 내수/수출 선택에 따라 시장 구조 전환
                focus_market = st.segmented_control(
                    "시장 선택",
                    ["내수", "수출"],
                    default="내수",
                    key="focus_market",
                    label_visibility="collapsed",
                )

                if focus_market is None:
                    focus_market = "내수"

                render_market_structure(focus_market)

        # 최신값은 그래프 아래 아주 작게 요약
        latest_cols = st.columns(4)

        for col, label in zip(
            latest_cols[:3],
            ["생산", "내수", "수출"],
        ):
            df = monthly_series(label)
            row = latest_actual(df)

            with col:
                if row is not None:
                    st.metric(
                        f"최근 {label}",
                        fmt_count(row["value"]),
                        delta=f"{row['date']:%Y-%m} · YoY {fmt_pct(safe_yoy(df))}",
                        delta_color="off",
                    )
                else:
                    st.metric(f"최근 {label}", "-")

        with latest_cols[3]:
            # 결측월은 생산 기준으로 표시
            prod = monthly_series("생산")
            f = calendar_features(prod)
            missing = int(f["missing"].sum()) if not f.empty else 0

            st.metric(
                "데이터 공백",
                f"{missing}개월",
                delta="임의 보간 없음",
                delta_color="off",
            )



# ============================================================
# PAGE 2
# 3. 상세분석
# 4. 질문 → 해석 → 우리의 기회
# ============================================================

with page2:

    top_left, top_right = st.columns(2, gap="medium")

    # --------------------------------------------------------
    # ③ 상세분석
    # --------------------------------------------------------
    with top_left:
        with st.container(border=True):
            head1, head2 = st.columns([2.4, 1.0])

            with head1:
                st.markdown(
                    '<div class="section-title">내수 · 수출 상세 추이</div>',
                    unsafe_allow_html=True,
                )
                detail_series = st.segmented_control(
                    "지표",
                    ["내수", "수출"],
                    default="내수",
                    key="detail_series",
                    label_visibility="collapsed",
                )

            with head2:
                detail_period = st.selectbox(
                    "기간",
                    ["최근 3년", "최근 5년", "최근 10년", "전체"],
                    index=1,
                    key="detail_period",
                    label_visibility="collapsed",
                )

            if detail_series is None:
                detail_series = "내수"

            detailed_trend_chart(detail_series, detail_period)

            st.caption(
                "실제 월별값과 3개월 이동평균을 함께 표시합니다. "
                "기술별 판매량은 근거 데이터 확보 전 임의로 분해하지 않습니다."
            )

    # --------------------------------------------------------
    # 변동성
    # --------------------------------------------------------
    with top_right:
        with st.container(border=True):
            st.markdown(
                '<div class="section-title">변동성 분석</div>',
                unsafe_allow_html=True,
            )
            st.markdown(
                '<div class="section-sub">'
                '12개월 표준편차로 시장 움직임이 커진 시점을 확인합니다.'
                '</div>',
                unsafe_allow_html=True,
            )

            volatility_target = st.multiselect(
                "표시 지표",
                ["내수", "수출"],
                default=["내수", "수출"],
                key="volatility_target",
            )

            volatility_chart(
                volatility_target if volatility_target else ["내수", "수출"],
                detail_period,
            )

    bottom_left, bottom_right = st.columns([1.15, 1.0], gap="medium")

    # --------------------------------------------------------
    # ④ 질문 → 관찰 → 해석 → 기회
    # --------------------------------------------------------
    with bottom_left:
        with st.container(border=True):
            st.markdown(
                '<div class="section-title">그래서 무엇을 알고 싶은가?</div>',
                unsafe_allow_html=True,
            )

            question = st.selectbox(
                "분석 질문",
                [
                    "최근 내수 흐름은 어떻게 변했나?",
                    "수출 변동성이 커진 시점은 언제인가?",
                    "기술 전환에서 우리의 기회는 어디인가?",
                ],
                key="analysis_question",
            )

            fact, why, action = insight_for_question(question)

            st.markdown(
                f'<div class="insight-box"><b>관찰</b> · {fact}</div>',
                unsafe_allow_html=True,
            )
            st.markdown(
                f'<div class="insight-box"><b>해석</b> · {why}</div>',
                unsafe_allow_html=True,
            )
            st.markdown(
                f'<div class="insight-box"><b>기회</b> · {action}</div>',
                unsafe_allow_html=True,
            )

            st.caption(
                "※ 관찰은 계산된 데이터 사실이며, 해석과 기회는 "
                "시장·기술 근거를 추가 확인해야 하는 분석 가설입니다."
            )

    # --------------------------------------------------------
    # 신기술 대비 + 근거
    # --------------------------------------------------------
    with bottom_right:
        with st.container(border=True):
            st.markdown(
                '<div class="section-title">신기술 대비 · 시장 근거</div>',
                unsafe_allow_html=True,
            )
            st.markdown(
                """
                <div class="tech-flow">
                    <div class="tech-node"><strong>ABS</strong><span>MGH20</span></div>
                    <div class="tech-arrow">→</div>
                    <div class="tech-node"><strong>ESC</strong><span>MEB5</span></div>
                    <div class="tech-arrow">→</div>
                    <div class="tech-node"><strong>통합제동</strong><span>MEB5.2 · iMEB3</span></div>
                    <div class="tech-arrow">→</div>
                    <div class="tech-node"><strong>Brake-by-Wire</strong><span>차세대 기술</span></div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            render_technology_evidence()


# ============================================================
# PAGE 3 · 기술/특허
# ============================================================
with page3:
    render_technology_tab()

# ============================================================
# FOOTER
# ============================================================

st.caption(
    "분석 원칙 · NULL/미수집 월을 0으로 대체하지 않음 · 실제 관측값/추정값 구분 · "
    "시장점유율은 계산 근거 확보 후 표시"
)
