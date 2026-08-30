# -*- coding: utf-8 -*-
"""Lab: simulate what an investor would actually have done."""

from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

import analytics as an
import i18n
from ui import components as C
from ui.theme import BENCH, GAIN, LOSS, style_fig


def render(ctx) -> None:
    tabs = st.tabs(["💸 " + ctx.t("lab_dca"), "⚔️ " + ctx.t("lab_lsdca"),
                    "🧩 " + ctx.t("lab_portfolio"), "💰 " + ctx.t("lab_costs")])
    with tabs[0]:
        _dca(ctx)
    with tabs[1]:
        _lump_vs_dca(ctx)
    with tabs[2]:
        _portfolio(ctx)
    with tabs[3]:
        _costs(ctx)


def _fund_picker(ctx, key: str) -> str:
    options = list(ctx.window.columns)
    index = options.index(ctx.focus) if ctx.focus in options else 0
    return st.selectbox(ctx.t("focus_fund"), options, index=index,
                        format_func=ctx.label, key=key)


def _dca(ctx) -> None:
    cols = st.columns([2, 1, 1])
    fund = _fund_picker(ctx, "lab_dca_fund")
    amount = cols[1].number_input(ctx.t("c_contribution"), 100.0, 1e9, 1000.0, 100.0,
                                  key="lab_amount")
    freq_label = cols[2].selectbox(ctx.t("c_frequency"),
                                   [ctx.t("c_monthly"), ctx.t("c_weekly")],
                                   key="lab_freq")
    freq = "ME" if freq_label == ctx.t("c_monthly") else "W"

    plan = an.simulate_dca(ctx.window[fund], amount, freq)
    if plan.empty:
        st.info(ctx.t("not_enough_data"))
        return
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=plan.index, y=plan.invested, name=ctx.t("invested"),
                             line=dict(color=BENCH, dash="dash")))
    fig.add_trace(go.Scatter(x=plan.index, y=plan.value, name=ctx.t("value"),
                             line=dict(color="#0F766E"), fill="tonexty",
                             fillcolor="rgba(15,118,110,.12)"))
    st.plotly_chart(style_fig(fig, fund, ctx.t("x_date"),
                              f"{ctx.t('y_value')} ({ctx.currency})", height=400),
                    width="stretch")
    metrics = st.columns(3)
    metrics[0].metric(ctx.t("invested"), f"{plan.invested.iloc[-1]:,.0f}")
    metrics[1].metric(ctx.t("value"), f"{plan.value.iloc[-1]:,.0f}")
    metrics[2].metric(ctx.t("profit"), f"{plan.profit.iloc[-1]:,.0f}",
                      f"{plan['return'].iloc[-1] * 100:.1f}%")


def _lump_vs_dca(ctx) -> None:
    cols = st.columns([2, 1, 1])
    fund = _fund_picker(ctx, "lab_ls_fund")
    hold = cols[1].slider(ctx.t("c_hold_years"), 1, 15, 5, key="lab_hold")
    spread = cols[2].slider(ctx.t("c_spread_months"), 3, 36, 12, key="lab_spread")

    result = an.rolling_dca_vs_lumpsum(ctx.prices[fund], hold, spread)
    if not result.get("windows"):
        st.info(ctx.t("not_enough_data"))
        return
    C.commentary(ctx, i18n.strategy_narrative(
        ctx.lang, result["lump_sum_win_rate"], result["median_lump"],
        result["median_dca"], hold))
    metrics = st.columns(4)
    metrics[0].metric(ctx.t("windows"), f"{result['windows']}")
    metrics[1].metric(f"{ctx.t('win_rate')} · {ctx.t('lump_sum')}",
                      f"{result['lump_sum_win_rate']:.1f}%")
    metrics[2].metric(f"{ctx.t('median')} · {ctx.t('lump_sum')}",
                      C.pct(result["median_lump"], 1))
    metrics[3].metric(f"{ctx.t('median')} · {ctx.t('dca')}",
                      C.pct(result["median_dca"], 1))

    fig = go.Figure()
    fig.add_trace(go.Bar(x=[ctx.t("lump_sum"), ctx.t("dca")],
                         y=[result["median_lump"] * 100, result["median_dca"] * 100],
                         marker_color=[GAIN, "#0F766E"]))
    st.plotly_chart(style_fig(fig, "", "", ctx.t("y_return"), height=300,
                              hover="closest", legend=False), width="stretch")
    C.explain(ctx, "x_strategy")


def _portfolio(ctx) -> None:
    candidates = [t for t in ctx.window.columns if t != ctx.benchmark]
    if len(candidates) < 2:
        st.info(ctx.t("not_enough_data"))
        return

    default = pd.DataFrame({
        "ticker": candidates,
        ctx.t("weights"): [round(100 / len(candidates), 1)] * len(candidates),
    })
    cols = st.columns([3, 1, 1])
    with cols[0]:
        edited = st.data_editor(
            default, hide_index=True, width="stretch", key="lab_weights",
            column_config={
                "ticker": st.column_config.TextColumn(ctx.t("m_name"), disabled=True),
                ctx.t("weights"): st.column_config.NumberColumn(
                    ctx.t("weights"), min_value=0.0, max_value=100.0, step=5.0,
                    format="%.1f")})
    rebalance = cols[1].radio(ctx.t("c_rebalance"),
                              [ctx.t("c_quarterly"), ctx.t("c_annually")],
                              key="lab_rebalance")
    freq = "QE" if rebalance == ctx.t("c_quarterly") else "YE"

    weights = {row.ticker: float(row[ctx.t("weights")]) for _, row in edited.iterrows()
               if float(row[ctx.t("weights")]) > 0}
    if not weights:
        st.info(ctx.t("not_enough_data"))
        return
    total = sum(weights.values())
    cols[2].metric(ctx.t("normalize_weights"), f"{total:.0f}%")

    curve = an.rebalanced_portfolio(ctx.window, weights, freq)
    if curve.empty:
        st.info(ctx.t("not_enough_data"))
        return

    compare = pd.DataFrame({ctx.t("lab_portfolio"): curve})
    if ctx.benchmark in ctx.window.columns:
        compare[ctx.benchmark] = an.cumulative_growth(
            ctx.window[[ctx.benchmark]].ffill())[ctx.benchmark]
    fig = px.line(compare.dropna(), height=400)
    st.plotly_chart(style_fig(fig, "", ctx.t("x_date"), ctx.t("y_value")),
                    width="stretch")

    returns = an.daily_returns(curve)
    metrics = st.columns(4)
    metrics[0].metric(ctx.t("m_cagr"), C.pct(an.cagr(curve), 1))
    metrics[1].metric(ctx.t("m_volatility"), C.pct(an.annual_volatility(returns), 1))
    metrics[2].metric(ctx.t("m_maxdd"), C.pct(an.max_drawdown(curve), 1))
    metrics[3].metric(ctx.t("m_sharpe"), C.num(an.sharpe(curve, ctx.rf)))

    st.markdown("##### " + ctx.t("risk_contribution"))
    contribution = an.risk_contribution(ctx.window, weights)
    if not contribution.empty:
        frame = pd.DataFrame({
            ctx.t("weights"): pd.Series({k: v / total for k, v in weights.items()}),
            ctx.t("risk_contribution"): contribution})
        fig = go.Figure()
        fig.add_trace(go.Bar(x=frame.index, y=frame[ctx.t("weights")] * 100,
                             name=ctx.t("weights"), marker_color=BENCH))
        fig.add_trace(go.Bar(x=frame.index, y=frame[ctx.t("risk_contribution")] * 100,
                             name=ctx.t("risk_contribution"), marker_color=LOSS))
        fig.update_layout(barmode="group")
        st.plotly_chart(style_fig(fig, "", "", "%", height=320, hover="closest"),
                        width="stretch")


def _costs(ctx) -> None:
    cols = st.columns(4)
    fund = _fund_picker(ctx, "lab_fee_fund")
    default_ter = 0.5
    if "ter" in ctx.metrics.columns and fund in ctx.metrics.index:
        value = ctx.metrics.loc[fund, "ter"]
        default_ter = float(value) if pd.notna(value) else 0.5
    ter = cols[1].number_input(ctx.t("m_ter") + " (%)", 0.0, 5.0, default_ter, 0.05,
                               key="lab_ter") / 100
    gross = cols[2].number_input(ctx.t("c_gross_return"), 0.0, 30.0, 10.0, 0.5,
                                 key="lab_gross") / 100
    years = cols[3].slider(ctx.t("c_years"), 5, 40, 20, key="lab_years")

    erosion = an.fee_erosion(100.0, gross, ter, years)
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=erosion.year, y=erosion.gross, name=ctx.t("gross"),
                             line=dict(color="#0F766E")))
    fig.add_trace(go.Scatter(x=erosion.year, y=erosion.net, name=ctx.t("net"),
                             line=dict(color="#B45309"), fill="tonexty",
                             fillcolor="rgba(180,83,9,.15)"))
    st.plotly_chart(style_fig(fig, "", ctx.t("c_years"), ctx.t("y_value"), height=380),
                    width="stretch")
    lost = float(erosion.lost.iloc[-1] / erosion.gross.iloc[-1]) if erosion.gross.iloc[-1] else np.nan
    C.commentary(ctx, i18n.cost_narrative(ctx.lang, fund, ter * 100, lost, years))

    st.markdown("##### " + ctx.t("h_ter_vs_perf"))
    if "ter" in ctx.metrics.columns and ctx.metrics.ter.notna().any():
        frame = ctx.metrics.dropna(subset=["ter"]).copy()
        frame["cagr_pct"] = frame.cagr * 100
        C.scatter_picker(ctx, frame, "ter", "cagr_pct", "lab_fee_scatter",
                         ctx.t("m_ter") + " (%)", ctx.t("y_cagr"),
                         color="issuer" if "issuer" in frame.columns else None,
                         height=420)
    C.explain(ctx, "x_costs")
