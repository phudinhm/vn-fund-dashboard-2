"""Tests for the UI layer: state handling, components and every view rendering."""

from __future__ import annotations

import os
import sys

import pandas as pd
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import report as rp  # noqa: E402
from tests import fixture  # noqa: E402

streamlit = pytest.importorskip("streamlit")
from streamlit.testing.v1 import AppTest  # noqa: E402

from ui import components as C  # noqa: E402
from ui import state as S  # noqa: E402

VIEWS = ["nav_overview", "nav_screener", "nav_compare", "nav_markets",
         "nav_profile", "nav_lab", "nav_data"]
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
APP = os.path.join(ROOT, "app.py")

has_data = os.path.exists(os.path.join(ROOT, "data", "prices.csv")) or \
    os.path.exists(os.path.join(ROOT, "funds_data.csv"))
needs_data = pytest.mark.skipif(not has_data, reason="no dataset checked in")


# --------------------------------------------------------------- formatting
def test_formatting_handles_missing_values():
    assert C.pct(0.1234) == "12.34%"
    assert C.pct(None) == "—"
    assert C.pct(float("nan")) == "—"
    assert C.num(1.239) == "1.24"
    assert C.num(float("nan")) == "—"


def test_sparkline_is_rebased_and_bounded(tmp_path):
    fixture.build(str(tmp_path))
    prices = pd.read_csv(tmp_path / "prices.csv", parse_dates=["Date"], index_col="Date")
    spark = C.sparkline_series(prices, ["SPY", "MISSING"], points=52)
    assert spark["SPY"][0] == pytest.approx(100.0)
    assert 2 < len(spark["SPY"]) <= 52
    assert spark["MISSING"] == []


def test_metric_columns_are_translated(tmp_path):
    class Ctx:
        lang = "DE"

        def t(self, key):
            import i18n
            return i18n.t("DE", key)

    cfg = C.metric_columns(Ctx(), ["cagr", "sharpe", "ter", "unknown_metric"])
    assert set(cfg) == {"cagr", "sharpe", "ter"}


# -------------------------------------------------------------------- state
def test_query_map_covers_every_state_key():
    assert set(S.DEFAULTS) == set(S.QUERY_MAP)
    assert len(set(S.QUERY_MAP.values())) == len(S.QUERY_MAP)  # no clashes


def test_default_benchmark_prefers_a_known_index(tmp_path):
    fixture.build(str(tmp_path))
    ds = rp.load_dataset(data_dir=str(tmp_path), root=str(tmp_path))
    assert S.pick_default_benchmark(ds) == "VNINDEX"


# -------------------------------------------------------------------- views
@needs_data
@pytest.mark.parametrize("view", VIEWS)
def test_every_view_renders(view):
    at = AppTest.from_file(APP, default_timeout=600)
    at.session_state["view"] = view
    at.session_state["lang"] = "EN"
    at.run()
    assert not at.exception, [str(e.value) for e in at.exception]


@needs_data
@pytest.mark.parametrize("lang", ["VI", "EN", "DE"])
def test_overview_renders_in_every_language(lang):
    at = AppTest.from_file(APP, default_timeout=600)
    at.session_state["lang"] = lang
    at.run()
    assert not at.exception, [str(e.value) for e in at.exception]


@needs_data
def test_state_is_mirrored_into_the_url():
    at = AppTest.from_file(APP, default_timeout=600)
    at.session_state["lang"] = "DE"
    at.session_state["view"] = "nav_markets"
    at.run()
    def one(value):  # AppTest hands back a list per key
        return value[0] if isinstance(value, list) else value

    params = {k: one(v) for k, v in dict(at.query_params).items()}
    assert params["l"] == "DE"
    assert params["v"] == "nav_markets"
    assert params["s"]  # the selection travels in the link too
    assert params["c"] == at.session_state["currency"]


@needs_data
def test_settings_changes_do_not_break_the_report():
    at = AppTest.from_file(APP, default_timeout=600)
    at.session_state["view"] = "nav_compare"
    at.run()
    at.selectbox(key="currency").set_value("EUR").run()
    at.select_slider(key="period").set_value("MAX").run()
    assert not at.exception, [str(e.value) for e in at.exception]
    assert at.session_state["currency"] == "EUR"
    assert at.session_state["period"] == "MAX"


@needs_data
def test_screener_filters_narrow_the_result_set():
    at = AppTest.from_file(APP, default_timeout=600)
    at.session_state["view"] = "nav_screener"
    at.run()
    unfiltered = at.metric[0].value
    at.slider(key="scr_sharpe").set_value(1.0).run()
    assert not at.exception, [str(e.value) for e in at.exception]
    assert int(at.metric[0].value) <= int(unfiltered)
