from engine.card import build_card
from engine.components import Result
from engine.evidence import describe
from tests.helpers import make_crop

CTX = {"weather": {"dataset": "NASA POWER daily (AG community)", "period": "1981-2025",
                   "resolution": "~50 km grid, point value"}}
FIELDS = {"claim", "value", "dataset", "period", "resolution", "validity", "validity_reason", "used_in", "gap"}


def test_an_ok_water_fit_line_has_every_field_and_quotes_its_numbers():
    r = Result(80.0, "ok", "degraded", {"kind": "kharif rain / need", "rain_mm": 749.3, "need_mm": 575.0})
    line = describe("water_fit", r, CTX)
    assert FIELDS <= set(line)
    assert "NASA POWER" in line["dataset"] and line["period"] == "1981-2025"
    assert "749" in line["claim"] and "575" in line["claim"]
    assert line["validity"] == "degraded" and line["validity_reason"]


def test_a_missing_component_becomes_a_gap_line_not_a_score():
    r = Result(None, "missing", "unverified", {"reason": "water_need_mm is missing for: pig"})
    line = describe("water_fit", r, CTX)
    assert line["value"] is None
    assert "pig" in line["gap"]
    assert line["validity"] == "unverified"


def test_not_applicable_components_have_no_line():
    assert describe("market", Result(None, "na", "valid", {}), CTX) is None


def test_market_line_names_prices_and_msp():
    r = Result(40.0, "ok", "unverified", {"ratio": 0.96, "price_rs_per_quintal": 5655.0, "msp_rs_per_quintal": 5875.0,
                                           "volatility": 0.05, "months": 12, "msp_season": "rabi 2026-27"})
    line = describe("market", r, CTX)
    assert "5655" in line["claim"] and "5875" in line["claim"]
    assert "Agmarknet" in line["dataset"]


def comps():
    return {
        "water_fit": Result(90.0, "ok", "degraded", {}),
        "market": Result(None, "missing", "unverified", {"reason": "no mandi price data (MSP only)"}),
        "nitrogen": Result(100.0, "ok", "unverified", {}),
    }


def test_card_always_has_the_five_sections_and_a_review_risk():
    card = build_card("S1", comps(), {"water_fit": 60.0, "nitrogen": 40.0}, [], {}, [make_crop()])
    assert set(card) == {"why_suggested", "evidence", "benefits", "gaps", "risks_for_local_review"}
    assert any("local" in r.lower() for r in card["risks_for_local_review"])


def test_card_lists_missing_components_as_gaps():
    card = build_card("S1", comps(), {"water_fit": 60.0, "nitrogen": 40.0}, [], {}, [make_crop()])
    assert any("no mandi price data" in g for g in card["gaps"])


def test_card_explains_why_with_the_biggest_contributor():
    card = build_card("S1", comps(), {"water_fit": 60.0, "nitrogen": 40.0}, [], {}, [make_crop()])
    assert "water" in card["why_suggested"].lower()


def test_card_flags_sprayer_crop_when_farmer_has_basic_equipment():
    sprayer = make_crop(name="cotton", equipment="sprayer")
    card = build_card("S2", comps(), {"water_fit": 100.0}, [], {"equipment": "basic"}, [sprayer])
    assert any("sprayer" in r.lower() for r in card["risks_for_local_review"])


def test_card_benefits_list_strong_components():
    card = build_card("S1", comps(), {"water_fit": 60.0, "nitrogen": 40.0}, [], {}, [make_crop()])
    assert any("nitrogen" in b.lower() for b in card["benefits"])


def test_card_flags_unverified_inputs_as_gaps():
    card = build_card("S1", comps(), {"water_fit": 60.0, "nitrogen": 40.0}, [], {}, [make_crop()])
    assert any("unverified" in g.lower() for g in card["gaps"])
