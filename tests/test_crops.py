from engine.crops import load_crops, mmdd_to_doy

CSV = "data/crops.csv"


def test_mmdd_to_doy_converts_sowing_dates():
    assert mmdd_to_doy("06-15") == 166  # non-leap year day of year
    assert mmdd_to_doy("10-01") == 274


def test_mmdd_to_doy_blank_is_none_not_zero():
    assert mmdd_to_doy("") is None


def test_blank_water_need_stays_none_not_zero():
    crops = load_crops(CSV)
    assert crops["pigeon_pea"].water_need_mm_min is None
    assert crops["pigeon_pea"].water_need_mid is None


def test_water_need_midpoint_when_present():
    crops = load_crops(CSV)
    assert crops["soybean"].water_need_mid == (450 + 700) / 2


def test_sowing_window_parsed_to_day_of_year():
    c = load_crops(CSV)["chickpea"]
    assert (c.sow_start_doy, c.sow_end_doy) == (274, 288)


def test_unverified_fields_are_split_into_a_set():
    c = load_crops(CSV)["soybean"]
    assert "sensitive_stage" in c.unverified
    assert "ratings" in c.unverified


def test_fallow_has_no_duration():
    c = load_crops(CSV)["fallow"]
    assert c.duration_mid is None
