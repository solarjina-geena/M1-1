from pathlib import Path
from datetime import datetime

import pandas as pd
import streamlit as st


BASE_DIR = Path(__file__).resolve().parents[1]

MARKET_MART = (
    BASE_DIR / "data" / "mart" / "market_monthly.parquet"
)

SIGNAL_MART = (
    BASE_DIR / "data" / "mart" / "technology_signal.parquet"
)

SOURCE_LOG = (
    BASE_DIR / "data" / "metadata" / "source_log.csv"
)


# --------------------------------------------------
# PAGE
# --------------------------------------------------

st.set_page_config(
    page_title="Brake & Actuator Market Intelligence",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)


# --------------------------------------------------
# STYLE
# --------------------------------------------------

st.markdown(
    """
    <style>
    .block-container {
        padding-top: 1.5rem;
        padding-bottom: 3rem;
        max-width: 1550px;
    }

    [data-testid="stMetric"] {
        border: 1px solid rgba(49, 51, 63, 0.12);
        padding: 14px 16px;
        border-radius: 14px;
        background: white;
        box-shadow: 0 2px 8px rgba(0,0,0,0.035);
    }

    .hero {
        padding: 4px 0 10px 0;
    }

    .hero-title {
        font-size: 2rem;
        font-weight: 750;
        letter-spacing: -0.03em;
        margin-bottom: 2px;
    }

    .hero-sub {
        color: #667085;
        font-size: 0.95rem;
    }

    .section-title {
        font-size: 1.18rem;
        font-weight: 700;
        margin-top: 0.8rem;
        margin-bottom: 0.15rem;
    }

    .section-sub {
        color: #667085;
        font-size: 0.86rem;
        margin-bottom: 0.7rem;
    }

    .tech-flow {
        border: 1px solid rgba(49,51,63,.12);
        border-radius: 16px;
        padding: 22px;
        background: white;
        margin-top: 5px;
    }

    .tech-row {
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 8px;
    }

    .tech-box {
        flex: 1;
        text-align: center;
        padding: 14px 8px;
        border-radius: 12px;
        background: #f7f8fa;
        border: 1px solid #eaecf0;
    }

    .tech-main {
        font-weight: 700;
        font-size: 0.98rem;
    }

    .tech-state {
        color: #667085;
        font-size: 0.78rem;
        margin-top: 4px;
    }

    .tech-arrow {
        color: #98a2b3;
        font-size: 1.4rem;
        font-weight: 700;
    }

    .product-map {
        margin-top: 14px;
        color: #475467;
        font-size: 0.86rem;
        text-align: center;
    }

    .signal-card {
        border: 1px solid rgba(49,51,63,.12);
        border-radius: 13px;
        padding: 13px 14px;
        margin-bottom: 8px;
        background: white;
    }

    .signal-company {
        font-weight: 700;
    }

    .signal-meta {
        font-size: 0.78rem;
        color: #667085;
    }

    .signal-event {
        margin-top: 4px;
        font-size: 0.9rem;
    }

    .small-note {
        color: #667085;
        font-size: 0.8rem;
    }

    .status-ok {
        color: #027a48;
        font-weight: 650;
    }

    @media (max-width: 768px) {
        .block-container {
            padding-left: .7rem;
            padding-right: .7rem;
        }

        .hero-title {
            font-size: 1.55rem;
        }

        .tech-row {
            flex-direction: column;
        }

        .tech-box {
            width: 100%;
        }

        .tech-arrow {
            transform: rotate(90deg);
        }
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# --------------------------------------------------
# LOADERS
# --------------------------------------------------

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
        return pd.read_csv(
            SOURCE_LOG,
            dtype="string",
        )
    except Exception:
        return pd.DataFrame()


market = load_market()
signals = load_signals()
source_log = load_source_log()


# --------------------------------------------------
# HELPERS
# --------------------------------------------------

def vehicle_series(scope, category="TOTAL"):
    if market.empty:
        return pd.DataFrame()

    metric = f"VEHICLE_PRODUCTION_{category}"

    df = market[
        (market["market_scope"] == scope)
        & (market["metric"] == metric)
    ].copy()

    if df.empty:
        return df

    df["year"] = pd.to_numeric(
        df["period"].astype(str).str[:4],
        errors="coerce",
    )

    df["value"] = pd.to_numeric(
        df["value"],
        errors="coerce",
    )

    return (
        df.dropna(subset=["year", "value"])
        .sort_values("year")
        .reset_index(drop=True)
    )


def apply_year_filter(df, start_year, end_year):
    if df.empty:
        return df

    return df[
        (df["year"] >= start_year)
        & (df["year"] <= end_year)
    ].copy()


def latest_value(df):
    if df.empty:
        return None

    return float(df.iloc[-1]["value"])


def previous_value(df):
    if len(df) < 2:
        return None

    return float(df.iloc[-2]["value"])


def yoy(df):
    current = latest_value(df)
    previous = previous_value(df)

    if current is None or previous in (None, 0):
        return None

    return (current / previous - 1) * 100


def period_change(df):
    if len(df) < 2:
        return None

    first = float(df.iloc[0]["value"])
    last = float(df.iloc[-1]["value"])

    if first == 0:
        return None

    return (last / first - 1) * 100


def cagr(df):
    if len(df) < 2:
        return None

    first = float(df.iloc[0]["value"])
    last = float(df.iloc[-1]["value"])

    first_year = int(df.iloc[0]["year"])
    last_year = int(df.iloc[-1]["year"])

    years = last_year - first_year

    if first <= 0 or years <= 0:
        return None

    return ((last / first) ** (1 / years) - 1) * 100


def pct_text(value):
    if value is None or pd.isna(value):
        return "계산 불가"

    return f"{value:+.1f}%"


def million_vehicle(value):
    if value is None or pd.isna(value):
        return "데이터 없음"

    return f"{value / 1_000_000:,.1f}M"


def get_latest_collection_time():
    if source_log.empty:
        return None

    if "collected_at" not in source_log.columns:
        return None

    dt = pd.to_datetime(
        source_log["collected_at"],
        errors="coerce",
    ).dropna()

    if dt.empty:
        return None

    return dt.max()


global_all = vehicle_series("GLOBAL")
korea_all = vehicle_series("KOREA")

available_years = sorted(
    set(global_all.get("year", pd.Series(dtype=float)).dropna().astype(int))
    | set(korea_all.get("year", pd.Series(dtype=float)).dropna().astype(int))
)

if available_years:
    min_year = min(available_years)
    max_year = max(available_years)
else:
    min_year = 2010
    max_year = datetime.now().year


# --------------------------------------------------
# HEADER
# --------------------------------------------------

st.markdown(
    """
    <div class="hero">
        <div class="hero-title">
            Brake & Actuator Market Intelligence
        </div>
        <div class="hero-sub">
            시장 변화 · 기술 전환 · 제품 포트폴리오 · 사업기회 모니터링
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

latest_collection = get_latest_collection_time()

h1, h2, h3 = st.columns([1.3, 1.3, 3])

with h1:
    st.caption("시장 데이터 기준")
    st.markdown(
        f"**{max_year}년**"
        if available_years
        else "**확인 필요**"
    )

with h2:
    st.caption("최근 외부자료 수집")
    if latest_collection is not None:
        st.markdown(
            f"**{latest_collection:%Y-%m-%d %H:%M}**"
        )
    else:
        st.markdown("**기록 없음**")

with h3:
    st.caption("데이터 상태")
    st.markdown(
        "<span class='status-ok'>● 데이터 연결 정상</span>",
        unsafe_allow_html=True,
    )


# --------------------------------------------------
# SIDEBAR FILTER
# --------------------------------------------------

with st.sidebar:
    st.header("분석 기간")

    range_mode = st.radio(
        "기간 선택",
        [
            "최근 3년",
            "최근 5년",
            "최근 10년",
            "전체",
            "직접 선택",
        ],
    )

    if range_mode == "최근 3년":
        start_year = max(min_year, max_year - 2)
        end_year = max_year

    elif range_mode == "최근 5년":
        start_year = max(min_year, max_year - 4)
        end_year = max_year

    elif range_mode == "최근 10년":
        start_year = max(min_year, max_year - 9)
        end_year = max_year

    elif range_mode == "전체":
        start_year = min_year
        end_year = max_year

    else:
        selected = st.slider(
            "연도 범위",
            min_value=min_year,
            max_value=max_year,
            value=(min_year, max_year),
        )

        start_year, end_year = selected

    st.divider()

    st.markdown("**현재 분석 구간**")
    st.write(f"{start_year} ~ {end_year}")

    st.caption(
        "기간을 변경하면 시장 그래프와 성장지표가 함께 재계산됩니다."
    )

    st.divider()

    if st.button(
        "↻ 최신 데이터 확인",
        use_container_width=True,
    ):
        st.info(
            "V2-1에서는 수집 상태를 확인합니다. "
            "다음 단계에서 실제 외부자료 갱신 파이프라인을 연결합니다."
        )

    if st.button(
        "화면 데이터 새로고침",
        use_container_width=True,
    ):
        st.cache_data.clear()
        st.rerun()


global_df = apply_year_filter(
    global_all,
    start_year,
    end_year,
)

korea_df = apply_year_filter(
    korea_all,
    start_year,
    end_year,
)


# --------------------------------------------------
# KPI
# --------------------------------------------------

st.divider()

st.markdown(
    '<div class="section-title">시장 한눈에 보기</div>',
    unsafe_allow_html=True,
)

st.markdown(
    f'<div class="section-sub">{start_year}~{end_year} 선택기간 기준</div>',
    unsafe_allow_html=True,
)

k1, k2, k3, k4 = st.columns(4)

with k1:
    st.metric(
        "글로벌 자동차 생산",
        million_vehicle(latest_value(global_df)),
        delta=(
            pct_text(yoy(global_df)) + " YoY"
            if yoy(global_df) is not None
            else None
        ),
    )

with k2:
    st.metric(
        "한국 자동차 생산",
        million_vehicle(latest_value(korea_df)),
        delta=(
            pct_text(yoy(korea_df)) + " YoY"
            if yoy(korea_df) is not None
            else None
        ),
    )

with k3:
    st.metric(
        "글로벌 선택기간 변화",
        pct_text(period_change(global_df)),
        delta=f"CAGR {pct_text(cagr(global_df))}",
        delta_color="off",
    )

with k4:
    forecast = signals[
        signals["signal_type"] == "FORECAST"
    ].copy() if not signals.empty else pd.DataFrame()

    if not forecast.empty:
        forecast = forecast.sort_values(
            "forecast_year",
            ascending=False,
        )

        row = forecast.iloc[0]

        value = pd.to_numeric(
            row.get("forecast_value"),
            errors="coerce",
        )

        year = row.get("forecast_year")

        if not pd.isna(value):
            forecast_label = f">{value / 1_000_000:.1f}M대"
        else:
            forecast_label = "전망 확인"

        st.metric(
            "Brake-by-Wire 전망 신호",
            forecast_label,
            delta=f"{year} · {row.get('company')}",
            delta_color="off",
        )
    else:
        st.metric(
            "Brake-by-Wire 전망 신호",
            "데이터 없음",
        )


# --------------------------------------------------
# MARKET TREND
# --------------------------------------------------

st.markdown(
    '<div class="section-title">시장 시계열</div>',
    unsafe_allow_html=True,
)

st.markdown(
    '<div class="section-sub">실제 자동차 생산 통계를 기준으로 장기·최근 흐름을 비교합니다.</div>',
    unsafe_allow_html=True,
)

left, right = st.columns(2)

with left:
    st.markdown("#### 글로벌 자동차 생산")

    if global_df.empty:
        st.warning("선택 기간의 글로벌 데이터가 없습니다.")
    else:
        chart = global_df[
            ["year", "value"]
        ].set_index("year")

        chart.columns = ["생산대수"]

        st.line_chart(
            chart,
            height=310,
        )

        st.caption(
            f"선택기간 변화 {pct_text(period_change(global_df))} · "
            f"CAGR {pct_text(cagr(global_df))}"
        )

with right:
    st.markdown("#### 한국 자동차 생산")

    if korea_df.empty:
        st.warning("선택 기간의 한국 데이터가 없습니다.")
    else:
        chart = korea_df[
            ["year", "value"]
        ].set_index("year")

        chart.columns = ["생산대수"]

        st.line_chart(
            chart,
            height=310,
        )

        st.caption(
            f"선택기간 변화 {pct_text(period_change(korea_df))} · "
            f"CAGR {pct_text(cagr(korea_df))}"
        )


# --------------------------------------------------
# --------------------------------------------------
# TECHNOLOGY TRANSITION
# --------------------------------------------------

st.divider()

st.subheader("\uc81c\ub3d9 \uae30\uc220 \uc804\ud658")
st.caption(
    "\uc2dc\uc7a5 \ud1b5\uacc4\uc640 \uacf5\uc2dd \uae30\uc220 \uc2e0\ud638\ub97c \ud568\uaed8 \ubcf4\uba70 "
    "\uc81c\ub3d9 \uae30\uc220\uc758 \uc774\ub3d9 \ubc29\ud5a5\uc744 \ud655\uc778\ud569\ub2c8\ub2e4."
)

c1, a1, c2, a2, c3, a3, c4 = st.columns(
    [2.0, 0.35, 2.0, 0.35, 2.2, 0.35, 2.3],
    vertical_alignment="center",
)

with c1:
    st.markdown("### ABS")
    st.caption("\uc131\uc219 \uae30\uc220")
    st.markdown("**MGH20**")

with a1:
    st.markdown("### ?")

with c2:
    st.markdown("### ESC")
    st.caption("\uc8fc\ub958 \uc81c\uc5b4 \uae30\uc220")
    st.markdown("**MEB5**")

with a2:
    st.markdown("### ?")

with c3:
    st.markdown("### \ud1b5\ud569 \uc81c\ub3d9")
    st.caption("\uc131\uc7a5 \u00b7 \uc804\ud658 \uc601\uc5ed")
    st.markdown("**MEB5.2 ? iMEB3**")

with a3:
    st.markdown("### ?")

with c4:
    st.markdown("### Brake-by-Wire")
    st.caption("\ucc28\uc138\ub300 \uae30\uc220 \uc2e0\ud638")
    st.markdown("**\uc2dc\uc7a5 \uc9c4\uc785 \ubaa8\ub2c8\ud130\ub9c1**")

st.caption(
    "\uc2dc\uc7a5 \uc774\ub3d9 \ubc29\ud5a5  ?  "
    "ABS  ?  ESC  ?  \ud1b5\ud569 \uc81c\ub3d9  ?  Brake-by-Wire"
)


# --------------------------------------------------
# SIGNALS
# --------------------------------------------------

st.markdown("### \ucd5c\uc2e0 \uae30\uc220 \uc2e0\ud638")
st.caption(
    "\uacf5\uc2dd \uc6d0\uc790\ub8cc\uac00 \uc800\uc7a5\u00b7\uac80\uc99d\ub41c "
    "\uae30\uc220 \uc774\ubca4\ud2b8\ub9cc \ud45c\uc2dc\ud569\ub2c8\ub2e4."
)

if signals.empty:
    st.warning("\ub4f1\ub85d\ub41c \uae30\uc220 \uc2e0\ud638\uac00 \uc5c6\uc2b5\ub2c8\ub2e4.")

else:
    signal_view = signals.sort_values(
        ["signal_year", "company"],
        ascending=[False, True],
    )

    cols = st.columns(min(3, len(signal_view)))

    for i, (_, row) in enumerate(signal_view.iterrows()):
        with cols[i % len(cols)]:
            signal_type = str(row.get("signal_type", ""))
            company = str(row.get("company", ""))
            event = str(row.get("event", ""))
            signal_year = row.get("signal_year", "")

            forecast_year = row.get("forecast_year", pd.NA)

            forecast_value = pd.to_numeric(
                row.get("forecast_value"),
                errors="coerce",
            )

            with st.container(border=True):
                st.markdown(f"#### {company}")
                st.caption(f"{signal_year} ? {signal_type}")
                st.write(event)

                if (
                    signal_type == "FORECAST"
                    and not pd.isna(forecast_value)
                ):
                    if pd.isna(forecast_year):
                        forecast_label = "-"
                    else:
                        forecast_label = str(int(forecast_year))

                    st.markdown(
                        f"**{forecast_label} ? "
                        f"> {forecast_value / 1_000_000:.1f}M vehicles**"
                    )

                status = row.get("verification_status", "")

                if str(status) == "VERIFIED":
                    st.caption("\uacf5\uc2dd \ucd9c\ucc98 \u00b7 \uac80\uc99d \uc644\ub8cc")


# --------------------------------------------------
# OPPORTUNITY
# --------------------------------------------------

st.divider()

st.markdown(
    '<div class="section-title">시장기회 분석 구조</div>',
    unsafe_allow_html=True,
)

st.markdown(
    '<div class="section-sub">당사 생산수량 자체가 아니라 시장 대비 접근 가능한 영역을 계산하는 구조입니다.</div>',
    unsafe_allow_html=True,
)

o1, o2, o3, o4, o5 = st.columns(5)

o1.metric("① 전체 자동차시장", million_vehicle(latest_value(global_df)))
o2.metric("② 기술 적용시장", "추가 구축")
o3.metric("③ Coil 적용시장", "계산 준비")
o4.metric("④ 접근가능 시장", "적용차종 연결 필요")
o5.metric("⑤ Opportunity Gap", "계산 준비")

st.caption(
    "※ 값이 확인되지 않은 시장을 0으로 표시하지 않습니다. "
    "공식자료·추정·내부참조를 구분하여 단계적으로 계산합니다."
)


# --------------------------------------------------
# SOURCE / DATA STATUS
# --------------------------------------------------

st.divider()

st.markdown(
    '<div class="section-title">데이터 및 근거 현황</div>',
    unsafe_allow_html=True,
)

d1, d2 = st.columns([1.1, 1.9])

with d1:
    actual_count = (
        int((market["estimate_flag"] == "ACTUAL").sum())
        if not market.empty
        else 0
    )

    estimated_count = (
        int((market["estimate_flag"] == "ESTIMATED").sum())
        if not market.empty
        else 0
    )

    verified_signals = (
        int(
            (
                signals["verification_status"]
                == "VERIFIED"
            ).sum()
        )
        if not signals.empty
        else 0
    )

    st.metric("시장 실제 데이터", f"{actual_count}건")
    st.metric("시장 추정/참조 데이터", f"{estimated_count}건")
    st.metric("검증 기술 신호", f"{verified_signals}건")

with d2:
    if source_log.empty:
        st.info("Source Log가 없습니다.")
    else:
        view_columns = [
            col
            for col in [
                "collected_at",
                "source_name",
                "status",
                "source_id",
            ]
            if col in source_log.columns
        ]

        recent_sources = source_log.copy()

        if "collected_at" in recent_sources.columns:
            recent_sources["_sort"] = pd.to_datetime(
                recent_sources["collected_at"],
                errors="coerce",
            )

            recent_sources = recent_sources.sort_values(
                "_sort",
                ascending=False,
            )

        recent_sources = recent_sources.head(8)

        st.markdown("#### 최근 수집 근거")

        st.dataframe(
            recent_sources[view_columns],
            use_container_width=True,
            hide_index=True,
        )


st.markdown(
    """
    <div class="small-note">
    V2.1 · 실제값 / 추정값 / 전망값 분리 ·
    원자료 Source ID 추적 · 미확인 값은 0으로 대체하지 않음
    </div>
    """,
    unsafe_allow_html=True,
)
