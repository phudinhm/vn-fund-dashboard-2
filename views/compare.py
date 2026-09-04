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
    tabs = st.tabs([ctx.t("tab_performance"), ctx.t("tab_risk"),
                    ctx.t("tab_riskreturn"), ctx.t("tab_benchmark"),
                    ctx.t("tab_correlation"), ctx.t("tab_cycles")])
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
    with tabs[5]:
        seasonality(ctx)


# ---------------------------------------------------------------- performance
def performance(ctx) -> None:
    with C.card(ctx.t("h_growth")):
        opts = C.chart_options(ctx, "cmp")
        C.growth_chart(ctx, ctx.window, log_scale=opts["log"],
                       relative=opts["relative"])
        _growth_readout(ctx)
        C.explain(ctx, "x_growth")

    with C.card(ctx.t("h_period_returns")):
        periods = an.period_returns(ctx.prices)
        st.dataframe(
            periods, width="stretch",
            column_config={c: st.column_config.NumberColumn(c, format="percent")
                           for c in periods.columns})
        C.explain(ctx, "x_periods")

    with C.card(ctx.t("h_calendar")):
        calendar = an.calendar_year_returns(ctx.prices)
        if not calendar.empty:
            long = (calendar.tail(12).reset_index()
                    .melt(id_vars="year", var_name="ticker", value_name="ret").dropna())
            long["ret"] *= 100
            fig = px.bar(long, x="year", y="ret", color="ticker", barmode="group",
                         height=400)
            fig.add_hline(y=0, line_color=BENCH)
            st.plotly_chart(style_fig(fig, "", ctx.t("x_date"), ctx.t("y_return"),
                                      hover="closest"), width="stretch")
            _calendar_readout(ctx, calendar)

    st.markdown("### " + ctx.t("h_rolling"))
    left, right = st.columns([1, 3])
    years = left.slider(ctx.t("c_window_years"), 0.5, 5.0, 1.0, 0.5, key="cmp_roll")
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
        focus = ctx.focus if ctx.focus in stats.index else stats.index[0]
        row = stats.loc[focus]
        if pd.notna(row.get("win_rate")):
            C.readout(ctx, i18n.rolling_readout(
                ctx.lang, focus, years, float(row.win_rate), float(row["median"]),
                float(row["min"])))
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
    card = C.card(ctx.t("h_drawdown"))
    drawdowns = an.drawdown(ctx.window.ffill()) * 100
    fig = go.Figure()
    for i, ticker in enumerate(drawdowns.columns):
        fig.add_trace(go.Scatter(
            x=drawdowns.index, y=drawdowns[ticker], name=ticker, fill="tozeroy",
            line=dict(width=1.2, color=color_for(i)), opacity=.5))
    with card:
        st.plotly_chart(style_fig(fig, "", ctx.t("x_date"), ctx.t("y_dd"), height=400),
                        width="stretch")
        _drawdown_readout(ctx, drawdowns)
        C.explain(ctx, "x_drawdown")

    with C.card(ctx.t("h_riskmetrics")):
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
    _positioning_readout(ctx)
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
    cols = ["beta", "alpha", "r_squared", "tracking_error", "tracking_difference",
            "information_ratio", "up_capture", "down_capture", "capture_spread",
            "batting_average"]
    have = [c for c in cols if c in ctx.metrics.columns]
    relative = ctx.metrics.loc[[t for t in ctx.metrics.index if t != ctx.benchmark], have]
    st.dataframe(relative, width="stretch", column_config=C.metric_columns(ctx, have))

    bench_kind = ctx.profile.set_index("ticker").get("kind", pd.Series(dtype=str))
    if bench_kind.get(ctx.benchmark) == "Index":
        st.caption(ctx.t("price_index_caveat"))

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
        st.plotly_chart(style_fig(fig, "", "", "%", height=340, hover="closest"),
                        width="stretch")
        up, down = capture.up_capture.dropna(), capture.down_capture.dropna()
        if len(up) and len(down):
            C.readout(ctx, i18n.capture_readout(
                ctx.lang, up.idxmax(), float(up.max()), down.idxmin(),
                float(down.min()), ctx.benchmark))
    C.explain(ctx, "x_benchmark")


# ---------------------------------------------------------------- correlation
def correlation(ctx) -> None:
    st.markdown("### " + ctx.t("h_corr"))
    corr = an.correlation_matrix(ctx.window)
    fig = px.imshow(corr, text_auto=".2f", color_continuous_scale="RdBu_r",
                    zmin=-1, zmax=1, height=max(400, 40 * len(corr)))
    st.plotly_chart(style_fig(fig, "", hover="closest", legend=False), width="stretch")

    _correlation_readout(ctx, corr)
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


# ---------------------------------------------------------------- readouts
def _growth_readout(ctx) -> None:
    growth = an.cumulative_growth(ctx.window.ffill())
    if growth.empty:
        return
    final = (growth.iloc[-1] / 100 - 1).dropna()
    if len(final) < 2 or ctx.benchmark not in final.index:
        return
    bench = float(final[ctx.benchmark])
    C.readout(ctx, i18n.performance_readout(
        ctx.lang, final.idxmax(), float(final.max()), final.idxmin(),
        float(final.min()), ctx.benchmark, bench,
        int((final > bench).sum()), int(len(final))))


def _calendar_readout(ctx, calendar: pd.DataFrame) -> None:
    focus = ctx.focus if ctx.focus in calendar.columns else calendar.columns[0]
    series = calendar[focus].dropna()
    if len(series) < 2:
        return
    C.readout(ctx, i18n.calendar_readout(
        ctx.lang, str(series.idxmax()), float(series.max()),
        str(series.idxmin()), float(series.min()),
        int((series > 0).sum()), int(len(series))))


def _drawdown_readout(ctx, drawdowns: pd.DataFrame) -> None:
    deepest = drawdowns.min().dropna() / 100
    current = drawdowns.iloc[-1].dropna() / 100
    if deepest.empty or current.empty:
        return
    C.readout(ctx, i18n.drawdown_readout(
        ctx.lang, deepest.idxmin(), float(deepest.min()),
        deepest.idxmax(), float(deepest.max()),
        current.idxmin(), float(current.min())))


def _positioning_readout(ctx) -> None:
    metrics = ctx.metrics
    sharpe, cagr, vol = (metrics.sharpe.dropna(), metrics.cagr.dropna(),
                         metrics.volatility.dropna())
    if sharpe.empty or cagr.empty or vol.empty:
        return
    C.readout(ctx, i18n.positioning_readout(
        ctx.lang, sharpe.idxmax(), float(sharpe.max()), cagr.idxmax(),
        float(cagr.max()), vol.idxmax(), float(vol.max())))


def _correlation_readout(ctx, corr: pd.DataFrame) -> None:
    if corr.shape[0] < 2:
        return
    pairs = corr.where(np.triu(np.ones(corr.shape), k=1).astype(bool)).stack()
    if pairs.empty:
        return
    low, high = pairs.idxmin(), pairs.idxmax()
    C.readout(ctx, i18n.correlation_readout(
        ctx.lang, an.diversification_score(corr), low[0], low[1],
        float(pairs.min()), high[0], high[1], float(pairs.max())))


# -------------------------------------------------------------- seasonality
def seasonality(ctx) -> None:
    """Year x month growth grid, plus the month-of-year pattern underneath."""
    options = list(ctx.window.columns)
    focus = st.selectbox(ctx.t("focus_fund"), options, format_func=ctx.label,
                         index=options.index(ctx.focus) if ctx.focus in options else 0,
                         key="cmp_heat_fund")
    with C.card(ctx.t("h_growth_heatmap")):
        heat = C.growth_heatmap(ctx, ctx.prices[focus], focus)

    if heat is None or heat.empty:
        return
    left, right = st.columns(2, gap="medium")
    with left:
        with C.card(ctx.t("h_seasonality")):
            monthly = heat.mean()
            monthly.index = [i18n.month_name(ctx.lang, m) for m in monthly.index]
            C.bar_compare(ctx, monthly / 100, y_title=ctx.t("y_return"), height=320)
    with right:
        with C.card(ctx.t("h_bullbear")):
            if ctx.bench_ret is None:
                st.info(ctx.t("not_enough_data"))
            else:
                split = an.bull_bear_split(an.daily_returns(ctx.window[focus]),
                                           ctx.bench_ret)
                fig = go.Figure()
                fig.add_trace(go.Bar(x=[ctx.t("bull")], y=[split["bull"] * 100],
                                     marker_color=GAIN, name=ctx.t("bull")))
                fig.add_trace(go.Bar(x=[ctx.t("bear")], y=[split["bear"] * 100],
                                     marker_color=LOSS, name=ctx.t("bear")))
                st.plotly_chart(style_fig(fig, "", "", ctx.t("y_return"), height=320,
                                          hover="closest", legend=False),
                                width="stretch")
    C.explain(ctx, "x_cycles")
