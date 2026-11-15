"""The pigeon pea water need in data/crops.csv comes from pipeline/pigeon_pea_water_need.py. These tests keep the two together."""

import pytest

from engine.crops import load_crops
from pipeline.pigeon_pea_water_need import STAGES, summary

S = summary()


def test_stage_lengths_and_kc_are_the_pdkv_akola_lysimeter_values():
    assert STAGES == [(24, 0.53), (52, 0.81), (58, 1.10), (46, 0.79)]
    assert sum(days for days, _ in STAGES) == 180


def test_two_methods_agree_within_ten_percent_and_land_near_600_mm():
    pm, hg = S["penman_monteith"]["mean"], S["hargreaves"]["mean"]
    assert 570 <= pm <= 630
    assert 610 <= hg <= 670
    assert abs(pm - hg) / pm < 0.10


def test_penman_monteith_skips_years_without_solar_radiation_and_hargreaves_does_not():
    assert S["penman_monteith"]["years"] == 42  # 1981-2025 is 45 years; POWER solar radiation starts in 1984
    assert S["hargreaves"]["years"] == 45


def test_csv_range_is_the_lower_quartile_of_one_method_to_the_upper_quartile_of_the_other():
    c = load_crops("data/crops.csv")["pigeon_pea"]
    assert c.water_need_mm_min == pytest.approx(S["penman_monteith"]["p25"], abs=10)
    assert c.water_need_mm_max == pytest.approx(S["hargreaves"]["p75"], abs=10)
