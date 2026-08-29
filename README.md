# 🌍 Global ETF & Fund Report

Fully automated, trilingual (🇻🇳 Tiếng Việt · 🇬🇧 English · 🇩🇪 Deutsch) analytics report
comparing **ETFs from every major market** — Vietnam, the US, Europe, Asia-Pacific,
the Americas, emerging and frontier markets — against **their benchmark indices**,
with Vietnamese open-ended funds included for reference.

Every number in the report is computed from data that refreshes itself daily; no
manual step, no API key, no spreadsheet.

```bash
pip install -r requirements.txt
python update_data.py     # fetch everything (Vietnam + world + FX)
streamlit run app.py      # open the report
```

---

## What the report covers

| | |
|---|---|
| **Universe** | ~190 curated instruments: 14 Vietnamese ETFs, 11 Vietnamese indices, 100+ world ETFs (US, Germany/Xetra, London, Euronext, Tokyo, Hong Kong, Seoul, Taipei, Mumbai, Sydney, Toronto…), 32 world benchmark indices, bonds, commodities, REITs and crypto — plus every Vietnamese open-ended fund distributed on fmarket, discovered automatically |
| **Currencies** | 20 trading currencies, all convertible to a single reporting currency (USD / EUR / VND) at the **daily** FX rate, so cross-market comparison is honest |
| **Benchmarks** | any index in the universe can be made the benchmark; beta, alpha, R², tracking error, information ratio, up/down capture and batting average are computed against it |
| **Languages** | the whole UI *and* the generated commentary exist in VI / EN / DE; a test fails CI if a translation is missing |

## The twelve sections

1. **Summary** — auto-written commentary, headline KPIs, composite leaderboard, exports
2. **Performance** — rebased wealth curves, returns by period (1M…MAX), calendar years, rolling returns with win rates
3. **Risk** — drawdown bands, deepest drawdown episodes with recovery times, VaR/CVaR, Ulcer, skew, kurtosis, rolling volatility
4. **Risk–Return** — risk/return map against the benchmark, ranking table, Monte-Carlo efficient frontier
5. **vs Benchmark** — alpha/beta/TE/IR table, rolling tracking error, rolling beta, capture ratios
6. **Global markets** — performance by region and by country, currency-effect decomposition
7. **Correlation** — correlation matrix, average pairwise correlation, rolling correlation to the benchmark
8. **Costs & Structure** — TER against realised performance, fee-erosion simulation, liquidity
9. **Cycles & Seasonality** — bull/bear behaviour, monthly heatmap, month-of-year seasonality
10. **Strategy** — DCA simulation, lump sum vs DCA rolled over the whole history, rebalanced portfolios
11. **Forecast** — damped-trend ETS with a confidence band, Monte-Carlo distribution
12. **Data & Method** — coverage, staleness, the full universe table, methodology

Every chart is accompanied by an explanation, and each section carries an
**automatically generated comment** built from that section's own numbers —
in the language currently selected.

## Automation

`.github/workflows/daily_update.yml` runs every day at 10:15 UTC (17:15 Vietnam):

1. installs dependencies and **runs the test suite**
2. `python update_data.py` — Vietnam (VNDIRECT) → open-ended funds (fmarket) →
   world ETFs and indices (Yahoo Finance, Stooq as fallback) → FX rates
   (Yahoo → Frankfurter → open.er-api)
3. writes `data/prices.csv`, `data/volume.csv`, `data/profile.csv`, `data/fx.csv`
   and a machine-readable health report in `data/status.json`
4. renders `docs/report_VI.md`, `docs/report_EN.md`, `docs/report_DE.md`
5. commits and pushes

Any single source failing degrades gracefully: the ticker is recorded in
`status.json` and the rest of the report still builds.

## Files

| File | Purpose |
|---|---|
| `universe.py` | master metadata of every ETF, index and currency |
| `sources.py` | VNDIRECT, Yahoo, Stooq, fmarket and FX fetchers |
| `update_data.py` | daily orchestrator, writes `data/` and the legacy CSVs |
| `analytics.py` | the metric engine (risk, benchmark-relative, rolling, strategy, scoring) |
| `i18n.py` | VI/EN/DE dictionary and the data-driven narrative generators |
| `report.py` | dataset loading + Markdown export (`python report.py --lang DE`) |
| `app.py` | the Streamlit report |
| `metrics.py` | thin compatibility shim over `analytics.py` |
| `tests/` | 41 tests covering analytics, i18n completeness and the pipeline |

---

## 🇻🇳 Tiếng Việt

Báo cáo phân tích **tự động hoàn toàn**, so sánh ETF trên **mọi thị trường** (Việt Nam,
Mỹ, châu Âu, châu Á – Thái Bình Dương, châu Mỹ, thị trường mới nổi và cận biên) với
**các chỉ số tham chiếu**, kèm quỹ mở Việt Nam để đối chiếu.

- Mọi mức giá được **quy đổi về cùng một đồng tiền** (USD / EUR / VND) theo tỷ giá từng
  ngày, nên việc so sánh giữa các thị trường là công bằng.
- Danh sách quỹ mở được **lấy trực tiếp từ fmarket**: quỹ mới xuất hiện trong báo cáo
  mà không cần sửa code.
- Toàn bộ nhận định trong báo cáo được **sinh tự động từ số liệu**, bằng ngôn ngữ đang chọn.
- GitHub Actions cập nhật dữ liệu hàng ngày lúc 17:15 giờ Việt Nam.

## 🇩🇪 Deutsch

Ein **vollautomatischer**, dreisprachiger Analysebericht, der ETFs **aus allen großen
Märkten** (Vietnam, USA, Europa, Asien-Pazifik, Amerika, Schwellen- und Frontier-Märkte)
mit **ihren Benchmark-Indizes** vergleicht; vietnamesische Publikumsfonds sind als
Referenz enthalten.

- Alle Kurse werden zum **Tageskurs in eine gemeinsame Berichtswährung** (USD / EUR / VND)
  umgerechnet — nur so ist ein Marktvergleich fair.
- Der Fondskatalog wird **live von fmarket** geladen, neue Fonds erscheinen ohne Codeänderung.
- Sämtliche Kommentare werden **aus den Zahlen selbst generiert**, in der gewählten Sprache.
- GitHub Actions aktualisiert die Daten täglich um 10:15 UTC.

---

*Automated report — for information only, not investment advice.*
*Báo cáo tự động — chỉ mang tính tham khảo, không phải khuyến nghị đầu tư.*
*Automatisierter Bericht — nur zur Information, keine Anlageberatung.*
