# -*- coding: utf-8 -*-
"""Screener: filter and rank the whole universe, then add rows to the comparison.

This is the answer to "compare every ETF on every market": the metrics are
computed once for all ~250 instruments and the user narrows them down with the
numbers themselves rather than hunting through a 250-item dropdown.
"""

from __future__ import annotations

import pandas as pd
import streamlit as st

import analytics as an
import report as rp
from ui import components as C
from ui import state as S

RESULT_COLUMNS = ["name", "kind", "region", "country", "currency", "cagr",
                  "volatility", "max_drawdown", "sharpe", "sortino", "calmar",
                  "ter", "observations", "score"]

SORT_KEYS = ["score", "cagr", "sharpe", "sortino", "calmar", "volatility",
             "max_drawdown", "ter"]


@st.cache_data(show_spinner=False, ttl=3600)
def universe_metrics(_ds, currency: str, period: str, rf: float, last_date: str):
    """Every metric for every instrument, in one reporting currency."""
    prices = an.convert_prices(_ds.prices, _ds.profile, _ds.fx, currency)
    window = rp.slice_window(prices, period).dropna(axis=1, how="all")
    metrics = an.metrics_table(window, benchmark=None, rf=rf, profile=_ds.profile)
    scored = an.composite_score(metrics)
    scored["history_years"] = [
        (window[t].dropna().index[-1] - window[t].dropna().index[0]).days / 365.25
        if t in window.columns and window[t].notna().any() else 0.0
        for t in scored.index]
    return scored, window


def render(ctx) -> None:
    st.markdown("### " + ctx.t("screener_title"))
    with st.spinner(ctx.t("screener_computing")):
        scored, window = universe_metrics(
            ctx.ds, ctx.currency, ctx.period, ctx.rf,
            ctx.ds.last_date.strftime("%Y-%m-%d"))
    st.caption(ctx.t("screener_help").format(n=len(scored)))

    frame = _filters(ctx, scored)
    if frame.empty:
        st.warning(ctx.t("screener_no_results"))
        return

    _summary(ctx, frame, scored)

    st.markdown(f"#### {ctx.t('screener_results')} · {len(frame)}")
    st.caption(ctx.t("screener_hint"))
    top_n = st.session_state.get("screener_top_n", 40)
    picked = C.leaderboard(ctx, frame.head(top_n), window, RESULT_COLUMNS,
                           key="screener_table", height=520)

    cols = st.columns([2, 2, 4])
    if cols[0].button(f"➕ {ctx.t('add_to_compare')} ({len(picked)})",
                      disabled=not picked, width="stretch", key="scr_add"):
        added = S.add_to_selection(picked)
        S.go_to("nav_compare")
        st.toast(f"{ctx.t('added')}: {added}")
        st.rerun()
    if cols[1].button(f"🔬 {ctx.t('open_profile')}", disabled=len(picked) != 1,
                      width="stretch", key="scr_profile"):
        S.set_focus(picked[0])
        S.go_to("nav_profile")
        st.rerun()


def _filters(ctx, scored: pd.DataFrame) -> pd.DataFrame:
    prof = ctx.ds.profile.set_index("ticker")
    frame = scored.copy()

    with st.container(border=True):
        row1 = st.columns([2, 2, 2, 2])
        regions = sorted(prof.region.dropna().unique())
        sel_regions = row1[0].multiselect(ctx.t("region"), regions, default=[],
                                          key="scr_regions")
        kinds = sorted(prof.kind.dropna().unique())
        sel_kinds = row1[1].multiselect(ctx.t("kind"), kinds, default=[], key="scr_kinds")
        classes = sorted(prof.asset_class.dropna().unique())
        sel_classes = row1[2].multiselect(ctx.t("asset_class"), classes, default=[],
                                          key="scr_classes")
        search = row1[3].text_input("🔎 " + ctx.t("search_ticker"), key="scr_search")

        row2 = st.columns(6)
        min_cagr = row2[0].slider(ctx.t("screener_min_cagr"), -30.0, 40.0, -30.0, 1.0,
                                  key="scr_cagr")
        max_vol = row2[1].slider(ctx.t("screener_max_vol"), 0.0, 80.0, 80.0, 1.0,
                                 key="scr_vol")
        min_sharpe = row2[2].slider(ctx.t("screener_min_sharpe"), -2.0, 3.0, -2.0, 0.1,
                                    key="scr_sharpe")
        max_dd = row2[3].slider(ctx.t("screener_max_dd"), 0.0, 100.0, 100.0, 5.0,
                                key="scr_dd")
        max_ter = row2[4].slider(ctx.t("screener_max_ter"), 0.0, 1.5, 1.5, 0.05,
                                 key="scr_ter")
        # a fund with three months of history produces meaningless ratios, so the
        # screener asks for a year before it will rank anything
        min_hist = row2[5].slider(ctx.t("screener_min_history"), 0.0, 10.0, 1.0, 0.5,
                                  key="scr_hist")

        row3 = st.columns([2, 2, 2])
        sort_by = row3[0].selectbox(
            ctx.t("screener_sort"), SORT_KEYS, key="scr_sort",
            format_func=lambda k: ctx.t(C.METRIC_FORMAT.get(k, (None, k))[1] or k))
        row3[1].select_slider(ctx.t("top_n"), options=[20, 40, 80, 150, 300],
                              value=40, key="screener_top_n")
        if row3[2].button("↺ " + ctx.t("screener_reset"), width="stretch",
                          key="scr_reset"):
            for key in ["scr_regions", "scr_kinds", "scr_classes", "scr_search",
                        "scr_cagr", "scr_vol", "scr_sharpe", "scr_dd", "scr_ter",
                        "scr_hist"]:
                st.session_state.pop(key, None)
            st.rerun()

    meta_cols = ["region", "kind", "asset_class", "country", "name", "issuer", "category"]
    for col in meta_cols:
        if col not in frame.columns and col in prof.columns:
            frame[col] = prof[col].reindex(frame.index)

    if sel_regions:
        frame = frame[frame.region.isin(sel_regions)]
    if sel_kinds:
        frame = frame[frame.kind.isin(sel_kinds)]
    if sel_classes:
        frame = frame[frame.asset_class.isin(sel_classes)]
    if search:
        needle = search.lower()
        haystack = (frame.index.to_series().str.lower() + " "
                    + frame.get("name", pd.Series("", index=frame.index)).astype(str).str.lower()
                    + " " + frame.get("issuer", pd.Series("", index=frame.index)).astype(str).str.lower()
                    + " " + frame.get("country", pd.Series("", index=frame.index)).astype(str).str.lower())
        frame = frame[haystack.str.contains(needle, na=False)]

    frame = frame[(frame.cagr.fillna(-9) >= min_cagr / 100)
                  & (frame.volatility.fillna(9) <= max_vol / 100)
                  & (frame.sharpe.fillna(-9) >= min_sharpe)
                  & (frame.max_drawdown.fillna(-9) >= -max_dd / 100)
                  & (frame.history_years.fillna(0) >= min_hist)]
    if "ter" in frame.columns:
        frame = frame[frame.ter.isna() | (frame.ter <= max_ter)]

    ascending = sort_by in ("volatility", "ter")
    return frame.sort_values(sort_by, ascending=ascending, na_position="last")


def _summary(ctx, frame: pd.DataFrame, everything: pd.DataFrame) -> None:
    cols = st.columns(5)
    cols[0].metric(ctx.t("screener_results"), f"{len(frame)}",
                   f"/ {len(everything)}", delta_color="off")
    cols[1].metric(ctx.t("median") + " " + ctx.t("m_cagr"),
                   C.pct(frame.cagr.median(), 1))
    cols[2].metric(ctx.t("median") + " " + ctx.t("m_volatility"),
                   C.pct(frame.volatility.median(), 1))
    cols[3].metric(ctx.t("median") + " " + ctx.t("m_sharpe"),
                   C.num(frame.sharpe.median()))
    cols[4].metric(ctx.t("median") + " " + ctx.t("m_ter"),
                   C.num(frame.ter.median(), 2) if "ter" in frame else "—")
