"""Pipeline / universe / report tests that never touch the network."""

from __future__ import annotations

import os
import sys

import pandas as pd
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import i18n  # noqa: E402
import report as rp  # noqa: E402
import sources  # noqa: E402
import universe as uni  # noqa: E402
from tests import fixture  # noqa: E402


def test_universe_is_consistent():
    u = uni.static_universe()
    assert len(u) > 150
    assert u.ticker.is_unique
    for column in ["source", "kind", "asset_class", "region", "country", "currency"]:
        assert u[column].notna().all()
    unknown = {b for b in u.benchmark.unique() if b and b not in set(u.ticker)}
    assert not unknown, f"benchmarks pointing nowhere: {unknown}"


def test_universe_covers_every_major_region():
    u = uni.static_universe()
    for region in ["Vietnam", "US", "Europe", "Asia-Pacific", "Emerging", "Global"]:
        assert (u.region == region).any(), region
    assert u[u.kind == "ETF"].country.nunique() >= 15
    assert u.currency.nunique() >= 8


def test_stooq_symbol_mapping():
    assert sources._stooq_symbol("SPY") == "spy.us"
    assert sources._stooq_symbol("EUNL.DE") == "eunl.de"
    assert sources._stooq_symbol("^GSPC") == "^spx"
    assert sources._stooq_symbol("BTC-USD") is None


def test_fetchers_fail_softly(monkeypatch):
    def boom(*args, **kwargs):
        raise RuntimeError("network down")
    monkeypatch.setattr(sources._SESSION, "get", boom)
    monkeypatch.setattr(sources._SESSION, "post", boom)
    assert sources.fetch_vndirect("VNINDEX", retries=1).empty
    assert sources.fetch_stooq("SPY").empty
    assert sources.fetch_fmarket_catalogue() == []
    assert sources.fetch_fmarket_nav(1).empty
    assert sources.fetch_fx_frankfurter(["EUR"]).empty
    assert sources.fetch_fx_latest_erapi() == {}


@pytest.fixture(scope="module")
def dataset(tmp_path_factory):
    out = tmp_path_factory.mktemp("data")
    fixture.build(str(out))
    return rp.load_dataset(data_dir=str(out), root=str(out))


def test_dataset_loads(dataset):
    assert dataset is not None
    assert not dataset.legacy
    assert dataset.prices.shape[1] == 16
    assert dataset.markets >= 4
    assert dataset.currencies >= 3


def test_legacy_fallback_still_works(tmp_path):
    prices = pd.DataFrame(
        {"VNINDEX": [1000, 1010], "E1VFVN30": [20, 21]},
        index=pd.to_datetime(["2026-01-02", "2026-01-03"]))
    prices.index.name = "Date"
    prices.to_csv(tmp_path / "funds_data.csv")
    ds = rp.load_dataset(data_dir=str(tmp_path / "missing"), root=str(tmp_path))
    assert ds is not None and ds.legacy
    assert set(ds.profile.ticker) == {"VNINDEX", "E1VFVN30"}
    assert (ds.profile.currency == "VND").all()


def test_presets_only_contain_available_tickers(dataset):
    for name, tickers in rp.presets(dataset.profile, dataset.prices).items():
        assert set(tickers) <= set(dataset.prices.columns), name


def test_default_selection_is_not_empty(dataset):
    sel = rp.default_selection(dataset.profile, dataset.prices)
    assert sel and set(sel) <= set(dataset.prices.columns)


def test_region_performance_covers_regions(dataset):
    window = rp.slice_window(dataset.prices, "3Y")
    perf = rp.region_performance(window, dataset.profile)
    assert not perf.empty
    assert {"US", "Europe", "Vietnam"} <= set(perf.region)


@pytest.mark.parametrize("lang", ["VI", "EN", "DE"])
def test_markdown_report_renders_in_each_language(dataset, lang):
    tickers = ["SP500", "SPY", "QQQ", "EUNL.DE", "VNINDEX", "GLD"]
    text = rp.markdown_report(lang, dataset, tickers, "3Y", "SP500", "USD", 0.02)
    assert i18n.t(lang, "app_title") in text
    assert i18n.t(lang, "h_leaderboard") in text
    for ticker in tickers:
        assert ticker in text
    assert len(text) > 1500


def test_slice_window_respects_period(dataset):
    full = dataset.prices
    year = rp.slice_window(full, "1Y")
    assert year.index.min() > full.index.min()
    assert (year.index.max() - year.index.min()).days <= 370


# ---------------------------------------------------------------------------
# end-to-end run of the daily updater with every network call stubbed out
# ---------------------------------------------------------------------------

def _fake_series(start="2018-01-02", n=1200, level=100.0):
    import numpy as np
    idx = pd.bdate_range(start, periods=n)
    rng = np.random.default_rng(5)
    values = level * (1 + rng.normal(0.0004, 0.01, n)).cumprod()
    return pd.DataFrame({"Close": values, "Volume": 1000}, index=idx)


def test_update_data_end_to_end(tmp_path, monkeypatch):
    import update_data

    monkeypatch.setattr(sources, "fetch_vndirect", lambda symbol, retries=3: _fake_series())
    monkeypatch.setattr(sources, "fetch_yahoo_batch",
                        lambda symbols, **kw: {s: _fake_series() for s in symbols[:40]})
    monkeypatch.setattr(sources, "fetch_stooq", lambda symbol: _fake_series())
    monkeypatch.setattr(sources, "fetch_fmarket_catalogue", lambda page_size=200: [
        {"ticker": "VESAF", "product_id": 1, "name": "Test fund",
         "issuer": "VinaCapital", "asset_class": "Equity", "category": "Equity Fund"}])
    monkeypatch.setattr(sources, "fetch_fmarket_nav", lambda pid: _fake_series())
    monkeypatch.setattr(sources, "fetch_fx_yahoo",
                        lambda ccys: pd.DataFrame(
                            {c: 1.0 for c in ccys},
                            index=pd.bdate_range("2018-01-02", periods=1200)))
    monkeypatch.setattr(update_data.time, "sleep", lambda *a, **k: None)

    rc = update_data.main(root=str(tmp_path), data_dir=str(tmp_path / "data"))
    assert rc == 0

    data = tmp_path / "data"
    for name in ["prices.csv", "volume.csv", "profile.csv", "fx.csv", "status.json"]:
        assert (data / name).exists(), name

    prices = pd.read_csv(data / "prices.csv", parse_dates=["Date"], index_col="Date")
    profile = pd.read_csv(data / "profile.csv")
    assert prices.shape[1] == profile.shape[0]
    assert "VESAF" in prices.columns          # open-ended fund discovered live
    assert "VNINDEX" in prices.columns        # Vietnam
    assert prices.shape[1] > 50               # world instruments included
    assert {"first_date", "last_date", "observations", "stale_days"} <= set(profile.columns)

    import json
    status = json.loads((data / "status.json").read_text())
    assert status["instruments"] == prices.shape[1]
    assert status["last_date"]

    # legacy Vietnam-only files stay in place for older consumers
    legacy = pd.read_csv(tmp_path / "funds_data.csv", parse_dates=["Date"], index_col="Date")
    assert "E1VFVN30" in legacy.columns
    assert "SPY" not in legacy.columns
    legacy_profile = pd.read_csv(tmp_path / "funds_profile.csv")
    assert list(legacy_profile.columns) == ["Ticker", "Name", "Issuer", "Type",
                                            "Benchmark", "Launch", "Fee"]

    # the freshly produced dataset loads back into the report layer
    ds = rp.load_dataset(data_dir=str(data), root=str(tmp_path))
    assert ds is not None and not ds.legacy
    text = rp.markdown_report("DE", ds, ["VNINDEX", "E1VFVN30"], "1Y", "VNINDEX", "VND")
    assert "VNINDEX" in text


def test_update_data_reports_failure_when_every_source_is_down(tmp_path, monkeypatch):
    import update_data

    empty = pd.DataFrame(columns=["Close", "Volume"])
    monkeypatch.setattr(sources, "fetch_vndirect", lambda symbol, retries=3: empty)
    monkeypatch.setattr(sources, "fetch_yahoo_batch", lambda symbols, **kw: {})
    monkeypatch.setattr(sources, "fetch_stooq", lambda symbol: empty)
    monkeypatch.setattr(sources, "fetch_fmarket_catalogue", lambda page_size=200: [])
    monkeypatch.setattr(sources, "fetch_fx_yahoo", lambda ccys: pd.DataFrame())
    monkeypatch.setattr(sources, "fetch_fx_frankfurter",
                        lambda ccys, start=None: pd.DataFrame())
    monkeypatch.setattr(sources, "fetch_fx_latest_erapi", lambda base="USD": {})
    monkeypatch.setattr(update_data.time, "sleep", lambda *a, **k: None)

    rc = update_data.main(root=str(tmp_path), data_dir=str(tmp_path / "data"))
    assert rc == 1
    import json
    status = json.loads((tmp_path / "data" / "status.json").read_text())
    assert status["error"] == "no data"


def test_skip_flags_are_honoured(monkeypatch):
    import update_data
    monkeypatch.setenv("SKIP_WORLD", "1")
    monkeypatch.setenv("SKIP_MUTUAL_FUNDS", "1")
    status = {"failed": [], "warnings": []}
    assert update_data.collect_world(status) == ({}, {}, [])
    assert update_data.collect_mutual_funds(status) == ({}, [])
