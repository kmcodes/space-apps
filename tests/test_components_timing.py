import pytest

from engine.components import bare_days, timing_fit
from tests.helpers import make_crop

KHARIF = dict(season="kharif", sow_start_doy=166, sow_end_doy=196, duration_min=90.0, duration_max=110.0)


def yf(onset, withdrawal=278):
    return {"onset_doy": onset, "withdrawal_doy": withdrawal}


# ---- timing_fit -----------------------------------------------------------
def test_kharif_sows_at_onset_when_inside_window_and_small_delay_is_free():
    r = timing_fit(make_crop(**KHARIF), yf(170))
    assert r.detail["sow_doy"] == 170
    assert r.score == 100


def test_kharif_early_onset_waits_for_window_start_without_penalty():
    r = timing_fit(make_crop(**KHARIF), yf(150))
    assert r.detail["sow_doy"] == 166
    assert r.score == 100


def test_kharif_delay_beyond_free_days_costs_one_point_per_day():
    r = timing_fit(make_crop(**KHARIF), yf(190))  # delay 24 days, 14 free -> 10 points
    assert r.score == pytest.approx(90)


def test_onset_after_window_closes_is_flagged_and_penalised():
    r = timing_fit(make_crop(**KHARIF), yf(210))
    assert "onset_after_window" in r.detail["flags"]
    assert r.detail["sow_doy"] == 196
    assert r.score == pytest.approx(100 - 30 - 16)  # late-onset 30 + delay (30-14)


def test_rabi_crop_sows_at_window_start_regardless_of_onset():
    r = timing_fit(make_crop(season="rabi", sow_start_doy=274, sow_end_doy=288), yf(190))
    assert r.detail["sow_doy"] == 274


def test_crop_running_into_the_pre_monsoon_heat_is_penalised():
    crop = make_crop(season="rabi", sow_start_doy=274, sow_end_doy=288, duration_min=190.0, duration_max=210.0)
    r = timing_fit(crop, yf(165))  # harvest 474, heat starts 439 -> 35 days x2 -> capped at 60
    assert r.score == pytest.approx(40)
    assert "heat_exposure" in r.detail["flags"]


def test_rabi_crop_finishing_before_march_is_not_penalised():
    crop = make_crop(season="rabi", sow_start_doy=274, sow_end_doy=288, duration_min=85.0, duration_max=110.0)
    assert timing_fit(crop, yf(165)).score == 100


def test_missing_duration_or_window_is_a_gap_not_zero():
    assert timing_fit(make_crop(duration_min=None, duration_max=None), yf(165)).status == "missing"
    assert timing_fit(make_crop(sow_start_doy=None, sow_end_doy=None), yf(165)).status == "missing"


def test_fallow_timing_is_not_applicable():
    assert timing_fit(make_crop(role="baseline", season=None, sow_start_doy=None, sow_end_doy=None,
                                duration_min=None, duration_max=None), yf(165)).status == "na"


def test_timing_validity_unverified_when_sowing_window_or_duration_unverified():
    assert timing_fit(make_crop(**KHARIF, unverified=frozenset({"sow_start"})), yf(170)).validity == "unverified"
    assert timing_fit(make_crop(**KHARIF, unverified=frozenset({"duration_days_max"})), yf(170)).validity == "unverified"
    assert timing_fit(make_crop(**KHARIF), yf(170)).validity == "degraded"


# ---- bare_days ------------------------------------------------------------
def test_bare_days_for_one_crop_cycle():
    r = bare_days([(166, 266)])
    assert r.detail["covered_days"] == 100
    assert r.detail["bare_days"] == 265
    assert r.score == pytest.approx(100 * (1 - 265 / 365))


def test_overlapping_crops_are_counted_once():
    assert bare_days([(166, 266), (200, 300)]).detail["covered_days"] == 134


def test_crop_cycle_wrapping_over_new_year_is_counted():
    assert bare_days([(340, 400)]).detail["covered_days"] == 60


def test_no_crop_at_all_is_all_bare_with_a_real_zero_score():
    r = bare_days([])
    assert (r.score, r.status, r.detail["bare_days"]) == (0.0, "ok", 365)
