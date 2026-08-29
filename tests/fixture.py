"""Synthetic multi-market dataset used by the tests.

Generates the same file layout ``update_data.py`` produces, so the analytics
and the report can be exercised without touching the network.
"""

from __future__ import annotations

import json
import os

import numpy as np
import pandas as pd

SPECS = [
    # ticker, source, kind, asset_class, region, country, currency, issuer, ter, benchmark, drift, vol, start
    ("VNINDEX", "vndirect", "Index", "Equity", "Vietnam", "Vietnam", "VND", "HOSE", 0.0, "", 0.10, 0.19, "2015-01-01"),
    ("E1VFVN30", "vndirect", "ETF", "Equity", "Vietnam", "Vietnam", "VND", "Dragon Capital", 0.65, "VNINDEX", 0.11, 0.21, "2015-01-01"),
    ("FUEVFVND", "vndirect", "ETF", "Equity", "Vietnam", "Vietnam", "VND", "Dragon Capital", 0.80, "VNINDEX", 0.13, 0.24, "2020-06-01"),
    ("VESAF", "fmarket", "Mutual Fund", "Equity", "Vietnam", "Vietnam", "VND", "VinaCapital", float("nan"), "VNINDEX", 0.15, 0.20, "2017-05-01"),
    ("VFF", "fmarket", "Mutual Fund", "Bond", "Vietnam", "Vietnam", "VND", "VinaCapital", float("nan"), "VNINDEX", 0.07, 0.03, "2016-01-01"),
    ("SP500", "yahoo", "Index", "Equity", "US", "United States", "USD", "-", 0.0, "", 0.10, 0.17, "2015-01-01"),
    ("SPY", "yahoo", "ETF", "Equity", "US", "United States", "USD", "State Street", 0.09, "SP500", 0.10, 0.17, "2015-01-01"),
    ("QQQ", "yahoo", "ETF", "Equity", "US", "United States", "USD", "Invesco", 0.20, "SP500", 0.14, 0.22, "2015-01-01"),
    ("DAX", "yahoo", "Index", "Equity", "Europe", "Germany", "EUR", "-", 0.0, "", 0.07, 0.19, "2015-01-01"),
    ("EXS1.DE", "yahoo", "ETF", "Equity", "Europe", "Germany", "EUR", "BlackRock", 0.16, "DAX", 0.07, 0.19, "2015-01-01"),
    ("EUNL.DE", "yahoo", "ETF", "Equity", "Europe", "Germany", "EUR", "BlackRock", 0.20, "", 0.09, 0.16, "2015-01-01"),
    ("NIKKEI225", "yahoo", "Index", "Equity", "Asia-Pacific", "Japan", "JPY", "-", 0.0, "", 0.08, 0.20, "2015-01-01"),
    ("EWJ", "yahoo", "ETF", "Equity", "Asia-Pacific", "Japan", "USD", "BlackRock", 0.50, "NIKKEI225", 0.06, 0.18, "2015-01-01"),
    ("VNM", "yahoo", "ETF", "Equity", "Emerging", "Vietnam", "USD", "VanEck", 0.66, "VNINDEX", 0.05, 0.23, "2015-01-01"),
    ("GLD", "yahoo", "ETF", "Commodity", "Global", "Global", "USD", "State Street", 0.40, "", 0.08, 0.15, "2015-01-01"),
    ("AGG", "yahoo", "ETF", "Bond", "US", "United States", "USD", "BlackRock", 0.03, "", 0.02, 0.05, "2015-01-01"),
]

FX_LEVELS = {"USD": 1.0, "EUR": 1.08, "VND": 1 / 25000, "JPY": 1 / 150}


def build(out_dir: str, seed: int = 11) -> None:
    os.makedirs(out_dir, exist_ok=True)
    rng = np.random.default_rng(seed)
    dates = pd.bdate_range("2015-01-01", "2026-08-28")

    prices, volume, rows = {}, {}, []
    for (tk, source, kind, aclass, region, country, ccy, issuer, ter, bench,
         drift, vol, start) in SPECS:
        idx = dates[dates >= start]
        steps = rng.normal(drift / 252, vol / np.sqrt(252), len(idx))
        level = 100.0 * (1 + FX_LEVELS[ccy]) ** 0  # start every series at 100 units
        series = pd.Series(level * np.exp(np.cumsum(steps)), index=idx)
        prices[tk] = series
        volume[tk] = pd.Series(rng.integers(1e4, 1e6, len(idx)), index=idx)
        rows.append(dict(ticker=tk, source=source, symbol=tk, name=f"{tk} test fund",
                         kind=kind, asset_class=aclass, region=region, country=country,
                         currency=ccy, issuer=issuer, ter=ter, benchmark=bench,
                         category="Broad Market", inception=start,
                         first_date=str(idx[0].date()), last_date=str(idx[-1].date()),
                         observations=len(idx), stale_days=0))

    px = pd.concat(prices, axis=1).sort_index()
    px.index.name = "Date"
    vol_df = pd.concat(volume, axis=1).sort_index()
    vol_df.index.name = "Date"
    profile = pd.DataFrame(rows)

    fx = pd.DataFrame(index=dates)
    for ccy, level in FX_LEVELS.items():
        drift = rng.normal(0, 0.002, len(dates)).cumsum()
        fx[ccy] = level * np.exp(drift) if ccy != "USD" else 1.0
    fx.index.name = "Date"

    px.to_csv(os.path.join(out_dir, "prices.csv"))
    vol_df.to_csv(os.path.join(out_dir, "volume.csv"))
    profile.to_csv(os.path.join(out_dir, "profile.csv"), index=False)
    fx.to_csv(os.path.join(out_dir, "fx.csv"))
    with open(os.path.join(out_dir, "status.json"), "w", encoding="utf-8") as fh:
        json.dump({"instruments": px.shape[1], "last_date": str(px.index[-1].date()),
                   "failed": [], "warnings": [], "stale": []}, fh, indent=2)


if __name__ == "__main__":
    import sys
    build(sys.argv[1] if len(sys.argv) > 1 else "data")
    print("fixture written")
