"""
Fully automatic daily data update for the global ETF report.

Run ``python update_data.py`` (the GitHub Action does this every day). The
script needs no API key and no manual input:

1. Vietnamese ETFs + indices           -> VNDIRECT
2. Vietnamese open-ended funds         -> fmarket.vn catalogue (auto-discovered)
3. World ETFs + world indices          -> Yahoo Finance, Stooq as fallback
4. FX rates for every trading currency -> Yahoo, Frankfurter, er-api fallbacks

Outputs (all committed by the workflow):

    data/prices.csv        wide close prices in local currency, Date x ticker
    data/volume.csv        traded volume where available
    data/profile.csv       one metadata row per instrument + coverage stats
    data/fx.csv            USD value of one unit of each currency, per day
    data/status.json       machine readable health report of the run
    funds_data.csv         legacy Vietnam-only price file (kept for compatibility)
    funds_volume.csv       legacy Vietnam-only volume file
    funds_profile.csv      legacy Vietnam-only profile file
"""

from __future__ import annotations

import json
import os
import sys
import time
from datetime import datetime, timezone

import pandas as pd

import sources
import universe as uni

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
def skip_world() -> bool:
    return os.environ.get("SKIP_WORLD") == "1"


def skip_mutual_funds() -> bool:
    return os.environ.get("SKIP_MUTUAL_FUNDS") == "1"


def max_mutual_funds() -> int:
    return int(os.environ.get("MAX_MUTUAL_FUNDS", "120"))


def log(msg: str) -> None:
    print(msg, flush=True)


# ---------------------------------------------------------------------------
# collectors
# ---------------------------------------------------------------------------

def collect_vietnam(status: dict) -> tuple[dict, dict, list[dict]]:
    prices, volumes, rows = {}, {}, []
    static = uni.static_universe()
    vn = static[static.source == "vndirect"]
    log(f"Vietnam: fetching {len(vn)} listed symbols from VNDIRECT ...")
    for _, meta in vn.iterrows():
        df = sources.fetch_vndirect_multi(uni.vn_symbol_candidates(meta.ticker))
        if df.empty:
            status["failed"].append({"ticker": meta.ticker, "source": "vndirect"})
            log(f"  ! {meta.ticker}: no data")
            continue
        prices[meta.ticker] = df["Close"]
        volumes[meta.ticker] = df["Volume"]
        rows.append(meta.to_dict())
        time.sleep(0.4)
    log(f"Vietnam: {len(prices)} series")
    return prices, volumes, rows


def collect_mutual_funds(status: dict) -> tuple[dict, list[dict]]:
    """Vietnamese open-ended funds, discovered live from the fmarket catalogue."""
    if skip_mutual_funds():
        return {}, []
    catalogue = sources.fetch_fmarket_catalogue()
    if not catalogue:
        status["warnings"].append("fmarket catalogue unavailable")
        log("Mutual funds: catalogue unavailable, skipped")
        return {}, []

    catalogue = catalogue[:max_mutual_funds()]
    log(f"Mutual funds: {len(catalogue)} funds discovered on fmarket ...")
    prices, rows = {}, []
    for fund in catalogue:
        df = sources.fetch_fmarket_nav(fund["product_id"])
        if df.empty or len(df) < 20:
            status["failed"].append({"ticker": fund["ticker"], "source": "fmarket"})
            continue
        prices[fund["ticker"]] = df["Close"]
        rows.append(dict(
            ticker=fund["ticker"], source="fmarket", symbol=str(fund["product_id"]),
            name=fund["name"], kind="Mutual Fund", asset_class=fund["asset_class"],
            region="Vietnam", country="Vietnam", currency="VND",
            issuer=fund["issuer"], ter=float("nan"), benchmark="VNINDEX",
            category=fund["category"], inception="",
        ))
        time.sleep(0.3)
    log(f"Mutual funds: {len(prices)} NAV series")
    return prices, rows


def collect_world(status: dict) -> tuple[dict, dict, list[dict]]:
    if skip_world():
        return {}, {}, []
    static = uni.static_universe()
    world = static[static.source == "yahoo"]
    symbols = world.symbol.tolist()
    log(f"World: downloading {len(symbols)} symbols from Yahoo Finance ...")
    got = sources.fetch_yahoo_batch(symbols)
    log(f"World: Yahoo returned {len(got)} series")

    prices, volumes, rows = {}, {}, []
    missing = []
    for _, meta in world.iterrows():
        df = got.get(meta.symbol)
        if df is None or df.empty:
            missing.append(meta)
            continue
        prices[meta.ticker] = df["Close"]
        volumes[meta.ticker] = df["Volume"]
        rows.append(meta.to_dict())

    if missing:
        log(f"World: retrying {len(missing)} symbols on Stooq ...")
        for meta in missing:
            df = sources.fetch_stooq(meta.symbol)
            if df.empty:
                status["failed"].append({"ticker": meta.ticker, "source": "yahoo/stooq"})
                continue
            prices[meta.ticker] = df["Close"]
            volumes[meta.ticker] = df["Volume"]
            row = meta.to_dict()
            row["source"] = "stooq"
            rows.append(row)
            time.sleep(0.3)
    log(f"World: {len(prices)} series")
    return prices, volumes, rows


def collect_fx(status: dict, needed: list[str]) -> pd.DataFrame:
    log(f"FX: fetching {len(needed)} currencies ...")
    fx = pd.DataFrame()
    if not skip_world():
        fx = sources.fetch_fx_yahoo(needed)
    have = [c for c in needed if c in fx.columns]
    missing = [c for c in needed if c not in have]

    if missing:
        log(f"FX: {len(missing)} currencies missing from Yahoo, trying Frankfurter ...")
        alt = sources.fetch_fx_frankfurter(missing)
        if not alt.empty:
            fx = alt if fx.empty else fx.join(alt[[c for c in alt.columns if c in missing]],
                                              how="outer")
            missing = [c for c in needed if c not in fx.columns]

    if missing:
        log(f"FX: {len(missing)} currencies still missing, using latest snapshot ...")
        snap = sources.fetch_fx_latest_erapi()
        for ccy in list(missing):
            if ccy in snap:
                if fx.empty:
                    fx = pd.DataFrame(index=pd.DatetimeIndex([pd.Timestamp.today().normalize()]))
                fx[ccy] = snap[ccy]
                status["warnings"].append(f"FX {ccy}: constant snapshot rate used")
                missing.remove(ccy)

    if missing:
        status["warnings"].append("FX unavailable for: " + ", ".join(missing))
    if not fx.empty:
        fx["USD"] = 1.0
        fx = fx.sort_index().ffill()
        fx.index = pd.to_datetime(fx.index)
        fx.index.name = "Date"
    return fx


# ---------------------------------------------------------------------------
# assembly
# ---------------------------------------------------------------------------

def merge_with_existing(new: pd.DataFrame, path: str,
                        keep_days: int = 400) -> pd.DataFrame:
    """Union today's download with the history already committed to the repo.

    Sources have their own limits (VNDIRECT only serves a window at a time, a
    provider can drop a ticker for a day), so the committed file is the memory
    of the dataset: new values win on overlapping dates, older history is kept,
    and a column nobody has priced for ``keep_days`` is retired.
    """
    if not os.path.exists(path) or new.empty:
        return new
    try:
        old = pd.read_csv(path, parse_dates=["Date"], index_col="Date")
    except Exception:
        return new
    if old.empty:
        return new
    merged = new.combine_first(old).sort_index()
    cutoff = merged.index.max() - pd.Timedelta(days=keep_days)
    keep = [c for c in merged.columns
            if c in new.columns or merged[c].loc[cutoff:].notna().any()]
    return merged[keep]


def drop_thin_series(prices: pd.DataFrame, minimum: int = 30) -> tuple[pd.DataFrame, list[str]]:
    """Remove series with too few observations to compute anything meaningful."""
    thin = [c for c in prices.columns if prices[c].notna().sum() < minimum]
    return prices.drop(columns=thin), thin


def build_frame(series_map: dict) -> pd.DataFrame:
    if not series_map:
        return pd.DataFrame()
    df = pd.concat(series_map, axis=1)
    df = df[~df.index.duplicated(keep="last")].sort_index()
    df.index.name = "Date"
    return df


def coverage_stats(prices: pd.DataFrame) -> pd.DataFrame:
    stats = []
    today = prices.index.max()
    for col in prices.columns:
        s = prices[col].dropna()
        if s.empty:
            stats.append({"ticker": col, "first_date": "", "last_date": "",
                          "observations": 0, "stale_days": -1})
            continue
        stats.append({
            "ticker": col,
            "first_date": s.index.min().strftime("%Y-%m-%d"),
            "last_date": s.index.max().strftime("%Y-%m-%d"),
            "observations": int(s.shape[0]),
            "stale_days": int((today - s.index.max()).days),
        })
    return pd.DataFrame(stats)


def write_legacy_files(prices: pd.DataFrame, volume: pd.DataFrame,
                       profile: pd.DataFrame, root: str) -> None:
    """Keep the original Vietnam-only CSVs in place for backwards compatibility."""
    vn = profile[(profile.region == "Vietnam") & (profile.kind != "Mutual Fund")]
    cols = [c for c in vn.ticker if c in prices.columns]
    if not cols:
        return
    prices[cols].dropna(how="all").to_csv(os.path.join(root, "funds_data.csv"))
    vcols = [c for c in cols if c in volume.columns]
    if vcols:
        volume[vcols].fillna(0).to_csv(os.path.join(root, "funds_volume.csv"))
    legacy = vn.rename(columns={
        "ticker": "Ticker", "name": "Name", "issuer": "Issuer",
        "kind": "Kind", "benchmark": "Benchmark", "inception": "Launch", "ter": "Fee",
    })
    legacy["Type"] = vn.apply(
        lambda r: r.category if r.kind == "Index" else f"{r.asset_class} ETF", axis=1).values
    legacy[["Ticker", "Name", "Issuer", "Type", "Benchmark", "Launch", "Fee"]].to_csv(
        os.path.join(root, "funds_profile.csv"), index=False)


def main(root: str | None = None, data_dir: str | None = None) -> int:
    root = root or os.path.dirname(os.path.abspath(__file__))
    data_dir = data_dir or os.path.join(root, "data")
    os.makedirs(data_dir, exist_ok=True)
    started = datetime.now(timezone.utc)
    status = {"started_utc": started.isoformat(), "failed": [], "warnings": []}

    price_map, vol_map, rows = {}, {}, []

    vn_p, vn_v, vn_rows = collect_vietnam(status)
    price_map.update(vn_p); vol_map.update(vn_v); rows += vn_rows

    mf_p, mf_rows = collect_mutual_funds(status)
    price_map.update(mf_p); rows += mf_rows

    w_p, w_v, w_rows = collect_world(status)
    price_map.update(w_p); vol_map.update(w_v); rows += w_rows

    if not price_map:
        log("FATAL: no data could be downloaded from any source.")
        status["error"] = "no data"
        with open(os.path.join(data_dir, "status.json"), "w", encoding="utf-8") as fh:
            json.dump(status, fh, indent=2)
        return 1

    prices = build_frame(price_map)
    volume = build_frame(vol_map)
    profile = pd.DataFrame(rows).drop_duplicates(subset="ticker").reset_index(drop=True)

    # keep the history that previous runs already collected
    prices = merge_with_existing(prices, os.path.join(data_dir, "prices.csv"))
    if not volume.empty:
        volume = merge_with_existing(volume, os.path.join(data_dir, "volume.csv"))

    prices, thin = drop_thin_series(prices)
    if thin:
        status["warnings"].append("dropped, too few observations: " + ", ".join(thin))
        volume = volume.drop(columns=[c for c in thin if c in volume.columns],
                             errors="ignore")
        profile = profile[~profile.ticker.isin(thin)]
    profile = profile[profile.ticker.isin(prices.columns)].reset_index(drop=True)

    currencies = sorted(set(profile.currency.dropna()) | {"USD", "EUR", "VND"})
    fx = collect_fx(status, currencies)

    # ---- coverage & profile enrichment -----------------------------------
    cov = coverage_stats(prices)
    profile = profile.merge(cov, on="ticker", how="left")
    profile.loc[profile.inception.isin(["", None]) | profile.inception.isna(),
                "inception"] = profile["first_date"]

    # ---- write -----------------------------------------------------------
    prices.to_csv(os.path.join(data_dir, "prices.csv"))
    if not volume.empty:
        volume.to_csv(os.path.join(data_dir, "volume.csv"))
    profile.to_csv(os.path.join(data_dir, "profile.csv"), index=False)
    if not fx.empty:
        fx.to_csv(os.path.join(data_dir, "fx.csv"))

    write_legacy_files(prices, volume, profile, root)

    status.update({
        "finished_utc": datetime.now(timezone.utc).isoformat(),
        "duration_seconds": round((datetime.now(timezone.utc) - started).total_seconds(), 1),
        "instruments": int(prices.shape[1]),
        "observations": int(prices.notna().sum().sum()),
        "first_date": prices.index.min().strftime("%Y-%m-%d"),
        "last_date": prices.index.max().strftime("%Y-%m-%d"),
        "by_region": profile.groupby("region").size().to_dict(),
        "by_kind": profile.groupby("kind").size().to_dict(),
        "currencies": [c for c in fx.columns] if not fx.empty else [],
        "stale": cov[cov.stale_days > 7][["ticker", "last_date", "stale_days"]]
                    .to_dict(orient="records"),
    })
    with open(os.path.join(data_dir, "status.json"), "w", encoding="utf-8") as fh:
        json.dump(status, fh, indent=2, ensure_ascii=False)

    log(f"DONE: {status['instruments']} instruments, "
        f"{status['first_date']} -> {status['last_date']}, "
        f"{len(status['failed'])} failures")
    return 0


if __name__ == "__main__":
    sys.exit(main())
