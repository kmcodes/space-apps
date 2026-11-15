from engine.crops import load_crops, mmdd_to_doy

CSV = "data/crops.csv"


def test_mmdd_to_doy_converts_sowing_dates():
    assert mmdd_to_doy("06-15") == 166  # non-leap year day of year
    assert mmdd_to_doy("10-01") == 274


def test_mmdd_to_doy_blank_is_none_not_zero():
    assert mmdd_to_doy("") is None


def test_blank_water_need_stays_none_not_zero():
    crops = load_crops(CSV)
    assert crops["sunn_hemp"].water_need_mm_min is None  # still a gap in the crop sheet
    assert crops["sunn_hemp"].water_need_mid is None


def test_pigeon_pea_water_need_is_derived_from_measured_kc_and_flagged_unverified():
    # PDKV Akola lysimeter Kc (0.53, 0.81, 1.10, 0.79; stages 24/52/58/46 days) x POWER ETo at Akola, 1981-2025:
    # Penman-Monteith about 600 mm, Hargreaves about 640 mm; between-year spread 550-670 mm. Derived by us, not published.
    c = load_crops(CSV)["pigeon_pea"]
    assert (c.water_need_mm_min, c.water_need_mm_max) == (550, 670)
    assert c.water_need_mid == 610
    assert "water_need_mm" in c.unverified


def test_pigeon_pea_season_length_at_akola_is_read_from_the_pdkv_report_but_the_minimum_is_not():
    c = load_crops(CSV)["pigeon_pea"]
    assert c.duration_max == 180
    assert "duration_days_max" not in c.unverified
    assert "duration_days_min" in c.unverified


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
