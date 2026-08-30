# -*- coding: utf-8 -*-
"""
Design system: Enterprise bento, minimalist.

Modular white cards on a neutral ground, hairline borders, no shadows and no
decorative colour. Colour carries meaning only — one accent for interactive
chrome, green and red reserved for gains and losses. Type is Roboto, the same
grotesque YouTube and the Google consoles use, with tabular figures so columns
of numbers line up.
"""

from __future__ import annotations

import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# --- neutral ground --------------------------------------------------------
BG = "#F1F3F4"
SURFACE = "#FFFFFF"
LINE = "#E1E3E6"
LINE_SOFT = "#EDEFF1"
INK = "#16181B"
MUTED = "#606468"
FAINT = "#9AA0A6"

# --- semantic --------------------------------------------------------------
ACCENT = "#0B57D0"
ACCENT_SOFT = "#E8F0FE"
GAIN = "#146C2E"
LOSS = "#B3261E"
BENCH = "#80868B"

# --- categorical series ----------------------------------------------------
# Distinguishable at hairline weight, in print, and for the common colour
# vision deficiencies; deliberately desaturated so the data, not the palette,
# is what stands out.
PALETTE = ["#0B57D0", "#146C2E", "#B3261E", "#7B3FBF", "#B06000",
           "#00696E", "#8C1D5B", "#3F6212", "#1F4E79", "#6B4E16"]

# diverging scale for heatmaps: red -> neutral -> green
DIVERGING = [[0.0, "#B3261E"], [0.25, "#E8A9A3"], [0.5, "#F4F5F6"],
             [0.75, "#8FC5A2"], [1.0, "#146C2E"]]

px.defaults.color_discrete_sequence = PALETTE

FONT = "Roboto, 'Helvetica Neue', Arial, sans-serif"

CSS = f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Roboto:wght@400;500;700&family=Roboto+Mono:wght@400;500&display=swap');

html, body, .stApp, [class*="st-"] {{ font-family: {FONT}; }}
.stApp {{ background: {BG}; color: {INK}; }}

h1, h2, h3, h4 {{ color: {INK}; font-weight: 500; letter-spacing: -.011em; }}
h1 {{ font-size: 1.5rem; font-weight: 500; }}
h2 {{ font-size: 1.15rem; }}
h3 {{ font-size: 1rem; margin: .2rem 0 .4rem; }}
h4 {{ font-size: .875rem; color: {MUTED}; font-weight: 500;
      text-transform: uppercase; letter-spacing: .06em; }}

/* numbers line up */
table, .stDataFrame, div[data-testid="stMetricValue"] {{
    font-variant-numeric: tabular-nums; font-feature-settings: "tnum";
}}

/* ---------- bento cards ---------- */
div[data-testid="stVerticalBlockBorderWrapper"] {{
    background: {SURFACE}; border: 1px solid {LINE}; border-radius: 12px;
    padding: 2px 4px;
}}

/* ---------- metrics as bento tiles ---------- */
div[data-testid="stMetric"] {{
    background: {SURFACE}; border: 1px solid {LINE}; border-radius: 12px;
    padding: 14px 16px;
}}
div[data-testid="stMetric"] label p {{
    color: {MUTED} !important; font-size: .75rem; font-weight: 500;
    text-transform: uppercase; letter-spacing: .05em;
}}
div[data-testid="stMetricValue"] {{ font-size: 1.4rem; font-weight: 500; color: {INK}; }}
div[data-testid="stMetricDelta"] {{ font-size: .78rem; }}

/* ---------- sidebar dock: dim until you reach for it ---------- */
section[data-testid="stSidebar"] {{
    background: {SURFACE}; border-right: 1px solid {LINE};
    opacity: .62; transition: opacity .18s ease-in-out;
}}
section[data-testid="stSidebar"]:hover,
section[data-testid="stSidebar"]:focus-within {{ opacity: 1; }}
section[data-testid="stSidebar"] .block-container {{ padding-top: 1.2rem; }}

/* nav dock: buttons styled as a rail */
section[data-testid="stSidebar"] div[data-testid="stButton"] {{ margin-bottom: -8px; }}
section[data-testid="stSidebar"] div[data-testid="stButton"] button {{
    justify-content: flex-start; border: none; min-height: 0;
    background: transparent; padding: 6px 10px; border-radius: 8px;
    border-left: 2px solid transparent; color: {INK}; font-weight: 400;
}}
section[data-testid="stSidebar"] div[data-testid="stButton"] button > div {{
    width: 100%; justify-content: flex-start; text-align: left;
}}
section[data-testid="stSidebar"] div[data-testid="stButton"] button p {{
    text-align: left; width: 100%; font-size: .875rem; margin: 0;
}}
section[data-testid="stSidebar"] div[data-testid="stButton"] button:hover {{
    background: {LINE_SOFT}; color: {INK};
}}
section[data-testid="stSidebar"] div[data-testid="stButton"] button[kind="primary"] {{
    background: {ACCENT_SOFT}; border-left-color: {ACCENT}; color: {ACCENT};
    font-weight: 500;
}}
/* language switch keeps its pill shape */
section[data-testid="stSidebar"] div[data-testid="stHorizontalBlock"]
    div[data-testid="stButton"] button {{
    justify-content: center; border: 1px solid {LINE}; border-left-width: 1px;
    padding: 5px 0;
}}
section[data-testid="stSidebar"] div[data-testid="stHorizontalBlock"]
    div[data-testid="stButton"] button > div {{ justify-content: center; }}
section[data-testid="stSidebar"] div[data-testid="stHorizontalBlock"]
    div[data-testid="stButton"] button p {{ text-align: center; }}

/* legacy radio rail */
section[data-testid="stSidebar"] div[role="radiogroup"] {{ gap: 1px; }}
section[data-testid="stSidebar"] div[role="radiogroup"] label {{
    padding: 7px 10px; border-radius: 8px; border-left: 2px solid transparent;
    transition: background .12s, border-color .12s;
}}
section[data-testid="stSidebar"] div[role="radiogroup"] label:hover {{
    background: {LINE_SOFT};
}}
section[data-testid="stSidebar"] div[role="radiogroup"] label:has(input:checked) {{
    background: {ACCENT_SOFT}; border-left-color: {ACCENT};
}}
section[data-testid="stSidebar"] div[role="radiogroup"] label p {{
    font-size: .875rem; font-weight: 500; color: {INK};
}}
section[data-testid="stSidebar"] div[role="radiogroup"] input {{ display: none; }}
/* the circle marker: a nav item is not a form field */
section[data-testid="stSidebar"] div[role="radiogroup"] label > div:first-child {{
    display: none !important;
}}
section[data-testid="stSidebar"] div[role="radiogroup"] label {{
    width: 100%; margin: 0;
}}

.dock-brand {{
    font-size: .95rem; font-weight: 700; letter-spacing: -.01em; color: {INK};
    margin-bottom: 2px;
}}
.dock-sub {{ font-size: .72rem; color: {FAINT}; margin-bottom: 14px; }}
.dock-group {{
    font-size: .7rem; font-weight: 500; text-transform: uppercase;
    letter-spacing: .07em; color: {FAINT}; margin: 16px 0 2px;
}}

/* ---------- narrative blocks ---------- */
.commentary {{
    background: {SURFACE}; border: 1px solid {LINE}; border-left: 3px solid {ACCENT};
    border-radius: 12px; padding: 14px 18px; color: {INK};
    font-size: .9rem; line-height: 1.6;
}}
.commentary .lead {{
    font-size: .7rem; font-weight: 500; text-transform: uppercase;
    letter-spacing: .07em; color: {FAINT}; display: block; margin-bottom: 6px;
}}
.readout {{
    color: {MUTED}; font-size: .82rem; line-height: 1.55; margin: 6px 0 2px;
    padding-left: 10px; border-left: 2px solid {LINE};
}}
.readout b {{ color: {INK}; font-weight: 500; }}
.facts {{ font-size: .82rem; line-height: 1.8; color: {MUTED}; }}
.facts b {{ color: {INK}; font-weight: 500; }}

/* ---------- chips ---------- */
.chip {{
    display: inline-block; background: {SURFACE}; border: 1px solid {LINE};
    color: {MUTED}; border-radius: 6px; padding: 2px 8px; margin: 2px 4px 2px 0;
    font-size: .75rem; font-weight: 500;
}}
.chip-key {{ background: {ACCENT_SOFT}; border-color: #C9DAF8; color: {ACCENT}; }}
.selbar {{ font-size: .8rem; color: {MUTED}; }}

/* freshness pill */
.fresh {{ font-size: .72rem; font-weight: 500; padding: 2px 8px;
          border-radius: 999px; display: inline-block; }}
.fresh-ok {{ background: #E6F4EA; color: {GAIN}; }}
.fresh-warn {{ background: #FEF7E0; color: #A16207; }}
.fresh-old {{ background: #FCE8E6; color: {LOSS}; }}

/* ---------- tabs: quiet, underline only ---------- */
.stTabs [data-baseweb="tab-list"] {{
    gap: 20px; border-bottom: 1px solid {LINE}; padding-bottom: 0;
}}
.stTabs [data-baseweb="tab"] {{
    background: transparent; border: none; padding: 8px 0;
    font-size: .875rem; font-weight: 500; color: {MUTED};
}}
.stTabs [aria-selected="true"] {{
    color: {ACCENT} !important; box-shadow: inset 0 -2px 0 {ACCENT};
}}
.stTabs [data-baseweb="tab-highlight"] {{ display: none; }}

/* ---------- controls ---------- */
.stButton button {{
    border-radius: 8px; border: 1px solid {LINE}; font-weight: 500;
    font-size: .82rem;
}}
div[data-testid="stDataFrame"] {{ border-radius: 10px; }}
hr {{ border-color: {LINE_SOFT}; }}
#MainMenu, footer {{ visibility: hidden; }}
</style>
"""


def inject() -> None:
    st.markdown(CSS, unsafe_allow_html=True)


def style_fig(fig: go.Figure, title: str = "", x_title: str = "", y_title: str = "",
              height: int | None = None, hover: str = "x unified",
              log_y: bool = False, legend: bool = True) -> go.Figure:
    """One chart grammar: no frame, hairline grid, Roboto, generous whitespace."""
    fig.update_layout(
        template="plotly_white",
        colorway=PALETTE,
        title=dict(text=title, font=dict(size=14, color=INK, family=FONT)),
        xaxis_title=x_title, yaxis_title=y_title,
        hovermode=hover,
        margin=dict(t=44 if title else 18, b=32, l=6, r=6),
        showlegend=legend,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0,
                    font=dict(size=11, color=MUTED), title_text=""),
        font=dict(color=MUTED, size=11, family=FONT),
        paper_bgcolor=SURFACE, plot_bgcolor=SURFACE,
        hoverlabel=dict(font_family=FONT, font_size=11),
    )
    fig.update_xaxes(showgrid=False, showline=True, linecolor=LINE,
                     zeroline=False, ticks="outside", tickcolor=LINE,
                     title_font=dict(size=11, color=FAINT))
    fig.update_yaxes(showgrid=True, gridcolor=LINE_SOFT, showline=False,
                     zeroline=False, title_font=dict(size=11, color=FAINT))
    if log_y:
        fig.update_yaxes(type="log")
    if height:
        fig.update_layout(height=height)
    return fig


def color_for(index: int) -> str:
    return PALETTE[index % len(PALETTE)]
