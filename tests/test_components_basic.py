import math

from engine.components import forage, nitrogen, water_fit
from tests.helpers import make_crop


# ---- nitrogen -------------------------------------------------------------
def test_nitrogen_score_follows_rating():
    assert nitrogen(make_crop(n_fixation="high")).score == 100
    assert nitrogen(make_crop(n_fixation="medium")).score == 60
    assert nitrogen(make_crop(n_fixation="low")).score == 25


def test_non_legume_nitrogen_is_a_real_zero():
    r = nitrogen(make_crop(legume=False, n_fixation="none"))
    assert r.score == 0 and r.status == "ok"


def test_missing_nitrogen_rating_is_a_gap_not_zero():
    r = nitrogen(make_crop(legume=True, n_fixation=None))
    assert r.score is None and r.status == "missing"


def test_nitrogen_validity_is_unverified_when_ratings_unverified():
    assert nitrogen(make_crop(unverified=frozenset({"ratings"}))).validity == "unverified"
    assert nitrogen(make_crop(unverified=frozenset())).validity == "valid"


# ---- forage ---------------------------------------------------------------
def test_forage_score_follows_rating_and_blank_is_gap():
    assert forage(make_crop(fodder_value="high")).score == 100
    assert forage(make_crop(fodder_value="none")).score == 0
    assert forage(make_crop(fodder_value=None)).status == "missing"


# ---- water fit ------------------------------------------------------------
def test_kharif_water_fit_is_rain_over_need_capped_at_100():
    crop = make_crop(water_need_mm_min=500, water_need_mm_max=700)  # mid 600
    assert water_fit(crop, {"kharif_rain_mm": 300, "wet_root_days_oct_dec": 40}).score == 50
    assert water_fit(crop, {"kharif_rain_mm": 900, "wet_root_days_oct_dec": 40}).score == 100


def test_kharif_water_fit_missing_need_is_a_gap_not_zero():
    crop = make_crop(water_need_mm_min=None, water_need_mm_max=None)
    r = water_fit(crop, {"kharif_rain_mm": 800, "wet_root_days_oct_dec": 40})
    assert r.score is None and r.status == "missing"
    assert "water_need_mm" in r.detail["reason"]


def test_rabi_water_fit_uses_wet_root_days_against_rating():
    low = make_crop(season="rabi", water_need="low")  # needs 30 wet days
    assert water_fit(low, {"kharif_rain_mm": 700, "wet_root_days_oct_dec": 15}).score == 50
    assert water_fit(low, {"kharif_rain_mm": 700, "wet_root_days_oct_dec": 60}).score == 100
    medium = make_crop(season="rabi", water_need="medium")  # needs 50 wet days
    assert water_fit(medium, {"kharif_rain_mm": 700, "wet_root_days_oct_dec": 25}).score == 50


def test_rabi_water_fit_without_soil_wetness_data_is_a_gap():
    r = water_fit(make_crop(season="rabi", water_need="low"), {"kharif_rain_mm": 700, "wet_root_days_oct_dec": math.nan})
    assert r.score is None and r.status == "missing"


def test_rabi_water_fit_is_always_unverified_because_it_is_a_proxy():
    r = water_fit(make_crop(season="rabi", water_need="low"), {"kharif_rain_mm": 700, "wet_root_days_oct_dec": 40})
    assert r.validity == "unverified"


def test_kharif_water_fit_validity_degraded_or_unverified():
    ok = water_fit(make_crop(), {"kharif_rain_mm": 700, "wet_root_days_oct_dec": 40})
    assert ok.validity == "degraded"  # weather is gridded
    bad = water_fit(make_crop(unverified=frozenset({"water_need_mm"})), {"kharif_rain_mm": 700, "wet_root_days_oct_dec": 40})
    assert bad.validity == "unverified"


def test_fallow_is_not_applicable_for_water_fit():
    r = water_fit(make_crop(role="baseline", season=None, water_need=None, water_need_mm_min=None, water_need_mm_max=None),
                  {"kharif_rain_mm": 700, "wet_root_days_oct_dec": 40})
    assert r.status == "na"


def test_crop_with_unknown_season_is_a_gap():
    r = water_fit(make_crop(season=None), {"kharif_rain_mm": 700, "wet_root_days_oct_dec": 40})
    assert r.status == "missing"
