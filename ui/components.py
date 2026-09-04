# -*- coding: utf-8 -*-
"""Reusable building blocks shared by the views."""

from __future__ import annotations

import re

import numpy as np
import pandas as pd
import streamlit as st

import analytics as an
from ui import state as S
from ui.theme import BENCH, GAIN, LOSS, style_fig

# --------------------------------------------------------------------------
# formatting
# --------------------------------------------------------------------------

def pct(value, digits: int = 2) -> str:
    return "—" if value is None or pd.isna(value) else f"{value * 100:.{digits}f}%"


def num(value, digits: int = 2) -> str:
    return "—" if value is None or pd.isna(value) else f"{value:.{digits}f}"


# --------------------------------------------------------------------------
# narrative boxes
# --------------------------------------------------------------------------

def _md_bold(text: str) -> str:
    """The narratives are written in Markdown; the boxes are raw HTML."""
    return re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)


def commentary(ctx, text: str) -> None:
    """The headline narrative for a section."""
    st.markdown(
        f"<div class='commentary'><span class='lead'>{ctx.t('auto_commentary')}</span>"
        f"{_md_bold(text)}</div>", unsafe_allow_html=True)


def readout(ctx, text: str) -> None:
    """A quiet line under a chart saying what it actually shows."""
    st.markdown(f"<div class='readout'>{_md_bold(text)}</div>", unsafe_allow_html=True)


def explain(ctx, key: str) -> None:
    """Static teaching text, folded away so it never competes with the data."""
    with st.popover(ctx.t("insight"), width="content"):
        st.markdown(ctx.t(key))


def card(title: str = "", subtitle: str = ""):
    """A bento tile: white surface, hairline border, optional heading."""
    box = st.container(border=True)
    if title:
        box.markdown(f"##### {title}")
    if subtitle:
        box.caption(subtitle)
    return box


# --------------------------------------------------------------------------
# metric tables with in-cell visuals
# --------------------------------------------------------------------------

METRIC_FORMAT = {
    "cagr": ("pct", "m_cagr"), "total_return": ("pct", "m_total_return"),
    "volatility": ("pct", "m_volatility"), "downside_dev": ("pct", "m_downside"),
    "max_drawdown": ("pct", "m_maxdd"), "alpha": ("pct", "m_alpha"),
    "tracking_error": ("pct", "m_te"), "var95": ("pct", "m_var"),
    "cvar95": ("pct", "m_cvar"), "best_day": ("pct", "m_best_day"),
    "worst_day": ("pct", "m_worst_day"), "sharpe": ("num", "m_sharpe"),
    "sortino": ("num", "m_sortino"), "calmar": ("num", "m_calmar"),
    "omega": ("num", "m_omega"), "ulcer": ("num", "m_ulcer"),
    "martin": ("num", "m_martin"), "stability": ("num", "m_stability"),
    "skew": ("num", "m_skew"), "kurtosis": ("num", "m_kurtosis"),
    "tail_ratio": ("num", "m_tail"), "beta": ("num", "m_beta"),
    "r_squared": ("num", "m_r2"), "information_ratio": ("num", "m_ir"),
    "score": ("num", "m_score"), "ter": ("fee", "m_ter"),
    "hit_rate": ("pct100", "m_hit"), "up_capture": ("pct100", "m_up"),
    "down_capture": ("pct100", "m_down"), "capture_spread": ("pct100", "m_capture_spread"),
    "batting_average": ("pct100", "m_batting"), "rank": ("int", "m_rank"),
    "observations": ("int", "m_obs"),
    "tracking_difference": ("pct", "m_td"), "time_under_water": ("int", "m_tuw"),
    "adv": ("money", "m_adv"), "coverage": ("pct100x", "m_coverage"),
}


def metric_columns(ctx, columns: list[str]) -> dict:
    """``column_config`` for a metric frame, in the current language."""
    cfg = {}
    for col in columns:
        kind, label_key = METRIC_FORMAT.get(col, (None, None))
        label = ctx.t(label_key) if label_key else col
        if kind == "pct":
            cfg[col] = st.column_config.NumberColumn(label, format="percent", width="small")
        elif kind == "pct100":
            cfg[col] = st.column_config.NumberColumn(label, format="%.1f%%", width="small")
        elif kind == "pct100x":
            cfg[col] = st.column_config.ProgressColumn(label, format="percent",
                                                       min_value=0.0, max_value=1.0,
                                                       width="small")
        elif kind == "fee":
            cfg[col] = st.column_config.NumberColumn(label, format="%.2f%%", width="small")
        elif kind == "num":
            cfg[col] = st.column_config.NumberColumn(label, format="%.2f", width="small")
        elif kind == "int":
            cfg[col] = st.column_config.NumberColumn(label, format="%d", width="small")
        elif kind == "money":
            cfg[col] = st.column_config.NumberColumn(label, format="compact",
                                                     width="small")
    return cfg


def sparkline_series(prices: pd.DataFrame, tickers: list[str],
                     points: int = 52) -> dict[str, list[float]]:
    """Weekly rebased path of the last year, for LineChartColumn cells."""
    out = {}
    for ticker in tickers:
        s = prices[ticker].dropna() if ticker in prices.columns else pd.Series(dtype=float)
        if s.empty:
            out[ticker] = []
            continue
        s = s.iloc[-min(len(s), 252):]
        weekly = s.resample("W").last().dropna()
        weekly = weekly.iloc[-points:]
        base = weekly.iloc[0] if len(weekly) and weekly.iloc[0] else np.nan
        out[ticker] = list((weekly / base * 100).round(2)) if base else []
    return out


def column_choice(ctx, key: str, essential: list[str], full: list[str]) -> list[str]:
    """Let the reader trade width for detail instead of scrolling by default."""
    choice = st.segmented_control(
        ctx.t("columns"), [ctx.t("cols_essential"), ctx.t("cols_full")],
        default=ctx.t("cols_essential"), key=key, label_visibility="collapsed")
    return full if choice == ctx.t("cols_full") else essential


def leaderboard(ctx, scored: pd.DataFrame, prices: pd.DataFrame,
                columns: list[str], key: str, height: int | None = None,
                selectable: bool = True):
    """Ranking table with a sparkline column and optional row selection."""
    if scored.empty:
        st.info(ctx.t("not_enough_data"))
        return []

    frame = scored.copy()
    frame.insert(0, "spark", pd.Series(sparkline_series(prices, list(frame.index)),
                                       index=frame.index))
    keep = ["spark"] + [c for c in columns if c in frame.columns]
    frame = frame[keep].copy()
    # a metric column that arrived as object dtype renders its gaps as the word
    # "None"; numeric dtype renders them as an empty cell, which is the truth
    for col in keep:
        if col in METRIC_FORMAT and frame[col].dtype == object:
            frame[col] = pd.to_numeric(frame[col], errors="coerce")

    cfg = metric_columns(ctx, keep)
    cfg["spark"] = st.column_config.LineChartColumn(ctx.t("sparkline"), width="small")
    if "name" in keep:
        cfg["name"] = st.column_config.TextColumn(ctx.t("m_name"), width="medium")
    for col, label in (("region", "region"), ("currency", "ccy"),
                       ("country", "market"), ("issuer", "issuer"),
                       ("category", "category"), ("kind", "kind")):
        if col in keep:
            cfg[col] = st.column_config.TextColumn(ctx.t(label), width="small")
    if "score" in keep:
        lo, hi = float(frame["score"].min()), float(frame["score"].max())
        cfg["score"] = st.column_config.ProgressColumn(
            ctx.t("m_score"), format="%.2f",
            min_value=lo - 0.01, max_value=hi + 0.01, width="small")

    event = st.dataframe(
        frame, column_config=cfg, width="stretch", height=height,
        key=key, on_select="rerun" if selectable else "ignore",
        selection_mode="multi-row" if selectable else None)
    if not selectable:
        return []
    rows = event.selection.rows if hasattr(event, "selection") else []
    return [frame.index[i] for i in rows if i < len(frame.index)]


# --------------------------------------------------------------------------
# charts
# --------------------------------------------------------------------------

def growth_facts(ctx):
    """Total growth per instrument over the window, comparable rows only.

    A fund that only existed for the last two months of the window would
    otherwise be read as if its short run were a full-window result.
    """
    keep = set(an.comparable(ctx.metrics).index) if not ctx.metrics.empty else set()
    growth = an.cumulative_growth(ctx.window.ffill())
    if growth.empty:
        return None
    final = (growth.iloc[-1] / 100 - 1).dropna()
    if keep:
        final = final[[t for t in final.index if t in keep]]
    if len(final) < 2 or ctx.benchmark not in final.index:
        return None
    return final


def growth_chart(ctx, window: pd.DataFrame, log_scale: bool = False,
                 relative: bool = False, height: int = 440):
    """Wealth curves, optionally shown relative to the benchmark."""
    import plotly.express as px

    # markets keep different holidays, so the union index has gaps that would
    # break every line into dashes; carrying the last price forward only affects
    # how the curve is drawn, never how the metrics are computed
    growth = an.cumulative_growth(window.ffill())
    if relative and ctx.benchmark in growth.columns:
        base = growth[ctx.benchmark]
        growth = growth.div(base, axis=0) * 100
        growth = growth.drop(columns=[ctx.benchmark])
        y_title = f"{ctx.t('y_value')} / {ctx.benchmark} × 100"
    else:
        y_title = f"{ctx.t('y_value')} ({ctx.currency})"
    if growth.empty:
        st.info(ctx.t("not_enough_data"))
        return

    fig = px.line(growth, height=height)
    for trace in fig.data:
        if trace.name == ctx.benchmark:
            trace.line.color = BENCH
            trace.line.dash = "dot"
            trace.line.width = 2
    if relative:
        fig.add_hline(y=100, line_dash="dot", line_color=BENCH)
    fig.update_xaxes(rangeslider_visible=True)
    st.plotly_chart(style_fig(fig, "", ctx.t("x_date"), y_title, log_y=log_scale),
                    width="stretch")


def chart_options(ctx, key: str, allow_relative: bool = True) -> dict:
    """Compact toggle row that every performance chart honours."""
    cols = st.columns([1, 1, 2])
    log_scale = cols[0].toggle(ctx.t("opt_log"), key=f"{key}_log")
    relative = False
    if allow_relative and ctx.benchmark in ctx.window.columns:
        relative = cols[1].toggle(ctx.t("opt_relative"), key=f"{key}_rel")
    return {"log": log_scale, "relative": relative}


def scatter_picker(ctx, frame: pd.DataFrame, x: str, y: str, key: str,
                   x_title: str, y_title: str, color: str | None = None,
                   height: int = 520):
    """Risk/return style scatter where clicking a point focuses that fund."""
    import plotly.express as px

    data = frame.reset_index().rename(columns={"index": "ticker"})
    if "ticker" not in data.columns:
        data = data.rename(columns={data.columns[0]: "ticker"})
    hover = [c for c in ["name", "region", "currency", "ter"] if c in data.columns]
    fig = px.scatter(data, x=x, y=y, text="ticker", height=height,
                     color=color if color in data.columns else None,
                     hover_data=hover, custom_data=["ticker"])
    fig.update_traces(textposition="top center", marker=dict(size=13, opacity=.85))
    if ctx.benchmark in frame.index:
        fig.add_hline(y=float(frame.loc[ctx.benchmark, y]), line_dash="dot",
                      line_color=BENCH)
        fig.add_vline(x=float(frame.loc[ctx.benchmark, x]), line_dash="dot",
                      line_color=BENCH)
    event = st.plotly_chart(
        style_fig(fig, "", x_title, y_title, hover="closest"),
        width="stretch", key=key, on_select="rerun", selection_mode="points")

    points = getattr(getattr(event, "selection", None), "points", []) or []
    if points:
        picked = points[0].get("customdata", [None])[0]
        if picked and picked != st.session_state.get("focus"):
            S.set_focus(picked)
            S.go_to("nav_profile")
            st.rerun()
    st.caption(ctx.t("click_hint"))


def bar_compare(ctx, series: pd.Series, title: str = "", y_title: str = "",
                height: int = 360, percent: bool = True):
    """Horizontal ranking bar, green above zero and red below."""
    import plotly.graph_objects as go

    s = series.dropna().sort_values()
    if s.empty:
        st.info(ctx.t("not_enough_data"))
        return
    values = s * 100 if percent else s
    fig = go.Figure(go.Bar(
        x=values, y=s.index, orientation="h",
        marker_color=[GAIN if v >= 0 else LOSS for v in values],
        hovertemplate="%{y}: %{x:.2f}<extra></extra>"))
    st.plotly_chart(style_fig(fig, title, y_title, "", height=height,
                              hover="closest", legend=False), width="stretch")


def growth_heatmap(ctx, prices: pd.Series, ticker: str, height: int | None = None):
    """Year × month growth grid — the calendar view of a track record."""
    import plotly.graph_objects as go

    import analytics as an
    import i18n
    from ui.theme import DIVERGING

    heat = an.monthly_returns(prices)
    if heat.empty:
        st.info(ctx.t("not_enough_data"))
        return heat

    months = [i18n.month_name(ctx.lang, m) for m in heat.columns]
    limit = float(np.nanmax(np.abs(heat.values))) or 1.0
    fig = go.Figure(go.Heatmap(
        z=heat.values, x=months, y=[str(y) for y in heat.index],
        colorscale=DIVERGING, zmid=0, zmin=-limit, zmax=limit,
        xgap=2, ygap=2, colorbar=dict(title="%", thickness=10, len=.7,
                                      outlinewidth=0),
        hovertemplate="%{y} %{x}: %{z:.2f}%<extra></extra>",
        # empty string, not "NaN", for months a fund did not yet exist
        text=[["" if np.isnan(v) else f"{v:.1f}" for v in row] for row in heat.values],
        texttemplate="%{text}", textfont=dict(size=10)))
    fig.update_yaxes(autorange="reversed", tickfont=dict(size=10))
    # month labels sit in a narrow card; without a forced tick per column and a
    # smaller face they run into each other as "JanFebMar"
    fig.update_xaxes(side="top", tickangle=0, tickfont=dict(size=10),
                     dtick=1, automargin=True)
    st.plotly_chart(
        style_fig(fig, "", "", "",
                  height=height or max(240, 30 * len(heat) + 90),
                  hover="closest", legend=False), width="stretch")

    monthly_avg = heat.mean()
    yearly = an.calendar_year_returns(prices.to_frame(ticker))[ticker].dropna()
    flat = heat.values[~np.isnan(heat.values)]
    if len(monthly_avg.dropna()) and len(yearly) and len(flat):
        readout(ctx, i18n.heatmap_readout(
            ctx.lang, ticker,
            i18n.month_name(ctx.lang, monthly_avg.idxmax()), float(monthly_avg.max()),
            i18n.month_name(ctx.lang, monthly_avg.idxmin()), float(monthly_avg.min()),
            float((flat > 0).mean() * 100),
            str(yearly.idxmax()), float(yearly.max())))
    return heat
