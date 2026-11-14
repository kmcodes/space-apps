import pandas as pd
import pytest

from engine.market import MarketData, market_score


def mandi(rows):
    return pd.DataFrame(rows, columns=["point", "crop", "month", "n_prices", "median_modal_price",
                                       "min_modal_price", "max_modal_price"])


def msp(rows):
    return pd.DataFrame(rows, columns=["crop", "variety", "marketing_season", "msp_rs_per_quintal", "validity"])


def months(n, start="2025-12"):
    y, m = map(int, start.split("-"))
    out = []
    for _ in range(n):
        out.append(f"{y}-{m:02d}")
        m += 1
        if m > 12:
            y, m = y + 1, 1
    return out


# ---- the score formula ----------------------------------------------------
def test_price_at_msp_scores_a_third_and_no_volatility_means_no_haircut():
    assert market_score(1.0, 0.0) == pytest.approx(100 / 3)


def test_price_far_above_msp_caps_at_100_and_far_below_floors_at_0():
    assert market_score(1.6, 0.0) == 100
    assert market_score(0.7, 0.0) == 0


def test_volatility_takes_a_haircut_capped_at_thirty_percent():
    assert market_score(1.4, 0.15) == pytest.approx(100 * (1 - 0.30 * 0.15 / 0.30))
    assert market_score(1.4, 0.90) == pytest.approx(70)


# ---- the data layer -------------------------------------------------------
def test_signal_uses_last_12_months_against_msp():
    rows = [("akola", "chickpea", mo, 10, 5000, 4500, 5500) for mo in months(12)]
    rows.append(("akola", "chickpea", "2020-01", 10, 99999, 1, 99999))  # old outlier must be ignored
    md = MarketData(mandi(rows), msp([("chickpea", "gram", "rabi 2026-27", 5000, "valid")]))
    r = md.component("akola", "chickpea")
    assert r.status == "ok"
    assert r.detail["ratio"] == pytest.approx(1.0)
    assert r.score == pytest.approx(100 / 3)


def test_no_mandi_rows_is_a_gap_even_if_an_msp_exists():
    md = MarketData(mandi([]), msp([("cotton", "medium staple", "kharif 2026-27", 8267, "unverified")]))
    r = md.component("washim", "cotton")
    assert r.score is None and r.status == "missing"
    assert "MSP only" in r.detail["reason"]


def test_validity_is_the_worst_of_prices_and_msp():
    rows = [("akola", "soybean", mo, 10, 5000, 4500, 5500) for mo in months(12)]
    md = MarketData(mandi(rows), msp([("soybean", "yellow", "kharif 2026-27", 5000, "unverified")]))
    assert md.component("akola", "soybean").validity == "unverified"
    md2 = MarketData(mandi(rows), msp([("soybean", "yellow", "kharif 2026-27", 5000, "valid")]))
    assert md2.component("akola", "soybean").validity == "valid"


def test_prefers_current_marketing_season_msp():
    rows = [("akola", "chickpea", mo, 10, 6000, 5500, 6500) for mo in months(12)]
    md = MarketData(mandi(rows), msp([("chickpea", "gram", "rabi 2025-26", 5000, "valid"),
                                      ("chickpea", "gram", "rabi 2026-27", 6000, "valid")]))
    assert md.component("akola", "chickpea").detail["ratio"] == pytest.approx(1.0)


def test_volatile_prices_lower_the_score():
    steady = [("akola", "soybean", mo, 10, 5000, 4500, 5500) for mo in months(12)]
    wild = [("akola", "soybean", mo, 10, 5000 + (1500 if i % 2 else -1500), 4500, 5500) for i, mo in enumerate(months(12))]
    m = msp([("soybean", "yellow", "kharif 2026-27", 4000, "valid")])
    assert MarketData(mandi(wild), m).component("akola", "soybean").score < MarketData(mandi(steady), m).component("akola", "soybean").score


def test_fallow_is_not_applicable_and_unpriced_crops_are_gaps():
    md = MarketData(mandi([]), msp([]))
    assert md.component("akola", "fallow").status == "na"
    assert md.component("akola", "sunn_hemp").status == "missing"
