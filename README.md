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

## How the report is organised

Seven sections, not a wall of tabs. The sidebar holds the four settings that
define *every* number on screen (reporting currency, benchmark, time range,
risk-free rate); everything else is one click away.

| Section | What it answers |
|---|---|
| 🏠 **Overview** | What does my current selection look like — auto-written commentary, headline KPIs, a ranked leaderboard with sparklines, wealth curves, exports |
| 🔎 **Screener** | Which of the ~250 instruments deserve a look — filter the whole universe on CAGR, volatility, Sharpe, drawdown, fee and history, then tick rows to add them to the comparison |
| 📊 **Compare** | How do they stack up — sub-tabs for performance, risk, risk-return positioning, benchmark-relative statistics and correlation |
| 🌐 **Markets** | Which market won — region and country matrix, plus how much of the result was currency rather than performance |
| 🔬 **Fund profile** | Everything about one fund — key facts, percentile against its peer group, price and moving averages, drawdown episodes, monthly heatmap, seasonality, forecast, every metric |
| 🧪 **Lab** | What would an investor actually have got — DCA, lump sum vs DCA rolled over history, a portfolio builder with risk contribution, fee erosion |
| 🗂️ **Data** | Can I trust this — coverage, staleness, failed downloads, the searchable universe and the methodology |

### Interaction

- **A navigation dock** on the left holds the seven sections, the scope filters
  and the four parameters, grouped. It dims to 62% until the pointer reaches it,
  so the data owns the screen.
- **Scope filters cascade**: region narrows the countries, country narrows the
  asset classes, and so on. Whatever survives is the report's universe — the
  screener, the markets view, the pickers *and* the comparison list all follow it.
- **Click a point** on any risk-return or fee-vs-performance chart to open that
  fund's profile.
- **Tick rows** in the screener, the leaderboard or the universe table and add
  them to the comparison in one click.
- **Chart toggles** on the wealth curves: logarithmic scale, and a relative mode
  that divides every line by the benchmark.
- **A readout under every chart** states what that chart actually shows —
  written from its own numbers, in the current language, not a static caption.
- **The URL carries the state.** Language, section, filters, selection,
  benchmark, currency, period and risk-free rate all travel in the link.

### Design

Enterprise bento, minimalist. Modular white cards on a neutral ground, hairline
borders, no shadows, no decorative colour. Colour carries meaning only: one
accent for interactive chrome, green and red reserved for gains and losses, a
diverging red-to-green scale for the year × month growth heatmap. Type is Roboto
with tabular figures, so columns of numbers line up. Charts follow the same
grammar — no frame, hairline gridlines, and the benchmark always dotted grey.

## Automation

`.github/workflows/daily_update.yml` runs **twice a day** — 10:15 UTC (17:15
Vietnam, after the HOSE close) and 22:30 UTC (after the US close, so Europe and
Asia are captured on their own trading day). There is no refresh button in the
report: freshness is the pipeline's job, and the header shows how old the data
is at a glance.

1. installs dependencies and **runs the test suite**
2. `python update_data.py` — Vietnam (VNDIRECT) → open-ended funds (fmarket) →
   world ETFs and indices (Yahoo Finance, Stooq as fallback) → FX rates
   (Yahoo → Frankfurter → open.er-api)
3. retries three times, then fails the run if the newest date is more than 5
   days old or fewer than 100 instruments came back
4. writes `data/prices.csv`, `data/volume.csv`, `data/profile.csv`, `data/fx.csv`
   and a machine-readable health report in `data/status.json`
5. renders `docs/report_VI.md`, `docs/report_EN.md`, `docs/report_DE.md`
6. commits and pushes

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
| `app.py` | application shell: page frame, sidebar, navigation |
| `ui/theme.py` | palette, CSS and chart styling |
| `ui/state.py` | session state, URL sync and the context handed to every view |
| `ui/components.py` | shared widgets: leaderboards, sparklines, click-to-focus charts |
| `views/*.py` | one module per section (overview, screener, compare, markets, profile, lab, data) |
| `.streamlit/config.toml` | the design tokens Streamlit applies to its own widgets |
| `metrics.py` | thin compatibility shim over `analytics.py` |
| `tests/` | 75 tests covering analytics, i18n completeness, the pipeline and every view |

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
- Giao diện chia thành 7 phần: Tổng quan · Bộ lọc quỹ · So sánh · Thị trường · Hồ sơ quỹ ·
  Phòng thí nghiệm · Dữ liệu. Bấm vào một điểm trên biểu đồ để mở hồ sơ quỹ đó, tick dòng
  trong bộ lọc để thêm vào danh sách so sánh, và mọi cấu hình đều nằm trong URL để chia sẻ.
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
- Die Oberfläche gliedert sich in sieben Bereiche: Überblick · Screener · Vergleich · Märkte ·
  Fondsprofil · Labor · Daten. Ein Klick auf einen Punkt im Diagramm öffnet das Fondsprofil,
  markierte Zeilen wandern in den Vergleich, und der komplette Zustand steht in der URL.
- GitHub Actions aktualisiert die Daten täglich um 10:15 UTC.

---

*Automated report — for information only, not investment advice.*
*Báo cáo tự động — chỉ mang tính tham khảo, không phải khuyến nghị đầu tư.*
*Automatisierter Bericht — nur zur Information, keine Anlageberatung.*
