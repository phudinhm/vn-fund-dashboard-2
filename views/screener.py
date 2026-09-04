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
import i18n
import report as rp
from ui import components as C
from ui import state as S

ESSENTIAL_COLUMNS = ["name", "kind", "region", "cagr", "volatility",
                     "max_drawdown", "sharpe", "ter", "adv", "score"]
FULL_COLUMNS = ["name", "kind", "region", "country", "currency", "category",
                "issuer", "cagr", "volatility", "max_drawdown",
                "time_under_water", "sharpe", "sortino", "calmar", "ter", "adv",
                "observations", "coverage", "score"]

SORT_KEYS = ["score", "cagr", "sharpe", "sortino", "calmar", "adv", "volatility",
             "max_drawdown", "ter"]
# metrics whose leading value reads as a percentage rather than a ratio
PERCENT_SORTS = {"cagr", "volatility", "max_drawdown", "ter"}


@st.cache_data(show_spinner=False, ttl=3600)
def universe_metrics(_ds, tickers: tuple, currency: str, period: str, rf: float,
                     last_date: str):
    """Every metric for every instrument the scope filters allow."""
    columns = [t for t in tickers if t in _ds.prices.columns]
    prices = an.convert_prices(_ds.prices[columns], _ds.profile, _ds.fx, currency)
    window = rp.slice_window(prices, period).dropna(axis=1, how="all")
    volume = _ds.volume if not _ds.volume.empty else None
    metrics = an.metrics_table(window, benchmark=None, rf=rf, profile=_ds.profile,
                               volume=volume)
    scored = an.composite_score(metrics)
    scored["history_years"] = [
        (window[t].dropna().index[-1] - window[t].dropna().index[0]).days / 365.25
        if t in window.columns and window[t].notna().any() else 0.0
        for t in scored.index]
    return scored, window


def render(ctx) -> None:
    with st.spinner(ctx.t("screener_computing")):
        scored, window = universe_metrics(
            ctx.ds, tuple(ctx.universe), ctx.currency, ctx.period, ctx.rf,
            ctx.ds.last_date.strftime("%Y-%m-%d"))
    if scored.empty:
        st.warning(ctx.t("screener_no_results"))
        return
    st.caption(ctx.t("screener_help").format(n=len(scored)))

    frame = _filters(ctx, scored)
    if frame.empty:
        st.warning(ctx.t("screener_no_results"))
        return

    _summary(ctx, frame, scored)

    with C.card(f"{ctx.t('screener_results')} · {len(frame)}",
                f"{ctx.t('screener_hint')} {ctx.t('unranked_note')}"):
        columns = C.column_choice(ctx, "scr_cols", ESSENTIAL_COLUMNS, FULL_COLUMNS)
        top_n = st.session_state.get("screener_top_n", 40)
        picked = C.leaderboard(ctx, frame.head(top_n), window, columns,
                               key="screener_table", height=500)

        cols = st.columns([2, 2, 4])
        if cols[0].button(f"{ctx.t('add_to_compare')} ({len(picked)})",
                          disabled=not picked, width="stretch", key="scr_add"):
            added = S.add_to_selection(picked)
            S.go_to("nav_compare")
            st.toast(f"{ctx.t('added')}: {added}")
            st.rerun()
        if cols[1].button(ctx.t("open_profile"), disabled=len(picked) != 1,
                          width="stretch", key="scr_profile"):
            S.set_focus(picked[0])
            S.go_to("nav_profile")
            st.rerun()


def _filters(ctx, scored: pd.DataFrame) -> pd.DataFrame:
    prof = ctx.ds.profile.set_index("ticker")
    frame = scored.copy()

    with st.container(border=True):
        st.caption(ctx.t("filter_note"))
        search = st.text_input(ctx.t("search_ticker"), key="scr_search")

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
        # with several hundred ETFs in scope, liquidity is the filter that
        # separates tradable funds from listed-but-dormant ones
        min_adv = st.slider(ctx.t("screener_min_adv"), 0.0, 100.0, 0.0, 1.0,
                            key="scr_adv")
        # a 2x single-stock fund will always top a return ranking; it belongs in
        # the universe but not in the default view of it
        hide_leveraged = st.toggle(ctx.t("exclude_leveraged"), value=True,
                                   key="scr_leverage")

        row3 = st.columns([2, 2, 2])
        sort_by = row3[0].selectbox(
            ctx.t("screener_sort"), SORT_KEYS, key="scr_sort",
            format_func=lambda k: ctx.t(C.METRIC_FORMAT.get(k, (None, k))[1] or k))
        row3[1].select_slider(ctx.t("top_n"), options=[20, 40, 80, 150, 300],
                              value=40, key="screener_top_n")
        if row3[2].button(ctx.t("screener_reset"), width="stretch", key="scr_reset"):
            for key in ["scr_search", "scr_cagr", "scr_vol", "scr_sharpe",
                        "scr_dd", "scr_ter", "scr_hist", "scr_adv",
                        "scr_leverage"]:
                st.session_state.pop(key, None)
            st.rerun()

    meta_cols = ["region", "kind", "asset_class", "country", "name", "issuer", "category"]
    for col in meta_cols:
        if col not in frame.columns and col in prof.columns:
            frame[col] = prof[col].reindex(frame.index)

    if search:
        needle = search.lower()
        haystack = (frame.index.to_series().str.lower() + " "
                    + frame.get("name", pd.Series("", index=frame.index)).astype(str).str.lower()
                    + " " + frame.get("issuer", pd.Series("", index=frame.index)).astype(str).str.lower()
                    + " " + frame.get("country", pd.Series("", index=frame.index)).astype(str).str.lower())
        frame = frame[haystack.str.contains(needle, na=False)]

    if hide_leveraged and "category" in frame.columns:
        frame = frame[frame.category != "Leveraged / Inverse"]
    if "adv" in frame.columns and min_adv > 0:
        frame = frame[frame.adv.fillna(0) >= min_adv * 1e6]
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
    if len(frame):
        sort_by = st.session_state.get("scr_sort", "score")
        label = ctx.t(C.METRIC_FORMAT.get(sort_by, (None, sort_by))[1] or sort_by)
        top_value = frame[sort_by].iloc[0] if sort_by in frame.columns else float("nan")
        C.readout(ctx, i18n.screener_readout(
            ctx.lang, len(frame), len(everything), frame.index[0],
            float(top_value) if pd.notna(top_value) else float("nan"), label,
            float(frame.cagr.median()),
            float(frame.ter.median()) if "ter" in frame else float("nan"),
            as_percent=sort_by in PERCENT_SORTS))
    cols = st.columns(5)
    cols[0].metric(f"{ctx.t('screener_results')} / {len(everything)}", f"{len(frame)}")
    cols[1].metric(ctx.t("median") + " " + ctx.t("m_cagr"),
                   C.pct(frame.cagr.median(), 1))
    cols[2].metric(ctx.t("median") + " " + ctx.t("m_volatility"),
                   C.pct(frame.volatility.median(), 1))
    cols[3].metric(ctx.t("median") + " " + ctx.t("m_sharpe"),
                   C.num(frame.sharpe.median()))
    cols[4].metric(ctx.t("median") + " " + ctx.t("m_ter"),
                   C.num(frame.ter.median(), 2) if "ter" in frame else "—")
