"""
Master universe of every fund / index tracked by the report.

The universe is intentionally global: Vietnamese ETFs and indices (fetched from
VNDIRECT), Vietnamese open-ended funds (discovered automatically from the
fmarket.vn catalogue) and exchange traded funds + benchmark indices from every
major market in the world (fetched from Yahoo Finance with a Stooq fallback).

Every row carries the metadata the analytics layer needs to compare funds
across markets: the trading currency (for FX normalisation), region, asset
class, category, issuer and the total expense ratio (TER, % p.a.).

Fields
------
ticker        canonical id used across every CSV and in the UI
source        'vndirect' | 'yahoo' | 'fmarket'
symbol        symbol as the source knows it
name          human readable name
kind          'ETF' | 'Index' | 'Mutual Fund'
asset_class   'Equity' | 'Bond' | 'Commodity' | 'Real Estate' | 'Crypto' | 'Multi-Asset'
region        'Vietnam' | 'US' | 'Europe' | 'Asia-Pacific' | 'Emerging' | 'Global' | 'Americas'
country       ISO-ish country / market label
currency      trading currency (ISO 4217)
issuer        fund house ('-' for indices)
ter           total expense ratio in % p.a. (0.0 for indices, NaN when unknown)
benchmark     canonical ticker of the natural benchmark ('' when none)
category      finer bucket, e.g. 'Broad Market', 'Sector: Technology'
inception     YYYY-MM-DD (best effort; only used for display)
"""

from __future__ import annotations

import pandas as pd

# --------------------------------------------------------------------------
# 1. VIETNAM — indices and exchange traded funds (source: VNDIRECT dchart API)
# --------------------------------------------------------------------------

# Aliases the VNDIRECT chart API uses for some indices; the loader tries the
# canonical ticker first and falls back through this list.
VN_SYMBOL_ALIASES = {
    "VNMIDCAP":   ["VNMID", "VNMIDCAP"],
    "VNSMALLCAP": ["VNSML", "VNSMALLCAP"],
    "HNXINDEX":   ["HNX", "HNXINDEX", "HNX-INDEX"],
    "UPCOMINDEX": ["UPCOM", "UPCOMINDEX", "UPCOM-INDEX"],
    "VNFINSELECT": ["VNFINSELECT", "VNFINSEL"],
    "VNFINLEAD":  ["VNFINLEAD", "VNFIN LEAD"],
}

VN_ASSETS = [
    # ticker, name, issuer, kind, asset_class, category, benchmark, ter, inception
    ("VNINDEX",   "VN-Index",                  "HOSE", "Index", "Equity", "Broad Market",        "",           0.0,  "2000-07-28"),
    ("VN30",      "VN30 Index",                "HOSE", "Index", "Equity", "Large Cap",           "",           0.0,  "2012-02-06"),
    ("VN100",     "VN100 Index",               "HOSE", "Index", "Equity", "Broad Market",        "",           0.0,  "2014-01-24"),
    ("VNMIDCAP",  "VN Midcap Index",           "HOSE", "Index", "Equity", "Mid Cap",             "",           0.0,  "2017-10-23"),
    ("VNSMALLCAP","VN Smallcap Index",         "HOSE", "Index", "Equity", "Small Cap",           "",           0.0,  "2017-10-23"),
    ("VNX50",     "VNX50 Index",               "HOSE", "Index", "Equity", "Large Cap",           "",           0.0,  "2017-10-23"),
    ("VNFINLEAD", "VN Financials Leading",     "HOSE", "Index", "Equity", "Sector: Financials",  "",           0.0,  "2019-11-18"),
    ("VNFINSELECT","VN Financials Select",     "HOSE", "Index", "Equity", "Sector: Financials",  "",           0.0,  "2019-11-18"),
    ("VNDIAMOND", "VN Diamond Index",          "HOSE", "Index", "Equity", "Thematic",            "",           0.0,  "2019-11-18"),
    ("HNXINDEX",  "HNX-Index",                 "HNX",  "Index", "Equity", "Broad Market",        "",           0.0,  "2005-07-14"),
    ("UPCOMINDEX","UPCoM-Index",               "UPCOM","Index", "Equity", "Broad Market",        "",           0.0,  "2009-06-24"),

    ("E1VFVN30",  "DCVFM VN30 ETF",            "Dragon Capital", "ETF", "Equity", "Large Cap",          "VN30",       0.65, "2014-10-06"),
    ("FUEVFVND",  "DCVFM VN Diamond ETF",      "Dragon Capital", "ETF", "Equity", "Thematic",           "VNDIAMOND",  0.80, "2020-05-12"),
    ("FUEDCMID",  "DCVFM VN Midcap ETF",       "Dragon Capital", "ETF", "Equity", "Mid Cap",            "VNMIDCAP",   0.80, "2022-09-29"),
    ("FUEIP100",  "IPAAM VN100 ETF",           "IPAAM",          "ETF", "Equity", "Broad Market",       "VN100",      0.70, "2021-09-14"),
    ("FUESSV30",  "SSIAM VN30 ETF",            "SSIAM",          "ETF", "Equity", "Large Cap",          "VN30",       0.55, "2020-08-18"),
    ("FUESSVFL",  "SSIAM VNFIN LEAD ETF",      "SSIAM",          "ETF", "Equity", "Sector: Financials", "VNFINLEAD",  0.65, "2020-01-14"),
    ("FUESSV50",  "SSIAM VNX50 ETF",           "SSIAM",          "ETF", "Equity", "Large Cap",          "VNX50",      0.50, "2014-11-17"),
    ("FUEVN100",  "VinaCapital VN100 ETF",     "VinaCapital",    "ETF", "Equity", "Broad Market",       "VN100",      0.67, "2020-06-16"),
    ("FUEMAV30",  "Mirae Asset VN30 ETF",      "Mirae Asset",    "ETF", "Equity", "Large Cap",          "VN30",       0.60, "2020-09-22"),
    ("FUEMAVND",  "MAFM VN Diamond ETF",       "Mirae Asset",    "ETF", "Equity", "Thematic",           "VNDIAMOND",  0.70, "2024-05-15"),
    ("FUETCV30",  "Techcom VN30 ETF",          "Techcom Capital","ETF", "Equity", "Large Cap",          "VN30",       0.00, "2021-06-15"),
    ("FUEKIV30",  "KIM Growth VN30 ETF",       "KIM Vietnam",    "ETF", "Equity", "Large Cap",          "VN30",       0.55, "2020-12-28"),
    ("FUEKIVFS",  "KIM Growth VNFIN SELECT",   "KIM Vietnam",    "ETF", "Equity", "Sector: Financials", "VNFINSELECT",0.60, "2021-11-12"),
    ("FUEBFVN",   "BVF VN Leader ETF",         "Bao Viet Fund",  "ETF", "Equity", "Broad Market",       "VNINDEX",    0.65, "2023-07-25"),
]

# --------------------------------------------------------------------------
# 2. WORLD — benchmark indices (source: Yahoo Finance)
# --------------------------------------------------------------------------

WORLD_INDICES = [
    # ticker, symbol, name, region, country, currency, category
    ("SP500",     "^GSPC",     "S&P 500",                     "US",           "United States", "USD", "Broad Market"),
    ("NASDAQ",    "^IXIC",     "Nasdaq Composite",            "US",           "United States", "USD", "Broad Market"),
    ("NASDAQ100", "^NDX",      "Nasdaq 100",                  "US",           "United States", "USD", "Large Cap"),
    ("DOWJONES",  "^DJI",      "Dow Jones Industrial Average","US",           "United States", "USD", "Large Cap"),
    ("RUSSELL2000","^RUT",     "Russell 2000",                "US",           "United States", "USD", "Small Cap"),
    ("VIX",       "^VIX",      "CBOE Volatility Index",       "US",           "United States", "USD", "Volatility"),
    ("DAX",       "^GDAXI",    "DAX 40",                      "Europe",       "Germany",       "EUR", "Broad Market"),
    ("MDAX",      "^MDAXI",    "MDAX",                        "Europe",       "Germany",       "EUR", "Mid Cap"),
    ("TECDAX",    "^TECDAX",   "TecDAX",                      "Europe",       "Germany",       "EUR", "Sector: Technology"),
    ("ESTX50",    "^STOXX50E", "EURO STOXX 50",               "Europe",       "Eurozone",      "EUR", "Large Cap"),
    ("STOXX600",  "^STOXX",    "STOXX Europe 600",            "Europe",       "Europe",        "EUR", "Broad Market"),
    ("FTSE100",   "^FTSE",     "FTSE 100",                    "Europe",       "United Kingdom","GBP", "Large Cap"),
    ("CAC40",     "^FCHI",     "CAC 40",                      "Europe",       "France",        "EUR", "Large Cap"),
    ("SMI",       "^SSMI",     "Swiss Market Index",          "Europe",       "Switzerland",   "CHF", "Large Cap"),
    ("AEX",       "^AEX",      "AEX Index",                   "Europe",       "Netherlands",   "EUR", "Large Cap"),
    ("IBEX35",    "^IBEX",     "IBEX 35",                     "Europe",       "Spain",         "EUR", "Large Cap"),
    ("NIKKEI225", "^N225",     "Nikkei 225",                  "Asia-Pacific", "Japan",         "JPY", "Large Cap"),
    ("HANGSENG",  "^HSI",      "Hang Seng Index",             "Asia-Pacific", "Hong Kong",     "HKD", "Large Cap"),
    ("SHANGHAI",  "000001.SS", "SSE Composite",               "Asia-Pacific", "China",         "CNY", "Broad Market"),
    ("KOSPI",     "^KS11",     "KOSPI",                       "Asia-Pacific", "South Korea",   "KRW", "Broad Market"),
    ("TAIEX",     "^TWII",     "TAIEX",                       "Asia-Pacific", "Taiwan",        "TWD", "Broad Market"),
    ("NIFTY50",   "^NSEI",     "NIFTY 50",                    "Asia-Pacific", "India",         "INR", "Large Cap"),
    ("SENSEX",    "^BSESN",    "BSE SENSEX",                  "Asia-Pacific", "India",         "INR", "Large Cap"),
    ("STI",       "^STI",      "Straits Times Index",         "Asia-Pacific", "Singapore",     "SGD", "Large Cap"),
    ("SET",       "^SET.BK",   "SET Index",                   "Asia-Pacific", "Thailand",      "THB", "Broad Market"),
    ("KLCI",      "^KLSE",     "FTSE Bursa Malaysia KLCI",    "Asia-Pacific", "Malaysia",      "MYR", "Large Cap"),
    ("JKSE",      "^JKSE",     "IDX Composite",               "Asia-Pacific", "Indonesia",     "IDR", "Broad Market"),
    ("PSEI",      "PSEI.PS",   "PSEi Composite",              "Asia-Pacific", "Philippines",   "PHP", "Broad Market"),
    ("ASX200",    "^AXJO",     "S&P/ASX 200",                 "Asia-Pacific", "Australia",     "AUD", "Large Cap"),
    ("TSX",       "^GSPTSE",   "S&P/TSX Composite",           "Americas",     "Canada",        "CAD", "Broad Market"),
    ("BOVESPA",   "^BVSP",     "Ibovespa",                    "Americas",     "Brazil",        "BRL", "Broad Market"),
    ("IPC",       "^MXX",      "S&P/BMV IPC",                 "Americas",     "Mexico",        "MXN", "Broad Market"),
]

# --------------------------------------------------------------------------
# 3. WORLD — exchange traded funds (source: Yahoo Finance)
# --------------------------------------------------------------------------
# ticker/symbol, name, issuer, asset_class, region, country, currency,
# category, benchmark (canonical ticker or ''), ter

WORLD_ETFS = [
    # ---------------- United States: broad market ----------------
    ("SPY",  "SPDR S&P 500 ETF Trust",                "State Street", "Equity", "US", "United States", "USD", "Broad Market", "SP500",      0.0945),
    ("IVV",  "iShares Core S&P 500 ETF",              "BlackRock",    "Equity", "US", "United States", "USD", "Broad Market", "SP500",      0.03),
    ("VOO",  "Vanguard S&P 500 ETF",                  "Vanguard",     "Equity", "US", "United States", "USD", "Broad Market", "SP500",      0.03),
    ("VTI",  "Vanguard Total Stock Market ETF",       "Vanguard",     "Equity", "US", "United States", "USD", "Broad Market", "SP500",      0.03),
    ("QQQ",  "Invesco QQQ Trust",                     "Invesco",      "Equity", "US", "United States", "USD", "Large Cap",    "NASDAQ100",  0.20),
    ("QQQM", "Invesco NASDAQ 100 ETF",                "Invesco",      "Equity", "US", "United States", "USD", "Large Cap",    "NASDAQ100",  0.15),
    ("DIA",  "SPDR Dow Jones Industrial Average ETF", "State Street", "Equity", "US", "United States", "USD", "Large Cap",    "DOWJONES",   0.16),
    ("IWM",  "iShares Russell 2000 ETF",              "BlackRock",    "Equity", "US", "United States", "USD", "Small Cap",    "RUSSELL2000",0.19),
    ("IJH",  "iShares Core S&P Mid-Cap ETF",          "BlackRock",    "Equity", "US", "United States", "USD", "Mid Cap",      "SP500",      0.05),
    ("IJR",  "iShares Core S&P Small-Cap ETF",        "BlackRock",    "Equity", "US", "United States", "USD", "Small Cap",    "RUSSELL2000",0.06),
    ("RSP",  "Invesco S&P 500 Equal Weight ETF",      "Invesco",      "Equity", "US", "United States", "USD", "Smart Beta",   "SP500",      0.20),
    # ---------------- United States: factor / style ----------------
    ("VTV",  "Vanguard Value ETF",                    "Vanguard",     "Equity", "US", "United States", "USD", "Style: Value",  "SP500",     0.04),
    ("VUG",  "Vanguard Growth ETF",                   "Vanguard",     "Equity", "US", "United States", "USD", "Style: Growth", "SP500",     0.04),
    ("MTUM", "iShares MSCI USA Momentum Factor ETF",  "BlackRock",    "Equity", "US", "United States", "USD", "Smart Beta",    "SP500",     0.15),
    ("QUAL", "iShares MSCI USA Quality Factor ETF",   "BlackRock",    "Equity", "US", "United States", "USD", "Smart Beta",    "SP500",     0.15),
    ("USMV", "iShares MSCI USA Min Vol Factor ETF",   "BlackRock",    "Equity", "US", "United States", "USD", "Smart Beta",    "SP500",     0.15),
    ("SCHD", "Schwab US Dividend Equity ETF",         "Schwab",       "Equity", "US", "United States", "USD", "Dividend",      "SP500",     0.06),
    ("VYM",  "Vanguard High Dividend Yield ETF",      "Vanguard",     "Equity", "US", "United States", "USD", "Dividend",      "SP500",     0.06),
    ("VIG",  "Vanguard Dividend Appreciation ETF",    "Vanguard",     "Equity", "US", "United States", "USD", "Dividend",      "SP500",     0.05),
    ("ARKK", "ARK Innovation ETF",                    "ARK Invest",   "Equity", "US", "United States", "USD", "Thematic",      "NASDAQ100", 0.75),
    # ---------------- United States: sectors ----------------
    ("XLK",  "Technology Select Sector SPDR",         "State Street", "Equity", "US", "United States", "USD", "Sector: Technology",       "SP500", 0.09),
    ("XLF",  "Financial Select Sector SPDR",          "State Street", "Equity", "US", "United States", "USD", "Sector: Financials",       "SP500", 0.09),
    ("XLV",  "Health Care Select Sector SPDR",        "State Street", "Equity", "US", "United States", "USD", "Sector: Health Care",      "SP500", 0.09),
    ("XLE",  "Energy Select Sector SPDR",             "State Street", "Equity", "US", "United States", "USD", "Sector: Energy",           "SP500", 0.09),
    ("XLI",  "Industrial Select Sector SPDR",         "State Street", "Equity", "US", "United States", "USD", "Sector: Industrials",      "SP500", 0.09),
    ("XLY",  "Consumer Discretionary Select SPDR",    "State Street", "Equity", "US", "United States", "USD", "Sector: Cons. Discr.",     "SP500", 0.09),
    ("XLP",  "Consumer Staples Select Sector SPDR",   "State Street", "Equity", "US", "United States", "USD", "Sector: Cons. Staples",    "SP500", 0.09),
    ("XLU",  "Utilities Select Sector SPDR",          "State Street", "Equity", "US", "United States", "USD", "Sector: Utilities",        "SP500", 0.09),
    ("XLB",  "Materials Select Sector SPDR",          "State Street", "Equity", "US", "United States", "USD", "Sector: Materials",        "SP500", 0.09),
    ("XLRE", "Real Estate Select Sector SPDR",        "State Street", "Real Estate", "US", "United States", "USD", "Sector: Real Estate", "SP500", 0.09),
    ("XLC",  "Communication Services Select SPDR",    "State Street", "Equity", "US", "United States", "USD", "Sector: Comm. Services",   "SP500", 0.09),
    ("SMH",  "VanEck Semiconductor ETF",              "VanEck",       "Equity", "US", "United States", "USD", "Sector: Semiconductors",   "NASDAQ100", 0.35),
    ("SOXX", "iShares Semiconductor ETF",             "BlackRock",    "Equity", "US", "United States", "USD", "Sector: Semiconductors",   "NASDAQ100", 0.35),
    ("IBB",  "iShares Biotechnology ETF",             "BlackRock",    "Equity", "US", "United States", "USD", "Sector: Biotech",          "NASDAQ100", 0.45),
    ("IGV",  "iShares Expanded Tech-Software ETF",    "BlackRock",    "Equity", "US", "United States", "USD", "Sector: Software",         "NASDAQ100", 0.41),
    # ---------------- United States: thematic ----------------
    ("ICLN", "iShares Global Clean Energy ETF",       "BlackRock",    "Equity", "Global", "Global",    "USD", "Thematic", "URTH", 0.41),
    ("TAN",  "Invesco Solar ETF",                     "Invesco",      "Equity", "Global", "Global",    "USD", "Thematic", "URTH", 0.67),
    ("BOTZ", "Global X Robotics & AI ETF",            "Global X",     "Equity", "Global", "Global",    "USD", "Thematic", "URTH", 0.68),
    ("LIT",  "Global X Lithium & Battery Tech ETF",   "Global X",     "Equity", "Global", "Global",    "USD", "Thematic", "URTH", 0.75),
    ("HACK", "Amplify Cybersecurity ETF",             "Amplify",      "Equity", "Global", "Global",    "USD", "Thematic", "URTH", 0.60),
    # ---------------- Global / developed / emerging equity ----------------
    ("VT",   "Vanguard Total World Stock ETF",        "Vanguard",     "Equity", "Global",   "Global",         "USD", "Broad Market", "", 0.06),
    ("ACWI", "iShares MSCI ACWI ETF",                 "BlackRock",    "Equity", "Global",   "Global",         "USD", "Broad Market", "", 0.32),
    ("URTH", "iShares MSCI World ETF",                "BlackRock",    "Equity", "Global",   "Developed",      "USD", "Broad Market", "", 0.24),
    ("VEA",  "Vanguard FTSE Developed Markets ETF",   "Vanguard",     "Equity", "Global",   "Developed ex-US","USD", "Broad Market", "", 0.03),
    ("EFA",  "iShares MSCI EAFE ETF",                 "BlackRock",    "Equity", "Global",   "Developed ex-US","USD", "Broad Market", "", 0.33),
    ("IEFA", "iShares Core MSCI EAFE ETF",            "BlackRock",    "Equity", "Global",   "Developed ex-US","USD", "Broad Market", "", 0.07),
    ("VXUS", "Vanguard Total International Stock ETF","Vanguard",     "Equity", "Global",   "Ex-US",          "USD", "Broad Market", "", 0.05),
    ("EEM",  "iShares MSCI Emerging Markets ETF",     "BlackRock",    "Equity", "Emerging", "Emerging",       "USD", "Broad Market", "", 0.72),
    ("VWO",  "Vanguard FTSE Emerging Markets ETF",    "Vanguard",     "Equity", "Emerging", "Emerging",       "USD", "Broad Market", "", 0.07),
    ("IEMG", "iShares Core MSCI Emerging Markets",    "BlackRock",    "Equity", "Emerging", "Emerging",       "USD", "Broad Market", "", 0.09),
    # ---------------- Single-country ETFs (US listed) ----------------
    ("VNM",  "VanEck Vietnam ETF",                    "VanEck",       "Equity", "Emerging",     "Vietnam",       "USD", "Country", "VNINDEX",  0.66),
    ("EWG",  "iShares MSCI Germany ETF",              "BlackRock",    "Equity", "Europe",       "Germany",       "USD", "Country", "DAX",      0.50),
    ("EWU",  "iShares MSCI United Kingdom ETF",       "BlackRock",    "Equity", "Europe",       "United Kingdom","USD", "Country", "FTSE100",  0.50),
    ("EWQ",  "iShares MSCI France ETF",               "BlackRock",    "Equity", "Europe",       "France",        "USD", "Country", "CAC40",    0.50),
    ("EWL",  "iShares MSCI Switzerland ETF",          "BlackRock",    "Equity", "Europe",       "Switzerland",   "USD", "Country", "SMI",      0.50),
    ("EWN",  "iShares MSCI Netherlands ETF",          "BlackRock",    "Equity", "Europe",       "Netherlands",   "USD", "Country", "AEX",      0.50),
    ("EWJ",  "iShares MSCI Japan ETF",                "BlackRock",    "Equity", "Asia-Pacific", "Japan",         "USD", "Country", "NIKKEI225",0.50),
    ("EWY",  "iShares MSCI South Korea ETF",          "BlackRock",    "Equity", "Asia-Pacific", "South Korea",   "USD", "Country", "KOSPI",    0.59),
    ("EWT",  "iShares MSCI Taiwan ETF",               "BlackRock",    "Equity", "Asia-Pacific", "Taiwan",        "USD", "Country", "TAIEX",    0.59),
    ("EWA",  "iShares MSCI Australia ETF",            "BlackRock",    "Equity", "Asia-Pacific", "Australia",     "USD", "Country", "ASX200",   0.50),
    ("EWS",  "iShares MSCI Singapore ETF",            "BlackRock",    "Equity", "Asia-Pacific", "Singapore",     "USD", "Country", "STI",      0.50),
    ("EWM",  "iShares MSCI Malaysia ETF",             "BlackRock",    "Equity", "Asia-Pacific", "Malaysia",      "USD", "Country", "KLCI",     0.50),
    ("THD",  "iShares MSCI Thailand ETF",             "BlackRock",    "Equity", "Asia-Pacific", "Thailand",      "USD", "Country", "SET",      0.59),
    ("EIDO", "iShares MSCI Indonesia ETF",            "BlackRock",    "Equity", "Asia-Pacific", "Indonesia",     "USD", "Country", "JKSE",     0.59),
    ("EPHE", "iShares MSCI Philippines ETF",          "BlackRock",    "Equity", "Asia-Pacific", "Philippines",   "USD", "Country", "PSEI",     0.59),
    ("INDA", "iShares MSCI India ETF",                "BlackRock",    "Equity", "Asia-Pacific", "India",         "USD", "Country", "NIFTY50",  0.62),
    ("MCHI", "iShares MSCI China ETF",                "BlackRock",    "Equity", "Asia-Pacific", "China",         "USD", "Country", "HANGSENG", 0.59),
    ("FXI",  "iShares China Large-Cap ETF",           "BlackRock",    "Equity", "Asia-Pacific", "China",         "USD", "Country", "HANGSENG", 0.74),
    ("ASHR", "Xtrackers Harvest CSI 300 China A ETF", "DWS",          "Equity", "Asia-Pacific", "China",         "USD", "Country", "SHANGHAI", 0.65),
    ("KWEB", "KraneShares CSI China Internet ETF",    "KraneShares",  "Equity", "Asia-Pacific", "China",         "USD", "Sector: Technology", "HANGSENG", 0.70),
    ("EWC",  "iShares MSCI Canada ETF",               "BlackRock",    "Equity", "Americas",     "Canada",        "USD", "Country", "TSX",      0.50),
    ("EWZ",  "iShares MSCI Brazil ETF",               "BlackRock",    "Equity", "Americas",     "Brazil",        "USD", "Country", "BOVESPA",  0.59),
    ("EWW",  "iShares MSCI Mexico ETF",               "BlackRock",    "Equity", "Americas",     "Mexico",        "USD", "Country", "IPC",      0.50),
    ("EZA",  "iShares MSCI South Africa ETF",         "BlackRock",    "Equity", "Emerging",     "South Africa",  "USD", "Country", "",         0.59),
    ("TUR",  "iShares MSCI Turkey ETF",               "BlackRock",    "Equity", "Emerging",     "Turkey",        "USD", "Country", "",         0.59),
    # ---------------- Europe: UCITS ETFs (Xetra / LSE / Euronext) ----------------
    ("EUNL.DE", "iShares Core MSCI World UCITS ETF",       "BlackRock", "Equity", "Europe", "Germany",     "EUR", "Broad Market", "",        0.20),
    ("SXR8.DE", "iShares Core S&P 500 UCITS ETF (Acc)",    "BlackRock", "Equity", "Europe", "Germany",     "EUR", "Broad Market", "SP500",   0.07),
    ("IUSQ.DE", "iShares MSCI ACWI UCITS ETF",             "BlackRock", "Equity", "Europe", "Germany",     "EUR", "Broad Market", "",        0.20),
    ("IS3N.DE", "iShares Core MSCI EM IMI UCITS ETF",      "BlackRock", "Equity", "Europe", "Germany",     "EUR", "Broad Market", "",        0.18),
    ("EXS1.DE", "iShares Core DAX UCITS ETF",              "BlackRock", "Equity", "Europe", "Germany",     "EUR", "Country",      "DAX",     0.16),
    ("EXSA.DE", "iShares STOXX Europe 600 UCITS ETF",      "BlackRock", "Equity", "Europe", "Germany",     "EUR", "Broad Market", "STOXX600",0.20),
    ("EXW1.DE", "iShares EURO STOXX 50 UCITS ETF",         "BlackRock", "Equity", "Europe", "Germany",     "EUR", "Large Cap",    "ESTX50",  0.10),
    ("EXSI.DE", "iShares STOXX Europe Mid 200 UCITS ETF",  "BlackRock", "Equity", "Europe", "Germany",     "EUR", "Mid Cap",      "STOXX600",0.20),
    ("VWCE.DE", "Vanguard FTSE All-World UCITS ETF (Acc)", "Vanguard",  "Equity", "Europe", "Germany",     "EUR", "Broad Market", "",        0.22),
    ("VGWL.DE", "Vanguard FTSE All-World UCITS ETF (Dist)","Vanguard",  "Equity", "Europe", "Germany",     "EUR", "Broad Market", "",        0.22),
    ("XDWD.DE", "Xtrackers MSCI World UCITS ETF",          "DWS",       "Equity", "Europe", "Germany",     "EUR", "Broad Market", "",        0.19),
    ("XMME.DE", "Xtrackers MSCI Emerging Markets UCITS",   "DWS",       "Equity", "Europe", "Germany",     "EUR", "Broad Market", "",        0.18),
    ("EUNA.DE", "iShares Core Euro Aggregate Bond UCITS",  "BlackRock", "Bond",   "Europe", "Germany",     "EUR", "Aggregate Bond","",       0.09),
    ("IBCI.DE", "iShares Euro Infl. Linked Govt Bond",     "BlackRock", "Bond",   "Europe", "Germany",     "EUR", "Inflation Linked","",     0.09),
    ("CSPX.L",  "iShares Core S&P 500 UCITS ETF",          "BlackRock", "Equity", "Europe", "United Kingdom","USD","Broad Market", "SP500",  0.07),
    ("VUSA.L",  "Vanguard S&P 500 UCITS ETF",              "Vanguard",  "Equity", "Europe", "United Kingdom","GBP","Broad Market", "SP500",  0.07),
    ("VWRL.L",  "Vanguard FTSE All-World UCITS ETF",       "Vanguard",  "Equity", "Europe", "United Kingdom","GBP","Broad Market", "",       0.22),
    ("ISF.L",   "iShares Core FTSE 100 UCITS ETF",         "BlackRock", "Equity", "Europe", "United Kingdom","GBP","Country",      "FTSE100",0.07),
    ("VUKE.L",  "Vanguard FTSE 100 UCITS ETF",             "Vanguard",  "Equity", "Europe", "United Kingdom","GBP","Country",      "FTSE100",0.09),
    ("IWDA.AS", "iShares Core MSCI World UCITS ETF (Acc)", "BlackRock", "Equity", "Europe", "Netherlands", "EUR", "Broad Market", "",        0.20),
    ("CW8.PA",  "Amundi MSCI World UCITS ETF",             "Amundi",    "Equity", "Europe", "France",      "EUR", "Broad Market", "",        0.38),
    # ---------------- Asia-Pacific: locally listed ETFs ----------------
    ("1306.T",    "NEXT FUNDS TOPIX ETF",                 "Nomura",     "Equity", "Asia-Pacific", "Japan",      "JPY", "Broad Market", "NIKKEI225", 0.06),
    ("1321.T",    "NEXT FUNDS Nikkei 225 ETF",            "Nomura",     "Equity", "Asia-Pacific", "Japan",      "JPY", "Large Cap",    "NIKKEI225", 0.19),
    ("2800.HK",   "Tracker Fund of Hong Kong",            "State Street","Equity","Asia-Pacific", "Hong Kong",  "HKD", "Large Cap",    "HANGSENG",  0.09),
    ("2828.HK",   "Hang Seng China Enterprises Index ETF","Hang Seng",  "Equity", "Asia-Pacific", "Hong Kong",  "HKD", "Large Cap",    "HANGSENG",  0.60),
    ("069500.KS", "KODEX 200 ETF",                        "Samsung",    "Equity", "Asia-Pacific", "South Korea","KRW", "Large Cap",    "KOSPI",     0.15),
    ("102110.KS", "TIGER 200 ETF",                        "Mirae Asset","Equity", "Asia-Pacific", "South Korea","KRW", "Large Cap",    "KOSPI",     0.05),
    ("0050.TW",   "Yuanta Taiwan Top 50 ETF",             "Yuanta",     "Equity", "Asia-Pacific", "Taiwan",     "TWD", "Large Cap",    "TAIEX",     0.32),
    ("0056.TW",   "Yuanta Taiwan Dividend Plus ETF",      "Yuanta",     "Equity", "Asia-Pacific", "Taiwan",     "TWD", "Dividend",     "TAIEX",     0.40),
    ("NIFTYBEES.NS","Nippon India ETF Nifty 50 BeES",     "Nippon",     "Equity", "Asia-Pacific", "India",      "INR", "Large Cap",    "NIFTY50",   0.04),
    ("VAS.AX",    "Vanguard Australian Shares Index ETF", "Vanguard",   "Equity", "Asia-Pacific", "Australia",  "AUD", "Broad Market", "ASX200",    0.07),
    ("STW.AX",    "SPDR S&P/ASX 200 Fund",                "State Street","Equity","Asia-Pacific", "Australia",  "AUD", "Large Cap",    "ASX200",    0.05),
    ("XIU.TO",    "iShares S&P/TSX 60 Index ETF",         "BlackRock",  "Equity", "Americas",     "Canada",     "CAD", "Large Cap",    "TSX",       0.18),
    ("VFV.TO",    "Vanguard S&P 500 Index ETF",           "Vanguard",   "Equity", "Americas",     "Canada",     "CAD", "Broad Market", "SP500",     0.09),
    # ---------------- Europe: more UCITS coverage ----------------
    ("SXR1.DE", "iShares Core MSCI EMU UCITS ETF",           "BlackRock", "Equity", "Europe", "Germany", "EUR", "Large Cap",     "ESTX50",  0.12),
    ("IQQQ.DE", "iShares Asia Pacific Dividend UCITS ETF",   "BlackRock", "Equity", "Europe", "Germany", "EUR", "Dividend",      "",        0.59),
    ("EXX5.DE", "iShares Dow Jones Global Titans 50",        "BlackRock", "Equity", "Europe", "Germany", "EUR", "Large Cap",     "",        0.51),
    ("EXH1.DE", "iShares STOXX Europe 600 Oil & Gas",        "BlackRock", "Equity", "Europe", "Germany", "EUR", "Sector: Energy","STOXX600",0.46),
    ("EXV1.DE", "iShares STOXX Europe 600 Banks",            "BlackRock", "Equity", "Europe", "Germany", "EUR", "Sector: Financials", "STOXX600", 0.46),
    ("EXV3.DE", "iShares STOXX Europe 600 Technology",       "BlackRock", "Equity", "Europe", "Germany", "EUR", "Sector: Technology", "STOXX600", 0.46),
    ("EXV4.DE", "iShares STOXX Europe 600 Health Care",      "BlackRock", "Equity", "Europe", "Germany", "EUR", "Sector: Health Care", "STOXX600", 0.46),
    ("EXH7.DE", "iShares STOXX Europe 600 Industrials",      "BlackRock", "Equity", "Europe", "Germany", "EUR", "Sector: Industrials", "STOXX600", 0.46),
    ("EUNK.DE", "iShares Core MSCI Europe UCITS ETF",        "BlackRock", "Equity", "Europe", "Germany", "EUR", "Broad Market",  "STOXX600",0.12),
    ("IUSN.DE", "iShares MSCI World Small Cap UCITS ETF",    "BlackRock", "Equity", "Europe", "Germany", "EUR", "Small Cap",     "",        0.35),
    ("QDVE.DE", "iShares S&P 500 Information Technology",    "BlackRock", "Equity", "Europe", "Germany", "EUR", "Sector: Technology", "SP500", 0.15),
    ("QDVD.DE", "iShares S&P 500 Health Care Sector",        "BlackRock", "Equity", "Europe", "Germany", "EUR", "Sector: Health Care", "SP500", 0.15),
    ("SXRV.DE", "iShares Nasdaq 100 UCITS ETF",              "BlackRock", "Equity", "Europe", "Germany", "EUR", "Large Cap",     "NASDAQ100", 0.33),
    ("SPYD.DE", "SPDR S&P Global Dividend Aristocrats",      "State Street", "Equity", "Europe", "Germany", "EUR", "Dividend",   "",        0.45),
    ("SPYW.DE", "SPDR S&P Euro Dividend Aristocrats",        "State Street", "Equity", "Europe", "Germany", "EUR", "Dividend",   "ESTX50",  0.30),
    ("ZPRV.DE", "SPDR MSCI USA Small Cap Value Weighted",    "State Street", "Equity", "Europe", "Germany", "EUR", "Small Cap",  "RUSSELL2000", 0.30),
    ("XDWT.DE", "Xtrackers MSCI World Information Tech",     "DWS",       "Equity", "Europe", "Germany", "EUR", "Sector: Technology", "", 0.25),
    ("XDWH.DE", "Xtrackers MSCI World Health Care",          "DWS",       "Equity", "Europe", "Germany", "EUR", "Sector: Health Care", "", 0.25),
    ("XEON.DE", "Xtrackers II EUR Overnight Rate Swap",      "DWS",       "Bond",   "Europe", "Germany", "EUR", "Money Market",  "",        0.10),
    ("XGLE.DE", "Xtrackers II Eurozone Government Bond",     "DWS",       "Bond",   "Europe", "Germany", "EUR", "Government Mid","",        0.15),
    ("VUAA.DE", "Vanguard S&P 500 UCITS ETF (Acc)",          "Vanguard",  "Equity", "Europe", "Germany", "EUR", "Broad Market",  "SP500",   0.07),
    ("VHYL.L",  "Vanguard FTSE All-World High Dividend",     "Vanguard",  "Equity", "Europe", "United Kingdom", "GBP", "Dividend", "",      0.29),
    ("VMID.L",  "Vanguard FTSE 250 UCITS ETF",               "Vanguard",  "Equity", "Europe", "United Kingdom", "GBP", "Mid Cap",  "FTSE100", 0.10),
    ("VFEM.L",  "Vanguard FTSE Emerging Markets UCITS",      "Vanguard",  "Equity", "Emerging", "Emerging",     "GBP", "Broad Market", "",   0.22),
    ("IWDG.L",  "iShares Core MSCI World UCITS (GBP Hedged)","BlackRock", "Equity", "Europe", "United Kingdom", "GBP", "Broad Market", "",   0.30),
    ("IUKD.L",  "iShares UK Dividend UCITS ETF",             "BlackRock", "Equity", "Europe", "United Kingdom", "GBP", "Dividend", "FTSE100", 0.40),
    ("SGLN.L",  "iShares Physical Gold ETC",                 "BlackRock", "Commodity", "Europe", "United Kingdom", "USD", "Gold", "",       0.12),
    ("EQQQ.L",  "Invesco EQQQ Nasdaq-100 UCITS ETF",         "Invesco",   "Equity", "Europe", "United Kingdom", "USD", "Large Cap", "NASDAQ100", 0.30),
    ("MEUD.PA", "Amundi Stoxx Europe 600 UCITS ETF",         "Amundi",    "Equity", "Europe", "France", "EUR", "Broad Market",    "STOXX600", 0.07),
    ("PAEEM.PA","Amundi MSCI Emerging Markets UCITS ETF",    "Amundi",    "Equity", "Emerging", "Emerging", "EUR", "Broad Market","",        0.20),
    ("LYPS.DE", "Amundi S&P 500 UCITS ETF",                  "Amundi",    "Equity", "Europe", "Germany", "EUR", "Broad Market",  "SP500",   0.05),
    ("IMEU.AS", "iShares Core MSCI Europe UCITS ETF",        "BlackRock", "Equity", "Europe", "Netherlands", "EUR", "Broad Market", "STOXX600", 0.12),
    ("VWRA.L",  "Vanguard FTSE All-World UCITS ETF (Acc)",   "Vanguard",  "Equity", "Europe", "United Kingdom", "USD", "Broad Market", "",   0.22),
    # ---------------- Asia-Pacific: more local listings ----------------
    ("1330.T",  "Daiwa ETF Nikkei 225",                      "Daiwa",     "Equity", "Asia-Pacific", "Japan", "JPY", "Large Cap", "NIKKEI225", 0.16),
    ("1348.T",  "MAXIS TOPIX ETF",                           "Mitsubishi UFJ", "Equity", "Asia-Pacific", "Japan", "JPY", "Broad Market", "NIKKEI225", 0.08),
    ("1671.T",  "WisdomTree WTI Crude Oil",                  "WisdomTree","Commodity", "Asia-Pacific", "Japan", "JPY", "Energy", "",        0.49),
    ("2801.HK", "iShares Core MSCI China ETF",               "BlackRock", "Equity", "Asia-Pacific", "Hong Kong", "HKD", "Country", "HANGSENG", 0.20),
    ("3067.HK", "iShares Hang Seng TECH ETF",                "BlackRock", "Equity", "Asia-Pacific", "Hong Kong", "HKD", "Sector: Technology", "HANGSENG", 0.25),
    ("2836.HK", "iShares Core S&P BSE SENSEX India ETF",     "BlackRock", "Equity", "Asia-Pacific", "India", "HKD", "Country",   "SENSEX",  0.64),
    ("3033.HK", "CSOP Hang Seng TECH Index ETF",             "CSOP",      "Equity", "Asia-Pacific", "Hong Kong", "HKD", "Sector: Technology", "HANGSENG", 0.99),
    ("069660.KS","KODEX 200 TR",                             "Samsung",   "Equity", "Asia-Pacific", "South Korea", "KRW", "Large Cap", "KOSPI", 0.15),
    ("091160.KS","KODEX Semiconductor ETF",                  "Samsung",   "Equity", "Asia-Pacific", "South Korea", "KRW", "Sector: Semiconductors", "KOSPI", 0.45),
    ("0051.TW", "Yuanta Taiwan Mid-Cap 100 ETF",             "Yuanta",    "Equity", "Asia-Pacific", "Taiwan", "TWD", "Mid Cap",   "TAIEX",   0.40),
    ("00878.TW","Cathay Sustainability High Dividend ETF",   "Cathay",    "Equity", "Asia-Pacific", "Taiwan", "TWD", "Dividend",  "TAIEX",   0.30),
    ("00646.TW","Yuanta S&P 500 ETF",                        "Yuanta",    "Equity", "Asia-Pacific", "Taiwan", "TWD", "Broad Market", "SP500", 0.53),
    ("BANKBEES.NS","Nippon India ETF Nifty Bank BeES",       "Nippon",    "Equity", "Asia-Pacific", "India", "INR", "Sector: Financials", "NIFTY50", 0.19),
    ("JUNIORBEES.NS","Nippon India ETF Nifty Next 50",       "Nippon",    "Equity", "Asia-Pacific", "India", "INR", "Mid Cap",   "NIFTY50", 0.15),
    ("SETFNIF50.NS","SBI Nifty 50 ETF",                      "SBI",       "Equity", "Asia-Pacific", "India", "INR", "Large Cap", "NIFTY50", 0.07),
    ("VGS.AX",  "Vanguard MSCI Intl Shares ETF",             "Vanguard",  "Equity", "Asia-Pacific", "Australia", "AUD", "Broad Market", "",   0.18),
    ("IOZ.AX",  "iShares Core S&P/ASX 200 ETF",              "BlackRock", "Equity", "Asia-Pacific", "Australia", "AUD", "Large Cap", "ASX200", 0.05),
    ("A200.AX", "Betashares Australia 200 ETF",              "Betashares","Equity", "Asia-Pacific", "Australia", "AUD", "Large Cap", "ASX200", 0.04),
    ("NDQ.AX",  "Betashares Nasdaq 100 ETF",                 "Betashares","Equity", "Asia-Pacific", "Australia", "AUD", "Large Cap", "NASDAQ100", 0.48),
    ("ES3.SI",  "SPDR Straits Times Index ETF",              "State Street", "Equity", "Asia-Pacific", "Singapore", "SGD", "Large Cap", "STI", 0.30),
    ("CLR.SI",  "Lion-OCBC Securities Hang Seng TECH ETF",   "Lion Global", "Equity", "Asia-Pacific", "Singapore", "SGD", "Sector: Technology", "HANGSENG", 0.45),
    # ---------------- Americas: more local listings ----------------
    ("XIC.TO",  "iShares Core S&P/TSX Capped Composite",     "BlackRock", "Equity", "Americas", "Canada", "CAD", "Broad Market",  "TSX",     0.06),
    ("ZSP.TO",  "BMO S&P 500 Index ETF",                     "BMO",       "Equity", "Americas", "Canada", "CAD", "Broad Market",  "SP500",   0.09),
    ("XEQT.TO", "iShares Core Equity ETF Portfolio",         "BlackRock", "Equity", "Americas", "Canada", "CAD", "Broad Market",  "",        0.20),
    ("BOVA11.SA","iShares Ibovespa Index Fund",              "BlackRock", "Equity", "Americas", "Brazil", "BRL", "Broad Market",  "BOVESPA", 0.54),
    ("IVVB11.SA","iShares S&P 500 BDR Fund",                 "BlackRock", "Equity", "Americas", "Brazil", "BRL", "Broad Market",  "SP500",   0.24),
    ("NAFTRAC.MX","BlackRock NAFTRAC S&P/BMV IPC",           "BlackRock", "Equity", "Americas", "Mexico", "MXN", "Broad Market",  "IPC",     0.25),
    # ---------------- Fixed income (US listed) ----------------
    ("AGG",  "iShares Core US Aggregate Bond ETF",     "BlackRock",  "Bond", "US",     "United States", "USD", "Aggregate Bond",   "", 0.03),
    ("BND",  "Vanguard Total Bond Market ETF",         "Vanguard",   "Bond", "US",     "United States", "USD", "Aggregate Bond",   "", 0.03),
    ("TLT",  "iShares 20+ Year Treasury Bond ETF",     "BlackRock",  "Bond", "US",     "United States", "USD", "Government Long",  "", 0.15),
    ("IEF",  "iShares 7-10 Year Treasury Bond ETF",    "BlackRock",  "Bond", "US",     "United States", "USD", "Government Mid",   "", 0.15),
    ("SHY",  "iShares 1-3 Year Treasury Bond ETF",     "BlackRock",  "Bond", "US",     "United States", "USD", "Government Short", "", 0.15),
    ("LQD",  "iShares iBoxx IG Corporate Bond ETF",    "BlackRock",  "Bond", "US",     "United States", "USD", "Corporate IG",     "", 0.14),
    ("HYG",  "iShares iBoxx High Yield Corporate ETF", "BlackRock",  "Bond", "US",     "United States", "USD", "High Yield",       "", 0.49),
    ("TIP",  "iShares TIPS Bond ETF",                  "BlackRock",  "Bond", "US",     "United States", "USD", "Inflation Linked", "", 0.19),
    ("EMB",  "iShares JP Morgan USD EM Bond ETF",      "BlackRock",  "Bond", "Emerging","Emerging",     "USD", "EM Debt",          "", 0.39),
    ("BNDX", "Vanguard Total International Bond ETF",  "Vanguard",   "Bond", "Global", "Global",        "USD", "Aggregate Bond",   "", 0.07),
    # ---------------- Commodities, real assets, crypto ----------------
    ("GLD",  "SPDR Gold Shares",                       "State Street","Commodity",  "Global", "Global",        "USD", "Gold",        "", 0.40),
    ("IAU",  "iShares Gold Trust",                     "BlackRock",   "Commodity",  "Global", "Global",        "USD", "Gold",        "", 0.25),
    ("SLV",  "iShares Silver Trust",                   "BlackRock",   "Commodity",  "Global", "Global",        "USD", "Silver",      "", 0.50),
    ("DBC",  "Invesco DB Commodity Index Tracking",    "Invesco",     "Commodity",  "Global", "Global",        "USD", "Broad Commodity","", 0.85),
    ("USO",  "United States Oil Fund",                 "USCF",        "Commodity",  "Global", "Global",        "USD", "Energy",      "", 0.60),
    ("4GLD.DE","Xetra-Gold",                           "Deutsche Boerse","Commodity","Europe","Germany",       "EUR", "Gold",        "", 0.00),
    ("VNQ",  "Vanguard Real Estate ETF",               "Vanguard",    "Real Estate","US",     "United States", "USD", "REIT",        "", 0.13),
    ("VNQI", "Vanguard Global ex-US Real Estate ETF",  "Vanguard",    "Real Estate","Global", "Global",        "USD", "REIT",        "", 0.12),
    ("IBIT", "iShares Bitcoin Trust ETF",              "BlackRock",   "Crypto",     "Global", "Global",        "USD", "Bitcoin",     "", 0.25),
    ("BTC-USD","Bitcoin (spot)",                       "-",           "Crypto",     "Global", "Global",        "USD", "Bitcoin",     "", 0.00),
]

# --------------------------------------------------------------------------
# 4. FX — currencies that must be converted for cross-market comparison
# --------------------------------------------------------------------------

CURRENCIES = [
    "USD", "EUR", "VND", "GBP", "JPY", "CHF", "HKD", "CNY", "KRW", "TWD",
    "INR", "SGD", "THB", "MYR", "IDR", "PHP", "AUD", "CAD", "BRL", "MXN",
]

# Currencies offered as a display / reporting currency in the UI.
DISPLAY_CURRENCIES = ["USD", "EUR", "VND"]

# Regions in a stable display order.
REGION_ORDER = ["Vietnam", "US", "Europe", "Asia-Pacific", "Americas", "Emerging", "Global"]


def vn_symbol_candidates(ticker: str) -> list[str]:
    """Every spelling worth trying for a Vietnamese ticker, best guess first."""
    return VN_SYMBOL_ALIASES.get(ticker, [ticker])


def _vn_rows():
    rows = []
    for tk, name, issuer, kind, aclass, cat, bench, ter, inception in VN_ASSETS:
        rows.append(dict(
            ticker=tk, source="vndirect", symbol=tk, name=name, kind=kind,
            asset_class=aclass, region="Vietnam", country="Vietnam", currency="VND",
            issuer=issuer, ter=ter, benchmark=bench, category=cat, inception=inception,
        ))
    return rows


def _index_rows():
    rows = []
    for tk, sym, name, region, country, ccy, cat in WORLD_INDICES:
        rows.append(dict(
            ticker=tk, source="yahoo", symbol=sym, name=name, kind="Index",
            asset_class="Equity" if cat != "Volatility" else "Volatility",
            region=region, country=country, currency=ccy, issuer="-", ter=0.0,
            benchmark="", category=cat, inception="",
        ))
    return rows


def _world_etf_rows():
    rows = []
    for tk, name, issuer, aclass, region, country, ccy, cat, bench, ter in WORLD_ETFS:
        rows.append(dict(
            ticker=tk, source="yahoo", symbol=tk, name=name, kind="ETF",
            asset_class=aclass, region=region, country=country, currency=ccy,
            issuer=issuer, ter=ter, benchmark=bench, category=cat, inception="",
        ))
    return rows


def static_universe() -> pd.DataFrame:
    """Everything that is known ahead of time (VN + world, no mutual funds)."""
    df = pd.DataFrame(_vn_rows() + _index_rows() + _world_etf_rows())
    return df.drop_duplicates(subset="ticker").reset_index(drop=True)


def vndirect_symbols() -> list[str]:
    return [r["symbol"] for r in _vn_rows()]


def yahoo_symbols() -> list[str]:
    return [r["symbol"] for r in _index_rows() + _world_etf_rows()]


def fx_pairs() -> list[tuple[str, str, bool]]:
    """(currency, yahoo symbol, invert) for every non-USD currency."""
    pairs = []
    for ccy in CURRENCIES:
        if ccy == "USD":
            continue
        pairs.append((ccy, f"{ccy}USD=X", False))
    return pairs


if __name__ == "__main__":
    u = static_universe()
    print(f"{len(u)} instruments")
    print(u.groupby(["region", "kind"]).size())
