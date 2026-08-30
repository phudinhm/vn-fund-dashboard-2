# -*- coding: utf-8 -*-
"""Compare: performance, risk, positioning, benchmark and correlation.

Five closely related questions about the same selection, grouped as sub-tabs
instead of five separate top-level destinations.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

import analytics as an
import i18n
from ui import components as C
from ui.theme import BENCH, GAIN, LOSS, color_for, style_fig


def render(ctx) -> None:
    tabs = st.tabs(["🚀 " + ctx.t("tab_performance"), "📉 " + ctx.t("tab_risk"),
                    "⚖️ " + ctx.t("tab_riskreturn"), "🎯 " + ctx.t("tab_benchmark"),
                    "🔗 " + ctx.t("tab_correlation")])
    with tabs[0]:
        performance(ctx)
    with tabs[1]:
        risk(ctx)
    with tabs[2]:
        risk_return(ctx)
    with tabs[3]:
        versus_benchmark(ctx)
    with tabs[4]:
        correlation(ctx)


# ---------------------------------------------------------------- performance
def performance(ctx) -> None:
    st.markdown("### " + ctx.t("h_growth"))
    opts = C.chart_options(ctx, "cmp")
    C.growth_chart(ctx, ctx.window, log_scale=opts["log"], relative=opts["relative"])
    C.explain(ctx, "x_growth")

    st.markdown("### " + ctx.t("h_period_returns"))
    periods = an.period_returns(ctx.prices)
    st.dataframe(
        periods, width="stretch",
        column_config={c: st.column_config.NumberColumn(c, format="percent")
                       for c in periods.columns})
    C.explain(ctx, "x_periods")

    st.markdown("### " + ctx.t("h_calendar"))
    calendar = an.calendar_year_returns(ctx.prices)
    if not calendar.empty:
        long = (calendar.tail(12).reset_index()
                .melt(id_vars="year", var_name="ticker", value_name="ret").dropna())
        long["ret"] *= 100
        fig = px.bar(long, x="year", y="ret", color="ticker", barmode="group",
                     height=420)
        fig.add_hline(y=0, line_color=BENCH)
        st.plotly_chart(style_fig(fig, "", ctx.t("x_date"), ctx.t("y_return"),
                                  hover="closest"), width="stretch")

    st.markdown("### " + ctx.t("h_rolling"))
    left, right = st.columns([1, 3])
    years = left.slider(ctx.t("c_window_years"), 0.5, 5.0, 1.0, 0.5, key="cmp_roll")
    left.caption(ctx.t("x_periods"))
    rolling = {}
    for ticker in ctx.window.columns:
        series = an.rolling_returns(ctx.prices[ticker], years)
        if not series.empty:
            rolling[ticker] = series * 100
    if rolling:
        fig = px.line(pd.DataFrame(rolling), height=380)
        fig.add_hline(y=0, line_dash="dot", line_color=LOSS)
        right.plotly_chart(style_fig(fig, "", ctx.t("x_date"), ctx.t("y_cagr")),
                           width="stretch")
        stats = pd.DataFrame({t: an.rolling_return_stats(ctx.prices[t], years)
                              for t in ctx.window.columns}).T
        st.dataframe(stats, width="stretch", column_config={
            "windows": st.column_config.NumberColumn(ctx.t("windows"), format="%d"),
            "mean": st.column_config.NumberColumn(ctx.t("average"), format="percent"),
            "median": st.column_config.NumberColumn(ctx.t("median"), format="percent"),
            "min": st.column_config.NumberColumn(ctx.t("worst"), format="percent"),
            "max": st.column_config.NumberColumn(ctx.t("best"), format="percent"),
            "win_rate": st.column_config.ProgressColumn(
                ctx.t("win_rate"), format="%.1f%%", min_value=0, max_value=100),
            "p05": st.column_config.NumberColumn("P05", format="percent"),
            "p95": st.column_config.NumberColumn("P95", format="percent")})


# ----------------------------------------------------------------------- risk
def risk(ctx) -> None:
    st.markdown("### " + ctx.t("h_drawdown"))
    drawdowns = an.drawdown(ctx.window.ffill()) * 100
    fig = go.Figure()
    for i, ticker in enumerate(drawdowns.columns):
        fig.add_trace(go.Scatter(
            x=drawdowns.index, y=drawdowns[ticker], name=ticker, fill="tozeroy",
            line=dict(width=1.2, color=color_for(i)), opacity=.5))
    st.plotly_chart(style_fig(fig, "", ctx.t("x_date"), ctx.t("y_dd"), height=420),
                    width="stretch")
    C.explain(ctx, "x_drawdown")

    st.markdown("### " + ctx.t("h_riskmetrics"))
    risk_cols = ["volatility", "downside_dev", "max_drawdown", "var95", "cvar95",
                 "ulcer", "martin", "skew", "kurtosis", "tail_ratio", "hit_rate",
                 "stability", "best_day", "worst_day"]
    have = [c for c in risk_cols if c in ctx.metrics.columns]
    st.dataframe(ctx.metrics[have], width="stretch",
                 column_config=C.metric_columns(ctx, have))

    left, right = st.columns(2)
    with left:
        st.markdown("#### " + ctx.t("m_volatility"))
        vol = pd.DataFrame({t: an.rolling_volatility(ctx.returns[t])
                            for t in ctx.window.columns}).dropna(how="all")
        if not vol.empty:
            st.plotly_chart(style_fig(px.line(vol, height=340), "", ctx.t("x_date"),
                                      ctx.t("x_vol")), width="stretch")
    with right:
        st.markdown("#### " + ctx.t("h_dd_table"))
        focus = st.selectbox(ctx.t("focus_fund"), list(ctx.window.columns),
                             index=list(ctx.window.columns).index(ctx.focus)
                             if ctx.focus in ctx.window.columns else 0,
                             format_func=ctx.label, key="risk_focus")
        episodes = an.drawdown_episodes(ctx.window[focus], top=5)
        if not episodes.empty:
            current = float(an.drawdown(ctx.window[focus].dropna()).iloc[-1])
            C.commentary(ctx, i18n.drawdown_narrative(
                ctx.lang, focus, current, float(episodes.depth.min()),
                episodes.recovery_days.iloc[0]))
            st.dataframe(episodes, width="stretch", hide_index=True, column_config={
                "peak": st.column_config.DateColumn(ctx.t("m_first")),
                "trough": st.column_config.DateColumn(ctx.t("worst")),
                "recovery": st.column_config.DateColumn(ctx.t("m_last")),
                "depth": st.column_config.NumberColumn(ctx.t("m_maxdd"), format="percent"),
                "length_days": st.column_config.NumberColumn(ctx.t("windows"), format="%d"),
                "recovery_days": st.column_config.NumberColumn(
                    ctx.t("c_hold_years"), format="%d")})


# --------------------------------------------------------------- risk/return
def risk_return(ctx) -> None:
    st.markdown("### " + ctx.t("h_scatter"))
    frame = ctx.metrics.copy()
    frame["vol_pct"] = frame.volatility * 100
    frame["cagr_pct"] = frame.cagr * 100
    C.scatter_picker(ctx, frame, "vol_pct", "cagr_pct", "cmp_scatter",
                     ctx.t("x_vol"), ctx.t("y_cagr"),
                     color="region" if "region" in frame.columns else None)
    C.explain(ctx, "x_riskreturn")

    left, right = st.columns(2)
    with left:
        st.markdown("#### " + ctx.t("h_leaderboard"))
        cols = ["cagr", "sharpe", "sortino", "calmar", "omega", "score"]
        have = [c for c in cols if c in ctx.scored.columns]
        st.dataframe(ctx.scored[have], width="stretch",
                     column_config=C.metric_columns(ctx, have))
    with right:
        st.markdown("#### " + ctx.t("h_frontier"))
        frontier = an.efficient_frontier(
            ctx.window.drop(columns=[ctx.benchmark], errors="ignore"),
            simulations=2500, rf=ctx.rf)
        if frontier.empty:
            st.info(ctx.t("not_enough_data"))
        else:
            fig = px.scatter(frontier, x="volatility", y="return", color="sharpe",
                             color_continuous_scale="Viridis", height=400, opacity=.5)
            fig.add_trace(go.Scatter(
                x=ctx.metrics.volatility, y=ctx.metrics.cagr, mode="markers+text",
                text=ctx.metrics.index, textposition="top center", name="",
                marker=dict(size=11, color=LOSS, symbol="diamond")))
            st.plotly_chart(style_fig(fig, "", ctx.t("x_vol"), ctx.t("y_cagr"),
                                      hover="closest", legend=False), width="stretch")


# ------------------------------------------------------------ vs benchmark
def versus_benchmark(ctx) -> None:
    if ctx.bench_ret is None:
        st.info(ctx.t("not_enough_data"))
        return

    st.markdown(f"### {ctx.t('h_alpha')} — {ctx.benchmark}")
    cols = ["beta", "alpha", "r_squared", "tracking_error", "information_ratio",
            "up_capture", "down_capture", "capture_spread", "batting_average"]
    have = [c for c in cols if c in ctx.metrics.columns]
    relative = ctx.metrics.loc[[t for t in ctx.metrics.index if t != ctx.benchmark], have]
    st.dataframe(relative, width="stretch", column_config=C.metric_columns(ctx, have))

    if not relative.empty:
        focus = st.selectbox(ctx.t("focus_fund"), list(relative.index),
                             format_func=ctx.label, key="bench_focus")
        row = ctx.metrics.loc[focus]
        C.commentary(ctx, i18n.tracking_narrative(
            ctx.lang, focus, row.get("tracking_error", np.nan),
            row.get("information_ratio", np.nan), row.get("beta", np.nan),
            row.get("alpha", np.nan), ctx.benchmark))

    left, right = st.columns(2)
    others = [t for t in ctx.window.columns if t != ctx.benchmark]
    with left:
        st.markdown("#### " + ctx.t("h_te"))
        te = pd.DataFrame({t: an.rolling_tracking_error(ctx.returns[t], ctx.bench_ret)
                           for t in others}).dropna(how="all")
        if not te.empty:
            st.plotly_chart(style_fig(px.line(te, height=340), "", ctx.t("x_date"),
                                      ctx.t("y_te")), width="stretch")
    with right:
        st.markdown("#### " + ctx.t("m_beta"))
        beta = pd.DataFrame({t: an.rolling_beta(ctx.returns[t], ctx.bench_ret)
                             for t in others}).dropna(how="all")
        if not beta.empty:
            fig = px.line(beta, height=340)
            fig.add_hline(y=1.0, line_dash="dot", line_color=BENCH)
            st.plotly_chart(style_fig(fig, "", ctx.t("x_date"), ctx.t("m_beta")),
                            width="stretch")

    st.markdown("#### " + ctx.t("h_capture"))
    capture = ctx.metrics.loc[others, ["up_capture", "down_capture"]].dropna(how="all")
    if not capture.empty:
        fig = go.Figure()
        fig.add_trace(go.Bar(x=capture.index, y=capture.up_capture,
                             name=ctx.t("m_up"), marker_color=GAIN))
        fig.add_trace(go.Bar(x=capture.index, y=capture.down_capture,
                             name=ctx.t("m_down"), marker_color=LOSS))
        fig.add_hline(y=100, line_dash="dot", line_color=BENCH)
        fig.update_layout(barmode="group")
        st.plotly_chart(style_fig(fig, "", "", "%", height=360, hover="closest"),
                        width="stretch")
    C.explain(ctx, "x_benchmark")


# ---------------------------------------------------------------- correlation
def correlation(ctx) -> None:
    st.markdown("### " + ctx.t("h_corr"))
    corr = an.correlation_matrix(ctx.window)
    fig = px.imshow(corr, text_auto=".2f", color_continuous_scale="RdBu_r",
                    zmin=-1, zmax=1, height=max(400, 40 * len(corr)))
    st.plotly_chart(style_fig(fig, "", hover="closest", legend=False), width="stretch")

    score = an.diversification_score(corr)
    cols = st.columns(3)
    cols[0].metric(ctx.t("average") + " ρ", C.num(score))
    least = corr.where(~np.eye(len(corr), dtype=bool)).mean().sort_values()
    if not least.empty:
        cols[1].metric(ctx.t("best") + " · " + ctx.t("h_corr"), least.index[0],
                       C.num(least.iloc[0]))
        cols[2].metric(ctx.t("worst") + " · " + ctx.t("h_corr"), least.index[-1],
                       C.num(least.iloc[-1]))
    C.explain(ctx, "x_correlation")

    if ctx.bench_ret is not None:
        st.markdown("### " + ctx.t("h_corr_rolling"))
        rolling = pd.DataFrame({
            t: an.rolling_correlation(ctx.returns[t], ctx.bench_ret)
            for t in ctx.window.columns if t != ctx.benchmark}).dropna(how="all")
        if not rolling.empty:
            st.plotly_chart(style_fig(px.line(rolling, height=360), "",
                                      ctx.t("x_date"), ctx.t("h_corr")),
                            width="stretch")
