import pandas as pd

from engine.compare import Engine
from pipeline.season_risk import frost_days_per_year, hot_days_per_month, level, monsoon_dry_share


def test_hot_days_per_month_is_an_average_over_years():
    idx = pd.date_range("2000-01-01", "2001-12-31")
    tmax = pd.Series(30.0, index=idx)
    tmax[(tmax.index.month == 4)] = 40.0  # every April day is hot, in both years
    days = hot_days_per_month(tmax, 38, n_years=2)
    assert len(days) == 12
    assert days[3] == 30.0 and days[0] == 0.0


def test_frost_days_per_year():
    idx = pd.date_range("2000-01-01", "2001-12-31")
    tmin = pd.Series(12.0, index=idx)
    tmin.iloc[[10, 11, 400]] = 1.0  # three frost nights over two years
    assert frost_days_per_year(tmin, 2, n_years=2) == 1.5


def test_dry_spells_count_only_inside_the_monsoon_and_only_if_long_enough():
    idx = pd.date_range("2001-01-01", "2001-12-31")
    rain = pd.Series(10.0, index=idx)
    rain["2001-07-10":"2001-07-25"] = 0.0  # 16 dry days in July: counts
    rain["2001-08-01":"2001-08-09"] = 0.0  # 9 dry days in August: too short
    rain["2001-11-01":"2001-11-30"] = 0.0  # November is after the monsoon: ignored
    share = monsoon_dry_share(rain, {2001: (170, 280)})
    assert share[6] == 1.0 and share[7] == 0.0 and share[10] == 0.0


def test_a_year_without_a_monsoon_window_is_left_out_of_the_share():
    idx = pd.date_range("2001-01-01", "2002-12-31")
    rain = pd.Series(10.0, index=idx)
    rain["2001-07-10":"2001-07-25"] = 0.0
    share = monsoon_dry_share(rain, {2001: (170, 280), 2002: (float("nan"), float("nan"))})
    assert share[6] == 1.0  # one usable year, and it had the spell


def test_level_is_how_many_datasets_agree():
    assert level(12, 15, 10) == 2
    assert level(12, 3, 10) == 1
    assert level(3, 2, 10) == 0
    assert level(12, None, 10) == 1


def test_compare_returns_season_risk_for_the_nearest_point():
    r = Engine.from_repo().compare({"location": "akola", "priorities": ["water_saving"], "constraints": {}})
    sr = r["season_risk"]
    assert len(sr["heat_level"]) == 12 and len(sr["dry_spell_level"]) == 12
    assert sr["heat_level"][3] == 2 and sr["heat_level"][4] == 2  # April and May are hot in both datasets
    assert set(sr["dry_spell_level"]) <= {0, 1, 2}
    assert sr["frost_days_per_year"] == {"power": 0.0, "era5": 0.0}  # no frost nights in the record
