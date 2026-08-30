# -*- coding: utf-8 -*-
"""
Global ETF & Fund Report — application shell.

The shell owns three things and nothing else: the page frame, the settings
sidebar and the navigation between the seven sections in ``views/``. Every
number comes from ``analytics.py``, every word from ``i18n.py`` and the state
that defines a view lives in ``ui/state.py`` (and in the URL, so any view of
the report can be shared as a link).

Run locally:  streamlit run app.py
"""

from __future__ import annotations

import subprocess
import sys

import streamlit as st

import i18n
import report as rp
from ui import state as S
from ui import theme
from views import compare, data, lab, markets, overview, profile, screener

st.set_page_config(page_title="Global ETF Report", page_icon="🌍",
                   layout="wide", initial_sidebar_state="expanded")
theme.inject()

SECTIONS = [
    ("nav_overview", "🏠", overview.render),
    ("nav_screener", "🔎", screener.render),
    ("nav_compare", "📊", compare.render),
    ("nav_markets", "🌐", markets.render),
    ("nav_profile", "🔬", profile.render),
    ("nav_lab", "🧪", lab.render),
    ("nav_data", "🗂️", data.render),
]


@st.cache_data(show_spinner=False)
def load_dataset():
    return rp.load_dataset()


def language_switch() -> None:
    cols = st.sidebar.columns(3)
    for col, code in zip(cols, ["VI", "EN", "DE"]):
        active = st.session_state.get("lang") == code
        if col.button(f"{i18n.FLAGS[code]} {code}", width="stretch",
                      type="primary" if active else "secondary", key=f"lang_{code}"):
            st.session_state["lang"] = code
            st.rerun()


def sidebar(ds, T) -> None:
    with st.sidebar:
        st.caption(f"📅 {T('data_updated')} **{ds.last_date:%d.%m.%Y}** · "
                   f"{ds.prices.shape[1]} {T('selection_count')}")

        st.markdown("#### " + T("settings"))
        currencies = ([c for c in ["USD", "EUR", "VND"] if c in ds.fx.columns]
                      or sorted(ds.profile.currency.dropna().unique()))
        st.selectbox(T("currency"), currencies, key="currency", help=T("currency_help"))

        benchmarks = sorted(set(ds.profile[ds.profile.kind == "Index"].ticker)
                            & set(ds.prices.columns))
        benchmarks = benchmarks or list(ds.prices.columns[:20])
        if st.session_state["benchmark"] not in benchmarks:
            benchmarks = [st.session_state["benchmark"]] + benchmarks
        st.selectbox(T("benchmark"), benchmarks, key="benchmark")

        st.select_slider(T("time_range"), options=rp.RANGES, key="period")
        st.slider(T("risk_free"), 0.0, 10.0, step=0.25, key="rf")

        st.markdown("#### " + T("quick_pick"))
        presets = {T(key): tickers
                   for key, tickers in rp.presets(ds.profile, ds.prices).items()
                   if tickers}
        chosen = st.selectbox(T("quick_pick"), ["—"] + list(presets),
                              label_visibility="collapsed", key="preset")
        if chosen != "—" and st.button("➕ " + T("apply"), width="stretch",
                                       key="apply_preset"):
            st.session_state["selection"] = presets[chosen][:12]
            st.rerun()

        with st.expander("🔄 " + T("update_btn")):
            st.caption(T("auto_note"))
            if st.button(T("update_btn"), width="stretch", key="do_update"):
                with st.spinner(T("updating")):
                    result = subprocess.run([sys.executable, "update_data.py"],
                                            capture_output=True, text=True)
                if result.returncode == 0:
                    st.cache_data.clear()
                    st.success(T("update_done"))
                else:
                    st.error(f"{T('update_failed')}: {result.stderr[-400:]}")

        st.markdown("---")
        st.caption("© 2026 Minh Phu Dinh · " + T("footer"))


def selection_bar(ctx) -> None:
    """Chips showing what is being compared, with a one-click way to change it."""
    T = ctx.t
    left, right = st.columns([5, 2])
    with left:
        chips = "".join(
            f"<span class='chip{' chip-bench' if t == ctx.benchmark else ''}'>{t}</span>"
            for t in ctx.tickers)
        st.markdown(
            f"<div class='selbar'><b>{T('selection')}</b> · {len(ctx.tickers)} "
            f"{T('selection_count')}<br>{chips}</div>", unsafe_allow_html=True)
    with right:
        picker, clear = st.columns([3, 2])
        with picker.popover("✏️ " + T("select_funds"), width="stretch"):
            options = list(ctx.ds.prices.columns)
            st.multiselect(T("select_funds"), options, key="selection",
                           format_func=ctx.label, max_selections=20)
            st.caption(T("nav_screener_help"))
        if clear.button("🗑️ " + T("clear_selection"), width="stretch", key="clear_sel"):
            st.session_state["selection"] = rp.default_selection(ctx.ds.profile,
                                                                 ctx.ds.prices)
            st.rerun()


def main() -> None:
    ds = load_dataset()
    if ds is None:
        st.title("🌍 Global ETF Report")
        st.warning(i18n.t("EN", "no_data"))
        st.stop()

    S.init_state(ds)
    language_switch()
    T = lambda key: i18n.t(st.session_state["lang"], key)

    sidebar(ds, T)

    st.title("🌍 " + T("app_title"))
    st.caption(T("app_subtitle"))

    labels = {f"{icon} {T(key)}": key for key, icon, _ in SECTIONS}
    current = st.session_state.get("view", "nav_overview")
    current_label = next((lbl for lbl, key in labels.items() if key == current),
                         list(labels)[0])
    chosen = st.segmented_control(T("compare_tabs"), list(labels),
                                  default=current_label, key="nav",
                                  label_visibility="collapsed")
    if chosen and labels[chosen] != current:
        st.session_state["view"] = labels[chosen]
        st.rerun()
    view_key = st.session_state["view"]
    st.caption(T(f"{view_key}_help"))

    if not st.session_state.get("selection"):
        st.session_state["selection"] = rp.default_selection(ds.profile, ds.prices)

    ctx = S.build_context(ds)
    if ctx.window.empty or len(ctx.window.columns) == 0:
        st.warning(T("not_enough_data"))
        st.stop()

    if view_key not in ("nav_screener", "nav_data"):
        selection_bar(ctx)

    render = dict((key, fn) for key, _, fn in SECTIONS)[view_key]
    render(ctx)

    S.sync_query_params()


main()
