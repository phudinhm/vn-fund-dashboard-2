"""Unit tests for the analytics engine (no network, synthetic data)."""

from __future__ import annotations

import os
import sys

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import analytics as an  # noqa: E402
from tests import fixture  # noqa: E402


@pytest.fixture(scope="module")
def data(tmp_path_factory):
    out = tmp_path_factory.mktemp("data")
    fixture.build(str(out))
    prices = pd.read_csv(out / "prices.csv", parse_dates=["Date"], index_col="Date")
    profile = pd.read_csv(out / "profile.csv")
    fx = pd.read_csv(out / "fx.csv", parse_dates=["Date"], index_col="Date")
    return prices, profile, fx


def test_cagr_matches_known_growth():
    idx = pd.bdate_range("2020-01-01", periods=252 * 4)
    s = pd.Series(100 * (1.10 ** (np.arange(len(idx)) / 252)), index=idx)
    assert an.cagr(s) == pytest.approx(0.10, abs=0.005)


def test_total_return_and_drawdown():
    s = pd.Series([100, 120, 90, 110], index=pd.bdate_range("2024-01-01", periods=4))
    assert an.total_return(s) == pytest.approx(0.10)
    assert an.max_drawdown(s) == pytest.approx(-0.25)


def test_volatility_scales_with_sqrt_time():
    rng = np.random.default_rng(0)
    r = pd.Series(rng.normal(0, 0.01, 5000))
    assert an.annual_volatility(r) == pytest.approx(0.01 * np.sqrt(252), rel=0.1)


def test_beta_of_series_against_itself_is_one(data):
    prices, _, _ = data
    r = an.daily_returns(prices["SPY"]).dropna()
    beta, alpha, r2 = an.beta_alpha(r, r)
    assert beta == pytest.approx(1.0, abs=1e-6)
    assert alpha == pytest.approx(0.0, abs=1e-6)
    assert r2 == pytest.approx(1.0, abs=1e-6)


def test_tracking_error_is_zero_against_itself(data):
    prices, _, _ = data
    r = an.daily_returns(prices["SPY"]).dropna()
    assert an.tracking_error(r, r) == pytest.approx(0.0, abs=1e-9)


def test_capture_ratios_are_100_against_itself(data):
    prices, _, _ = data
    r = an.daily_returns(prices["QQQ"]).dropna()
    up, down = an.capture_ratios(r, r)
    assert up == pytest.approx(100.0, abs=1e-6)
    assert down == pytest.approx(100.0, abs=1e-6)


def test_currency_conversion_uses_the_daily_fx_rate(data):
    prices, profile, fx = data
    usd = an.convert_prices(prices, profile, fx, "USD")
    # an instrument already quoted in the reporting currency is untouched
    pd.testing.assert_series_equal(usd["SPY"], prices["SPY"], check_names=False)
    # a VND instrument is scaled by the VND/USD rate of the same day
    rate = fx["VND"].reindex(prices.index).ffill()
    expected = (prices["VNINDEX"] * rate).dropna()
    pd.testing.assert_series_equal(usd["VNINDEX"].dropna(), expected,
                                   check_names=False, rtol=1e-9)
    # USD and EUR views of the same fund differ exactly by the EURUSD path
    eur = an.convert_prices(prices, profile, fx, "EUR")
    ratio = (usd["VNINDEX"] / eur["VNINDEX"]).dropna()
    eur_rate = fx["EUR"].reindex(prices.index).ffill().reindex(ratio.index)
    assert np.allclose(ratio.values, eur_rate.values, rtol=1e-9)


def test_missing_fx_leaves_prices_in_local_currency(data):
    prices, profile, fx = data
    partial = fx[["USD"]]
    out = an.convert_prices(prices, profile, partial, "USD")
    pd.testing.assert_series_equal(out["VNINDEX"], prices["VNINDEX"], check_names=False)
    assert "VNINDEX" in an.unconverted_tickers(prices, profile, partial, "USD")


def test_conversion_changes_return_but_not_ordering_within_currency(data):
    prices, profile, fx = data
    usd = an.convert_prices(prices, profile, fx, "USD")
    vnd = an.convert_prices(prices, profile, fx, "VND")
    # two USD funds keep their relative performance in any reporting currency
    a = an.cagr(usd["SPY"]) - an.cagr(usd["QQQ"])
    b = an.cagr(vnd["SPY"]) - an.cagr(vnd["QQQ"])
    assert np.sign(a) == np.sign(b)


def test_metrics_table_has_every_column(data):
    prices, profile, fx = data
    m = an.metrics_table(prices, benchmark="SP500", rf=0.02, profile=profile)
    for col in ["cagr", "volatility", "max_drawdown", "sharpe", "sortino", "calmar",
                "var95", "cvar95", "beta", "alpha", "tracking_error",
                "information_ratio", "up_capture", "down_capture", "region", "ter"]:
        assert col in m.columns, col
    assert len(m) == prices.shape[1]


def test_composite_score_ranks_the_better_fund_higher():
    idx = pd.bdate_range("2018-01-01", periods=252 * 5)
    good = pd.Series(100 * (1.15 ** (np.arange(len(idx)) / 252)), index=idx)
    bad = pd.Series(100 * (1.02 ** (np.arange(len(idx)) / 252)), index=idx)
    frame = pd.DataFrame({"GOOD": good, "BAD": bad})
    scored = an.composite_score(an.metrics_table(frame))
    assert scored.index[0] == "GOOD"
    assert scored.loc["GOOD", "rank"] == 1


def test_period_returns_blank_when_history_too_short(data):
    prices, _, _ = data
    per = an.period_returns(prices)
    assert np.isnan(per.loc["FUEVFVND", "10Y"])
    assert not np.isnan(per.loc["SPY", "5Y"])


def test_calendar_years_use_previous_year_end(data):
    prices, _, _ = data
    cal = an.calendar_year_returns(prices[["SPY"]])
    assert cal.index.name == "year"
    year = 2020
    s = prices["SPY"].dropna()
    expected = (s[s.index.year == year].iloc[-1] /
                s[s.index.year == year - 1].iloc[-1]) - 1
    assert cal.loc[year, "SPY"] == pytest.approx(expected, rel=1e-9)


def test_drawdown_episodes_are_sorted_by_depth(data):
    prices, _, _ = data
    ep = an.drawdown_episodes(prices["VNINDEX"], top=4)
    assert list(ep["depth"]) == sorted(ep["depth"])
    assert (ep["depth"] <= 0).all()


def test_dca_invests_expected_amount(data):
    prices, _, _ = data
    s = prices["SPY"].loc["2022":"2024"]
    dca = an.simulate_dca(s, contribution=100.0, freq="ME")
    months = len(s.resample("ME").last())
    assert dca["invested"].iloc[-1] == pytest.approx(months * 100.0)
    assert dca["value"].iloc[-1] > 0


def test_rolling_dca_vs_lumpsum_returns_probabilities(data):
    prices, _, _ = data
    res = an.rolling_dca_vs_lumpsum(prices["SPY"], hold_years=3, spread_months=12)
    assert res["windows"] > 0
    assert 0 <= res["lump_sum_win_rate"] <= 100


def test_rebalanced_portfolio_sits_between_its_holdings(data):
    prices, _, _ = data
    px = prices[["SPY", "AGG"]].dropna()
    curve = an.rebalanced_portfolio(px, {"SPY": 50, "AGG": 50}, "QE")
    assert curve.iloc[0] == pytest.approx(100.0)
    growth = an.cumulative_growth(px)
    lo, hi = sorted([growth["SPY"].iloc[-1], growth["AGG"].iloc[-1]])
    assert lo <= curve.iloc[-1] <= hi * 1.05


def test_fee_erosion_grows_with_the_fee():
    low = an.fee_erosion(100, 0.08, 0.001, 20)["net"].iloc[-1]
    high = an.fee_erosion(100, 0.08, 0.02, 20)["net"].iloc[-1]
    assert low > high


def test_efficient_frontier_weights_sum_to_one(data):
    prices, _, _ = data
    front = an.efficient_frontier(prices[["SPY", "AGG", "GLD"]], simulations=200)
    weights = front[[c for c in front.columns if c.startswith("w_")]]
    assert np.allclose(weights.sum(axis=1), 1.0)
    assert (front["volatility"] >= 0).all()


def test_monte_carlo_is_deterministic_with_a_seed(data):
    prices, _, _ = data
    a = an.monte_carlo(prices["SPY"], days=30, simulations=200, seed=3)
    b = an.monte_carlo(prices["SPY"], days=30, simulations=200, seed=3)
    assert a["median"] == pytest.approx(b["median"])
    assert 0 <= a["prob_up"] <= 100


def test_correlation_diagonal_is_one(data):
    prices, _, _ = data
    corr = an.correlation_matrix(prices[["SPY", "QQQ", "AGG"]])
    assert np.allclose(np.diag(corr.values), 1.0)
    assert -1 <= an.diversification_score(corr) <= 1


def test_empty_and_short_series_do_not_raise():
    empty = pd.Series(dtype=float)
    assert np.isnan(an.cagr(empty))
    assert np.isnan(an.max_drawdown(empty))
    assert an.metrics_table(pd.DataFrame({"X": empty})).empty


def test_risk_contribution_sums_to_one(data):
    prices, _, _ = data
    contribution = an.risk_contribution(prices[["SPY", "AGG", "GLD"]],
                                        {"SPY": 60, "AGG": 30, "GLD": 10})
    assert contribution.sum() == pytest.approx(1.0, abs=1e-9)
    # the volatile equity leg carries more risk than its 60% weight
    assert contribution["SPY"] > 0.6
    assert contribution["AGG"] < 0.3


def test_risk_contribution_handles_degenerate_input(data):
    prices, _, _ = data
    assert an.risk_contribution(prices[["SPY"]], {"SPY": 100}).empty
    assert an.risk_contribution(prices[["SPY", "AGG"]], {"SPY": 0, "AGG": 0}).empty


def test_coverage_marks_instruments_that_span_the_window(data):
    prices, profile, _ = data
    window = prices.loc["2020-01-01":]
    metrics = an.metrics_table(window, profile=profile)
    # FUEVFVND starts mid-2020 in the fixture, SPY spans the whole window
    assert metrics.loc["SPY", "coverage"] > 0.99
    assert metrics.loc["FUEVFVND", "coverage"] < metrics.loc["SPY", "coverage"]
    assert (metrics["coverage"] <= 1.0).all()


def test_short_history_is_listed_but_not_ranked():
    """A two-month-old fund must not out-rank a three-year track record."""
    idx = pd.bdate_range("2021-01-01", periods=252 * 4)
    seasoned = pd.Series(100 * (1.10 ** (np.arange(len(idx)) / 252)), index=idx)
    newcomer = pd.Series(np.nan, index=idx)
    tail = idx[-40:]
    newcomer.loc[tail] = 100 * (1.9 ** (np.arange(len(tail)) / 252))  # 90% annualised

    scored = an.composite_score(
        an.metrics_table(pd.DataFrame({"OLD": seasoned, "NEW": newcomer})))
    assert scored.loc["NEW", "cagr"] > scored.loc["OLD", "cagr"]   # raw number flatters it
    assert pd.isna(scored.loc["NEW", "score"])                     # but it is not ranked
    assert scored.loc["OLD", "rank"] == 1
    assert scored.index[0] == "OLD"                                # unranked sorts last


def test_comparable_filters_to_the_full_window():
    frame = pd.DataFrame({"coverage": [1.0, 0.9, 0.2]}, index=["A", "B", "C"])
    assert list(an.comparable(frame).index) == ["A", "B"]
    # never returns nothing: if no row qualifies, the caller still gets the data
    thin = pd.DataFrame({"coverage": [0.1, 0.2]}, index=["A", "B"])
    assert len(an.comparable(thin)) == 2


def test_time_under_water_counts_the_longest_stretch():
    idx = pd.bdate_range("2024-01-01", periods=6)
    # peak, fall, recovery on the fifth day
    prices = pd.Series([100, 90, 80, 95, 101, 102], index=idx)
    assert an.time_under_water(prices) == (idx[4] - idx[1]).days
    flat = pd.Series(np.arange(1, 7, dtype=float), index=idx)   # only new highs
    assert an.time_under_water(flat) == 0


def test_tracking_difference_is_the_return_gap(data):
    prices, _, _ = data
    gap = an.tracking_difference(prices["QQQ"], prices["SPY"])
    assert gap == pytest.approx(an.cagr(prices["QQQ"]) - an.cagr(prices["SPY"]), abs=1e-9)
    assert np.isnan(an.tracking_difference(prices["QQQ"].tail(10), prices["SPY"]))


def test_average_daily_value_uses_price_times_volume(data):
    prices, _, _ = data
    volume = pd.Series(1000.0, index=prices.index)
    adv = an.average_daily_value(prices["SPY"], volume)
    expected = (prices["SPY"] * volume).tail(63).median()
    assert adv == pytest.approx(expected)
    assert np.isnan(an.average_daily_value(prices["SPY"], pd.Series(dtype=float)))
