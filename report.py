"""
Headless report layer: dataset loading, fact extraction and Markdown export.

Kept free of Streamlit so it can be unit tested and re-used from a script
(``python report.py --lang DE > report_de.md`` writes the whole report as text).
"""

from __future__ import annotations

import argparse
import json
import os
from dataclasses import dataclass, field

import numpy as np
import pandas as pd

import analytics as an
import i18n
import universe as uni

ROOT = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(ROOT, "data")

RANGES = ["3M", "6M", "YTD", "1Y", "3Y", "5Y", "10Y", "MAX"]


@dataclass
class Dataset:
    prices: pd.DataFrame
    volume: pd.DataFrame
    profile: pd.DataFrame
    fx: pd.DataFrame
    status: dict = field(default_factory=dict)
    legacy: bool = False

    @property
    def last_date(self) -> pd.Timestamp:
        return self.prices.index.max()

    @property
    def markets(self) -> int:
        return int(self.profile["country"].nunique()) if "country" in self.profile else 0

    @property
    def currencies(self) -> int:
        return int(self.profile["currency"].nunique()) if "currency" in self.profile else 0


def _read_csv(path: str, **kw) -> pd.DataFrame:
    return pd.read_csv(path, **kw) if os.path.exists(path) else pd.DataFrame()


def load_dataset(data_dir: str = DATA_DIR, root: str = ROOT) -> Dataset | None:
    """Load the global dataset, falling back to the legacy Vietnam-only files.

    The fallback keeps the report usable in a fresh clone before the daily
    GitHub Action has produced ``data/prices.csv``.
    """
    prices = _read_csv(os.path.join(data_dir, "prices.csv"),
                       parse_dates=["Date"], index_col="Date")
    if not prices.empty:
        volume = _read_csv(os.path.join(data_dir, "volume.csv"),
                           parse_dates=["Date"], index_col="Date")
        profile = _read_csv(os.path.join(data_dir, "profile.csv"))
        fx = _read_csv(os.path.join(data_dir, "fx.csv"),
                       index_col=0, parse_dates=True)
        status = {}
        status_path = os.path.join(data_dir, "status.json")
        if os.path.exists(status_path):
            with open(status_path, encoding="utf-8") as fh:
                status = json.load(fh)
        return Dataset(prices.sort_index(), volume, profile, fx, status, legacy=False)

    # ---- legacy Vietnam-only layout -------------------------------------
    prices = _read_csv(os.path.join(root, "funds_data.csv"),
                       parse_dates=["Date"], index_col="Date")
    if prices.empty:
        return None
    volume = _read_csv(os.path.join(root, "funds_volume.csv"),
                       parse_dates=["Date"], index_col="Date")
    static = uni.static_universe()
    profile = static[static.ticker.isin(prices.columns)].copy()
    missing = [c for c in prices.columns if c not in set(profile.ticker)]
    if missing:
        extra = pd.DataFrame([{
            "ticker": c, "source": "vndirect", "symbol": c, "name": c, "kind": "ETF",
            "asset_class": "Equity", "region": "Vietnam", "country": "Vietnam",
            "currency": "VND", "issuer": "-", "ter": np.nan, "benchmark": "VNINDEX",
            "category": "", "inception": "",
        } for c in missing])
        profile = pd.concat([profile, extra], ignore_index=True)
    return Dataset(prices.sort_index(), volume, profile.reset_index(drop=True),
                   pd.DataFrame(), {}, legacy=True)


# ---------------------------------------------------------------------------
# selection helpers
# ---------------------------------------------------------------------------

def slice_window(prices: pd.DataFrame, period: str) -> pd.DataFrame:
    end = prices.index.max()
    start = an.period_start(end, period, prices.index.min())
    return prices.loc[prices.index >= start]


def default_selection(profile: pd.DataFrame, prices: pd.DataFrame,
                      limit: int = 6) -> list[str]:
    """A sensible opening comparison: Vietnam, US, Europe, world, gold."""
    wish = ["VNINDEX", "E1VFVN30", "FUEVFVND", "SPY", "EUNL.DE", "VNM", "GLD"]
    picked = [t for t in wish if t in prices.columns][:limit]
    if picked:
        return picked
    return list(prices.columns[:limit])


def presets(profile: pd.DataFrame, prices: pd.DataFrame) -> dict[str, list[str]]:
    p = profile[profile.ticker.isin(prices.columns)]

    def pick(mask, n=12):
        return p[mask].ticker.tolist()[:n]

    return {
        "preset_vn": pick((p.region == "Vietnam") & (p.kind == "ETF")),
        "preset_global": pick((p.region == "Global") & (p.kind == "ETF")),
        "preset_us": pick((p.region == "US") & (p.kind == "ETF")),
        "preset_europe": pick((p.region == "Europe") & (p.kind == "ETF")),
        "preset_asia": pick((p.region == "Asia-Pacific") & (p.kind == "ETF")),
        "preset_index": pick(p.kind == "Index"),
        "preset_bond": pick(p.asset_class.isin(["Bond", "Commodity"])),
        "preset_mutual": pick(p.kind == "Mutual Fund"),
    }


# ---------------------------------------------------------------------------
# facts for the automated commentary
# ---------------------------------------------------------------------------

def build_facts(window: pd.DataFrame, metrics: pd.DataFrame, benchmark: str,
                currency: str) -> dict:
    if metrics.empty:
        return {}
    # only rank instruments that actually span the window (see analytics.comparable)
    metrics = an.comparable(metrics)
    cagr = metrics["cagr"].dropna()
    if cagr.empty:
        return {}
    bench_cagr = float(metrics.loc[benchmark, "cagr"]) if benchmark in metrics.index else np.nan
    sharpe = metrics["sharpe"].dropna()
    dd = metrics["max_drawdown"].dropna()
    corr = an.correlation_matrix(window)
    return {
        "start": window.index.min().strftime("%d.%m.%Y"),
        "end": window.index.max().strftime("%d.%m.%Y"),
        "currency": currency,
        "benchmark": benchmark,
        "benchmark_cagr": bench_cagr,
        "best": cagr.idxmax(), "best_cagr": float(cagr.max()),
        "worst": cagr.idxmin(), "worst_cagr": float(cagr.min()),
        "best_sharpe": sharpe.idxmax() if not sharpe.empty else "n/a",
        "best_sharpe_value": float(sharpe.max()) if not sharpe.empty else np.nan,
        "deepest_dd": dd.idxmin() if not dd.empty else "n/a",
        "deepest_dd_value": float(dd.min()) if not dd.empty else np.nan,
        "beat_count": int((cagr > bench_cagr).sum()) if not np.isnan(bench_cagr) else 0,
        "total": int(len(cagr)),
        "avg_corr": an.diversification_score(corr),
    }


def region_performance(window: pd.DataFrame, profile: pd.DataFrame) -> pd.DataFrame:
    """Average CAGR and volatility per region, for the global-markets view."""
    meta = profile.set_index("ticker")
    rows = []
    for ticker in window.columns:
        if ticker not in meta.index:
            continue
        s = window[ticker].dropna()
        if len(s) < 30:
            continue
        rows.append({
            "region": meta.loc[ticker, "region"],
            "country": meta.loc[ticker, "country"],
            "kind": meta.loc[ticker, "kind"],
            "ticker": ticker,
            "cagr": an.cagr(s),
            "volatility": an.annual_volatility(an.daily_returns(s)),
            "max_drawdown": an.max_drawdown(s),
        })
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Markdown export
# ---------------------------------------------------------------------------

def _fmt_pct(x, digits=2):
    return "n/a" if x is None or (isinstance(x, float) and np.isnan(x)) else f"{x * 100:.{digits}f}%"


def markdown_report(lang: str, ds: Dataset, tickers: list[str], period: str,
                    benchmark: str, currency: str, rf: float = 0.0) -> str:
    T = lambda k: i18n.t(lang, k)
    prices = an.convert_prices(ds.prices[tickers], ds.profile, ds.fx, currency)
    window = slice_window(prices, period)
    metrics = an.metrics_table(window, benchmark=benchmark, rf=rf, profile=ds.profile)
    metrics = an.composite_score(metrics)
    facts = build_facts(window, metrics, benchmark, currency)

    lines = [
        f"# {T('app_title')}",
        f"*{T('app_subtitle')}*",
        "",
        f"- {T('data_updated')}: **{ds.last_date:%d.%m.%Y}**",
        f"- {T('time_range')}: **{period}** ({window.index.min():%d.%m.%Y} → {window.index.max():%d.%m.%Y})",
        f"- {T('currency')}: **{currency}** · {T('benchmark')}: **{benchmark}**",
        f"- {T('n_instruments')}: **{len(tickers)}** · {T('n_markets')}: **{ds.markets}** · "
        f"{T('n_currencies')}: **{ds.currencies}**",
        "",
        f"## {T('auto_commentary')}",
        "",
        i18n.summary_narrative(lang, facts) if facts else T("not_enough_data"),
        "",
        f"## {T('h_leaderboard')}",
        "",
    ]

    cols = [("m_rank", "rank"), ("m_name", "name"), ("m_cagr", "cagr"),
            ("m_volatility", "volatility"), ("m_maxdd", "max_drawdown"),
            ("m_sharpe", "sharpe"), ("m_sortino", "sortino"), ("m_calmar", "calmar"),
            ("m_beta", "beta"), ("m_alpha", "alpha"), ("m_te", "tracking_error"),
            ("m_score", "score")]
    header = "| Ticker | " + " | ".join(T(k) for k, _ in cols) + " |"
    lines += [header, "|" + "---|" * (len(cols) + 1)]
    for ticker, row in metrics.iterrows():
        cells = []
        for _, key in cols:
            v = row.get(key, np.nan)
            if key in ("cagr", "volatility", "max_drawdown", "alpha", "tracking_error"):
                cells.append(_fmt_pct(v))
            elif key == "name":
                cells.append(str(v)[:40] if isinstance(v, str) else ticker)
            elif key == "rank":
                cells.append("n/a" if pd.isna(v) else f"{int(v)}")
            else:
                cells.append("n/a" if pd.isna(v) else f"{v:.2f}")
        lines.append(f"| **{ticker}** | " + " | ".join(cells) + " |")

    # period and calendar tables use the full history, not the sliced window,
    # so the 5Y / 10Y columns keep their meaning
    lines += ["", f"## {T('h_period_returns')}", ""]
    per = an.period_returns(prices)
    lines += ["| Ticker | " + " | ".join(per.columns) + " |",
              "|" + "---|" * (len(per.columns) + 1)]
    for ticker, row in per.iterrows():
        lines.append(f"| **{ticker}** | " + " | ".join(_fmt_pct(v, 1) for v in row) + " |")

    lines += ["", f"## {T('h_calendar')}", ""]
    cal = an.calendar_year_returns(prices)
    if not cal.empty:
        years = list(cal.index)[-8:]
        lines += ["| Ticker | " + " | ".join(str(y) for y in years) + " |",
                  "|" + "---|" * (len(years) + 1)]
        for ticker in cal.columns:
            lines.append(f"| **{ticker}** | " +
                         " | ".join(_fmt_pct(cal.loc[y, ticker], 1) for y in years) + " |")

    lines += ["", f"## {T('h_method')}", "", T("x_data").strip(), "",
              f"> {T('footer')}"]
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser(description="Render the ETF report as Markdown")
    ap.add_argument("--lang", default="EN", choices=list(i18n.STRINGS))
    ap.add_argument("--period", default="3Y", choices=RANGES)
    ap.add_argument("--currency", default="USD")
    ap.add_argument("--benchmark", default=None)
    ap.add_argument("--tickers", default=None, help="comma separated")
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    ds = load_dataset()
    if ds is None:
        print("no data")
        return 1
    tickers = (args.tickers.split(",") if args.tickers
               else default_selection(ds.profile, ds.prices))
    tickers = [t for t in tickers if t in ds.prices.columns]
    # a broad global index is the most informative default benchmark; fall back
    # to the Vietnamese market and finally to the first selected instrument
    benchmark = args.benchmark or next(
        (b for b in ("SP500", "VNINDEX") if b in ds.prices.columns), tickers[0])
    if benchmark not in tickers:
        tickers = [benchmark] + tickers
    text = markdown_report(args.lang, ds, tickers, args.period, benchmark, args.currency)
    if args.out:
        with open(args.out, "w", encoding="utf-8") as fh:
            fh.write(text)
        print(f"written: {args.out}")
    else:
        print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
