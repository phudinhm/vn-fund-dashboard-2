# -*- coding: utf-8 -*-
"""Overview: what the current selection looks like at a glance."""

from __future__ import annotations

import numpy as np
import streamlit as st

import i18n
import report as rp
from ui import components as C
from ui import state as S

BOARD_COLUMNS = ["rank", "name", "region", "currency", "cagr", "volatility",
                 "max_drawdown", "sharpe", "sortino", "calmar", "beta", "alpha",
                 "tracking_error", "ter", "score"]


def render(ctx) -> None:
    if ctx.facts:
        C.commentary(ctx, i18n.summary_narrative(ctx.lang, ctx.facts))

    _kpis(ctx)

    st.markdown("### " + ctx.t("h_growth"))
    opts = C.chart_options(ctx, "ov")
    C.growth_chart(ctx, ctx.window, log_scale=opts["log"], relative=opts["relative"])
    C.explain(ctx, "x_growth")

    st.markdown("### " + ctx.t("h_leaderboard"))
    st.caption(ctx.t("screener_hint"))
    picked = C.leaderboard(ctx, ctx.scored, ctx.prices, BOARD_COLUMNS,
                           key="overview_board",
                           height=min(120 + 36 * len(ctx.scored), 460))
    if len(picked) == 1:
        if st.button(f"🔬 {ctx.t('open_profile')}: {picked[0]}", key="ov_profile"):
            S.set_focus(picked[0])
            S.go_to("nav_profile")
            st.rerun()

    _exports(ctx)


def _kpis(ctx) -> None:
    f = ctx.facts
    if not f:
        return
    bench_cagr = f.get("benchmark_cagr", np.nan)
    cols = st.columns(5)
    cols[0].metric(ctx.t("n_instruments"), f"{len(ctx.window.columns)}",
                   f"{f.get('beat_count', 0)}/{f.get('total', 0)} > {ctx.benchmark}",
                   delta_color="off")
    best_delta = f.get("best_cagr", np.nan) - bench_cagr if bench_cagr == bench_cagr else None
    cols[1].metric(ctx.t("best"), f.get("best", "—"),
                   C.pct(best_delta, 1) if best_delta is not None else None)
    cols[2].metric(ctx.t("worst"), f.get("worst", "—"),
                   C.pct(f.get("worst_cagr", np.nan), 1), delta_color="off")
    cols[3].metric(f"{ctx.t('m_sharpe')} · {f.get('best_sharpe', '—')}",
                   C.num(f.get("best_sharpe_value", np.nan)))
    cols[4].metric(f"{ctx.t('m_maxdd')} · {f.get('deepest_dd', '—')}",
                   C.pct(f.get("deepest_dd_value", np.nan), 1))


def _exports(ctx) -> None:
    st.markdown("### " + ctx.t("h_export"))
    cols = st.columns(3)
    cols[0].download_button(
        "⬇️ " + ctx.t("c_download_csv"), ctx.scored.to_csv().encode("utf-8"),
        file_name=f"etf_metrics_{ctx.period}_{ctx.currency}.csv",
        mime="text/csv", width="stretch")
    markdown = rp.markdown_report(ctx.lang, ctx.ds, ctx.tickers, ctx.period,
                                  ctx.benchmark, ctx.currency, ctx.rf)
    cols[1].download_button(
        "⬇️ " + ctx.t("c_download_report"), markdown.encode("utf-8"),
        file_name=f"etf_report_{ctx.lang}_{ctx.period}.md",
        mime="text/markdown", width="stretch")
    cols[2].download_button(
        "⬇️ " + ctx.t("y_value") + " (CSV)", ctx.window.to_csv().encode("utf-8"),
        file_name=f"prices_{ctx.currency}_{ctx.period}.csv",
        mime="text/csv", width="stretch")
