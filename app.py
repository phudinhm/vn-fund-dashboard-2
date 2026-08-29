# -*- coding: utf-8 -*-
"""
Global ETF & Fund Report — Streamlit front end.

Everything shown here is computed from the automatically updated dataset
(``data/prices.csv`` and friends). The UI is fully trilingual (VI / EN / DE)
and every price is converted into the chosen reporting currency so funds from
different markets can be compared on the same axis.

Run locally:  streamlit run app.py
"""

from __future__ import annotations

import subprocess
import sys

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

import analytics as an
import i18n
import report as rp

# ===========================================================================
# page setup
# ===========================================================================

st.set_page_config(page_title="Global ETF Report", page_icon="🌍",
                   layout="wide", initial_sidebar_state="expanded")

PALETTE = ["#0F766E", "#B45309", "#1D4ED8", "#BE123C", "#4D7C0F", "#7C3AED",
           "#0891B2", "#C2410C", "#4338CA", "#9D174D", "#15803D", "#A16207"]

st.markdown("""
<style>
    .stApp { background-color: #F7F7F4; }
    h1, h2, h3 { color: #14322E; font-weight: 700; }
    div[data-testid="stMetric"] {
        background: #FFFFFF; padding: 14px 16px; border-radius: 10px;
        border: 1px solid #E6E4DC; border-left: 4px solid #0F766E;
    }
    div[data-testid="stMetric"] label { color: #5E5D59 !important; font-size: .85rem; }
    .stTabs [data-baseweb="tab-list"] { gap: 6px; flex-wrap: wrap; }
    .stTabs [data-baseweb="tab"] {
        background: #FFFFFF; border: 1px solid #E6E4DC; border-radius: 8px;
        padding: 10px 18px; font-weight: 600; color: #3F3F3A;
    }
    .stTabs [aria-selected="true"] { background: #0F766E !important; color: #FFF !important; }
    .insight {
        background: #EEF6F4; border-left: 4px solid #0F766E; padding: 12px 16px;
        border-radius: 6px; margin-top: 8px; color: #14322E; font-size: .93rem;
    }
    .commentary {
        background: #FDF6EC; border-left: 4px solid #B45309; padding: 14px 18px;
        border-radius: 6px; color: #4A2E09; font-size: .97rem; line-height: 1.55;
    }
    .insight-title { font-weight: 700; display: block; margin-bottom: 4px; }
</style>
""", unsafe_allow_html=True)

if "lang" not in st.session_state:
    st.session_state["lang"] = "VI"


def T(key: str) -> str:
    return i18n.t(st.session_state["lang"], key)


def insight(text: str) -> None:
    st.markdown(f"<div class='insight'><span class='insight-title'>{T('insight')}</span>"
                f"{text}</div>", unsafe_allow_html=True)


def commentary(text: str) -> None:
    st.markdown(f"<div class='commentary'><b>{T('auto_commentary')}</b><br>{text}</div>",
                unsafe_allow_html=True)


try:  # optional: pandas Styler gradients need matplotlib
    import matplotlib  # noqa: F401
    HAS_MPL = True
except ImportError:
    HAS_MPL = False


def gradient(styler, **kwargs):
    """Apply a background gradient only when matplotlib is available."""
    return styler.background_gradient(**kwargs) if HAS_MPL else styler


def style_fig(fig, title="", x_title="", y_title="", height=None):
    fig.update_layout(
        template="plotly_white",
        colorway=PALETTE,
        title=dict(text=title, font=dict(size=17, color="#14322E")),
        xaxis_title=x_title, yaxis_title=y_title,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0),
        hovermode="x unified", margin=dict(t=60, b=40, l=10, r=10),
    )
    if height:
        fig.update_layout(height=height)
    return fig


# ===========================================================================
# data
# ===========================================================================

@st.cache_data(show_spinner=False)
def load():
    return rp.load_dataset()


ds = load()

# --------------------------------------------------------------- sidebar ---
with st.sidebar:
    cols = st.columns(3)
    for col, code in zip(cols, ["VI", "EN", "DE"]):
        if col.button(f"{i18n.FLAGS[code]} {code}", use_container_width=True):
            st.session_state["lang"] = code
    st.caption(f"{T('language')}: **{i18n.LANGUAGES[st.session_state['lang']]}**")
    st.markdown("---")

if ds is None:
    st.title("🌍 " + T("app_title"))
    st.warning(T("no_data"))
    st.stop()

profile = ds.profile
prices_all = ds.prices

with st.sidebar:
    st.header("⚙️ " + T("settings"))

    if st.button("🔄 " + T("update_btn"), use_container_width=True):
        with st.spinner(T("updating")):
            res = subprocess.run([sys.executable, "update_data.py"],
                                 capture_output=True, text=True)
        if res.returncode == 0:
            st.cache_data.clear()
            st.success(T("update_done"))
        else:
            st.error(f"{T('update_failed')}: {res.stderr[-500:]}")

    st.info(f"📅 {T('data_updated')}: **{ds.last_date:%d.%m.%Y}**")
    st.caption("🤖 " + T("auto_note"))

    st.subheader("🔎 " + T("filters"))
    avail = profile[profile.ticker.isin(prices_all.columns)]

    regions = sorted(avail.region.dropna().unique())
    sel_regions = st.multiselect(T("region"), regions, default=regions)
    kinds = sorted(avail.kind.dropna().unique())
    sel_kinds = st.multiselect(T("kind"), kinds, default=kinds)
    classes = sorted(avail.asset_class.dropna().unique())
    sel_classes = st.multiselect(T("asset_class"), classes, default=classes)

    pool = avail[avail.region.isin(sel_regions)
                 & avail.kind.isin(sel_kinds)
                 & avail.asset_class.isin(sel_classes)]

    issuers = sorted(pool.issuer.dropna().unique())
    sel_issuers = st.multiselect(T("issuer"), issuers, default=[])
    if sel_issuers:
        pool = pool[pool.issuer.isin(sel_issuers)]

    options = pool.ticker.tolist()
    label_map = pool.set_index("ticker")["name"].to_dict()

    preset_map = rp.presets(profile, prices_all)
    preset_labels = {T(k): v for k, v in preset_map.items() if v}
    chosen_preset = st.selectbox(T("quick_pick"), ["—"] + list(preset_labels))
    if chosen_preset != "—":
        st.session_state["selection"] = [t for t in preset_labels[chosen_preset]
                                         if t in options]

    default_sel = st.session_state.get("selection") or rp.default_selection(profile, prices_all)
    default_sel = [t for t in default_sel if t in options][:8]
    selection = st.multiselect(
        T("select_funds"), options, default=default_sel,
        format_func=lambda t: f"{t} · {str(label_map.get(t, ''))[:34]}")
    st.session_state["selection"] = selection

    bench_options = sorted(set(avail[avail.kind == "Index"].ticker) | set(selection))
    default_bench = next((b for b in ["VNINDEX", "SP500"] if b in bench_options),
                         bench_options[0] if bench_options else None)
    benchmark = st.selectbox(T("benchmark"), bench_options,
                             index=bench_options.index(default_bench) if default_bench else 0)

    ccy_options = [c for c in ["USD", "EUR", "VND"] if ds.fx.empty is False and c in ds.fx.columns] \
        or sorted(avail.currency.dropna().unique())
    currency = st.selectbox(T("currency"), ccy_options, help=T("currency_help"))

    period = st.select_slider(T("time_range"), options=rp.RANGES, value="3Y")
    rf = st.slider(T("risk_free"), 0.0, 10.0, 3.0, 0.25) / 100

    st.markdown("---")
    st.caption("© 2026 Minh Phu Dinh · " + T("footer"))

st.title("🌍 " + T("app_title"))
st.caption(T("app_subtitle"))

if not selection:
    st.info(T("no_selection"))
    st.stop()

tickers = list(dict.fromkeys(selection + ([benchmark] if benchmark else [])))
tickers = [t for t in tickers if t in prices_all.columns]

prices = an.convert_prices(prices_all[tickers], profile, ds.fx, currency)
window = rp.slice_window(prices, period)
window = window.dropna(axis=1, how="all")
if window.shape[0] < 5 or window.shape[1] == 0:
    st.warning(T("not_enough_data"))
    st.stop()

returns = an.daily_returns(window)
bench_series = window[benchmark] if benchmark in window.columns else None
bench_ret = an.daily_returns(bench_series) if bench_series is not None else None

metrics = an.metrics_table(window, benchmark=benchmark, rf=rf, profile=profile)
scored = an.composite_score(metrics)
facts = rp.build_facts(window, metrics, benchmark, currency)

missing_fx = an.unconverted_tickers(prices_all[tickers], profile, ds.fx, currency)
if missing_fx and not ds.fx.empty:
    st.warning(f"{T('fx_warning')}: {', '.join(sorted(set(missing_fx)))}")

fmt_pct = lambda v, d=2: "n/a" if pd.isna(v) else f"{v * 100:.{d}f}%"
fmt_num = lambda v, d=2: "n/a" if pd.isna(v) else f"{v:.{d}f}"

tabs = st.tabs([
    "📋 " + T("tab_summary"), "🚀 " + T("tab_performance"), "📉 " + T("tab_risk"),
    "⚖️ " + T("tab_riskreturn"), "🎯 " + T("tab_benchmark"), "🌐 " + T("tab_markets"),
    "🔗 " + T("tab_correlation"), "💰 " + T("tab_costs"), "🔄 " + T("tab_cycles"),
    "🧪 " + T("tab_strategy"), "🔮 " + T("tab_forecast"), "🗂️ " + T("tab_data"),
])

# ===========================================================================
# 1. summary
# ===========================================================================
with tabs[0]:
    if facts:
        commentary(i18n.summary_narrative(st.session_state["lang"], facts))

    st.markdown("### " + T("h_kpi"))
    k = st.columns(5)
    k[0].metric(T("n_instruments"), f"{len(window.columns)}")
    k[1].metric(T("best"), f"{facts.get('best', 'n/a')}",
                fmt_pct(facts.get("best_cagr", np.nan), 1))
    k[2].metric(T("m_sharpe"), f"{facts.get('best_sharpe', 'n/a')}",
                fmt_num(facts.get("best_sharpe_value", np.nan)))
    k[3].metric(T("m_maxdd"), f"{facts.get('deepest_dd', 'n/a')}",
                fmt_pct(facts.get("deepest_dd_value", np.nan), 1))
    k[4].metric(T("h_corr"), fmt_num(facts.get("avg_corr", np.nan)))

    st.markdown("### " + T("h_leaderboard"))
    show = scored.copy()
    board_cols = {
        "rank": T("m_rank"), "name": T("m_name"), "region": T("region"),
        "currency": T("currency"), "cagr": T("m_cagr"), "volatility": T("m_volatility"),
        "max_drawdown": T("m_maxdd"), "sharpe": T("m_sharpe"), "sortino": T("m_sortino"),
        "calmar": T("m_calmar"), "beta": T("m_beta"), "alpha": T("m_alpha"),
        "tracking_error": T("m_te"), "ter": T("m_ter"), "score": T("m_score"),
    }
    have = [c for c in board_cols if c in show.columns]
    board = show[have].rename(columns=board_cols)
    pct_cols = [board_cols[c] for c in ["cagr", "volatility", "max_drawdown", "alpha",
                                        "tracking_error"] if c in have]
    st.dataframe(
        board.style.format({**{c: "{:.2%}" for c in pct_cols},
                            **{board_cols[c]: "{:.2f}" for c in
                               ["sharpe", "sortino", "calmar", "beta", "score", "ter"]
                               if c in have},
                            **({board_cols["rank"]: "{:.0f}"} if "rank" in have else {})},
                           na_rep="n/a"),
        use_container_width=True, height=min(80 + 36 * len(board), 520))

    st.markdown("### " + T("h_growth"))
    growth = an.cumulative_growth(window)
    fig = px.line(growth, height=430)
    st.plotly_chart(style_fig(fig, "", T("x_date"), f"{T('y_value')} ({currency})"),
                    use_container_width=True)

    st.markdown("### " + T("h_export"))
    c1, c2, c3 = st.columns(3)
    c1.download_button("⬇️ " + T("c_download_csv"),
                       scored.to_csv().encode("utf-8"),
                       file_name=f"etf_metrics_{period}_{currency}.csv", mime="text/csv")
    md = rp.markdown_report(st.session_state["lang"], ds, tickers, period,
                            benchmark, currency, rf)
    c2.download_button("⬇️ " + T("c_download_report"), md.encode("utf-8"),
                       file_name=f"etf_report_{st.session_state['lang']}_{period}.md",
                       mime="text/markdown")
    c3.download_button("⬇️ " + T("y_value") + " (CSV)",
                       window.to_csv().encode("utf-8"),
                       file_name=f"prices_{currency}_{period}.csv", mime="text/csv")

# ===========================================================================
# 2. performance
# ===========================================================================
with tabs[1]:
    st.markdown("### " + T("h_growth"))
    growth = an.cumulative_growth(window)
    fig = px.line(growth, height=470)
    fig.update_xaxes(rangeslider_visible=True)
    st.plotly_chart(style_fig(fig, "", T("x_date"), f"{T('y_value')} ({currency})"),
                    use_container_width=True)
    insight(T("x_growth"))

    st.markdown("### " + T("h_period_returns"))
    per = an.period_returns(prices)
    st.dataframe(gradient(per.style.format("{:.2%}", na_rep="n/a"),
                          cmap="RdYlGn", axis=None), use_container_width=True)
    insight(T("x_periods"))

    st.markdown("### " + T("h_calendar"))
    cal = an.calendar_year_returns(prices)
    if not cal.empty:
        cal_long = cal.tail(12).reset_index().melt(id_vars="year", var_name="ticker",
                                                   value_name="ret").dropna()
        cal_long["ret"] *= 100
        fig = px.bar(cal_long, x="year", y="ret", color="ticker", barmode="group",
                     height=420)
        st.plotly_chart(style_fig(fig, "", T("x_date"), T("y_return")),
                        use_container_width=True)

    st.markdown("### " + T("h_rolling"))
    c1, c2 = st.columns([1, 3])
    years = c1.slider(T("c_window_years"), 0.5, 5.0, 1.0, 0.5)
    roll = {}
    for ticker in window.columns:
        r = an.rolling_returns(prices[ticker], years)
        if not r.empty:
            roll[ticker] = r * 100
    if roll:
        fig = px.line(pd.DataFrame(roll), height=400)
        fig.add_hline(y=0, line_dash="dot", line_color="#B45309")
        c2.plotly_chart(style_fig(fig, "", T("x_date"), T("y_cagr")),
                        use_container_width=True)
        stats = pd.DataFrame({tk: an.rolling_return_stats(prices[tk], years)
                              for tk in window.columns}).T
        stats = stats.rename(columns={
            "windows": T("windows"), "mean": T("average"), "median": T("median"),
            "min": T("worst"), "max": T("best"), "win_rate": T("win_rate"),
            "p05": "P05", "p95": "P95"})
        st.dataframe(stats.style.format({
            T("average"): "{:.2%}", T("median"): "{:.2%}", T("worst"): "{:.2%}",
            T("best"): "{:.2%}", "P05": "{:.2%}", "P95": "{:.2%}",
            T("win_rate"): "{:.1f}%", T("windows"): "{:.0f}"}, na_rep="n/a"),
            use_container_width=True)

# ===========================================================================
# 3. risk
# ===========================================================================
with tabs[2]:
    st.markdown("### " + T("h_drawdown"))
    dd = an.drawdown(window) * 100
    fig = go.Figure()
    for i, ticker in enumerate(dd.columns):
        fig.add_trace(go.Scatter(x=dd.index, y=dd[ticker], name=ticker, fill="tozeroy",
                                 line=dict(width=1, color=PALETTE[i % len(PALETTE)]),
                                 opacity=0.55))
    st.plotly_chart(style_fig(fig, "", T("x_date"), T("y_dd"), height=430),
                    use_container_width=True)
    insight(T("x_drawdown"))

    focus = st.selectbox(T("c_pick_one"), list(window.columns), key="dd_focus")
    episodes = an.drawdown_episodes(window[focus], top=5)
    if not episodes.empty:
        current_dd = float(an.drawdown(window[focus].dropna()).iloc[-1])
        commentary(i18n.drawdown_narrative(
            st.session_state["lang"], focus, current_dd,
            float(episodes["depth"].min()), episodes["recovery_days"].iloc[0]))
        st.markdown("#### " + T("h_dd_table"))
        show_ep = episodes.rename(columns={
            "peak": T("m_first"), "trough": T("worst"), "recovery": T("m_last"),
            "depth": T("m_maxdd"), "length_days": T("windows"),
            "recovery_days": T("c_hold_years")})
        st.dataframe(show_ep.style.format({T("m_maxdd"): "{:.2%}"}, na_rep="n/a"),
                     use_container_width=True)

    st.markdown("### " + T("h_riskmetrics"))
    risk_cols = {
        "volatility": T("m_volatility"), "downside_dev": T("m_downside"),
        "max_drawdown": T("m_maxdd"), "var95": T("m_var"), "cvar95": T("m_cvar"),
        "ulcer": T("m_ulcer"), "martin": T("m_martin"), "skew": T("m_skew"),
        "kurtosis": T("m_kurtosis"), "tail_ratio": T("m_tail"),
        "hit_rate": T("m_hit"), "stability": T("m_stability"),
        "best_day": T("m_best_day"), "worst_day": T("m_worst_day"),
    }
    have = [c for c in risk_cols if c in metrics.columns]
    risk_tbl = metrics[have].rename(columns=risk_cols)
    st.dataframe(risk_tbl.style.format({
        **{risk_cols[c]: "{:.2%}" for c in
           ["volatility", "downside_dev", "max_drawdown", "var95", "cvar95",
            "best_day", "worst_day"] if c in have},
        **{risk_cols[c]: "{:.2f}" for c in
           ["ulcer", "martin", "skew", "kurtosis", "tail_ratio", "stability"] if c in have},
        **({risk_cols["hit_rate"]: "{:.1f}%"} if "hit_rate" in have else {})},
        na_rep="n/a"), use_container_width=True)

    st.markdown("#### " + T("m_volatility"))
    vol = pd.DataFrame({tk: an.rolling_volatility(returns[tk]) for tk in window.columns})
    st.plotly_chart(style_fig(px.line(vol.dropna(how="all"), height=360), "",
                              T("x_date"), T("x_vol")), use_container_width=True)

# ===========================================================================
# 4. risk-return
# ===========================================================================
with tabs[3]:
    st.markdown("### " + T("h_scatter"))
    scat = metrics.reset_index()
    scat["vol_pct"] = scat["volatility"] * 100
    scat["cagr_pct"] = scat["cagr"] * 100
    scat["size"] = scat["sharpe"].fillna(0).clip(lower=0.1) * 10 + 8
    fig = px.scatter(scat, x="vol_pct", y="cagr_pct", text="ticker", size="size",
                     color="region" if "region" in scat.columns else None,
                     hover_data=["name"] if "name" in scat.columns else None, height=520)
    fig.update_traces(textposition="top center")
    if benchmark in metrics.index:
        fig.add_hline(y=float(metrics.loc[benchmark, "cagr"]) * 100,
                      line_dash="dot", line_color="#B45309")
        fig.add_vline(x=float(metrics.loc[benchmark, "volatility"]) * 100,
                      line_dash="dot", line_color="#B45309")
    fig.update_layout(hovermode="closest")
    st.plotly_chart(style_fig(fig, "", T("x_vol"), T("y_cagr")), use_container_width=True)
    insight(T("x_riskreturn"))

    c1, c2 = st.columns(2)
    with c1:
        st.markdown("#### " + T("h_leaderboard"))
        rank_cols = {"cagr": T("m_cagr"), "sharpe": T("m_sharpe"),
                     "sortino": T("m_sortino"), "calmar": T("m_calmar"),
                     "omega": T("m_omega"), "score": T("m_score")}
        have = [c for c in rank_cols if c in scored.columns]
        rank_styler = scored[have].rename(columns=rank_cols).style.format(
            {**{rank_cols["cagr"]: "{:.2%}"},
             **{rank_cols[c]: "{:.2f}" for c in have if c != "cagr"}}, na_rep="n/a")
        if "score" in have:
            rank_styler = gradient(rank_styler, cmap="Greens",
                                   subset=[rank_cols["score"]])
        st.dataframe(rank_styler, use_container_width=True)
    with c2:
        st.markdown("#### " + T("h_frontier"))
        frontier = an.efficient_frontier(window.drop(columns=[benchmark], errors="ignore"),
                                         simulations=2500, rf=rf)
        if frontier.empty:
            st.info(T("not_enough_data"))
        else:
            fig = px.scatter(frontier, x="volatility", y="return", color="sharpe",
                             color_continuous_scale="Viridis", height=420, opacity=0.55)
            fig.add_trace(go.Scatter(
                x=metrics["volatility"], y=metrics["cagr"], mode="markers+text",
                text=metrics.index, textposition="top center", name="Funds",
                marker=dict(size=11, color="#BE123C", symbol="diamond")))
            fig.update_layout(hovermode="closest")
            st.plotly_chart(style_fig(fig, "", T("x_vol"), T("y_cagr")),
                            use_container_width=True)

# ===========================================================================
# 5. benchmark
# ===========================================================================
with tabs[4]:
    if bench_ret is None:
        st.info(T("not_enough_data"))
    else:
        st.markdown(f"### {T('h_alpha')} — {benchmark}")
        rel_cols = {"beta": T("m_beta"), "alpha": T("m_alpha"), "r_squared": T("m_r2"),
                    "tracking_error": T("m_te"), "information_ratio": T("m_ir"),
                    "up_capture": T("m_up"), "down_capture": T("m_down"),
                    "capture_spread": T("m_capture_spread"),
                    "batting_average": T("m_batting")}
        have = [c for c in rel_cols if c in metrics.columns]
        rel = metrics.loc[[t for t in metrics.index if t != benchmark], have]
        st.dataframe(rel.rename(columns=rel_cols).style.format({
            **{rel_cols[c]: "{:.2%}" for c in ["alpha", "tracking_error"] if c in have},
            **{rel_cols[c]: "{:.2f}" for c in ["beta", "r_squared", "information_ratio"]
               if c in have},
            **{rel_cols[c]: "{:.1f}%" for c in
               ["up_capture", "down_capture", "capture_spread", "batting_average"]
               if c in have}}, na_rep="n/a"), use_container_width=True)

        if not rel.empty:
            focus_b = st.selectbox(T("c_pick_one"), list(rel.index), key="bench_focus")
            row = metrics.loc[focus_b]
            commentary(i18n.tracking_narrative(
                st.session_state["lang"], focus_b, row.get("tracking_error", np.nan),
                row.get("information_ratio", np.nan), row.get("beta", np.nan),
                row.get("alpha", np.nan), benchmark))

        c1, c2 = st.columns(2)
        with c1:
            st.markdown("#### " + T("h_te"))
            te = pd.DataFrame({
                tk: an.rolling_tracking_error(returns[tk], bench_ret)
                for tk in window.columns if tk != benchmark}).dropna(how="all")
            if not te.empty:
                st.plotly_chart(style_fig(px.line(te, height=380), "", T("x_date"),
                                          T("y_te")), use_container_width=True)
        with c2:
            st.markdown("#### " + T("m_beta"))
            rb = pd.DataFrame({
                tk: an.rolling_beta(returns[tk], bench_ret)
                for tk in window.columns if tk != benchmark}).dropna(how="all")
            if not rb.empty:
                fig = px.line(rb, height=380)
                fig.add_hline(y=1.0, line_dash="dot", line_color="#B45309")
                st.plotly_chart(style_fig(fig, "", T("x_date"), T("m_beta")),
                                use_container_width=True)

        st.markdown("#### " + T("h_capture"))
        cap = metrics.loc[[t for t in metrics.index if t != benchmark],
                          ["up_capture", "down_capture"]].dropna(how="all")
        if not cap.empty:
            fig = go.Figure()
            fig.add_trace(go.Bar(x=cap.index, y=cap["up_capture"], name=T("m_up"),
                                 marker_color="#0F766E"))
            fig.add_trace(go.Bar(x=cap.index, y=cap["down_capture"], name=T("m_down"),
                                 marker_color="#BE123C"))
            fig.add_hline(y=100, line_dash="dot", line_color="#5E5D59")
            fig.update_layout(barmode="group", hovermode="closest")
            st.plotly_chart(style_fig(fig, "", "", "%", height=380),
                            use_container_width=True)
        insight(T("x_benchmark"))

# ===========================================================================
# 6. global markets
# ===========================================================================
with tabs[5]:
    st.markdown("### " + T("h_region"))
    scope = st.radio(T("scope"), [T("select_funds"), T("h_universe")],
                     horizontal=True, key="market_scope")
    if scope == T("h_universe"):
        wide = an.convert_prices(prices_all, profile, ds.fx, currency)
        wide_window = rp.slice_window(wide, period)
    else:
        wide_window = window
    perf = rp.region_performance(wide_window, profile)

    if perf.empty:
        st.info(T("not_enough_data"))
    else:
        by_region = perf.groupby("region").agg(
            cagr=("cagr", "mean"), volatility=("volatility", "mean"),
            max_drawdown=("max_drawdown", "mean"), n=("ticker", "count")
        ).sort_values("cagr", ascending=False)
        best_r, worst_r = by_region.index[0], by_region.index[-1]
        commentary(i18n.market_narrative(
            st.session_state["lang"], best_r, float(by_region.cagr.iloc[0]),
            worst_r, float(by_region.cagr.iloc[-1]), currency))

        c1, c2 = st.columns([3, 2])
        with c1:
            fig = px.bar(by_region.reset_index(), x="region", y="cagr", color="region",
                         height=400)
            fig.update_layout(hovermode="closest")
            st.plotly_chart(style_fig(fig, "", T("region"), T("y_cagr")),
                            use_container_width=True)
        with c2:
            st.dataframe(by_region.rename(columns={
                "cagr": T("m_cagr"), "volatility": T("m_volatility"),
                "max_drawdown": T("m_maxdd"), "n": T("n_funds")}).style.format({
                    T("m_cagr"): "{:.2%}", T("m_volatility"): "{:.2%}",
                    T("m_maxdd"): "{:.2%}", T("n_funds"): "{:.0f}"}, na_rep="n/a"),
                use_container_width=True)

        st.markdown("### " + T("h_market_matrix"))
        by_country = perf.groupby("country").agg(
            cagr=("cagr", "mean"), volatility=("volatility", "mean"),
            max_drawdown=("max_drawdown", "mean"), n=("ticker", "count")
        ).sort_values("cagr", ascending=False)
        fig = px.scatter(by_country.reset_index(), x="volatility", y="cagr",
                         text="country", size="n", color="cagr",
                         color_continuous_scale="RdYlGn", height=480)
        fig.update_traces(textposition="top center")
        fig.update_layout(hovermode="closest")
        st.plotly_chart(style_fig(fig, "", T("x_vol"), T("y_cagr")),
                        use_container_width=True)

        st.markdown("### " + T("h_currency_effect"))
        if ds.fx.empty:
            st.info(T("not_enough_data"))
        else:
            local = rp.slice_window(prices_all[tickers], period)
            conv = window
            eff = []
            for tk in conv.columns:
                if tk not in local.columns:
                    continue
                l, c = local[tk].dropna(), conv[tk].dropna()
                if len(l) < 30 or len(c) < 30:
                    continue
                eff.append({"ticker": tk, "local": an.cagr(l), currency: an.cagr(c)})
            if eff:
                eff_df = pd.DataFrame(eff).set_index("ticker")
                eff_df["fx_effect"] = eff_df[currency] - eff_df["local"]
                fig = go.Figure()
                fig.add_trace(go.Bar(x=eff_df.index, y=eff_df["local"] * 100,
                                     name=T("currency") + " (local)", marker_color="#5E5D59"))
                fig.add_trace(go.Bar(x=eff_df.index, y=eff_df[currency] * 100,
                                     name=currency, marker_color="#0F766E"))
                fig.update_layout(barmode="group", hovermode="closest")
                st.plotly_chart(style_fig(fig, "", "", T("y_cagr"), height=380),
                                use_container_width=True)
        insight(T("x_markets"))

# ===========================================================================
# 7. correlation
# ===========================================================================
with tabs[6]:
    st.markdown("### " + T("h_corr"))
    corr = an.correlation_matrix(window)
    fig = px.imshow(corr, text_auto=".2f", color_continuous_scale="RdBu_r",
                    zmin=-1, zmax=1, height=max(420, 42 * len(corr)))
    fig.update_layout(hovermode="closest")
    st.plotly_chart(style_fig(fig), use_container_width=True)
    st.metric(T("h_corr"), fmt_num(an.diversification_score(corr)))
    insight(T("x_correlation"))

    if bench_ret is not None:
        st.markdown("### " + T("h_corr_rolling"))
        rc = pd.DataFrame({tk: an.rolling_correlation(returns[tk], bench_ret)
                           for tk in window.columns if tk != benchmark}).dropna(how="all")
        if not rc.empty:
            st.plotly_chart(style_fig(px.line(rc, height=380), "", T("x_date"),
                                      T("h_corr")), use_container_width=True)

# ===========================================================================
# 8. costs & structure
# ===========================================================================
with tabs[7]:
    st.markdown("### " + T("h_ter_vs_perf"))
    if "ter" in metrics.columns and metrics["ter"].notna().any():
        cost = metrics.reset_index().dropna(subset=["ter"])
        fig = px.scatter(cost, x="ter", y="cagr", text="ticker",
                         color="issuer" if "issuer" in cost.columns else None,
                         size=[12] * len(cost), height=430)
        fig.update_traces(textposition="top center")
        fig.update_layout(hovermode="closest")
        st.plotly_chart(style_fig(fig, "", T("m_ter") + " (%)", T("y_cagr")),
                        use_container_width=True)

    st.markdown("### " + T("h_fees"))
    c1, c2, c3, c4 = st.columns(4)
    fee_fund = c1.selectbox(T("c_pick_one"), list(window.columns), key="fee_fund")
    ter_default = float(metrics.loc[fee_fund, "ter"]) if (
        "ter" in metrics.columns and fee_fund in metrics.index
        and pd.notna(metrics.loc[fee_fund, "ter"])) else 0.5
    ter = c2.number_input(T("m_ter") + " (%)", 0.0, 5.0, ter_default, 0.05) / 100
    gross = c3.number_input(T("c_gross_return"), 0.0, 30.0, 10.0, 0.5) / 100
    years = c4.slider(T("c_years"), 5, 40, 20)
    ero = an.fee_erosion(100.0, gross, ter, years)
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=ero.year, y=ero.gross, name=T("gross"),
                             line=dict(color="#0F766E")))
    fig.add_trace(go.Scatter(x=ero.year, y=ero.net, name=T("net"),
                             line=dict(color="#B45309"), fill="tonexty",
                             fillcolor="rgba(180,83,9,.15)"))
    st.plotly_chart(style_fig(fig, "", T("c_years"), T("y_value"), height=380),
                    use_container_width=True)
    lost_pct = float(ero.lost.iloc[-1] / ero.gross.iloc[-1]) if ero.gross.iloc[-1] else np.nan
    commentary(i18n.cost_narrative(st.session_state["lang"], fee_fund, ter * 100,
                                   lost_pct, years))

    st.markdown("### " + T("h_liquidity"))
    if not ds.volume.empty:
        vcols = [c for c in window.columns if c in ds.volume.columns]
        if vcols:
            vol_window = ds.volume.loc[window.index.min():window.index.max(), vcols]
            avg_vol = (vol_window.mean().sort_values(ascending=False)
                       .rename("volume").rename_axis("ticker").reset_index())
            fig = px.bar(avg_vol, x="ticker", y="volume", height=360)
            fig.update_layout(hovermode="closest")
            st.plotly_chart(style_fig(fig, "", "", T("y_volume")), use_container_width=True)
    insight(T("x_costs"))

# ===========================================================================
# 9. cycles & seasonality
# ===========================================================================
with tabs[8]:
    if bench_ret is not None:
        st.markdown("### " + T("h_bullbear"))
        bb = []
        for tk in window.columns:
            if tk == benchmark:
                continue
            split = an.bull_bear_split(returns[tk], bench_ret)
            bb.append({"ticker": tk, "bull": split["bull"], "bear": split["bear"]})
        if bb:
            bb_df = pd.DataFrame(bb).set_index("ticker")
            fig = go.Figure()
            fig.add_trace(go.Bar(x=bb_df.index, y=bb_df["bull"] * 100, name=T("bull"),
                                 marker_color="#0F766E"))
            fig.add_trace(go.Bar(x=bb_df.index, y=bb_df["bear"] * 100, name=T("bear"),
                                 marker_color="#BE123C"))
            fig.update_layout(barmode="group", hovermode="closest")
            st.plotly_chart(style_fig(fig, f"vs {benchmark}", "", T("y_return"), height=400),
                            use_container_width=True)

    st.markdown("### " + T("h_monthly"))
    m_fund = st.selectbox(T("c_pick_one"), list(window.columns), key="month_fund")
    heat = an.monthly_returns(prices[m_fund])
    if not heat.empty:
        fig = px.imshow(heat, text_auto=".1f", color_continuous_scale="RdYlGn",
                        aspect="auto", height=max(320, 30 * len(heat)),
                        labels=dict(color="%"))
        fig.update_layout(hovermode="closest")
        st.plotly_chart(style_fig(fig, m_fund), use_container_width=True)

        st.markdown("#### " + T("h_seasonality"))
        season = heat.mean().reset_index()
        season.columns = ["month", "avg"]
        fig = px.bar(season, x="month", y="avg", height=320,
                     color="avg", color_continuous_scale="RdYlGn")
        fig.update_layout(hovermode="closest")
        st.plotly_chart(style_fig(fig, "", "", T("y_return")), use_container_width=True)
    insight(T("x_cycles"))

# ===========================================================================
# 10. strategy lab
# ===========================================================================
with tabs[9]:
    st.markdown("### " + T("h_dca"))
    c1, c2, c3 = st.columns(3)
    dca_fund = c1.selectbox(T("c_pick_one"), list(window.columns), key="dca_fund")
    amount = c2.number_input(T("c_contribution"), 100.0, 1e9, 1000.0, 100.0)
    freq_label = c3.selectbox(T("c_frequency"), [T("c_monthly"), T("c_weekly")])
    freq = "ME" if freq_label == T("c_monthly") else "W"

    dca = an.simulate_dca(window[dca_fund], amount, freq)
    if not dca.empty:
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=dca.index, y=dca["invested"], name=T("invested"),
                                 line=dict(color="#5E5D59", dash="dash")))
        fig.add_trace(go.Scatter(x=dca.index, y=dca["value"], name=T("value"),
                                 line=dict(color="#0F766E")))
        st.plotly_chart(style_fig(fig, dca_fund, T("x_date"), f"{T('y_value')} ({currency})",
                                  height=400), use_container_width=True)
        m = st.columns(3)
        m[0].metric(T("invested"), f"{dca['invested'].iloc[-1]:,.0f}")
        m[1].metric(T("value"), f"{dca['value'].iloc[-1]:,.0f}")
        m[2].metric(T("profit"), f"{dca['profit'].iloc[-1]:,.0f}",
                    f"{dca['return'].iloc[-1] * 100:.1f}%")

    st.markdown("### " + T("h_lsdca"))
    c1, c2 = st.columns(2)
    hold = c1.slider(T("c_hold_years"), 1, 15, 5)
    spread = c2.slider(T("c_spread_months"), 3, 36, 12)
    ls = an.rolling_dca_vs_lumpsum(prices[dca_fund], hold, spread)
    if ls.get("windows"):
        commentary(i18n.strategy_narrative(
            st.session_state["lang"], ls["lump_sum_win_rate"], ls["median_lump"],
            ls["median_dca"], hold))
        m = st.columns(4)
        m[0].metric(T("windows"), f"{ls['windows']}")
        m[1].metric(T("win_rate") + " · " + T("lump_sum"), f"{ls['lump_sum_win_rate']:.1f}%")
        m[2].metric(T("median") + " · " + T("lump_sum"), fmt_pct(ls["median_lump"], 1))
        m[3].metric(T("median") + " · " + T("dca"), fmt_pct(ls["median_dca"], 1))
    else:
        st.info(T("not_enough_data"))

    st.markdown("### " + T("h_portfolio"))
    port_tickers = [t for t in window.columns if t != benchmark]
    if len(port_tickers) >= 2:
        weights, cols = {}, st.columns(min(len(port_tickers), 6))
        for i, tk in enumerate(port_tickers):
            weights[tk] = cols[i % len(cols)].number_input(
                tk, 0.0, 100.0, round(100 / len(port_tickers), 1), 5.0, key=f"w_{tk}")
        rb_label = st.radio(T("c_rebalance"), [T("c_quarterly"), T("c_annually")],
                            horizontal=True)
        rb_freq = "QE" if rb_label == T("c_quarterly") else "YE"
        if sum(weights.values()) > 0:
            curve = an.rebalanced_portfolio(window, weights, rb_freq)
            if not curve.empty:
                compare = pd.DataFrame({T("h_portfolio"): curve})
                if benchmark in window.columns:
                    compare[benchmark] = an.cumulative_growth(window[[benchmark]])[benchmark]
                st.plotly_chart(style_fig(px.line(compare.dropna(), height=400), "",
                                          T("x_date"), T("y_value")),
                                use_container_width=True)
                p_ret = an.daily_returns(curve)
                m = st.columns(4)
                m[0].metric(T("m_cagr"), fmt_pct(an.cagr(curve), 1))
                m[1].metric(T("m_volatility"), fmt_pct(an.annual_volatility(p_ret), 1))
                m[2].metric(T("m_maxdd"), fmt_pct(an.max_drawdown(curve), 1))
                m[3].metric(T("m_sharpe"), fmt_num(an.sharpe(curve, rf)))
    insight(T("x_strategy"))

# ===========================================================================
# 11. forecast
# ===========================================================================
with tabs[10]:
    c1, c2 = st.columns([1, 1])
    f_fund = c1.selectbox(T("c_pick_one"), list(window.columns), key="fc_fund")
    horizon = c2.slider(T("c_horizon"), 10, 180, 60, 10)
    series = prices[f_fund].dropna()

    left, right = st.columns([3, 2])
    with left:
        st.markdown("### " + T("h_forecast"))
        fc = an.ets_forecast(series, horizon)
        if fc.empty:
            st.info(T("not_enough_data"))
        else:
            hist = series.iloc[-min(len(series), 250):]
            vol = float(an.daily_returns(series).std() * np.sqrt(horizon))
            upper, lower = fc * (1 + vol), fc * (1 - vol)
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=hist.index, y=hist, name=T("y_value"),
                                     line=dict(color="#14322E")))
            fig.add_trace(go.Scatter(x=fc.index, y=fc, name="ETS",
                                     line=dict(color="#0F766E", dash="dash")))
            fig.add_trace(go.Scatter(
                x=list(fc.index) + list(fc.index[::-1]),
                y=list(upper) + list(lower[::-1]), fill="toself",
                fillcolor="rgba(15,118,110,.18)", line=dict(color="rgba(0,0,0,0)"),
                name="90%"))
            st.plotly_chart(style_fig(fig, f_fund, T("x_date"),
                                      f"{T('y_value')} ({currency})", height=430),
                            use_container_width=True)
    with right:
        st.markdown("### " + T("h_montecarlo"))
        mc = an.monte_carlo(series, days=horizon)
        if not mc:
            st.info(T("not_enough_data"))
        else:
            st.metric(T("prob_up"), f"{mc['prob_up']:.1f}%", f"{mc['prob_up'] - 50:+.1f}")
            st.write(f"**{T('median')}:** {mc['median']:,.2f}")
            st.write(f"**{T('worst')} (P05):** :red[{mc['p05']:,.2f}]")
            st.write(f"**{T('best')} (P95):** :green[{mc['p95']:,.2f}]")
            paths = mc["paths"]
            fig = go.Figure()
            for i in range(min(60, paths.shape[1])):
                fig.add_trace(go.Scatter(y=paths[:, i], line=dict(color="#9CA3AF", width=.5),
                                         opacity=.35, showlegend=False))
            fig.add_trace(go.Scatter(y=np.median(paths, axis=1),
                                     line=dict(color="#BE123C", width=2), name=T("median")))
            fig.update_layout(template="plotly_white", height=280,
                              margin=dict(l=0, r=0, t=10, b=0),
                              xaxis=dict(visible=False), yaxis=dict(visible=False))
            st.plotly_chart(fig, use_container_width=True)
            commentary(i18n.forecast_narrative(
                st.session_state["lang"], f_fund, mc["prob_up"], mc["expected_return"],
                mc["p05"], mc["p95"], horizon))
    insight(T("x_forecast"))

# ===========================================================================
# 12. data & method
# ===========================================================================
with tabs[11]:
    st.markdown("### " + T("h_quality"))
    stale = ds.status.get("stale", []) if ds.status else []
    commentary(i18n.quality_narrative(
        st.session_state["lang"], int(prices_all.shape[1]), ds.markets, ds.currencies,
        f"{ds.last_date:%d.%m.%Y}", len(stale)))

    m = st.columns(4)
    m[0].metric(T("n_instruments"), f"{prices_all.shape[1]}")
    m[1].metric(T("n_markets"), f"{ds.markets}")
    m[2].metric(T("n_currencies"), f"{ds.currencies}")
    m[3].metric(T("data_updated"), f"{ds.last_date:%d.%m.%Y}")

    if stale:
        st.warning(T("stale_warning"))
        st.dataframe(pd.DataFrame(stale), use_container_width=True)

    st.markdown("### " + T("h_universe"))
    uni_view = profile[profile.ticker.isin(prices_all.columns)][
        [c for c in ["ticker", "name", "kind", "asset_class", "region", "country",
                     "currency", "issuer", "ter", "benchmark", "category",
                     "first_date", "last_date", "observations"]
         if c in profile.columns]]
    search = st.text_input("🔎 " + T("search_ticker"), "")
    if search:
        mask = uni_view.apply(lambda r: search.lower() in " ".join(
            str(v).lower() for v in r.values), axis=1)
        uni_view = uni_view[mask]
    st.dataframe(uni_view, use_container_width=True, height=440)

    st.markdown("### " + T("h_method"))
    insight(T("x_data"))
    if ds.status:
        with st.expander("status.json"):
            st.json(ds.status)
    if ds.legacy:
        st.info(T("no_data"))
