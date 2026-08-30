# -*- coding: utf-8 -*-
"""Report state: the single context object every view receives.

Selection, benchmark, currency, period and language live in ``st.session_state``
and are mirrored into the URL query string, so any view of the report can be
shared as a link and reopened exactly as it was.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from functools import cached_property

import pandas as pd
import streamlit as st

import analytics as an
import i18n
import report as rp

DEFAULTS = {
    "lang": "VI",
    "view": "nav_overview",
    "period": "3Y",
    "currency": "USD",
    "rf": 3.0,
    "benchmark": "",
    "selection": [],
    "focus": "",
}

# query-string keys are short on purpose: the shared link stays readable
QUERY_MAP = {"lang": "l", "view": "v", "period": "p", "currency": "c",
             "benchmark": "b", "selection": "s", "focus": "f", "rf": "rf"}


def init_state(ds) -> None:
    """Seed session state from the URL on the first run of a session."""
    if st.session_state.get("_state_ready"):
        return
    params = st.query_params
    for key, default in DEFAULTS.items():
        raw = params.get(QUERY_MAP[key])
        if raw is None:
            st.session_state.setdefault(key, default)
            continue
        if key == "selection":
            st.session_state[key] = [t for t in raw.split(",") if t in ds.prices.columns]
        elif key == "rf":
            try:
                st.session_state[key] = float(raw)
            except ValueError:
                st.session_state[key] = default
        else:
            st.session_state[key] = raw

    if not st.session_state.get("selection"):
        st.session_state["selection"] = rp.default_selection(ds.profile, ds.prices)
    if not st.session_state.get("benchmark"):
        st.session_state["benchmark"] = pick_default_benchmark(ds)
    if not st.session_state.get("focus"):
        st.session_state["focus"] = st.session_state["selection"][0]
    st.session_state["_state_ready"] = True


def pick_default_benchmark(ds) -> str:
    for candidate in ("VNINDEX", "SP500"):
        if candidate in ds.prices.columns:
            return candidate
    return ds.prices.columns[0]


def sync_query_params() -> None:
    """Write the current state back into the URL."""
    out = {}
    for key, short in QUERY_MAP.items():
        value = st.session_state.get(key, DEFAULTS[key])
        out[short] = ",".join(value) if isinstance(value, list) else str(value)
    st.query_params.from_dict(out)


# --------------------------------------------------------------------------
# mutations used by the interactive widgets
# --------------------------------------------------------------------------

def add_to_selection(tickers: list[str], limit: int = 20) -> int:
    current = list(st.session_state.get("selection", []))
    added = [t for t in tickers if t not in current]
    st.session_state["selection"] = (current + added)[:limit]
    return len(added)


def set_focus(ticker: str) -> None:
    st.session_state["focus"] = ticker
    add_to_selection([ticker])


def go_to(view_key: str) -> None:
    st.session_state["view"] = view_key


# --------------------------------------------------------------------------
# the context handed to every view
# --------------------------------------------------------------------------

@dataclass
class Ctx:
    """Everything a view needs, computed once per rerun."""

    ds: object
    lang: str
    tickers: list[str]
    benchmark: str
    currency: str
    period: str
    rf: float
    prices: pd.DataFrame          # selection, converted, full history
    window: pd.DataFrame          # selection, converted, sliced to the period
    metrics: pd.DataFrame
    scored: pd.DataFrame
    facts: dict = field(default_factory=dict)

    # ---- helpers -------------------------------------------------------
    def t(self, key: str) -> str:
        return i18n.t(self.lang, key)

    @property
    def profile(self) -> pd.DataFrame:
        return self.ds.profile

    @cached_property
    def returns(self) -> pd.DataFrame:
        return an.daily_returns(self.window)

    @cached_property
    def bench_ret(self) -> pd.Series | None:
        if self.benchmark not in self.window.columns:
            return None
        return an.daily_returns(self.window[self.benchmark])

    @cached_property
    def names(self) -> dict:
        return self.ds.profile.set_index("ticker")["name"].to_dict()

    def label(self, ticker: str, width: int = 38) -> str:
        name = str(self.names.get(ticker, ""))
        return f"{ticker} · {name[:width]}" if name else ticker

    @property
    def focus(self) -> str:
        current = st.session_state.get("focus", "")
        if current in self.window.columns:
            return current
        return self.window.columns[0] if len(self.window.columns) else ""

    def peers(self, ticker: str) -> list[str]:
        """Instruments of the same kind and category, for percentile ranking."""
        prof = self.ds.profile.set_index("ticker")
        if ticker not in prof.index:
            return []
        row = prof.loc[ticker]
        same = prof[(prof.kind == row.kind) & (prof.category == row.category)]
        if len(same) < 4:
            same = prof[(prof.kind == row.kind) & (prof.asset_class == row.asset_class)]
        return [t for t in same.index if t in self.ds.prices.columns]


@st.cache_data(show_spinner=False, ttl=3600)
def _compute(_ds, tickers: tuple, benchmark: str, currency: str, period: str,
             rf: float, last_date: str):
    """Heavy work behind the context, cached on the state that defines it."""
    cols = [t for t in dict.fromkeys(list(tickers) + [benchmark]) if t in _ds.prices.columns]
    prices = an.convert_prices(_ds.prices[cols], _ds.profile, _ds.fx, currency)
    window = rp.slice_window(prices, period).dropna(axis=1, how="all")
    metrics = an.metrics_table(window, benchmark=benchmark, rf=rf, profile=_ds.profile)
    scored = an.composite_score(metrics)
    facts = rp.build_facts(window, metrics, benchmark, currency)
    return prices, window, metrics, scored, facts


def build_context(ds) -> Ctx:
    lang = st.session_state["lang"]
    tickers = [t for t in st.session_state["selection"] if t in ds.prices.columns]
    benchmark = st.session_state["benchmark"]
    currency = st.session_state["currency"]
    period = st.session_state["period"]
    rf = float(st.session_state["rf"]) / 100

    prices, window, metrics, scored, facts = _compute(
        ds, tuple(tickers), benchmark, currency, period, rf,
        ds.last_date.strftime("%Y-%m-%d"))

    return Ctx(ds=ds, lang=lang, tickers=tickers, benchmark=benchmark,
               currency=currency, period=period, rf=rf, prices=prices,
               window=window, metrics=metrics, scored=scored, facts=facts)
