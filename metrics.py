"""Backwards-compatible shim.

The metric library moved to :mod:`analytics`, which covers far more ground
(benchmark-relative statistics, tail risk, rolling windows, strategy
simulations). This module keeps the original names working for any script or
notebook that still imports ``metrics``.
"""

from __future__ import annotations

import pandas as pd

import analytics
from analytics import (  # noqa: F401
    TRADING_DAYS,
    daily_returns as calculate_returns,
    drawdown as calculate_drawdown,
    rolling_beta as calculate_rolling_beta,
)


def calculate_cumulative_returns(df):
    """Cumulative return series (0 = flat), kept for the original API."""
    return (1 + analytics.daily_returns(df)).cumprod() - 1


def calculate_max_drawdown(df):
    return analytics.drawdown(df).min()


def calculate_risk_metrics(daily_ret: pd.Series, risk_free_rate: float = 0.0) -> pd.Series:
    """Original six-metric summary, now computed by :mod:`analytics`."""
    if daily_ret.empty:
        return pd.Series(dtype=float)
    equity = (1 + daily_ret.fillna(0)).cumprod()
    return pd.Series({
        "Ann. Return": analytics.cagr(equity),
        "Volatility": analytics.annual_volatility(daily_ret),
        "Max Drawdown": analytics.max_drawdown(equity),
        "Sharpe Ratio": analytics.sharpe(equity, risk_free_rate),
        "Sortino Ratio": analytics.sortino(equity, risk_free_rate),
        "Calmar Ratio": analytics.calmar(equity),
    })


def calculate_monthly_heatmap(series: pd.Series) -> pd.Series:
    monthly = series.resample("ME").apply(lambda x: (1 + x).prod() - 1)
    return monthly * 100
