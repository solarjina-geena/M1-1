import pandas as pd
import altair as alt
import streamlit as st

from processors.time_series_analysis import (
    add_timeseries_features,
    summarize_timeseries,
    compare_recent_vs_longterm,
    detect_frequency,
)


def _pct(value):
    if value is None or pd.isna(value):
        return "확인 불가"
    return f"{value:+.2f}%"


def _million(value):
    if value is None or pd.isna(value):
        return "확인 불가"
    return f"{value / 1_000_000:.2f}M대"


def _prepare(df):
    if df.empty:
        return df

    result = df.copy()

    if "date" not in result.columns:
        result["date"] = pd.to_datetime(
            result["period"],
            format="%Y-%m",
            errors="coerce",
        )

    if "period_label" not in result.columns:
        result["period_label"] = (
            result["date"].dt.strftime("%Y-%m")
        )

    result["year"] = result["date"].dt.year
    result["month"] = result["date"].dt.month

    return (
        result.dropna(subset=["date", "value"])
        .sort_values("date")
        .reset_index(drop=True)
    )


def _trend_chart(data, title):
    frequency = detect_frequency(data)
    analyzed = add_timeseries_features(data)

    if frequency == "MONTHLY":
        ma_col = "ma_12m"
        ma_name = "12개월 이동평균"
    else:
        ma_col = "ma_3y"
        ma_name = "3년 이동평균"

    chart_data = analyzed[
        ["date", "value", ma_col]
    ].copy()

    chart_data = chart_data.rename(
        columns={
            "value": "실제값",
            ma_col: ma_name,
        }
    )

    long = chart_data.melt(
        id_vars=["date"],
        var_name="구분",
        value_name="value",
    )

    base = (
        alt.Chart(long)
        .mark_line(
            strokeWidth=2.5,
            point=True,
        )
        .encode(
            x=alt.X(
                "date:T",
                title=None,
                axis=alt.Axis(format="%Y-%m"),
            ),
            y=alt.Y(
                "value:Q",
                title="자동차 생산대수",
                axis=alt.Axis(format="~s"),
                scale=alt.Scale(zero=False),
            ),
            color=alt.Color(
                "구분:N",
                title=None,
            ),
            tooltip=[
                alt.Tooltip(
                    "date:T",
                    title="기간",
                    format="%Y-%m",
                ),
                alt.Tooltip(
                    "구분:N",
                    title="구분",
                ),
                alt.Tooltip(
                    "value:Q",
                    title="생산대수",
                    format=",.0f",
                ),
            ],
        )
        .properties(
            height=300,
            title=title,
        )
        .interactive()
    )

    return base


def _change_chart(data):
    analyzed = add_timeseries_features(data)
    frequency = detect_frequency(analyzed)

    change_col = (
        "yoy_pct"
        if frequency == "ANNUAL"
        else "mom_pct"
    )

    label = (
        "연간 변화율 (YoY)"
        if frequency == "ANNUAL"
        else "전월 대비 변화율 (MoM)"
    )

    chart_data = analyzed[
        ["date", change_col]
    ].dropna().copy()

    chart_data["방향"] = chart_data[
        change_col
    ].apply(
        lambda x: "증가" if x >= 0 else "감소"
    )

    zero = (
        alt.Chart(pd.DataFrame({"y": [0]}))
        .mark_rule(
            strokeDash=[4, 4],
        )
        .encode(y="y:Q")
    )

    bars = (
        alt.Chart(chart_data)
        .mark_bar(
            cornerRadiusTopLeft=3,
            cornerRadiusTopRight=3,
        )
        .encode(
            x=alt.X(
                "date:T",
                title=None,
                axis=alt.Axis(format="%Y"),
            ),
            y=alt.Y(
                f"{change_col}:Q",
                title="변화율 (%)",
            ),
            color=alt.Color(
                "방향:N",
                title=None,
                scale=alt.Scale(
                    domain=["증가", "감소"],
                    range=["#2E7D32", "#C62828"],
                ),
            ),
            tooltip=[
                alt.Tooltip(
                    "date:T",
                    title="기간",
                    format="%Y-%m",
                ),
                alt.Tooltip(
                    f"{change_col}:Q",
                    title=label,
                    format=".2f",
                ),
            ],
        )
        .properties(height=235)
    )

    return (bars + zero), label


def _market_block(name, data):
    data = _prepare(data)

    if data.empty:
        st.warning(f"{name} 데이터가 없습니다.")
        return

    summary = summarize_timeseries(data)
    compare = compare_recent_vs_longterm(data)

    frequency = summary.get(
        "frequency",
        "UNKNOWN",
    )

    latest = float(data.iloc[-1]["value"])

    c1, c2, c3 = st.columns(3)

    c1.metric(
        f"{name} 최신 시장규모",
        _million(latest),
    )

    c2.metric(
        "장기 CAGR",
        _pct(
            compare.get(
                "longterm_cagr_pct"
            )
        ),
    )

    c3.metric(
        "최근 5년 CAGR",
        _pct(
            compare.get(
                "recent_cagr_pct"
            )
        ),
    )

    st.altair_chart(
        _trend_chart(
            data,
            f"{name} 자동차 시장 추세",
        ),
        width="stretch",
    )

    change_chart, change_label = (
        _change_chart(data)
    )

    st.markdown(
        f"##### {change_label}"
    )

    st.altair_chart(
        change_chart,
        width="stretch",
    )

    growth = summary.get("max_growth")
    decline = summary.get("max_decline")

    if growth and decline:
        st.caption(
            f"최대 상승 {growth['period']} "
            f"{growth['yoy_pct']:+.2f}%  ·  "
            f"최대 하락 {decline['period']} "
            f"{decline['yoy_pct']:+.2f}%"
        )

    if frequency == "MONTHLY":
        st.caption(
            "월간 데이터 · MoM / YoY / "
            "3개월·12개월 이동평균 분석"
        )
    else:
        st.caption(
            "현재 원자료는 연간 데이터 · "
            "YoY / 3년 이동평균 분석"
        )


def render_market_timeseries(
    global_df,
    korea_df,
):
    st.markdown(
        '<div class="section-title">'
        '시장 시계열 분석'
        '</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="section-sub">'
        '시장규모뿐 아니라 성장속도와 '
        '변곡점을 함께 확인합니다.'
        '</div>',
        unsafe_allow_html=True,
    )

    tab1, tab2 = st.tabs(
        ["🌍 글로벌 시장", "🇰🇷 한국 시장"]
    )

    with tab1:
        _market_block(
            "글로벌",
            global_df,
        )

    with tab2:
        _market_block(
            "한국",
            korea_df,
        )

    global_data = _prepare(global_df)

    if not global_data.empty:
        summary = summarize_timeseries(
            global_data
        )
        compare = compare_recent_vs_longterm(
            global_data
        )

        st.markdown("##### 데이터 인사이트")

        longterm = compare.get(
            "longterm_cagr_pct"
        )
        recent = compare.get(
            "recent_cagr_pct"
        )

        growth = summary.get("max_growth")
        decline = summary.get("max_decline")

        i1, i2, i3 = st.columns(3)

        with i1:
            st.info(
                "**관찰 · 성장속도**\n\n"
                f"장기 CAGR {_pct(longterm)} → "
                f"최근 5년 {_pct(recent)}"
            )

        with i2:
            if decline:
                st.info(
                    "**관찰 · 최대 하락**\n\n"
                    f"{decline['period']} · "
                    f"{decline['yoy_pct']:+.2f}%"
                )

        with i3:
            if growth:
                st.info(
                    "**관찰 · 최대 상승**\n\n"
                    f"{growth['period']} · "
                    f"{growth['yoy_pct']:+.2f}%"
                )

        if (
            longterm is not None
            and recent is not None
        ):
            if recent < longterm:
                interpretation = (
                    "최근 성장속도가 장기 평균보다 낮습니다. "
                    "전체 자동차 시장규모만으로 성장성을 판단하기보다 "
                    "통합제동·Brake-by-Wire 등 기술 전환 시장을 "
                    "별도로 관찰할 필요가 있습니다."
                )
            else:
                interpretation = (
                    "최근 성장속도가 장기 평균보다 높습니다. "
                    "시장 회복이 일시적인지 구조적인지 "
                    "기술 적용률과 함께 확인할 필요가 있습니다."
                )

            st.success(
                "**해석 가설** · "
                + interpretation
            )

        st.caption(
            "※ 관찰은 계산된 시계열 수치이며, "
            "해석은 추가 시장·기술 자료와 함께 검증해야 합니다."
        )
