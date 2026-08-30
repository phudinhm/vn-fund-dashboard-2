# -*- coding: utf-8 -*-
"""Fund profile: everything about one instrument on a single page.

The old report scattered six identical "pick one instrument" dropdowns across
its tabs. There is now a single focused fund, set from anywhere (a click on the
scatter, a row in the screener, this page's own picker).
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
from ui.theme import GAIN, LOSS, style_fig

PEER_METRICS = ["cagr", "sharpe", "sortino", "calmar", "volatility", "max_drawdown"]


def render(ctx) -> None:
    options = ctx.universe or list(ctx.ds.prices.columns)
    focus = ctx.focus
    picked = st.selectbox(ctx.t("profile_pick"), options,
                          index=options.index(focus) if focus in options else 0,
                          format_func=ctx.label, key="profile_pick")
    if picked != st.session_state.get("focus"):
        st.session_state["focus"] = picked
    focus = picked

    prices = an.convert_prices(ctx.ds.prices[[focus]], ctx.profile, ctx.ds.fx,
                               ctx.currency)[focus]
    series = prices.dropna()
    if len(series) < 30:
        st.warning(ctx.t("not_enough_data"))
        return

    _header(ctx, focus, prices)
    tabs = st.tabs([ctx.t("tab_performance"), ctx.t("tab_risk"),
                    ctx.t("tab_cycles"), ctx.t("tab_forecast"),
                    ctx.t("profile_metrics")])
    with tabs[0]:
        _performance(ctx, focus, prices)
    with tabs[1]:
        _risk(ctx, focus, prices)
    with tabs[2]:
        _cycles(ctx, focus, prices)
    with tabs[3]:
        _forecast(ctx, focus, prices)
    with tabs[4]:
        _all_metrics(ctx, focus, prices)


# ------------------------------------------------------------------- header
def _header(ctx, ticker: str, prices: pd.Series) -> None:
    """Facts on the left, headline numbers for the selected period on the right."""
    import report as rp

    prof = ctx.profile.set_index("ticker")
    meta = prof.loc[ticker] if ticker in prof.index else None
    series = prices.dropna()
    window = rp.slice_window(prices.to_frame(ticker), ctx.period)[ticker].dropna()
    if len(window) < 20:
        window = series

    left, right = st.columns([3, 2])
    with left:
        name = meta["name"] if meta is not None else ticker
        st.markdown(f"## {ticker} — {name}")
        if meta is not None:
            chips = [meta.kind, meta.asset_class, meta.category, meta.region,
                     meta.country, meta.currency, meta.issuer]
            seen, unique = set(), []
            for chip in chips:  # region and country are often the same word
                if isinstance(chip, str) and chip and chip != "-" and chip not in seen:
                    seen.add(chip)
                    unique.append(chip)
            st.markdown(" ".join(f"<span class='chip'>{c}</span>" for c in unique),
                        unsafe_allow_html=True)
            ter = meta.ter
            bench = meta.benchmark
            bench = "—" if pd.isna(bench) or not str(bench).strip() else bench
            facts = [
                f"<b>{ctx.t('inception')}:</b> {series.index.min():%d.%m.%Y}",
                f"<b>{ctx.t('m_obs')}:</b> {len(series):,}",
                f"<b>{ctx.t('m_ter')}:</b> {'—' if pd.isna(ter) else f'{ter:.2f}%'}",
                f"<b>{ctx.t('benchmark')}:</b> {bench}",
            ]
            st.markdown("<div class='facts'>" + " · ".join(facts) + "</div>",
                        unsafe_allow_html=True)
    with right:
        # the same window the rest of the report is showing
        st.caption(f"{ctx.t('time_range')}: {ctx.period}")
        cols = st.columns(2)
        cols[0].metric(ctx.t("m_cagr"), C.pct(an.cagr(window), 1))
        cols[1].metric(ctx.t("m_maxdd"), C.pct(an.max_drawdown(window), 1))
        cols2 = st.columns(2)
        cols2[0].metric(ctx.t("m_volatility"),
                        C.pct(an.annual_volatility(an.daily_returns(window)), 1))
        cols2[1].metric(ctx.t("m_sharpe"), C.num(an.sharpe(window, ctx.rf)))

    _peer_ranking(ctx, ticker)


def _peer_ranking(ctx, ticker: str) -> None:
    peers = ctx.peers(ticker)
    if len(peers) < 4:
        return
    prices = an.convert_prices(ctx.ds.prices[peers], ctx.profile, ctx.ds.fx, ctx.currency)
    import report as rp
    window = rp.slice_window(prices, ctx.period).dropna(axis=1, how="all")
    metrics = an.metrics_table(window, benchmark=None, rf=ctx.rf, profile=ctx.profile)
    if ticker not in metrics.index:
        return

    prof = ctx.profile.set_index("ticker")
    label = prof.loc[ticker, "category"] if ticker in prof.index else ""
    st.markdown(f"##### {ctx.t('profile_vs_peers')} · {label} ({len(metrics)})")

    cols = st.columns(len(PEER_METRICS))
    for col, metric in zip(cols, PEER_METRICS):
        if metric not in metrics.columns:
            continue
        values = metrics[metric].dropna()
        if ticker not in values.index or len(values) < 3:
            continue
        higher_is_better = metric not in ("volatility",)
        rank = values.rank(ascending=not higher_is_better, pct=True)
        pct_rank = float(rank.loc[ticker]) * 100
        shown = (C.pct(values.loc[ticker], 1)
                 if metric in ("cagr", "volatility", "max_drawdown")
                 else C.num(values.loc[ticker]))
        col.metric(ctx.t(C.METRIC_FORMAT[metric][1]), shown,
                   f"{ctx.t('percentile')} {pct_rank:.0f}", delta_color="off")


# -------------------------------------------------------------- performance
def _performance(ctx, ticker: str, prices: pd.Series) -> None:
    series = prices.dropna()
    left, right = st.columns([1, 3])
    log_scale = left.toggle(ctx.t("opt_log"), key="pf_log")
    show_ma = left.toggle("MA 50 / 200", value=True, key="pf_ma")

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=series.index, y=series, name=ticker,
                             line=dict(color="#14322E", width=1.6)))
    if show_ma:
        fig.add_trace(go.Scatter(x=series.index, y=series.rolling(50).mean(),
                                 name="MA50", line=dict(color="#B45309", width=1.2)))
        fig.add_trace(go.Scatter(x=series.index, y=series.rolling(200).mean(),
                                 name="MA200", line=dict(color=LOSS, width=1.2)))
    fig.update_xaxes(rangeslider_visible=True)
    right.plotly_chart(style_fig(fig, "", ctx.t("x_date"),
                                 f"{ctx.t('y_value')} ({ctx.currency})",
                                 height=420, log_y=log_scale), width="stretch")

    with C.card(ctx.t("h_period_returns")):
        periods = an.period_returns(prices.to_frame(ticker))
        st.dataframe(periods, width="stretch", column_config={
            c: st.column_config.NumberColumn(c, format="percent")
            for c in periods.columns})

    with C.card(ctx.t("h_calendar")):
        calendar = an.calendar_year_returns(prices.to_frame(ticker))
        if not calendar.empty:
            series = calendar[ticker].dropna()
            C.bar_compare(ctx, series.tail(12).iloc[::-1],
                          y_title=ctx.t("y_return"), height=320)
            if len(series) >= 2:
                C.readout(ctx, i18n.calendar_readout(
                    ctx.lang, str(series.idxmax()), float(series.max()),
                    str(series.idxmin()), float(series.min()),
                    int((series > 0).sum()), int(len(series))))


# --------------------------------------------------------------------- risk
def _risk(ctx, ticker: str, prices: pd.Series) -> None:
    series = prices.dropna()
    drawdowns = an.drawdown(series) * 100
    fig = go.Figure(go.Scatter(x=drawdowns.index, y=drawdowns, fill="tozeroy",
                               line=dict(color=LOSS, width=1), name=ticker))
    st.plotly_chart(style_fig(fig, "", ctx.t("x_date"), ctx.t("y_dd"), height=340,
                              legend=False), width="stretch")

    episodes = an.drawdown_episodes(series, top=5)
    if not episodes.empty:
        C.commentary(ctx, i18n.drawdown_narrative(
            ctx.lang, ticker, float(drawdowns.iloc[-1] / 100),
            float(episodes.depth.min()), episodes.recovery_days.iloc[0]))
        st.dataframe(episodes, width="stretch", hide_index=True, column_config={
            "peak": st.column_config.DateColumn(ctx.t("m_first")),
            "trough": st.column_config.DateColumn(ctx.t("worst")),
            "recovery": st.column_config.DateColumn(ctx.t("m_last")),
            "depth": st.column_config.NumberColumn(ctx.t("m_maxdd"), format="percent"),
            "length_days": st.column_config.NumberColumn(ctx.t("windows"), format="%d"),
            "recovery_days": st.column_config.NumberColumn(ctx.t("c_hold_years"),
                                                           format="%d")})

    returns = an.daily_returns(series).dropna()
    left, right = st.columns(2)
    with left:
        st.markdown("##### " + ctx.t("m_var"))
        fig = px.histogram(returns * 100, nbins=80, height=320)
        for level, color in ((an.value_at_risk(returns, .95) * 100, "#B45309"),
                             (an.conditional_var(returns, .95) * 100, LOSS)):
            fig.add_vline(x=level, line_dash="dot", line_color=color)
        st.plotly_chart(style_fig(fig, "", ctx.t("y_return"), "", hover="closest",
                                  legend=False), width="stretch")
    with right:
        st.markdown("##### " + ctx.t("h_rolling"))
        vol = an.rolling_volatility(returns).dropna()
        if not vol.empty:
            st.plotly_chart(style_fig(px.line(vol, height=320), "", ctx.t("x_date"),
                                      ctx.t("x_vol"), legend=False), width="stretch")


# ------------------------------------------------------------------- cycles
def _cycles(ctx, ticker: str, prices: pd.Series) -> None:
    with C.card(ctx.t("h_growth_heatmap")):
        heat = C.growth_heatmap(ctx, prices, ticker)
    if heat is None or heat.empty:
        return

    left, right = st.columns(2, gap="medium")
    with left:
        with C.card(ctx.t("h_seasonality")):
            monthly = heat.mean()
            monthly.index = [i18n.month_name(ctx.lang, m) for m in monthly.index]
            C.bar_compare(ctx, monthly / 100, y_title=ctx.t("y_return"), height=300)
    with right:
        with C.card(ctx.t("h_bullbear")):
            if ctx.bench_ret is None:
                st.info(ctx.t("not_enough_data"))
            else:
                split = an.bull_bear_split(an.daily_returns(prices), ctx.bench_ret)
                fig = go.Figure()
                fig.add_trace(go.Bar(x=[ctx.t("bull")], y=[split["bull"] * 100],
                                     marker_color=GAIN, name=ctx.t("bull")))
                fig.add_trace(go.Bar(x=[ctx.t("bear")], y=[split["bear"] * 100],
                                     marker_color=LOSS, name=ctx.t("bear")))
                st.plotly_chart(style_fig(fig, f"vs {ctx.benchmark}", "",
                                          ctx.t("y_return"), height=300,
                                          hover="closest", legend=False),
                                width="stretch")
    C.explain(ctx, "x_cycles")


# ----------------------------------------------------------------- forecast
def _forecast(ctx, ticker: str, prices: pd.Series) -> None:
    series = prices.dropna()
    horizon = st.slider(ctx.t("c_horizon"), 10, 180, 60, 10, key="pf_horizon")

    left, right = st.columns([3, 2])
    with left:
        forecast = an.ets_forecast(series, horizon)
        if forecast.empty:
            st.info(ctx.t("not_enough_data"))
        else:
            history = series.iloc[-min(len(series), 250):]
            vol = float(an.daily_returns(series).std() * np.sqrt(horizon))
            upper, lower = forecast * (1 + vol), forecast * (1 - vol)
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=history.index, y=history, name=ticker,
                                     line=dict(color="#14322E")))
            fig.add_trace(go.Scatter(x=forecast.index, y=forecast, name="ETS",
                                     line=dict(color="#0F766E", dash="dash")))
            fig.add_trace(go.Scatter(
                x=list(forecast.index) + list(forecast.index[::-1]),
                y=list(upper) + list(lower[::-1]), fill="toself",
                fillcolor="rgba(15,118,110,.18)", line=dict(color="rgba(0,0,0,0)"),
                name="90%"))
            st.plotly_chart(style_fig(fig, "", ctx.t("x_date"),
                                      f"{ctx.t('y_value')} ({ctx.currency})",
                                      height=400), width="stretch")
    with right:
        simulation = an.monte_carlo(series, days=horizon)
        if not simulation:
            st.info(ctx.t("not_enough_data"))
            return
        st.metric(ctx.t("prob_up"), f"{simulation['prob_up']:.1f}%",
                  f"{simulation['prob_up'] - 50:+.1f}")
        cols = st.columns(3)
        cols[0].metric(ctx.t("median"), f"{simulation['median']:,.2f}")
        cols[1].metric("P05", f"{simulation['p05']:,.2f}")
        cols[2].metric("P95", f"{simulation['p95']:,.2f}")
        paths = simulation["paths"]
        fig = go.Figure()
        for i in range(min(60, paths.shape[1])):
            fig.add_trace(go.Scatter(y=paths[:, i], line=dict(color="#9CA3AF", width=.5),
                                     opacity=.3, showlegend=False))
        fig.add_trace(go.Scatter(y=np.median(paths, axis=1), name=ctx.t("median"),
                                 line=dict(color=LOSS, width=2)))
        fig.update_layout(template="plotly_white", height=250, showlegend=False,
                          margin=dict(l=0, r=0, t=6, b=0),
                          xaxis=dict(visible=False), yaxis=dict(visible=False))
        st.plotly_chart(fig, width="stretch")
        C.commentary(ctx, i18n.forecast_narrative(
            ctx.lang, ticker, simulation["prob_up"], simulation["expected_return"],
            simulation["p05"], simulation["p95"], horizon))
    C.explain(ctx, "x_forecast")


# -------------------------------------------------------------- all metrics
def _all_metrics(ctx, ticker: str, prices: pd.Series) -> None:
    import report as rp
    frame = prices.to_frame(ticker)
    if ctx.benchmark in ctx.window.columns and ctx.benchmark != ticker:
        # the benchmark column is needed for beta / alpha / capture ratios
        frame = frame.join(ctx.window[[ctx.benchmark]], how="outer")
    window = rp.slice_window(frame, ctx.period)
    metrics = an.metrics_table(window, benchmark=ctx.benchmark, rf=ctx.rf,
                               profile=ctx.profile)
    if ticker not in metrics.index:
        st.info(ctx.t("not_enough_data"))
        return
    row = metrics.loc[ticker]
    tidy = pd.DataFrame({
        ctx.t("m_name"): [ctx.t(label) for _, (_, label) in
                          ((k, C.METRIC_FORMAT[k]) for k in C.METRIC_FORMAT
                           if k in metrics.columns)],
        ctx.t("value"): [row[k] for k in C.METRIC_FORMAT if k in metrics.columns],
    })
    st.dataframe(tidy, width="stretch", hide_index=True, height=560)
