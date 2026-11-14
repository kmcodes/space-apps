import pytest

from engine.weights import BASE_WEIGHTS, compute_weights

ALL = tuple(BASE_WEIGHTS)


def test_weights_always_sum_to_100():
    for prios in ([], ["water_saving"], ["forage", "market_income"]):
        assert sum(compute_weights(prios, {}, ALL).values()) == pytest.approx(100)


def test_no_priority_gives_the_base_weights():
    w = compute_weights([], {}, ALL)
    for k in ALL:
        assert w[k] == pytest.approx(BASE_WEIGHTS[k])


def test_first_priority_gets_a_fixed_forty_percent_share_plus_its_base_share():
    w = compute_weights(["water_saving"], {}, ALL)
    assert w["water_fit"] == pytest.approx(40 + 0.6 * BASE_WEIGHTS["water_fit"])


def test_a_small_base_weight_priority_still_dominates_when_first():
    # Amrita's issue 5: forage has a small base weight, but as first priority it must matter
    w = compute_weights(["forage"], {}, ALL)
    assert w["forage"] >= 40
    assert w["forage"] == max(w.values())


def test_second_priority_gets_twenty_percent():
    w = compute_weights(["water_saving", "market_income"], {}, ALL)
    assert w["market"] == pytest.approx(20 + 0.4 * BASE_WEIGHTS["market"])
    assert w["water_fit"] == pytest.approx(40 + 0.4 * BASE_WEIGHTS["water_fit"])


def test_each_priority_maps_to_the_right_component():
    assert max(compute_weights(["nitrogen"], {}, ALL).items(), key=lambda kv: kv[1])[0] == "nitrogen"
    assert max(compute_weights(["erosion"], {}, ALL).items(), key=lambda kv: kv[1])[0] == "bare_days"
    assert max(compute_weights(["market_income"], {}, ALL).items(), key=lambda kv: kv[1])[0] == "market"


def test_low_water_availability_raises_the_water_weight():
    normal = compute_weights([], {}, ALL)["water_fit"]
    low = compute_weights([], {"water_availability": "low"}, ALL)["water_fit"]
    assert low > normal


def test_own_use_market_preference_removes_market_weight_and_shares_it_out():
    w = compute_weights([], {"market": "own_use"}, ALL)
    assert w["market"] == 0
    assert sum(w.values()) == pytest.approx(100)


def test_components_with_no_score_are_dropped_and_weights_renormalised():
    present = tuple(k for k in ALL if k != "water_fit")
    w = compute_weights([], {}, present)
    assert "water_fit" not in w
    assert sum(w.values()) == pytest.approx(100)


def test_unknown_priority_is_rejected():
    with pytest.raises(ValueError):
        compute_weights(["shiny"], {}, ALL)
