"""
Data sources for the global ETF report.

Every fetcher returns a tidy ``pandas.DataFrame`` indexed by date with the
columns ``Close`` and (when the source provides it) ``Volume``. All fetchers
are defensive: a failure returns an empty frame and is recorded in the run
status instead of aborting the whole update, so the daily job always produces
a usable dataset.

Sources
-------
VNDIRECT   Vietnamese listed ETFs and indices (public dchart API, no key)
Yahoo      World ETFs, world indices and FX (via ``yfinance``)
Stooq      Fallback for world instruments when Yahoo fails
fmarket    Vietnamese open-ended (mutual) fund NAV history, catalogue is
           discovered automatically so new funds appear without code changes
Frankfurter / open.er-api  FX fallbacks
"""

from __future__ import annotations

import io
import re
import time
from datetime import datetime, timezone

import pandas as pd
import requests

USER_AGENT = "Mozilla/5.0 (compatible; vn-fund-dashboard/2.0)"
START_DATE = "2010-01-01"
START_TIMESTAMP = int(datetime(2010, 1, 1, tzinfo=timezone.utc).timestamp())

_SESSION = requests.Session()
_SESSION.headers.update({"User-Agent": USER_AGENT})


def _empty() -> pd.DataFrame:
    return pd.DataFrame(columns=["Close", "Volume"])


# ---------------------------------------------------------------- VNDIRECT --

def _vndirect_window(symbol: str, start: int, end: int, retries: int = 3) -> pd.DataFrame:
    url = "https://dchart-api.vndirect.com.vn/dchart/history"
    params = {"resolution": "D", "symbol": symbol, "from": start, "to": end}
    for attempt in range(retries):
        try:
            r = _SESSION.get(url, params=params, timeout=30,
                             headers={"Referer": "https://dchart.vndirect.com.vn/"})
            r.raise_for_status()
            data = r.json()
            if not data or "t" not in data or "c" not in data or not data["t"]:
                return _empty()
            df = pd.DataFrame({
                "Close": data["c"],
                "Volume": data.get("v", [0] * len(data["t"])),
            }, index=pd.to_datetime(data["t"], unit="s").normalize())
            df.index.name = "Date"
            return df[df["Close"] > 0]
        except Exception:
            if attempt == retries - 1:
                return _empty()
            time.sleep(2 ** attempt)
    return _empty()


def fetch_vndirect(symbol: str, retries: int = 3,
                   window_days: int = 1500) -> pd.DataFrame:
    """Daily history of a Vietnamese listed symbol (ETF or index).

    The range is walked in windows and stitched together so a per-request bar
    limit on the endpoint cannot silently shorten the history. How far back the
    data actually goes is decided by VNDIRECT: the ETFs reach their listing
    date, the indices currently start in August 2017.
    """
    now = int(time.time())
    step = window_days * 86400
    frames, cursor = [], START_TIMESTAMP
    while cursor < now:
        chunk = _vndirect_window(symbol, cursor, min(cursor + step, now), retries)
        if not chunk.empty:
            frames.append(chunk)
        cursor += step
        time.sleep(0.2)
    if not frames:
        return _empty()
    df = pd.concat(frames).sort_index()
    return df[~df.index.duplicated(keep="last")]


def fetch_vndirect_multi(symbols: list[str], retries: int = 3) -> pd.DataFrame:
    """Try several spellings of the same instrument, return the first that works.

    VNDIRECT names some indices differently from the exchange (``VNMID`` for the
    midcap index, ``HNX`` for the HNX-Index...), so the universe lists the
    plausible aliases and the first one that answers wins.
    """
    for symbol in symbols:
        df = fetch_vndirect(symbol, retries=retries)
        if not df.empty:
            return df
    return _empty()


# -------------------------------------------------------------------- Yahoo --

def fetch_yahoo_batch(symbols: list[str], start: str = START_DATE,
                      chunk: int = 25, pause: float = 1.0) -> dict[str, pd.DataFrame]:
    """Download many symbols from Yahoo Finance in chunks.

    Returns a mapping ``symbol -> DataFrame``. Symbols Yahoo cannot serve are
    simply missing from the mapping; the caller records them as failures.
    """
    try:
        import yfinance as yf
    except ImportError:
        return {}

    out: dict[str, pd.DataFrame] = {}
    for i in range(0, len(symbols), chunk):
        batch = symbols[i:i + chunk]
        try:
            raw = yf.download(batch, start=start, progress=False, auto_adjust=True,
                              group_by="ticker", threads=True, timeout=60)
        except Exception:
            raw = None
        if raw is None or raw.empty:
            time.sleep(pause)
            continue
        for sym in batch:
            try:
                if isinstance(raw.columns, pd.MultiIndex):
                    if sym not in raw.columns.get_level_values(0):
                        continue
                    sub = raw[sym]
                else:
                    sub = raw
                if "Close" not in sub.columns:
                    continue
                df = pd.DataFrame({
                    "Close": pd.to_numeric(sub["Close"], errors="coerce"),
                    "Volume": pd.to_numeric(sub.get("Volume", 0), errors="coerce").fillna(0),
                })
                df = df.dropna(subset=["Close"])
                df = df[df["Close"] > 0]
                if df.empty:
                    continue
                df.index = pd.to_datetime(df.index).tz_localize(None).normalize()
                df.index.name = "Date"
                out[sym] = df[~df.index.duplicated(keep="last")].sort_index()
            except Exception:
                continue
        time.sleep(pause)
    return out


# -------------------------------------------------------------------- Stooq --

_STOOQ_SUFFIX = {
    "": ".us", ".L": ".uk", ".DE": ".de", ".PA": ".fr", ".AS": ".nl",
    ".T": ".jp", ".HK": ".hk", ".TO": ".ca", ".AX": ".au",
}


def _stooq_symbol(symbol: str) -> str | None:
    """Best-effort mapping of a Yahoo symbol to a Stooq symbol."""
    if symbol.startswith("^"):
        mapping = {
            "^GSPC": "^spx", "^IXIC": "^ndq", "^DJI": "^dji", "^NDX": "^ndx",
            "^RUT": "^rut", "^GDAXI": "^dax", "^STOXX50E": "^stx50",
            "^FTSE": "^ukx", "^FCHI": "^cac", "^N225": "^nkx", "^HSI": "^hsi",
            "^KS11": "^kospi", "^TWII": "^twse", "^NSEI": "^nifty",
            "^BSESN": "^sensex", "^AXJO": "^axjo", "^GSPTSE": "^tsx",
            "^BVSP": "^bvsp", "^MXX": "^mxx", "^SSMI": "^smi", "^AEX": "^aex",
            "^IBEX": "^ibex", "^VIX": "^vix",
        }
        return mapping.get(symbol)
    if "-" in symbol:  # crypto pairs are not on Stooq in this form
        return None
    if "." in symbol:
        base, _, suffix = symbol.partition(".")
        suf = _STOOQ_SUFFIX.get("." + suffix)
        return f"{base.lower()}{suf}" if suf else None
    return f"{symbol.lower()}.us"


def fetch_stooq(symbol: str) -> pd.DataFrame:
    """Fallback price history from Stooq (free CSV endpoint, no key)."""
    s = _stooq_symbol(symbol)
    if not s:
        return _empty()
    try:
        r = _SESSION.get(f"https://stooq.com/q/d/l/?s={s}&i=d", timeout=30)
        r.raise_for_status()
        if not r.text.startswith("Date"):
            return _empty()
        df = pd.read_csv(io.StringIO(r.text), parse_dates=["Date"]).set_index("Date")
        df = pd.DataFrame({"Close": df["Close"], "Volume": df.get("Volume", 0)})
        df = df.dropna(subset=["Close"])
        df = df[df.index >= START_DATE]
        df.index.name = "Date"
        return df.sort_index()
    except Exception:
        return _empty()


# ------------------------------------------------------------------ fmarket --

FMARKET_FILTER_URL = "https://api.fmarket.vn/res/products/filter"
FMARKET_NAV_URL = "https://api.fmarket.vn/res/product/get-nav-history"

_FMARKET_ASSET_TYPE = {
    "STOCK": ("Equity", "Equity Fund"),
    "BOND": ("Bond", "Bond Fund"),
    "BALANCED": ("Multi-Asset", "Balanced Fund"),
    "IPO": ("Equity", "Equity Fund"),
}


def fetch_fmarket_catalogue(page_size: int = 200) -> list[dict]:
    """Discover every open-ended fund distributed on fmarket.vn.

    The catalogue is fetched live so newly launched funds enter the report
    automatically, with no code change.
    """
    body = {
        "types": ["NEW_FUND", "TRADING_FUND"],
        "issuerIds": [], "sortOrder": "DESC", "sortField": "navTo6Months",
        "page": 1, "pageSize": page_size, "isIpo": False,
        "fundAssetTypes": [], "bondRemainPeriods": [], "searchField": "",
        "isBuyByReward": False, "thirdAppIds": [],
    }
    try:
        r = _SESSION.post(FMARKET_FILTER_URL, json=body, timeout=40)
        r.raise_for_status()
        rows = (r.json().get("data") or {}).get("rows") or []
    except Exception:
        return []

    funds = []
    for row in rows:
        code = (row.get("shortName") or row.get("code") or "").strip().upper()
        if not code or not row.get("id"):
            continue
        raw_type = ((row.get("dataFundAssetType") or {}).get("name")
                    or row.get("fundAssetType") or "").upper()
        asset_class, category = _FMARKET_ASSET_TYPE.get(raw_type, ("Equity", "Equity Fund"))
        funds.append({
            "ticker": code,
            "product_id": row.get("id"),
            "name": (row.get("name") or code).strip(),
            "issuer": ((row.get("owner") or {}).get("shortName")
                       or (row.get("owner") or {}).get("name") or "-"),
            "asset_class": asset_class,
            "category": category,
        })
    # de-duplicate on ticker, keep first occurrence
    seen, unique = set(), []
    for f in funds:
        if f["ticker"] in seen:
            continue
        seen.add(f["ticker"])
        unique.append(f)
    return unique


def fetch_fmarket_nav(product_id: int) -> pd.DataFrame:
    """Full NAV history of one open-ended fund."""
    body = {
        "isAllData": 1, "productId": product_id,
        "fromDate": None, "toDate": datetime.now().strftime("%Y%m%d"),
    }
    try:
        r = _SESSION.post(FMARKET_NAV_URL, json=body, timeout=40)
        r.raise_for_status()
        data = r.json().get("data") or []
        if not data:
            return _empty()
        df = pd.DataFrame({
            "Close": [d.get("nav") for d in data],
            "Volume": 0,
        }, index=pd.to_datetime([d.get("navDate") for d in data], errors="coerce"))
        df = df[~df.index.isna()].dropna(subset=["Close"])
        df = df[df["Close"] > 0]
        df.index = df.index.normalize()
        df.index.name = "Date"
        return df[~df.index.duplicated(keep="last")].sort_index()
    except Exception:
        return _empty()


# ----------------------------------------------------------------------- FX --

def fetch_fx_yahoo(currencies: list[str]) -> pd.DataFrame:
    """Daily USD value of one unit of each currency (columns = currency codes)."""
    direct = {c: f"{c}USD=X" for c in currencies if c != "USD"}
    got = fetch_yahoo_batch(list(direct.values()), start=START_DATE)

    series: dict[str, pd.Series] = {}
    missing = []
    for ccy, sym in direct.items():
        if sym in got and not got[sym].empty:
            series[ccy] = got[sym]["Close"]
        else:
            missing.append(ccy)

    if missing:  # try the inverted pair (USDVND=X -> 1/rate)
        inv = {c: f"USD{c}=X" for c in missing}
        got_inv = fetch_yahoo_batch(list(inv.values()), start=START_DATE)
        for ccy, sym in inv.items():
            if sym in got_inv and not got_inv[sym].empty:
                s = got_inv[sym]["Close"]
                series[ccy] = 1.0 / s[s > 0]

    if not series:
        return pd.DataFrame()
    fx = pd.concat(series, axis=1)
    fx["USD"] = 1.0
    fx.index.name = "Date"
    return fx.sort_index()


def fetch_fx_frankfurter(currencies: list[str], start: str = START_DATE) -> pd.DataFrame:
    """ECB reference rates (no key). Covers the majors, not VND."""
    wanted = [c for c in currencies if c != "USD"]
    try:
        r = _SESSION.get(
            f"https://api.frankfurter.app/{start}..",
            params={"from": "USD", "to": ",".join(wanted)}, timeout=40)
        r.raise_for_status()
        rates = r.json().get("rates") or {}
    except Exception:
        return pd.DataFrame()
    if not rates:
        return pd.DataFrame()
    df = pd.DataFrame(rates).T  # units of CCY per USD
    df.index = pd.to_datetime(df.index)
    df = df.sort_index().apply(pd.to_numeric, errors="coerce")
    out = 1.0 / df[df > 0]      # USD per unit of CCY
    out["USD"] = 1.0
    out.index.name = "Date"
    return out


def fetch_fx_latest_erapi(base: str = "USD") -> dict[str, float]:
    """Last-resort single snapshot of FX rates (open.er-api.com, no key)."""
    try:
        r = _SESSION.get(f"https://open.er-api.com/v6/latest/{base}", timeout=30)
        r.raise_for_status()
        rates = r.json().get("rates") or {}
        return {c: 1.0 / v for c, v in rates.items() if v}
    except Exception:
        return {}


# --------------------------------------------------- US ETF catalogue (all) --

NASDAQ_LISTED = "https://www.nasdaqtrader.com/dynamic/symdir/nasdaqlisted.txt"
OTHER_LISTED = "https://www.nasdaqtrader.com/dynamic/symdir/otherlisted.txt"

# Nasdaq Trader publishes the official symbol directory for every US listing,
# with an ETF flag. It needs no key, so the report can know the whole US ETF
# market rather than a list somebody typed by hand.
_EXCHANGE = {"A": "NYSE American", "N": "NYSE", "P": "NYSE Arca",
             "Z": "Cboe BZX", "V": "IEXG"}

_ISSUER_PREFIX = [
    ("iShares", "BlackRock"), ("SPDR", "State Street"), ("Vanguard", "Vanguard"),
    ("Invesco", "Invesco"), ("Schwab", "Schwab"), ("Fidelity", "Fidelity"),
    ("JPMorgan", "J.P. Morgan"), ("First Trust", "First Trust"),
    ("VanEck", "VanEck"), ("WisdomTree", "WisdomTree"), ("ProShares", "ProShares"),
    ("Direxion", "Direxion"), ("Global X", "Global X"), ("ARK", "ARK Invest"),
    ("Xtrackers", "DWS"), ("Amplify", "Amplify"), ("KraneShares", "KraneShares"),
    ("Pacer", "Pacer"), ("Janus", "Janus Henderson"), ("PIMCO", "PIMCO"),
    ("Goldman Sachs", "Goldman Sachs"), ("Franklin", "Franklin Templeton"),
    ("Dimensional", "Dimensional"), ("American Century", "American Century"),
    ("Roundhill", "Roundhill"), ("YieldMax", "YieldMax"), ("Simplify", "Simplify"),
    ("Innovator", "Innovator"), ("Alpha Architect", "Alpha Architect"),
    ("Grayscale", "Grayscale"), ("Bitwise", "Bitwise"), ("Defiance", "Defiance"),
    ("Tidal", "Tidal"), ("Sprott", "Sprott"), ("abrdn", "abrdn"),
]

_CLASS_RULES = [
    ("Crypto", ("bitcoin", "ether", "crypto", "blockchain")),
    ("Bond", ("bond", "treasury", "municipal", "aggregate", "credit", "yield curve",
              "duration", "tips", "fixed income", "t-bill", "ultrashort",
              "short maturity", "ultra-short", "ultra short", "money market",
              "floating rate", "short duration", "short income")),
    ("Commodity", ("gold", "silver", "platinum", "palladium", "commodity", "oil",
                   "natural gas", "copper", "uranium", "agriculture")),
    ("Real Estate", ("real estate", "reit", "residential", "mortgage")),
    ("Multi-Asset", ("allocation", "balanced", "target risk", "multi-asset")),
]

# "Ultra Short Bond" is a maturity, not leverage, and "Short Maturity" is not a
# short position: leverage is matched on explicit multipliers and direction
# words instead of loose substrings.
_LEVERAGE_PATTERN = re.compile(
    r"(?:\b[-+]?[123](?:\.5)?x\b|\bultrapro\b|\bultrashort\b|\binverse\b"
    r"|\bleveraged\b|\bbull\b|\bbear\b)", re.IGNORECASE)

# "Short" alone means an inverse fund only when the name is not talking about
# maturity: "ProShares Short QQQ" is a short position, "Ultra Short Bond" is not.
_SHORT_PATTERN = re.compile(r"\bshort\b", re.IGNORECASE)
_MATURITY_WORDS = ("maturity", "duration", "bond", "treasury", "income", "term",
                   "credit", "bill")

_CATEGORY_RULES = [
    ("Derivative Income", ("covered call", "buywrite", "premium income",
                           "option income", "buffer", "yieldmax")),
    ("Dividend", ("dividend", "income equity", "high yield equity")),
    ("Smart Beta", ("equal weight", "momentum", "quality", "minimum volatility",
                    "low volatility", "value factor", "multifactor")),
    ("Thematic", ("innovation", "robotic", "clean energy", "solar", "cyber",
                  "cloud", "semiconductor", "lithium", "space", "artificial")),
    ("Sector", ("sector", "financials", "technology", "health care", "energy",
                "utilities", "industrials", "materials", "staples", "discretionary")),
    ("Country", ("msci ", "ftse ", "japan", "china", "india", "brazil", "europe",
                 "emerging", "developed")),
]


def _classify_etf(name: str) -> tuple[str, str, str]:
    """(issuer, asset_class, category) inferred from the fund's own name."""
    lower = name.lower()
    is_short_fund = (_SHORT_PATTERN.search(name)
                     and not any(w in lower for w in _MATURITY_WORDS))
    if _LEVERAGE_PATTERN.search(name) or is_short_fund:
        issuer = next((house for prefix, house in _ISSUER_PREFIX
                       if lower.startswith(prefix.lower())), "Other")
        return issuer, "Equity", "Leveraged / Inverse"
    issuer = next((house for prefix, house in _ISSUER_PREFIX
                   if lower.startswith(prefix.lower()) or f" {prefix.lower()} " in lower),
                  "Other")
    asset_class = next((cls for cls, words in _CLASS_RULES
                        if any(w in lower for w in words)), "Equity")
    category = next((cat for cat, words in _CATEGORY_RULES
                     if any(w in lower for w in words)), "")
    if not category:
        # a bond or commodity fund is better described by its asset class than
        # by a default of "Broad Market"
        category = "Broad Market" if asset_class == "Equity" else asset_class
    return issuer, asset_class, category


def _parse_symbol_directory(text: str, layout: str) -> list[dict]:
    rows = []
    lines = [ln for ln in text.splitlines() if ln and not ln.startswith("File Creation")]
    if not lines:
        return rows
    header = [h.strip() for h in lines[0].split("|")]
    for line in lines[1:]:
        parts = line.split("|")
        if len(parts) != len(header):
            continue
        record = dict(zip(header, (p.strip() for p in parts)))
        if record.get("ETF") != "Y" or record.get("Test Issue") == "Y":
            continue
        symbol = record.get("Symbol") or record.get("ACT Symbol") or ""
        name = record.get("Security Name", "")
        # units, warrants and rights carry punctuation Yahoo does not serve
        if not symbol or not symbol.isalpha() or len(symbol) > 5:
            continue
        rows.append({
            "ticker": symbol, "name": name.split(" - ")[-1].strip() or symbol,
            "exchange": _EXCHANGE.get(record.get("Exchange", ""),
                                      "Nasdaq" if layout == "nasdaq" else "US"),
        })
    return rows


def fetch_us_etf_catalogue() -> list[dict]:
    """Every ETF listed in the United States, from the official symbol directory."""
    out: list[dict] = []
    for url, layout in ((NASDAQ_LISTED, "nasdaq"), (OTHER_LISTED, "other")):
        try:
            response = _SESSION.get(url, timeout=60)
            response.raise_for_status()
            out += _parse_symbol_directory(response.text, layout)
        except Exception:
            continue

    seen, unique = set(), []
    for row in out:
        if row["ticker"] in seen:
            continue
        seen.add(row["ticker"])
        issuer, asset_class, category = _classify_etf(row["name"])
        row.update(issuer=issuer, asset_class=asset_class, category=category)
        unique.append(row)
    return sorted(unique, key=lambda r: r["ticker"])


def rank_by_liquidity(symbols: list[str], days: int = 90,
                      chunk: int = 60) -> pd.Series:
    """Median daily traded value over a short window, most liquid first.

    One cheap pass over the whole catalogue decides which ETFs are worth a full
    history download; it is what keeps "every ETF" from meaning "every dead
    ETF with three trades a week".
    """
    start = (datetime.now(timezone.utc) - pd.Timedelta(days=days)).strftime("%Y-%m-%d")
    frames = fetch_yahoo_batch(symbols, start=start, chunk=chunk, pause=0.4)
    values = {}
    for symbol, frame in frames.items():
        if frame.empty or "Volume" not in frame:
            continue
        traded = (frame["Close"] * frame["Volume"]).replace(0, pd.NA).dropna()
        if len(traded) < 5:
            continue
        values[symbol] = float(traded.median())
    return pd.Series(values, dtype="float64").sort_values(ascending=False)
