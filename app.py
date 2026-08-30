# -*- coding: utf-8 -*-
"""
Global ETF & Fund Report — application shell.

The shell owns the page frame, the navigation dock and the settings that define
every number on screen. Analysis lives in ``analytics.py``, wording in
``i18n.py``, shared widgets in ``ui/`` and one module per section in ``views/``.

State (language, section, scope filters, selection, benchmark, currency,
period, risk-free rate) is mirrored into the URL, so any view of the report can
be shared as a link.

Run locally:  streamlit run app.py
"""

from __future__ import annotations

import streamlit as st

import i18n
import report as rp
from ui import state as S
from ui import theme
from views import compare, data, lab, markets, overview, profile, screener

st.set_page_config(page_title="Global ETF Report", page_icon="◆",
                   layout="wide", initial_sidebar_state="expanded")
theme.inject()

SECTIONS = [
    ("nav_overview", overview.render),
    ("nav_screener", screener.render),
    ("nav_compare", compare.render),
    ("nav_markets", markets.render),
    ("nav_profile", profile.render),
    ("nav_lab", lab.render),
    ("nav_data", data.render),
]


@st.cache_data(show_spinner=False)
def load_dataset():
    return rp.load_dataset()


def dock(ds, T) -> str:
    """Navigation rail plus the settings, grouped. Dims until you reach for it.

    Nothing here calls ``st.rerun()`` in the middle: Streamlit drops the state of
    any widget a run did not draw, so a rerun before the settings are rendered
    would wipe the benchmark, currency and period. Clicks are recorded and acted
    on once the whole dock exists.
    """
    pending: dict = {}
    with st.sidebar:
        st.markdown(f"<div class='dock-brand'>{T('app_title')}</div>"
                    f"<div class='dock-sub'>{T('brand_sub')}</div>",
                    unsafe_allow_html=True)

        cols = st.columns(3)
        for col, code in zip(cols, ["VI", "EN", "DE"]):
            active = st.session_state.get("lang") == code
            if col.button(code, width="stretch", key=f"lang_{code}",
                          type="primary" if active else "secondary"):
                pending["lang"] = code

        st.markdown(f"<div class='dock-group'>{T('group_sections')}</div>",
                    unsafe_allow_html=True)
        # buttons rather than a radio: a navigation rail should not look like a
        # form field, and the active item needs a real selected state
        view_key = st.session_state.get("view", "nav_overview")
        for key, _ in SECTIONS:
            if st.button(T(key), key=f"nav_{key}", width="stretch",
                         type="primary" if key == view_key else "tertiary"):
                pending["view"] = key

        _scope_filters(ds, T, pending)
        _parameters(ds, T)

        st.markdown("---")
        st.caption(T("auto_daily"))
        st.caption("© 2026 Minh Phu Dinh · " + T("footer"))

    # every widget has now been drawn, so a rerun cannot lose their state
    if pending.get("clear_filters"):
        S.clear_filters()
    for key in ("lang", "view"):
        if key in pending:
            st.session_state[key] = pending[key]
    if pending:
        st.rerun()
    return view_key


def _scope_filters(ds, T, pending: dict) -> None:
    """Cascading filters: each one is limited by the ones above it."""
    st.markdown(f"<div class='dock-group'>{T('group_scope')}</div>",
                unsafe_allow_html=True)
    S.prune_stale_filter_values(ds.profile, ds.prices)
    for key, label in (("f_region", "region"), ("f_country", "filter_country"),
                       ("f_class", "asset_class"), ("f_kind", "kind"),
                       ("f_issuer", "issuer")):
        st.multiselect(T(label), S.filter_options(ds.profile, ds.prices, key),
                       key=key, placeholder=T("all"))
    universe = S.filtered_universe(ds.profile, ds.prices)
    st.caption(f"{T('universe_size')}: **{len(universe)}** / {ds.prices.shape[1]}")
    if S.filters_active() and st.button(T("filter_reset"), width="stretch",
                                        key="clear_filters"):
        pending["clear_filters"] = True


def _parameters(ds, T) -> None:
    st.markdown(f"<div class='dock-group'>{T('group_params')}</div>",
                unsafe_allow_html=True)
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


def header(ctx, ds, T, view_key: str) -> None:
    """Title, freshness and the current comparison, on one line each."""
    left, right = st.columns([4, 2])
    with left:
        st.markdown(f"## {T(f'{view_key}')}")
        st.caption(T(f"{view_key}_help"))
    with right:
        text, css = i18n.freshness_label(ctx.lang, ctx.stale_days)
        st.markdown(
            f"<div style='text-align:right'>"
            f"<span class='fresh {css}'>{text}</span><br>"
            f"<span class='selbar'>{T('data_updated')} {ds.last_date:%d.%m.%Y} · "
            f"{ds.prices.shape[1]} {T('selection_count')}</span></div>",
            unsafe_allow_html=True)


def selection_bar(ctx) -> None:
    """What is being compared, and the one control that changes it."""
    T = ctx.t
    with st.container(border=True):
        left, edit, clear = st.columns([5.5, 2, 1.4], vertical_alignment="center")
        with left:
            chips = "".join(
                f"<span class='chip{' chip-key' if t == ctx.benchmark else ''}'>{t}</span>"
                for t in ctx.tickers)
            st.markdown(
                f"<div class='selbar'>{T('selection')} · {len(ctx.tickers)} "
                f"{T('selection_count')}</div>{chips}", unsafe_allow_html=True)
        with edit.popover(T("edit_selection"), width="stretch"):
            options = ctx.universe or list(ctx.ds.prices.columns)
            seed = ({} if S.PICKER_KEY in st.session_state
                    else {"default": [t for t in ctx.tickers if t in options]})
            picked = st.multiselect(T("select_funds"), options, key=S.PICKER_KEY,
                                    format_func=ctx.label, max_selections=20, **seed)
            st.caption(T("filter_note"))
        if picked and list(picked) != list(ctx.tickers):
            st.session_state["selection"] = list(picked)
            st.rerun()
        if clear.button(T("clear_selection"), width="stretch", key="clear_sel"):
            S.set_selection(rp.default_selection(ctx.ds.profile, ctx.universe_prices))
            st.rerun()


def main() -> None:
    ds = load_dataset()
    if ds is None:
        st.title("Global ETF Report")
        st.warning(i18n.t("EN", "no_data"))
        st.stop()

    S.init_state(ds)
    T = lambda key: i18n.t(st.session_state["lang"], key)

    view_key = dock(ds, T)
    if view_key != st.session_state.get("view"):
        st.session_state["view"] = view_key

    # a scope filter is a statement about what the report should show, so the
    # comparison follows it: anything outside the filter drops out, and an empty
    # list is re-seeded from what the filter does allow
    universe = S.filtered_universe(ds.profile, ds.prices)
    if S.filters_active():
        kept = [t for t in st.session_state.get("selection", []) if t in universe]
        if kept != list(st.session_state.get("selection", [])):
            S.set_selection(kept)
    if not st.session_state.get("selection"):
        S.set_selection(rp.default_selection(
            ds.profile, ds.prices[[t for t in universe if t in ds.prices.columns]]
            if universe else ds.prices))

    ctx = S.build_context(ds)
    header(ctx, ds, T, view_key)

    if ctx.window.empty or len(ctx.window.columns) == 0:
        st.warning(T("not_enough_data"))
        st.stop()

    if view_key not in ("nav_screener", "nav_data"):
        selection_bar(ctx)

    dict(SECTIONS)[view_key](ctx)
    S.sync_query_params()


main()
