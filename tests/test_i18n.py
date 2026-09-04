"""The report must be complete in all three languages."""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import i18n  # noqa: E402


def test_all_languages_have_the_same_keys():
    assert i18n.missing_keys() == {"VI": [], "DE": []}
    base = set(i18n.STRINGS["EN"])
    for lang, table in i18n.STRINGS.items():
        assert set(table) == base, f"{lang} has extra/missing keys"


def test_no_empty_translations():
    for lang, table in i18n.STRINGS.items():
        for key, value in table.items():
            assert value and value.strip(), f"{lang}:{key} is empty"


def test_translations_are_actually_translated():
    """Prose keys must differ between languages (catches copy-paste stubs)."""
    prose = [k for k in i18n.STRINGS["EN"] if k.startswith(("x_", "app_", "h_"))]
    identical = [k for k in prose
                 if i18n.STRINGS["EN"][k] == i18n.STRINGS["VI"][k]
                 and i18n.STRINGS["EN"][k] == i18n.STRINGS["DE"][k]]
    assert not identical, f"untranslated keys: {identical}"


def test_narratives_render_in_every_language():
    facts = {
        "start": "01.01.2020", "end": "01.01.2026", "currency": "USD",
        "benchmark": "SP500", "benchmark_cagr": 0.10, "best": "QQQ",
        "best_cagr": 0.15, "worst": "AGG", "worst_cagr": 0.01,
        "best_sharpe": "QQQ", "best_sharpe_value": 0.9, "deepest_dd": "QQQ",
        "deepest_dd_value": -0.3, "beat_count": 2, "total": 5, "avg_corr": 0.42,
    }
    for lang in i18n.STRINGS:
        for text in [
            i18n.summary_narrative(lang, facts),
            i18n.tracking_narrative(lang, "SPY", 0.01, 0.5, 1.0, 0.002, "SP500"),
            i18n.market_narrative(lang, "US", 0.12, "Europe", 0.04, "USD"),
            i18n.drawdown_narrative(lang, "SPY", -0.05, -0.33, 180),
            i18n.strategy_narrative(lang, 66.0, 0.5, 0.4, 5),
            i18n.cost_narrative(lang, "SPY", 0.09, 0.02, 20),
            i18n.forecast_narrative(lang, "SPY", 55.0, 0.02, 380.0, 460.0, 60),
            i18n.quality_narrative(lang, 180, 25, 12, "28.08.2026", 3),
        ]:
            assert len(text) > 40
            assert "None" not in text


def test_narrative_handles_missing_numbers():
    for lang in i18n.STRINGS:
        text = i18n.tracking_narrative(lang, "X", float("nan"), float("nan"),
                                       float("nan"), float("nan"), "B")
        assert "n/a" in text


def test_fallback_to_english_for_unknown_key():
    assert i18n.t("VI", "does_not_exist") == "does_not_exist"
    assert i18n.t("XX", "tab_summary") == i18n.STRINGS["EN"]["tab_summary"]


def test_quality_narrative_agrees_in_number():
    """"1 tickers are stale" is the kind of thing that makes a report look
    generated rather than written."""
    assert "1 ticker is" in i18n.quality_narrative("EN", 500, 30, 20, "04.09.2026", 1)
    assert "2 tickers are" in i18n.quality_narrative("EN", 500, 30, 20, "04.09.2026", 2)
    assert "0 tickers are" in i18n.quality_narrative("EN", 500, 30, 20, "04.09.2026", 0)
    assert "1 Ticker ist" in i18n.quality_narrative("DE", 500, 30, 20, "04.09.2026", 1)
    assert "3 Ticker sind" in i18n.quality_narrative("DE", 500, 30, 20, "04.09.2026", 3)
