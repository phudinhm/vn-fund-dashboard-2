"""
Analytics engine for the global ETF report.

Everything the report shows is computed here from a wide price frame
(``DataFrame`` indexed by date, one column per instrument). The module is pure
pandas/numpy so it can be unit tested without Streamlit.

Groups of functions
-------------------
currency        FX normalisation so funds from different markets are comparable
core            returns, drawdowns, annualised risk & return, ratios
tail risk       VaR / CVaR / skew / kurtosis / Ulcer index / tail ratio
relative        beta, alpha, tracking error, information ratio, capture ratios
time slicing    period returns, calendar years, monthly matrix, rolling windows
strategy        DCA, lump sum vs DCA, rebalanced portfolios, fee erosion
scoring         composite ranking across every dimension
"""

from __future__ import annotations

import numpy as np
import pandas as pd

TRADING_DAYS = 252
PERIODS = ["1M", "3M", "6M", "YTD", "1Y", "3Y", "5Y", "10Y", "MAX"]


# ===========================================================================
# currency
# ===========================================================================

def convert_prices(prices: pd.DataFrame, profile: pd.DataFrame, fx: pd.DataFrame,
                   target: str = "USD") -> pd.DataFrame:
    """Convert every column of ``prices`` into ``target`` currency.

    ``fx`` holds the USD value of one unit of each currency (column per ISO
    code). Instruments already quoted in ``target`` are returned untouched, and
    a missing FX series leaves the column in its local currency (the caller
    surfaces that through the data-quality panel).
    """
    if fx is None or fx.empty or profile is None or profile.empty:
        return prices
    if target not in fx.columns:
        return prices

    ccy = profile.set_index("ticker")["currency"].to_dict()
    fx_daily = fx.reindex(prices.index).ffill().bfill()
    target_rate = fx_daily[target]

    out = {}
    for col in prices.columns:
        c = ccy.get(col, target)
        if c == target or c not in fx_daily.columns:
            out[col] = prices[col]
            continue
        out[col] = prices[col] * fx_daily[c] / target_rate
    return pd.DataFrame(out, index=prices.index)


def unconverted_tickers(prices: pd.DataFrame, profile: pd.DataFrame,
                        fx: pd.DataFrame, target: str) -> list[str]:
    if fx is None or fx.empty:
        return [c for c in prices.columns]
    ccy = profile.set_index("ticker")["currency"].to_dict()
    return [c for c in prices.columns
            if ccy.get(c, target) != target and ccy.get(c, target) not in fx.columns]


# ===========================================================================
# core
# ===========================================================================

def daily_returns(prices: pd.DataFrame | pd.Series) -> pd.DataFrame | pd.Series:
    return prices.pct_change(fill_method=None)


def cumulative_growth(prices: pd.DataFrame, base: float = 100.0) -> pd.DataFrame:
    """Rebased wealth curve; every series starts at ``base`` on its own first
    valid observation inside the window."""
    first = prices.apply(lambda s: s.dropna().iloc[0] if s.notna().any() else np.nan)
    return prices.div(first) * base


def drawdown(prices: pd.DataFrame | pd.Series) -> pd.DataFrame | pd.Series:
    roll_max = prices.cummax()
    return (prices - roll_max) / roll_max


def max_drawdown(prices: pd.Series) -> float:
    dd = drawdown(prices.dropna())
    return float(dd.min()) if not dd.empty else np.nan


def cagr(prices: pd.Series) -> float:
    s = prices.dropna()
    if len(s) < 2:
        return np.nan
    years = (s.index[-1] - s.index[0]).days / 365.25
    if years <= 0 or s.iloc[0] <= 0:
        return np.nan
    return float((s.iloc[-1] / s.iloc[0]) ** (1 / years) - 1)


def total_return(prices: pd.Series) -> float:
    s = prices.dropna()
    if len(s) < 2 or s.iloc[0] == 0:
        return np.nan
    return float(s.iloc[-1] / s.iloc[0] - 1)


def annual_volatility(ret: pd.Series) -> float:
    r = ret.dropna()
    return float(r.std() * np.sqrt(TRADING_DAYS)) if len(r) > 2 else np.nan


def downside_deviation(ret: pd.Series, mar: float = 0.0) -> float:
    r = ret.dropna()
    neg = r[r < mar]
    return float(neg.std() * np.sqrt(TRADING_DAYS)) if len(neg) > 2 else np.nan


def sharpe(prices: pd.Series, rf: float = 0.0) -> float:
    r = daily_returns(prices).dropna()
    vol = annual_volatility(r)
    g = cagr(prices)
    if not vol or np.isnan(vol) or vol == 0 or np.isnan(g):
        return np.nan
    return float((g - rf) / vol)


def sortino(prices: pd.Series, rf: float = 0.0) -> float:
    r = daily_returns(prices).dropna()
    dd = downside_deviation(r)
    g = cagr(prices)
    if not dd or np.isnan(dd) or dd == 0 or np.isnan(g):
        return np.nan
    return float((g - rf) / dd)


def calmar(prices: pd.Series) -> float:
    mdd = max_drawdown(prices)
    g = cagr(prices)
    if np.isnan(mdd) or mdd == 0 or np.isnan(g):
        return np.nan
    return float(g / abs(mdd))


def omega(ret: pd.Series, threshold: float = 0.0) -> float:
    r = ret.dropna() - threshold / TRADING_DAYS
    gains, losses = r[r > 0].sum(), -r[r < 0].sum()
    return float(gains / losses) if losses > 0 else np.nan


def ulcer_index(prices: pd.Series) -> float:
    dd = drawdown(prices.dropna()) * 100
    return float(np.sqrt((dd ** 2).mean())) if not dd.empty else np.nan


def martin_ratio(prices: pd.Series, rf: float = 0.0) -> float:
    ui = ulcer_index(prices)
    g = cagr(prices)
    if not ui or np.isnan(ui) or ui == 0 or np.isnan(g):
        return np.nan
    return float((g - rf) * 100 / ui)


def stability(prices: pd.Series) -> float:
    """R^2 of a linear fit through the log equity curve (trend consistency)."""
    s = prices.dropna()
    if len(s) < 10 or (s <= 0).any():
        return np.nan
    y = np.log(s.values)
    x = np.arange(len(y))
    corr = np.corrcoef(x, y)[0, 1]
    return float(corr ** 2)


# ===========================================================================
# tail risk
# ===========================================================================

def value_at_risk(ret: pd.Series, level: float = 0.95) -> float:
    r = ret.dropna()
    return float(np.percentile(r, (1 - level) * 100)) if len(r) > 10 else np.nan


def conditional_var(ret: pd.Series, level: float = 0.95) -> float:
    r = ret.dropna()
    if len(r) < 10:
        return np.nan
    var = np.percentile(r, (1 - level) * 100)
    tail = r[r <= var]
    return float(tail.mean()) if len(tail) else np.nan


def tail_ratio(ret: pd.Series) -> float:
    r = ret.dropna()
    if len(r) < 20:
        return np.nan
    left = abs(np.percentile(r, 5))
    right = abs(np.percentile(r, 95))
    return float(right / left) if left > 0 else np.nan


def drawdown_episodes(prices: pd.Series, top: int = 5) -> pd.DataFrame:
    """The deepest drawdown episodes with peak / trough / recovery dates."""
    s = prices.dropna()
    if len(s) < 3:
        return pd.DataFrame(columns=["peak", "trough", "recovery", "depth",
                                     "length_days", "recovery_days"])
    dd = drawdown(s)
    episodes, in_dd, peak_date = [], False, None
    for date, value in dd.items():
        if not in_dd and value < 0:
            in_dd, peak_date = True, date
        elif in_dd and value >= 0:
            window = dd.loc[peak_date:date]
            trough_date = window.idxmin()
            episodes.append({
                "peak": peak_date, "trough": trough_date, "recovery": date,
                "depth": float(window.min()),
                "length_days": int((date - peak_date).days),
                "recovery_days": int((date - trough_date).days),
            })
            in_dd = False
    if in_dd and peak_date is not None:
        window = dd.loc[peak_date:]
        episodes.append({
            "peak": peak_date, "trough": window.idxmin(), "recovery": pd.NaT,
            "depth": float(window.min()),
            "length_days": int((s.index[-1] - peak_date).days),
            "recovery_days": np.nan,
        })
    if not episodes:
        return pd.DataFrame(columns=["peak", "trough", "recovery", "depth",
                                     "length_days", "recovery_days"])
    return (pd.DataFrame(episodes).sort_values("depth").head(top).reset_index(drop=True))


# ===========================================================================
# relative to a benchmark
# ===========================================================================

def _aligned(a: pd.Series, b: pd.Series) -> pd.DataFrame:
    return pd.concat([a.rename("a"), b.rename("b")], axis=1, sort=True).dropna()


def beta_alpha(asset_ret: pd.Series, bench_ret: pd.Series, rf: float = 0.0) -> tuple[float, float, float]:
    """(beta, annualised Jensen alpha, R^2)."""
    df = _aligned(asset_ret, bench_ret)
    if len(df) < 20:
        return np.nan, np.nan, np.nan
    var = df["b"].var()
    if var == 0:
        return np.nan, np.nan, np.nan
    beta = float(df["a"].cov(df["b"]) / var)
    rf_d = rf / TRADING_DAYS
    alpha = float(((df["a"] - rf_d) - beta * (df["b"] - rf_d)).mean() * TRADING_DAYS)
    r2 = float(df["a"].corr(df["b"]) ** 2)
    return beta, alpha, r2


def tracking_error(asset_ret: pd.Series, bench_ret: pd.Series) -> float:
    df = _aligned(asset_ret, bench_ret)
    if len(df) < 20:
        return np.nan
    return float((df["a"] - df["b"]).std() * np.sqrt(TRADING_DAYS))


def information_ratio(asset_ret: pd.Series, bench_ret: pd.Series) -> float:
    df = _aligned(asset_ret, bench_ret)
    if len(df) < 20:
        return np.nan
    diff = df["a"] - df["b"]
    te = diff.std() * np.sqrt(TRADING_DAYS)
    return float(diff.mean() * TRADING_DAYS / te) if te else np.nan


def rolling_tracking_error(asset_ret: pd.Series, bench_ret: pd.Series,
                           window: int = 63) -> pd.Series:
    diff = (asset_ret - bench_ret).dropna()
    return diff.rolling(window).std() * np.sqrt(TRADING_DAYS) * 100


def rolling_beta(asset_ret: pd.Series, bench_ret: pd.Series, window: int = 126) -> pd.Series:
    df = _aligned(asset_ret, bench_ret)
    cov = df["a"].rolling(window).cov(df["b"])
    var = df["b"].rolling(window).var()
    return (cov / var).replace([np.inf, -np.inf], np.nan)


def capture_ratios(asset_ret: pd.Series, bench_ret: pd.Series) -> tuple[float, float]:
    """(upside capture, downside capture) in %, geometric."""
    df = _aligned(asset_ret, bench_ret)
    if len(df) < 20:
        return np.nan, np.nan
    out = []
    for mask in (df["b"] > 0, df["b"] < 0):
        sub = df[mask]
        if len(sub) < 5:
            out.append(np.nan)
            continue
        a = (1 + sub["a"]).prod() ** (1 / len(sub)) - 1
        b = (1 + sub["b"]).prod() ** (1 / len(sub)) - 1
        out.append(float(a / b * 100) if b != 0 else np.nan)
    return out[0], out[1]


def batting_average(asset_ret: pd.Series, bench_ret: pd.Series) -> float:
    """Share of days the fund beats its benchmark."""
    df = _aligned(asset_ret, bench_ret)
    return float((df["a"] > df["b"]).mean() * 100) if len(df) >= 20 else np.nan


# ===========================================================================
# time slicing
# ===========================================================================

def period_start(end: pd.Timestamp, period: str, first: pd.Timestamp) -> pd.Timestamp:
    if period == "MAX":
        return first
    if period == "YTD":
        return pd.Timestamp(year=end.year, month=1, day=1)
    months = {"1M": 1, "3M": 3, "6M": 6, "1Y": 12, "3Y": 36, "5Y": 60, "10Y": 120}
    return end - pd.DateOffset(months=months.get(period, 12))


def period_returns(prices: pd.DataFrame, annualise_from_years: float = 1.5) -> pd.DataFrame:
    """Total return per period; periods longer than ~1.5y are annualised."""
    end = prices.index.max()
    rows = {}
    for period in PERIODS:
        start = period_start(end, period, prices.index.min())
        window = prices.loc[prices.index >= start]
        col = {}
        for ticker in prices.columns:
            s = window[ticker].dropna()
            if len(s) < 2:
                col[ticker] = np.nan
                continue
            # a fund without enough history for this window gets no number,
            # so a "10Y" cell never quietly shows a 3-year track record
            if period not in ("MAX", "YTD"):
                covered = (s.index[0] - start).days
                requested = max((end - start).days, 1)
                if covered / requested > 0.1:
                    col[ticker] = np.nan
                    continue
            years = (s.index[-1] - s.index[0]).days / 365.25
            col[ticker] = cagr(s) if years >= annualise_from_years else total_return(s)
        rows[period] = col
    return pd.DataFrame(rows)


def calendar_year_returns(prices: pd.DataFrame) -> pd.DataFrame:
    """Return per calendar year (rows = years, columns = instruments)."""
    out = {}
    for ticker in prices.columns:
        s = prices[ticker].dropna()
        if s.empty:
            continue
        year_end = s.resample("YE").last()
        # base = previous year-end close; for the first (partial) year use the
        # first observation so a fund launched mid-year is not misread
        base = year_end.shift(1)
        base.iloc[0] = s.iloc[0]
        ret = (year_end / base) - 1
        ret.index = ret.index.year
        out[ticker] = ret
    frame = pd.DataFrame(out)
    frame.index.name = "year"
    return frame


def monthly_returns(prices: pd.Series) -> pd.DataFrame:
    """Year x month matrix of monthly returns (%)."""
    s = prices.dropna()
    if s.empty:
        return pd.DataFrame()
    m = s.resample("ME").last().pct_change(fill_method=None) * 100
    frame = pd.DataFrame({"year": m.index.year, "month": m.index.month, "ret": m.values})
    return frame.pivot_table(index="year", columns="month", values="ret")


def rolling_returns(prices: pd.Series, years: float = 1.0) -> pd.Series:
    """Annualised return of every rolling window of ``years`` length."""
    s = prices.dropna()
    window = max(int(years * TRADING_DAYS), 5)
    if len(s) <= window:
        return pd.Series(dtype=float)
    roll = (s / s.shift(window)) ** (1 / years) - 1
    return roll.dropna()


def rolling_return_stats(prices: pd.Series, years: float = 1.0) -> dict:
    r = rolling_returns(prices, years)
    if r.empty:
        return {"windows": 0, "mean": np.nan, "median": np.nan, "min": np.nan,
                "max": np.nan, "win_rate": np.nan, "p05": np.nan, "p95": np.nan}
    return {
        "windows": int(len(r)), "mean": float(r.mean()), "median": float(r.median()),
        "min": float(r.min()), "max": float(r.max()),
        "win_rate": float((r > 0).mean() * 100),
        "p05": float(np.percentile(r, 5)), "p95": float(np.percentile(r, 95)),
    }


def rolling_volatility(ret: pd.Series, window: int = 63) -> pd.Series:
    return ret.rolling(window).std() * np.sqrt(TRADING_DAYS) * 100


def rolling_correlation(a: pd.Series, b: pd.Series, window: int = 126) -> pd.Series:
    df = _aligned(a, b)
    return df["a"].rolling(window).corr(df["b"])


# ===========================================================================
# metric table
# ===========================================================================

def metrics_table(prices: pd.DataFrame, benchmark: str | None = None,
                  rf: float = 0.0, profile: pd.DataFrame | None = None) -> pd.DataFrame:
    """One row per instrument with the full metric set."""
    bench_ret = None
    if benchmark and benchmark in prices.columns:
        bench_ret = daily_returns(prices[benchmark])

    meta = profile.set_index("ticker") if profile is not None and not profile.empty else None
    rows = []
    for ticker in prices.columns:
        s = prices[ticker].dropna()
        if len(s) < 5:
            continue
        r = daily_returns(s)
        row = {
            "ticker": ticker,
            "total_return": total_return(s),
            "cagr": cagr(s),
            "volatility": annual_volatility(r),
            "downside_dev": downside_deviation(r),
            "max_drawdown": max_drawdown(s),
            "sharpe": sharpe(s, rf),
            "sortino": sortino(s, rf),
            "calmar": calmar(s),
            "omega": omega(r),
            "ulcer": ulcer_index(s),
            "martin": martin_ratio(s, rf),
            "stability": stability(s),
            "var95": value_at_risk(r, 0.95),
            "cvar95": conditional_var(r, 0.95),
            "skew": float(r.skew()) if len(r.dropna()) > 5 else np.nan,
            "kurtosis": float(r.kurtosis()) if len(r.dropna()) > 5 else np.nan,
            "tail_ratio": tail_ratio(r),
            "hit_rate": float((r.dropna() > 0).mean() * 100) if r.notna().any() else np.nan,
            "best_day": float(r.max()) if r.notna().any() else np.nan,
            "worst_day": float(r.min()) if r.notna().any() else np.nan,
            "observations": int(len(s)),
            "first_date": s.index.min(),
            "last_date": s.index.max(),
        }
        if bench_ret is not None and ticker != benchmark:
            b, a, r2 = beta_alpha(r, bench_ret, rf)
            up, down = capture_ratios(r, bench_ret)
            row.update({
                "beta": b, "alpha": a, "r_squared": r2,
                "tracking_error": tracking_error(r, bench_ret),
                "information_ratio": information_ratio(r, bench_ret),
                "up_capture": up, "down_capture": down,
                "capture_spread": (up - down) if not (np.isnan(up) or np.isnan(down)) else np.nan,
                "batting_average": batting_average(r, bench_ret),
            })
        else:
            row.update({"beta": np.nan, "alpha": np.nan, "r_squared": np.nan,
                        "tracking_error": np.nan, "information_ratio": np.nan,
                        "up_capture": np.nan, "down_capture": np.nan,
                        "capture_spread": np.nan, "batting_average": np.nan})
        if meta is not None and ticker in meta.index:
            m = meta.loc[ticker]
            row.update({
                "name": m.get("name", ticker), "kind": m.get("kind", ""),
                "region": m.get("region", ""), "country": m.get("country", ""),
                "currency": m.get("currency", ""), "issuer": m.get("issuer", ""),
                "asset_class": m.get("asset_class", ""), "category": m.get("category", ""),
                "ter": m.get("ter", np.nan), "benchmark_ref": m.get("benchmark", ""),
            })
        rows.append(row)
    df = pd.DataFrame(rows)
    return df.set_index("ticker") if not df.empty else df


# ===========================================================================
# scoring
# ===========================================================================

SCORE_WEIGHTS = {
    "cagr": 0.25, "sharpe": 0.20, "sortino": 0.15, "calmar": 0.10,
    "max_drawdown": 0.10, "volatility": 0.10, "information_ratio": 0.05,
    "ter": 0.05,
}
# metrics where lower is better
_LOWER_IS_BETTER = {"volatility", "ter"}


def _zscore(s: pd.Series) -> pd.Series:
    s = pd.to_numeric(s, errors="coerce")
    if s.notna().sum() < 2 or s.std(skipna=True) in (0, np.nan):
        return pd.Series(0.0, index=s.index)
    return (s - s.mean(skipna=True)) / s.std(skipna=True)


def composite_score(metrics: pd.DataFrame,
                    weights: dict | None = None) -> pd.DataFrame:
    """Weighted z-score ranking across every risk / return dimension.

    ``max_drawdown`` is negative, so a shallower drawdown is already a higher
    z-score; ``volatility`` and ``ter`` are inverted explicitly.
    """
    weights = weights or SCORE_WEIGHTS
    if metrics.empty:
        return metrics
    score = pd.Series(0.0, index=metrics.index)
    used = 0.0
    for metric, weight in weights.items():
        if metric not in metrics.columns:
            continue
        col = pd.to_numeric(metrics[metric], errors="coerce")
        if col.notna().sum() < 2:
            continue
        z = _zscore(col)
        if metric in _LOWER_IS_BETTER:
            z = -z
        score += z.fillna(0.0) * weight
        used += weight
    out = metrics.copy()
    out["score"] = score / used if used else np.nan
    out["rank"] = out["score"].rank(ascending=False, method="min")
    return out.sort_values("score", ascending=False)


# ===========================================================================
# strategy lab
# ===========================================================================

def simulate_dca(prices: pd.Series, contribution: float = 1000.0,
                 freq: str = "ME") -> pd.DataFrame:
    """Buy ``contribution`` worth of the fund on the first trading day of every
    period (``freq`` follows pandas offset aliases: ``ME`` monthly, ``W`` weekly)."""
    s = prices.dropna()
    if len(s) < 2:
        return pd.DataFrame()
    buy_dates = set(s.groupby(s.index.to_period(_freq_to_period(freq))).apply(
        lambda g: g.index[0]).values)
    units, invested, rows = 0.0, 0.0, []
    for date, price in s.items():
        if np.datetime64(date) in buy_dates and price > 0:
            units += contribution / price
            invested += contribution
        rows.append({"date": date, "invested": invested, "value": units * price})
    df = pd.DataFrame(rows).set_index("date")
    df["profit"] = df["value"] - df["invested"]
    df["return"] = np.where(df["invested"] > 0, df["profit"] / df["invested"], 0.0)
    return df


def _freq_to_period(freq: str) -> str:
    return {"ME": "M", "M": "M", "W": "W", "QE": "Q", "Q": "Q", "YE": "Y", "Y": "Y"}.get(freq, "M")


def dca_vs_lumpsum(prices: pd.Series, months: int = 12,
                   amount: float = 12000.0) -> dict:
    """Compare investing everything at the start against spreading it out."""
    s = prices.dropna()
    if len(s) < TRADING_DAYS:
        return {}
    lump_units = amount / s.iloc[0]
    lump_value = lump_units * s.iloc[-1]

    monthly = s.resample("ME").last()
    slots = monthly.iloc[:months]
    per = amount / max(len(slots), 1)
    dca_units = sum(per / p for p in slots.values if p > 0)
    dca_value = dca_units * s.iloc[-1]
    return {
        "lump_sum_value": float(lump_value),
        "dca_value": float(dca_value),
        "lump_sum_return": float(lump_value / amount - 1),
        "dca_return": float(dca_value / amount - 1),
        "lump_sum_wins": bool(lump_value > dca_value),
        "spread_months": int(len(slots)),
    }


def rolling_dca_vs_lumpsum(prices: pd.Series, hold_years: int = 5,
                           spread_months: int = 12, step: int = 21) -> dict:
    """Roll the comparison over history: how often does lump sum win?"""
    s = prices.dropna()
    hold_days = int(hold_years * TRADING_DAYS)
    if len(s) < hold_days + 30:
        return {"windows": 0, "lump_sum_win_rate": np.nan,
                "median_lump": np.nan, "median_dca": np.nan}
    lump_wins, lumps, dcas = 0, [], []
    for start in range(0, len(s) - hold_days, step):
        window = s.iloc[start:start + hold_days]
        res = dca_vs_lumpsum(window, months=spread_months)
        if not res:
            continue
        lumps.append(res["lump_sum_return"])
        dcas.append(res["dca_return"])
        lump_wins += int(res["lump_sum_wins"])
    n = len(lumps)
    if n == 0:
        return {"windows": 0, "lump_sum_win_rate": np.nan,
                "median_lump": np.nan, "median_dca": np.nan}
    return {
        "windows": n,
        "lump_sum_win_rate": float(lump_wins / n * 100),
        "median_lump": float(np.median(lumps)),
        "median_dca": float(np.median(dcas)),
    }


def rebalanced_portfolio(prices: pd.DataFrame, weights: dict,
                         freq: str = "QE") -> pd.Series:
    """Wealth curve of a periodically rebalanced portfolio (base = 100)."""
    cols = [c for c in weights if c in prices.columns]
    if not cols:
        return pd.Series(dtype=float)
    px = prices[cols].dropna()
    if px.empty:
        return pd.Series(dtype=float)
    w = np.array([weights[c] for c in cols], dtype=float)
    w = w / w.sum()
    rebal_dates = set(px.resample(freq).last().index)

    value, units = 100.0, (100.0 * w) / px.iloc[0].values
    out = {px.index[0]: value}
    for date in px.index[1:]:
        value = float((units * px.loc[date].values).sum())
        out[date] = value
        if date in rebal_dates:
            units = (value * w) / px.loc[date].values
    return pd.Series(out).sort_index()


def fee_erosion(initial: float, gross_return: float, ter: float,
                years: int = 20) -> pd.DataFrame:
    """Wealth with and without the annual expense ratio."""
    rows = []
    for year in range(years + 1):
        gross = initial * (1 + gross_return) ** year
        net = initial * (1 + gross_return - ter) ** year
        rows.append({"year": year, "gross": gross, "net": net, "lost": gross - net})
    return pd.DataFrame(rows)


def efficient_frontier(prices: pd.DataFrame, simulations: int = 3000,
                       rf: float = 0.0, seed: int = 42) -> pd.DataFrame:
    """Random long-only portfolios of the given instruments."""
    px = prices.dropna(how="all")
    cols = [c for c in px.columns if px[c].notna().sum() > TRADING_DAYS // 2]
    if len(cols) < 2:
        return pd.DataFrame()
    rets = daily_returns(px[cols]).dropna()
    if rets.empty:
        return pd.DataFrame()
    mean, cov = rets.mean() * TRADING_DAYS, rets.cov() * TRADING_DAYS
    rng = np.random.default_rng(seed)
    w = rng.random((simulations, len(cols)))
    w /= w.sum(axis=1, keepdims=True)
    port_ret = w @ mean.values
    port_vol = np.sqrt(np.einsum("ij,jk,ik->i", w, cov.values, w))
    out = pd.DataFrame({"return": port_ret, "volatility": port_vol})
    out["sharpe"] = np.where(out.volatility > 0, (out["return"] - rf) / out.volatility, np.nan)
    for i, col in enumerate(cols):
        out[f"w_{col}"] = w[:, i]
    return out


def correlation_matrix(prices: pd.DataFrame, method: str = "pearson") -> pd.DataFrame:
    return daily_returns(prices).corr(method=method)


def diversification_score(corr: pd.DataFrame) -> float:
    """Average pairwise correlation (lower = better diversified)."""
    if corr.empty or corr.shape[0] < 2:
        return np.nan
    m = corr.to_numpy(dtype=float, copy=True)
    iu = np.triu_indices_from(m, k=1)
    vals = m[iu]
    vals = vals[~np.isnan(vals)]
    return float(vals.mean()) if vals.size else np.nan


# ===========================================================================
# regimes & forecast
# ===========================================================================

def bull_bear_split(asset_ret: pd.Series, bench_ret: pd.Series) -> dict:
    df = _aligned(asset_ret, bench_ret)
    if df.empty:
        return {"bull": np.nan, "bear": np.nan, "bull_days": 0, "bear_days": 0}
    bull = df[df["b"] > 0]["a"]
    bear = df[df["b"] < 0]["a"]
    return {
        "bull": float(bull.mean() * TRADING_DAYS) if len(bull) else np.nan,
        "bear": float(bear.mean() * TRADING_DAYS) if len(bear) else np.nan,
        "bull_days": int(len(bull)), "bear_days": int(len(bear)),
    }


def monte_carlo(prices: pd.Series, days: int = 60, simulations: int = 1000,
                seed: int = 7) -> dict:
    s = prices.dropna()
    r = daily_returns(s).dropna()
    if len(r) < 30:
        return {}
    rng = np.random.default_rng(seed)
    mu, sigma = r.mean(), r.std()
    shocks = rng.normal(mu, sigma, (days, simulations))
    paths = np.zeros_like(shocks)
    paths[0] = s.iloc[-1] * (1 + shocks[0])
    for i in range(1, days):
        paths[i] = paths[i - 1] * (1 + shocks[i])
    final = paths[-1]
    return {
        "paths": paths,
        "last_price": float(s.iloc[-1]),
        "prob_up": float((final > s.iloc[-1]).mean() * 100),
        "median": float(np.median(final)),
        "p05": float(np.percentile(final, 5)),
        "p95": float(np.percentile(final, 95)),
        "expected_return": float(np.median(final) / s.iloc[-1] - 1),
    }


def ets_forecast(prices: pd.Series, days: int = 60) -> pd.Series:
    s = prices.dropna()
    if len(s) < 60:
        return pd.Series(dtype=float)
    try:
        from statsmodels.tsa.holtwinters import ExponentialSmoothing
        ts = s.asfreq("B").ffill()
        model = ExponentialSmoothing(ts, trend="add", damped_trend=True,
                                     seasonal=None).fit()
        return model.forecast(days)
    except Exception:
        last = float(s.iloc[-1])
        idx = pd.bdate_range(s.index[-1] + pd.Timedelta(days=1), periods=days)
        return pd.Series([last] * days, index=idx)
