# -*- coding: utf-8 -*-
"""Visual language of the report: palette, CSS and chart styling."""

from __future__ import annotations

import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# Warm, high-contrast palette. Financial semantics (green = gain, red = loss)
# stay reserved for data; the chrome uses teal and amber.
PALETTE = ["#0F766E", "#B45309", "#1D4ED8", "#BE123C", "#4D7C0F", "#7C3AED",
           "#0891B2", "#C2410C", "#4338CA", "#9D174D", "#15803D", "#A16207"]

INK = "#14322E"
MUTED = "#5E5D59"
GAIN = "#15803D"
LOSS = "#BE123C"
BENCH = "#8A8A82"

# plotly express picks its colours when the figure is built, so the sequence has
# to be set here rather than through the layout colorway afterwards
px.defaults.color_discrete_sequence = PALETTE

CSS = """
<style>
    .stApp { background-color: #F7F7F4; }
    h1, h2, h3 { color: #14322E; font-weight: 700; letter-spacing: -.01em; }
    h1 { font-size: 1.75rem; }
    h3 { font-size: 1.15rem; margin-top: .4rem; }

    div[data-testid="stMetric"] {
        background: #FFFFFF; padding: 12px 14px; border-radius: 10px;
        border: 1px solid #E6E4DC; border-left: 4px solid #0F766E;
    }
    div[data-testid="stMetric"] label { color: #5E5D59 !important; font-size: .8rem; }
    div[data-testid="stMetricValue"] { font-size: 1.35rem; }

    /* selection bar sitting under the title */
    .selbar {
        background: #FFFFFF; border: 1px solid #E6E4DC; border-radius: 10px;
        padding: 8px 14px; margin-bottom: 10px; font-size: .9rem; color: #3F3F3A;
    }
    .chip {
        display: inline-block; background: #EEF6F4; border: 1px solid #CFE3DF;
        color: #0F766E; border-radius: 999px; padding: 2px 10px; margin: 2px 4px 2px 0;
        font-weight: 600; font-size: .82rem;
    }
    .chip-bench { background: #FDF6EC; border-color: #EBD9BF; color: #B45309; }

    .insight {
        background: #EEF6F4; border-left: 4px solid #0F766E; padding: 12px 16px;
        border-radius: 6px; margin-top: 8px; color: #14322E; font-size: .9rem;
    }
    .commentary {
        background: #FDF6EC; border-left: 4px solid #B45309; padding: 14px 18px;
        border-radius: 8px; color: #4A2E09; font-size: .96rem; line-height: 1.55;
    }
    .insight-title { font-weight: 700; display: block; margin-bottom: 4px; }
    .facts { font-size: .9rem; line-height: 1.7; color: #3F3F3A; }
    .facts b { color: #14322E; }
    .hint { color: #5E5D59; font-size: .82rem; }

    section[data-testid="stSidebar"] { background: #FFFFFF; border-right: 1px solid #E6E4DC; }
    .stTabs [data-baseweb="tab-list"] { gap: 4px; flex-wrap: wrap; }
    .stTabs [data-baseweb="tab"] {
        background: #FFFFFF; border: 1px solid #E6E4DC; border-radius: 8px;
        padding: 8px 16px; font-weight: 600; color: #3F3F3A;
    }
    .stTabs [aria-selected="true"] { background: #0F766E !important; color: #FFF !important; }
</style>
"""


def inject() -> None:
    st.markdown(CSS, unsafe_allow_html=True)


def style_fig(fig: go.Figure, title: str = "", x_title: str = "", y_title: str = "",
              height: int | None = None, hover: str = "x unified",
              log_y: bool = False, legend: bool = True) -> go.Figure:
    fig.update_layout(
        template="plotly_white",
        colorway=PALETTE,
        title=dict(text=title, font=dict(size=16, color=INK)),
        xaxis_title=x_title, yaxis_title=y_title,
        hovermode=hover,
        margin=dict(t=50 if title else 26, b=36, l=8, r=8),
        showlegend=legend,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0,
                    font=dict(size=11)),
        font=dict(color=INK, size=12),
        legend_title_text="",
    )
    if log_y:
        fig.update_yaxes(type="log")
    if height:
        fig.update_layout(height=height)
    return fig


def color_for(index: int) -> str:
    return PALETTE[index % len(PALETTE)]
