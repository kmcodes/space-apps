import pytest

from engine.compare import Engine

ENGINE = Engine.from_repo()
REQ = {"location": "akola", "current_rotation": "soybean_fallow", "water_source": "rainfed",
       "priorities": ["water_saving"],
       "constraints": {"water_availability": "low", "equipment": "basic", "market": "mandi"}}
LINE_FIELDS = {"claim", "value", "dataset", "period", "resolution", "validity", "validity_reason", "used_in", "gap"}


def run(**over):
    return ENGINE.compare({**REQ, **over})


def test_returns_four_strategies_in_order_with_the_expected_keys():
    out = run()
    assert [s["id"] for s in out["strategies"]] == ["S0", "S1", "S2", "S3"]
    for s in out["strategies"]:
        assert {"name", "total_score", "score_band", "rank_stability", "confidence", "confidence_label",
                "components", "card", "evidence", "score_by_source", "weights"} <= set(s)


def test_top_level_has_weights_disclaimer_and_location_levels():
    out = run()
    assert out["served"] is True
    assert sum(out["weights_used"].values()) == pytest.approx(100)
    assert "does not replace" in out["disclaimer"]
    assert out["location"]["nearest"] == "akola"
    assert out["location"]["layers"]["soil"]["resolution_m"] == 250


def test_no_strategy_is_shown_without_gaps_and_review_risks():
    for s in run()["strategies"]:
        assert s["card"]["gaps"], s["id"]
        assert any("local review" in r for r in s["card"]["risks_for_local_review"]), s["id"]


def test_every_evidence_line_carries_dataset_period_and_validity():
    for s in run()["strategies"]:
        for line in s["evidence"]:
            assert LINE_FIELDS <= set(line)
            assert line["dataset"] and line["period"] and line["validity"] in {"valid", "degraded", "unverified"}


def test_blank_is_not_zero_pigeon_pea_water_need_is_a_gap_for_the_intercrop():
    s2 = {s["id"]: s for s in run()["strategies"]}["S2"]
    assert s2["components"]["water_fit"]["status"] == "missing"
    assert s2["components"]["water_fit"]["score"] is None
    assert any("water" in g.lower() and "pigeon" in g.lower() for g in s2["card"]["gaps"])


def test_changing_priority_changes_the_scores():
    a = {s["id"]: s["total_score"] for s in run(priorities=["water_saving"])["strategies"]}
    b = {s["id"]: s["total_score"] for s in run(priorities=["market_income"])["strategies"]}
    assert a != b


def test_score_band_brackets_the_median_and_rank_stability_sums_to_one():
    out = run()
    for s in out["strategies"]:
        lo, hi = s["score_band"]
        assert lo <= s["total_score"] <= hi
    assert sum(s["rank_stability"] for s in out["strategies"]) == pytest.approx(1.0)


def test_era5_cross_check_is_reported_for_each_strategy():
    for s in run()["strategies"]:
        assert {"power", "era5"} <= set(s["score_by_source"])


def test_s3_shows_variants_as_alternatives_not_as_the_default():
    s3 = {s["id"]: s for s in run()["strategies"]}["S3"]
    assert set(s3["variants"]) == {"sunn_hemp", "horse_gram"}


def test_existing_rotation_equal_to_s1_is_flagged_as_duplicate():
    s0 = run(current_rotation="soybean_chickpea")["strategies"][0]
    assert s0["duplicate_of"] == "S1"


def test_gps_point_far_from_any_data_is_not_served_and_gets_no_strategies():
    out = ENGINE.compare({**REQ, "location": None, "lat": 21.7, "lon": 76.1})
    assert out["served"] is False
    assert "strategies" not in out
    assert out["reason"]


def test_gps_point_near_a_preset_is_snapped_and_says_how_far():
    out = ENGINE.compare({**REQ, "location": None, "lat": 20.36, "lon": 77.12})
    assert out["served"] is True
    assert out["location"]["nearest"] == "washim"
    assert out["location"]["distance_km"] > 10


def test_unknown_priority_is_rejected():
    with pytest.raises(ValueError):
        run(priorities=["shiny"])


def test_site_evidence_describes_bare_windows_and_soil():
    out = run()
    kinds = {e["topic"] for e in out["site_evidence"]}
    assert {"bare_field_window", "soil", "monsoon"} <= kinds


def test_era5_cross_check_compares_like_with_like():
    s = {x["id"]: x for x in run()["strategies"]}
    # S0 has only kharif crops, so ERA5 loses nothing: the comparable total equals the full total
    assert s["S0"]["score_by_source"]["power_comparable"] == s["S0"]["score_by_source"]["power"]
    # S1 has a rabi crop whose soil-wetness proxy is missing in ERA5: the comparable total must differ from the full one
    assert s["S1"]["score_by_source"]["power_comparable"] != s["S1"]["score_by_source"]["power"]
    assert abs(s["S1"]["score_by_source"]["power_comparable"] - s["S1"]["score_by_source"]["era5"]) < 25


def test_scores_within_five_points_of_the_top_are_reported_as_a_tie():
    out = run()
    totals = {s["id"]: s["total_score"] for s in out["strategies"]}
    top = max(totals.values())
    assert out["ranking"][0] == max(totals, key=totals.get)
    assert set(out["tied_with_top"]) == {i for i, t in totals.items() if top - t <= 5}
    assert len(out["tied_with_top"]) >= 2  # Akola, water saving: several strategies are close


def test_a_strategy_scored_on_too_little_of_the_intended_weight_is_incomplete_and_not_ranked():
    out = run(priorities=["water_saving"])  # S2 has no water fit (pigeon pea need is blank): water is 55% of the weight
    s2 = {s["id"]: s for s in out["strategies"]}["S2"]
    assert s2["data_coverage"] < 0.7
    assert s2["incomplete"] is True
    assert "S2" not in out["ranking"] and "S2" not in out["tied_with_top"]
    assert any("not ranked" in g for g in s2["card"]["gaps"])


def test_a_strategy_with_a_small_gap_is_still_ranked():
    out = run(priorities=["market_income"])  # water fit is only a small share of the weight here
    s2 = {s["id"]: s for s in out["strategies"]}["S2"]
    assert s2["incomplete"] is False
    assert "S2" in out["ranking"]


def test_a_missing_price_does_not_win_a_market_priority():
    # Washim has no cotton prices, so S2 market is a gap; with a market priority it must not top the ranking
    out = ENGINE.compare({**REQ, "location": "washim", "priorities": ["market_income"]})
    s2 = {s["id"]: s for s in out["strategies"]}["S2"]
    assert s2["incomplete"] is True
    assert out["ranking"][0] != "S2"
