# -*- coding: utf-8 -*-
"""Markets: how regions, countries and currencies compare once converted."""

from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

import analytics as an
import i18n
import report as rp
from ui import components as C
from ui.theme import BENCH, LOSS, style_fig


@st.cache_data(show_spinner=False, ttl=3600)
def _universe_performance(_ds, currency: str, period: str, last_date: str):
    prices = an.convert_prices(_ds.prices, _ds.profile, _ds.fx, currency)
    window = rp.slice_window(prices, period)
    return rp.region_performance(window, _ds.profile)


def render(ctx) -> None:
    scope = st.segmented_control(
        ctx.t("scope"), [ctx.t("h_universe"), ctx.t("select_funds")],
        default=ctx.t("h_universe"), key="markets_scope")

    if scope == ctx.t("select_funds"):
        perf = rp.region_performance(ctx.window, ctx.profile)
    else:
        perf = _universe_performance(ctx.ds, ctx.currency, ctx.period,
                                     ctx.ds.last_date.strftime("%Y-%m-%d"))
    if perf.empty:
        st.info(ctx.t("not_enough_data"))
        return

    kinds = sorted(perf.kind.dropna().unique())
    chosen = st.pills(ctx.t("kind"), kinds, selection_mode="multi",
                      default=[k for k in kinds if k == "ETF"] or kinds,
                      key="markets_kinds")
    if chosen:
        perf = perf[perf.kind.isin(chosen)]
    if perf.empty:
        st.info(ctx.t("not_enough_data"))
        return

    # median rather than mean: one thin or leveraged product should not decide
    # how a whole region looks
    by_region = perf.groupby("region").agg(
        cagr=("cagr", "median"), volatility=("volatility", "median"),
        max_drawdown=("max_drawdown", "median"), n=("ticker", "count")
    ).sort_values("cagr", ascending=False)

    C.commentary(ctx, i18n.market_narrative(
        ctx.lang, by_region.index[0], float(by_region.cagr.iloc[0]),
        by_region.index[-1], float(by_region.cagr.iloc[-1]), ctx.currency))

    st.markdown("### " + ctx.t("h_region"))
    left, right = st.columns([3, 2])
    with left:
        C.bar_compare(ctx, by_region.cagr, y_title=ctx.t("y_cagr"), height=340)
    with right:
        st.dataframe(by_region, width="stretch", column_config={
            "cagr": st.column_config.NumberColumn(ctx.t("m_cagr"), format="percent"),
            "volatility": st.column_config.NumberColumn(ctx.t("m_volatility"),
                                                        format="percent"),
            "max_drawdown": st.column_config.NumberColumn(ctx.t("m_maxdd"),
                                                          format="percent"),
            "n": st.column_config.NumberColumn(ctx.t("n_funds"), format="%d")})

    st.markdown("### " + ctx.t("h_market_matrix"))
    by_country = perf.groupby("country").agg(
        cagr=("cagr", "median"), volatility=("volatility", "median"),
        max_drawdown=("max_drawdown", "median"), n=("ticker", "count")
    ).sort_values("cagr", ascending=False)
    data = by_country.reset_index()
    fig = px.scatter(data, x="volatility", y="cagr", text="country", size="n",
                     color="cagr", color_continuous_scale="RdYlGn", height=480,
                     hover_data=["n"])
    fig.update_traces(textposition="top center")
    fig.add_hline(y=float(data.cagr.median()), line_dash="dot", line_color=BENCH)
    st.plotly_chart(style_fig(fig, "", ctx.t("x_vol"), ctx.t("y_cagr"),
                              hover="closest", legend=False), width="stretch")

    st.markdown("### " + ctx.t("h_currency_effect"))
    _currency_effect(ctx)
    C.explain(ctx, "x_markets")


def _currency_effect(ctx) -> None:
    """Same funds, local currency versus the reporting currency."""
    if ctx.ds.fx.empty:
        st.info(ctx.t("not_enough_data"))
        return
    local = rp.slice_window(ctx.ds.prices[ctx.window.columns.tolist()], ctx.period)
    rows = []
    for ticker in ctx.window.columns:
        if ticker not in local.columns:
            continue
        native, converted = local[ticker].dropna(), ctx.window[ticker].dropna()
        if len(native) < 30 or len(converted) < 30:
            continue
        rows.append({"ticker": ticker, "local": an.cagr(native),
                     "converted": an.cagr(converted)})
    if not rows:
        st.info(ctx.t("not_enough_data"))
        return

    frame = pd.DataFrame(rows).set_index("ticker")
    frame["fx"] = frame.converted - frame["local"]
    fig = go.Figure()
    fig.add_trace(go.Bar(x=frame.index, y=frame["local"] * 100, name="local",
                         marker_color=BENCH))
    fig.add_trace(go.Bar(x=frame.index, y=frame.converted * 100, name=ctx.currency,
                         marker_color="#0F766E"))
    fig.add_trace(go.Scatter(x=frame.index, y=frame.fx * 100, name="FX",
                             mode="markers", marker=dict(size=10, color=LOSS,
                                                         symbol="diamond")))
    fig.update_layout(barmode="group")
    st.plotly_chart(style_fig(fig, "", "", ctx.t("y_cagr"), height=360,
                              hover="closest"), width="stretch")
