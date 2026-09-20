from pathlib import Path

import pandas as pd
import streamlit as st


BASE_DIR = Path(__file__).resolve().parents[1]

MARKET_MART = (
    BASE_DIR / "data" / "mart" / "market_monthly.parquet"
)

APPLICATION_MASTER = (
    BASE_DIR / "data" / "metadata" / "vehicle_application_master.csv"
)


st.set_page_config(
    page_title="ABS Coil 시장분석",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)


st.markdown(
    """
    <style>
    .block-container {
        padding-top: 1.2rem;
        padding-bottom: 2rem;
        max-width: 1500px;
    }

    div[data-testid="stMetric"] {
        border: 1px solid rgba(49,51,63,.12);
        padding: 12px 14px;
        border-radius: 14px;
    }

    .small-note {
        font-size: .82rem;
        color: #667085;
    }

    @media (max-width: 768px) {
        .block-container {
            padding-left: .75rem;
            padding-right: .75rem;
        }

        h1 {
            font-size: 1.65rem !important;
        }

        h2, h3 {
            font-size: 1.15rem !important;
        }
    }
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_data
def load_market_mart():
    if not MARKET_MART.exists():
        return pd.DataFrame()

    return pd.read_parquet(MARKET_MART)


@st.cache_data
def load_application_master():
    if not APPLICATION_MASTER.exists():
        return pd.DataFrame()

    return pd.read_csv(
        APPLICATION_MASTER,
        dtype="string",
    )


def get_value(
    df,
    scope,
    metric,
    period=None,
):
    matched = df[
        (df["market_scope"] == scope)
        & (df["metric"] == metric)
    ]

    if period is not None:
        matched = matched[
            matched["period"] == period
        ]

    if matched.empty:
        return None

    value = pd.to_numeric(
        matched.iloc[-1]["value"],
        errors="coerce",
    )

    if pd.isna(value):
        return None

    return float(value)


def fmt_ea(value):
    if value is None:
        return "미확인"

    return f"{value:,.0f} 대"


def fmt_qty(value):
    if value is None:
        return "미확인"

    return f"{value:,.0f} EA"


def model_summary(df, model_id):
    model = df[
        df["market_scope"] == model_id
    ].copy()

    total = get_value(
        model,
        model_id,
        "COILS_PER_SYSTEM",
    )

    components = {}

    for name in ["IV", "OV", "HSV"]:
        components[name] = get_value(
            model,
            model_id,
            f"COMPANY_{name}_PER_SYSTEM",
        )

    supply_values = [
        value
        for value in components.values()
        if value is not None
    ]

    company_supply = (
        sum(supply_values)
        if supply_values
        else None
    )

    return {
        "total": total,
        "company_supply": company_supply,
        "components": components,
    }


market_df = load_market_mart()
application_df = load_application_master()


st.title("ABS Coil 시장분석")
st.caption(
    "공개 통계 · 기술자료 · 내부 기준을 분리하여 "
    "시장규모와 당사 공급범위를 추적합니다."
)


if market_df.empty:
    st.error(
        "시장 Mart가 없습니다. "
        "`python -m processors.market_mart`를 먼저 실행하세요."
    )
    st.stop()


with st.sidebar:
    st.header("분석 기준")

    page = st.radio(
        "화면 선택",
        [
            "시장 개요",
            "제품별 분석",
            "적용차종",
            "데이터 근거",
        ],
    )

    st.divider()

    st.caption("ACTUAL : 공개자료 실제값")
    st.caption("ESTIMATED : 근거 기반 추정/내부 기준")
    st.caption("PARTIAL : 일부만 확인")
    st.caption("MISSING : 아직 확인되지 않음")


global_total = get_value(
    market_df,
    "GLOBAL",
    "VEHICLE_PRODUCTION_TOTAL",
    "2024-12",
)

global_passenger = get_value(
    market_df,
    "GLOBAL",
    "VEHICLE_PRODUCTION_PASSENGER",
    "2024-12",
)

korea_total = get_value(
    market_df,
    "KOREA",
    "VEHICLE_PRODUCTION_TOTAL",
    "2024-12",
)

korea_passenger = get_value(
    market_df,
    "KOREA",
    "VEHICLE_PRODUCTION_PASSENGER",
    "2024-12",
)


if page == "시장 개요":

    st.subheader("2024 자동차 생산시장")

    c1, c2, c3, c4 = st.columns(4)

    c1.metric(
        "세계 자동차 생산",
        fmt_ea(global_total),
    )

    c2.metric(
        "세계 승용차 생산",
        fmt_ea(global_passenger),
    )

    c3.metric(
        "한국 자동차 생산",
        fmt_ea(korea_total),
    )

    c4.metric(
        "한국 승용차 생산",
        fmt_ea(korea_passenger),
    )

    st.caption(
        "출처: KOSIS 연계 자료 / ACTUAL. "
        "개별 제동시스템 시장규모와 동일한 값이 아닙니다."
    )

    st.divider()

    st.subheader("제품별 Coil 구성 및 당사 공급범위")

    model_names = {
        "MODEL_IMEB3": "iMEB3",
        "MODEL_MEB52": "MEB5.2",
        "MODEL_MEB5": "MEB5",
    }

    rows = []

    for model_id, model_name in model_names.items():
        summary = model_summary(
            market_df,
            model_id,
        )

        components = summary["components"]

        rows.append(
            {
                "제품": model_name,
                "시스템 전체 Coil": summary["total"],
                "당사 IV": components["IV"],
                "당사 OV": components["OV"],
                "당사 HSV": components["HSV"],
                "당사 공급범위": summary["company_supply"],
            }
        )

    product_df = pd.DataFrame(rows)

    st.dataframe(
        product_df,
        use_container_width=True,
        hide_index=True,
    )

    st.info(
        "iMEB3 및 MEB5.2의 당사 공급범위는 현재 등록된 "
        "내부 기준을 표시합니다. MEB5는 전체 12개 중 "
        "현재 당사 공급범위가 OV 4개 + HSV 2개로 등록되어 있습니다."
    )


elif page == "제품별 분석":

    st.subheader("제품별 Coil 구조")

    model_names = {
        "iMEB3": "MODEL_IMEB3",
        "MEB5.2": "MODEL_MEB52",
        "MEB5": "MODEL_MEB5",
    }

    selected_name = st.selectbox(
        "제품",
        list(model_names.keys()),
    )

    model_id = model_names[selected_name]

    summary = model_summary(
        market_df,
        model_id,
    )

    total = summary["total"]
    company_supply = summary["company_supply"]
    components = summary["components"]

    c1, c2, c3, c4 = st.columns(4)

    c1.metric(
        "시스템 전체 Coil",
        fmt_qty(total),
    )

    c2.metric(
        "당사 공급범위",
        fmt_qty(company_supply),
    )

    c3.metric(
        "당사 공급비율",
        (
            f"{company_supply / total * 100:.1f}%"
            if total and company_supply is not None
            else "산출불가"
        ),
    )

    c4.metric(
        "시장수량",
        "산출보류",
    )

    component_df = pd.DataFrame(
        [
            {
                "구분": "IV",
                "당사 공급수량": components["IV"],
            },
            {
                "구분": "OV",
                "당사 공급수량": components["OV"],
            },
            {
                "구분": "HSV",
                "당사 공급수량": components["HSV"],
            },
        ]
    )

    st.dataframe(
        component_df,
        use_container_width=True,
        hide_index=True,
    )

    if selected_name == "iMEB3":
        st.warning(
            "iMEB3 적용차량 전체 생산량과 적용률이 아직 "
            "외부 근거로 확정되지 않아 전체 시장수량은 산출보류 상태입니다."
        )

    elif selected_name == "MEB5.2":
        st.warning(
            "MEB5.2 적용차종 및 적용물량 근거가 추가로 필요합니다."
        )

    else:
        st.warning(
            "MEB5 시스템 전체 Coil 수량과 당사 공급범위는 구분되어 있습니다. "
            "당사가 시스템 전체 물량을 공급한다는 의미가 아닙니다."
        )


elif page == "적용차종":

    st.subheader("확인된 차량 적용정보")

    if application_df.empty:
        st.warning("등록된 차량 적용정보가 없습니다.")

    else:
        display_columns = [
            col
            for col in [
                "model_id",
                "vehicle_maker",
                "vehicle_model",
                "vehicle_code",
                "powertrain",
                "region",
                "verification_status",
                "internal_reference",
            ]
            if col in application_df.columns
        ]

        st.dataframe(
            application_df[display_columns],
            use_container_width=True,
            hide_index=True,
        )

        st.info(
            "PARTIAL은 일부 연결근거는 확보됐지만 "
            "모델 세대·적용률·적용기간 등이 완전히 확정되지 않았다는 의미입니다."
        )


else:

    st.subheader("데이터 근거 현황")

    status = (
        market_df["estimate_flag"]
        .fillna("UNKNOWN")
        .value_counts()
        .rename_axis("구분")
        .reset_index(name="건수")
    )

    st.dataframe(
        status,
        use_container_width=True,
        hide_index=True,
    )

    st.subheader("시장 Mart")

    show_columns = [
        "period",
        "market_scope",
        "metric",
        "value",
        "unit",
        "source_key",
        "estimate_flag",
        "confidence_grade",
    ]

    st.dataframe(
        market_df[show_columns],
        use_container_width=True,
        hide_index=True,
    )


st.divider()

st.markdown(
    """
    <span class="small-note">
    원칙: 실제값과 추정값 분리 · 미확인 값을 0으로 대체하지 않음 ·
    출처와 내부 기준 구분 · 근거 변경 시 Master 수정 후 Mart 재생성
    </span>
    """,
    unsafe_allow_html=True,
)
