import pytest

from engine.components import Result
from engine.score import confidence, rank_stability, score_variants, strategy_components, total_score
from engine.strategies import Strategy
from tests.helpers import make_crop

YF = {"kharif_rain_mm": 750.0, "wet_root_days_oct_dec": 50.0, "onset_doy": 170, "withdrawal_doy": 278}


class FakeMarket:
    """Returns a fixed price score per crop; the combining logic is what is under test."""
    def __init__(self, scores):
        self.scores = scores

    def component(self, point, crop):
        if crop == "fallow":  # same as the real MarketData: fallow is not applicable
            return Result(None, "na", "valid", {})
        s = self.scores.get(crop)
        if s is None:
            return Result(None, "missing", "unverified", {"reason": "no price"})
        return Result(s, "ok", "valid", {})


def crops():
    return {
        "soy": make_crop(name="soy", season="kharif", water_need_mm_min=500, water_need_mm_max=700,
                         n_fixation="medium", fodder_value="low", duration_min=90, duration_max=110),
        "chick": make_crop(name="chick", season="rabi", sow_start_doy=274, sow_end_doy=288, duration_min=85,
                           duration_max=110, water_need="low", n_fixation="high", fodder_value="low"),
        "cot": make_crop(name="cot", season="kharif", sow_start_doy=166, sow_end_doy=196, duration_min=180,
                         duration_max=200, water_need_mm_min=500, water_need_mm_max=700, legume=False, n_fixation="none"),
        "pig": make_crop(name="pig", season="kharif", sow_start_doy=166, sow_end_doy=196, duration_min=150,
                         duration_max=180, water_need_mm_min=300, water_need_mm_max=500, n_fixation="medium"),
        "pig_nowater": make_crop(name="pig_nowater", season="kharif", water_need_mm_min=None, water_need_mm_max=None),
        "fallow": make_crop(name="fallow", role="baseline", season=None, sow_start_doy=None, sow_end_doy=None,
                            duration_min=None, duration_max=None, water_need=None, water_need_mm_min=None,
                            water_need_mm_max=None, legume=False, n_fixation="none", fodder_value="none"),
    }


MKT = FakeMarket({"soy": 40, "chick": 80, "cot": 60, "pig": 100})


def comps(strategy):
    return strategy_components(strategy, crops(), YF, MKT, "akola")


# ---- single ---------------------------------------------------------------
def test_single_crop_uses_its_own_scores():
    c = comps(Strategy("S0", "x", "single", ("cot",)))
    assert c["nitrogen"].score == 0 and c["nitrogen"].status == "ok"
    assert c["water_fit"].score == 100  # rain 750 vs need 600
    assert c["market"].score == 60


# ---- sequence -------------------------------------------------------------
def test_sequence_risk_components_take_the_worse_crop():
    c = comps(Strategy("S1", "x", "sequence", ("soy", "chick")))
    soy_water = 100.0                              # rain 750 / need 600 capped
    chick_water = min(100.0, 100 * 50 / 30)        # wet days 50 / needed 30 -> capped 100
    assert c["water_fit"].score == min(soy_water, chick_water)
    # make chickpea the weaker one
    c2 = strategy_components(Strategy("S1", "x", "sequence", ("soy", "chick")), crops(),
                             {**YF, "wet_root_days_oct_dec": 15.0}, MKT, "akola")
    assert c2["water_fit"].score == pytest.approx(50)


def test_sequence_benefit_components_are_averaged_weighted_by_days_in_ground():
    c = comps(Strategy("S1", "x", "sequence", ("soy", "chick")))
    soy_days, chick_days = 100.0, 97.5
    expected = (60 * soy_days + 100 * chick_days) / (soy_days + chick_days)
    assert c["nitrogen"].score == pytest.approx(expected)


def test_fallow_adds_no_days_so_it_does_not_dilute_averages():
    c = comps(Strategy("S0", "x", "sequence", ("soy", "fallow")))
    assert c["nitrogen"].score == pytest.approx(60)
    assert c["market"].score == pytest.approx(40)
    assert c["water_fit"].score == 100 and c["timing_fit"].status == "ok"


def test_a_missing_crop_value_makes_the_strategy_value_missing_not_zero():
    c = comps(Strategy("S", "x", "sequence", ("soy", "pig_nowater")))
    assert c["water_fit"].status == "missing"
    assert c["water_fit"].score is None
    assert "pig_nowater" in c["water_fit"].detail["reason"]


def test_bare_days_use_every_crop_in_the_strategy():
    one = comps(Strategy("S", "x", "sequence", ("soy",)))["bare_days"].detail["covered_days"]
    two = comps(Strategy("S", "x", "sequence", ("soy", "chick")))["bare_days"].detail["covered_days"]
    assert two > one


# ---- mixed (intercrop) ----------------------------------------------------
def test_mixed_water_need_is_main_crop_plus_thirty_percent_of_partner():
    s = Strategy("S2", "x", "mixed", ("cot", "pig"))
    need = 600 + 0.30 * 400  # = 720
    c = strategy_components(s, crops(), {**YF, "kharif_rain_mm": 360.0}, MKT, "akola")
    assert c["water_fit"].score == pytest.approx(100 * 360 / need)


def test_mixed_missing_partner_water_need_is_a_gap():
    s = Strategy("S2", "x", "mixed", ("cot", "pig_nowater"))
    assert comps(s)["water_fit"].status == "missing"


def test_mixed_nitrogen_comes_from_the_best_legume_and_timing_from_the_worse_crop():
    c = comps(Strategy("S2", "x", "mixed", ("cot", "pig")))
    assert c["nitrogen"].score == 60  # max(0, 60)
    late = strategy_components(Strategy("S2", "x", "mixed", ("cot", "pig")), crops(), {**YF, "onset_doy": 190}, MKT, "akola")
    assert late["timing_fit"].score <= 100


def test_mixed_bare_days_are_the_union_of_both_crops():
    c = comps(Strategy("S2", "x", "mixed", ("cot", "pig")))
    assert c["bare_days"].detail["covered_days"] == pytest.approx(190, abs=1)  # the longer crop covers the shorter


# ---- total ----------------------------------------------------------------
def test_total_is_the_weighted_sum_over_scored_components():
    c = comps(Strategy("S0", "x", "single", ("cot",)))
    total, weights, used = total_score(c, [], {})
    assert total == pytest.approx(sum(weights[k] * c[k].score for k in used) / 100)
    assert sum(weights.values()) == pytest.approx(100)


def test_total_drops_missing_components_and_renormalises():
    c = comps(Strategy("S", "x", "sequence", ("soy", "pig_nowater")))
    total, weights, used = total_score(c, [], {})
    assert "water_fit" not in used and "water_fit" not in weights
    assert sum(weights.values()) == pytest.approx(100)


def test_changing_priority_changes_the_ranking_in_the_expected_direction():
    a = comps(Strategy("A", "x", "single", ("pig",)))   # market 100, nitrogen 60
    b = comps(Strategy("B", "x", "single", ("chick",)))  # market 80, nitrogen 100
    ta_n, _, _ = total_score(a, ["nitrogen"], {})
    tb_n, _, _ = total_score(b, ["nitrogen"], {})
    ta_m, _, _ = total_score(a, ["market_income"], {})
    tb_m, _, _ = total_score(b, ["market_income"], {})
    assert (tb_n - ta_n) > (tb_m - ta_m)


# ---- confidence -----------------------------------------------------------
def test_confidence_is_the_share_of_weight_on_non_unverified_inputs():
    c = {"water_fit": Result(80, "ok", "degraded"), "market": Result(50, "ok", "unverified")}
    assert confidence(c, {"water_fit": 50.0, "market": 50.0}) == pytest.approx(0.5)


def test_confidence_label_thresholds():
    from engine.score import confidence_label
    assert confidence_label(0.9) == "green"
    assert confidence_label(0.5) == "yellow"
    assert confidence_label(0.1) == "grey"


# ---- rank stability and variants -----------------------------------------
def test_rank_stability_is_share_of_years_each_strategy_ranks_first():
    totals = {"S0": [10, 10, 10, 10], "S1": [20, 20, 5, 5]}
    assert rank_stability(totals) == {"S0": 0.5, "S1": 0.5}


def test_ties_share_the_first_rank():
    assert rank_stability({"A": [5, 5], "B": [5, 5]}) == {"A": 0.5, "B": 0.5}


def test_variants_replace_the_last_crop_and_are_scored_separately():
    s = Strategy("S3", "x", "sequence", ("soy", "chick"), variants=("pig",))
    out = score_variants(s, crops(), YF, MKT, "akola", [], {})
    assert set(out) == {"pig"}
    assert out["pig"]["total"] is not None


# ---- detail is kept so evidence can quote real numbers --------------------
def test_worst_crop_detail_keeps_the_underlying_numbers_and_the_crop_name():
    c = comps(Strategy("S1", "x", "sequence", ("soy", "chick")))
    d = c["water_fit"].detail
    assert d["worst_crop"] in {"soy", "chick"}
    assert "rain_mm" in d or "wet_days" in d


def test_benefit_average_keeps_each_crops_score():
    d = comps(Strategy("S1", "x", "sequence", ("soy", "chick")))["nitrogen"].detail
    assert d["by_crop"] == {"soy": 60.0, "chick": 100.0}


# ---- hand-off between consecutive crops -----------------------------------
def test_a_late_first_crop_that_misses_the_next_sowing_window_is_flagged_and_lowers_timing():
    s = Strategy("S1", "x", "sequence", ("soy", "chick"))
    on_time = strategy_components(s, crops(), {**YF, "onset_doy": 170}, MKT, "akola")
    late = strategy_components(s, crops(), {**YF, "onset_doy": 196}, MKT, "akola")  # soy harvest 196+100=296 > 288
    assert "misses_next_sowing_window" in late["timing_fit"].detail["flags"]
    assert "misses_next_sowing_window" not in on_time["timing_fit"].detail["flags"]
    assert late["timing_fit"].score < on_time["timing_fit"].score


# ---- data coverage: a gap must not flatter a strategy ---------------------
def test_coverage_is_the_share_of_intended_weight_that_could_be_scored():
    from engine.score import coverage
    ok = Result(80, "ok", "degraded")
    miss = Result(None, "missing", "unverified", {"reason": "x"})
    full = {k: ok for k in ("water_fit", "timing_fit", "bare_days", "nitrogen", "forage", "market")}
    assert coverage(full, [], {}) == pytest.approx(1.0)
    # water fit has 25 base weight (55 as first priority) and is missing
    assert coverage({**full, "water_fit": miss}, [], {}) == pytest.approx(0.75)
    assert coverage({**full, "water_fit": miss}, ["water_saving"], {}) == pytest.approx(0.45)


def test_not_applicable_components_do_not_count_as_gaps():
    from engine.score import coverage
    ok = Result(80, "ok", "degraded")
    na = Result(None, "na", "valid")
    assert coverage({"water_fit": na, "market": ok, "nitrogen": ok}, [], {}) == pytest.approx(1.0)
