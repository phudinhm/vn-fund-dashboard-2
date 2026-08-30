# -*- coding: utf-8 -*-
"""Data: coverage, health and the methodology behind every number."""

from __future__ import annotations

import pandas as pd
import streamlit as st

import i18n
from ui import components as C
from ui import state as S

UNIVERSE_COLUMNS = ["ticker", "name", "kind", "asset_class", "region", "country",
                    "currency", "issuer", "ter", "benchmark", "category",
                    "first_date", "last_date", "observations"]


def render(ctx) -> None:
    ds = ctx.ds
    stale = ds.status.get("stale", []) if ds.status else []

    C.commentary(ctx, i18n.quality_narrative(
        ctx.lang, int(ds.prices.shape[1]), ds.markets, ds.currencies,
        f"{ds.last_date:%d.%m.%Y}", len(stale)))

    cols = st.columns(4)
    cols[0].metric(ctx.t("n_instruments"), f"{ds.prices.shape[1]}")
    cols[1].metric(ctx.t("n_markets"), f"{ds.markets}")
    cols[2].metric(ctx.t("n_currencies"), f"{ds.currencies}")
    cols[3].metric(ctx.t("data_updated"), f"{ds.last_date:%d.%m.%Y}")

    tabs = st.tabs(["🗂️ " + ctx.t("h_universe"), "🩺 " + ctx.t("h_quality"),
                    "📐 " + ctx.t("h_method")])

    with tabs[0]:
        _universe(ctx)
    with tabs[1]:
        _quality(ctx, stale)
    with tabs[2]:
        C.explain(ctx, "x_data")
        st.markdown(ctx.t("x_data"))
        if ds.status:
            with st.expander("status.json"):
                st.json(ds.status)


def _universe(ctx) -> None:
    frame = ctx.profile[ctx.profile.ticker.isin(ctx.ds.prices.columns)]
    frame = frame[[c for c in UNIVERSE_COLUMNS if c in frame.columns]]

    cols = st.columns([2, 2, 2])
    search = cols[0].text_input("🔎 " + ctx.t("search_ticker"), key="data_search")
    regions = sorted(frame.region.dropna().unique()) if "region" in frame else []
    chosen = cols[1].multiselect(ctx.t("region"), regions, key="data_regions")
    kinds = sorted(frame.kind.dropna().unique()) if "kind" in frame else []
    chosen_kinds = cols[2].multiselect(ctx.t("kind"), kinds, key="data_kinds")

    if search:
        needle = search.lower()
        mask = frame.apply(
            lambda row: needle in " ".join(str(v).lower() for v in row.values), axis=1)
        frame = frame[mask]
    if chosen:
        frame = frame[frame.region.isin(chosen)]
    if chosen_kinds:
        frame = frame[frame.kind.isin(chosen_kinds)]

    event = st.dataframe(
        frame, width="stretch", height=460, hide_index=True,
        key="data_universe", on_select="rerun", selection_mode="multi-row",
        column_config={
            "ter": st.column_config.NumberColumn(ctx.t("m_ter"), format="%.2f%%"),
            "observations": st.column_config.NumberColumn(ctx.t("m_obs"), format="%d"),
        })
    rows = event.selection.rows if hasattr(event, "selection") else []
    picked = [frame.iloc[i]["ticker"] for i in rows if i < len(frame)]
    if st.button(f"➕ {ctx.t('add_to_compare')} ({len(picked)})", disabled=not picked,
                 key="data_add"):
        S.add_to_selection(picked)
        S.go_to("nav_compare")
        st.rerun()


def _quality(ctx, stale: list) -> None:
    status = ctx.ds.status or {}
    if stale:
        st.warning(ctx.t("stale_warning"))
        st.dataframe(pd.DataFrame(stale), width="stretch", hide_index=True)
    failed = status.get("failed", [])
    if failed:
        st.markdown(f"##### {ctx.t('update_failed')} ({len(failed)})")
        st.dataframe(pd.DataFrame(failed), width="stretch", hide_index=True)
    for warning in status.get("warnings", []):
        st.info(warning)

    coverage = ctx.profile[ctx.profile.ticker.isin(ctx.ds.prices.columns)]
    if "observations" in coverage.columns:
        st.markdown("##### " + ctx.t("m_obs"))
        import plotly.express as px
        from ui.theme import style_fig
        fig = px.histogram(coverage, x="observations", color="region", nbins=40,
                           height=320)
        st.plotly_chart(style_fig(fig, "", ctx.t("m_obs"), ctx.t("n_funds"),
                                  hover="closest"), width="stretch")
