"""Which months are risky for a crop in the ground: heat, dry spells inside the monsoon, and frost.

Reads the daily NASA POWER and ERA5 files (through pipeline/features.py) and writes
data/processed/season_risk.json, which the engine returns with /compare.

Rules (our own thresholds, shown to users; not official definitions):
  hot month    at least HOT_DAYS_MIN days a month above HOT_TMAX_C (average over 1981-2025)
  dry-spell    at least DRY_SHARE_MIN of years have a dry run of DRY_RUN_DAYS or more days inside that year's
  month        monsoon (onset to withdrawal) that overlaps the month; a "rainy day" is 2.5 mm, as in features.py
  frost        nights at or below FROST_TMIN_C
A month's level is how many of the two datasets reach the threshold: 2 both, 1 one (they disagree), 0 neither.
"""
import json
import math

import numpy as np
import pandas as pd

from pipeline.features import OUT, RAIN_DAY_MM, load_daily

POINTS = ("akola", "buldhana", "washim")
HOT_TMAX_C = 38
HOT_DAYS_MIN = 10
DRY_RUN_DAYS = 10
DRY_SHARE_MIN = 0.4
FROST_TMIN_C = 2


def hot_days_per_month(tmax, threshold, n_years):
    """Average number of days a year above `threshold`, for each calendar month (index 0 = January)."""
    counts = (tmax > threshold).groupby(tmax.index.month).sum()
    return [round(float(counts.get(m, 0)) / n_years, 1) for m in range(1, 13)]


def frost_days_per_year(tmin, threshold, n_years):
    return round(float((tmin <= threshold).sum()) / n_years, 2)


def monsoon_dry_share(rain, windows, min_run=DRY_RUN_DAYS, rain_day_mm=RAIN_DAY_MM):
    """Share of years (that have a monsoon window) with a dry run of min_run+ days overlapping each month.

    windows: {year: (onset_doy, withdrawal_doy)}. Dry days outside the monsoon do not count.
    """
    hits, used = np.zeros(12), 0
    for year, (onset, withdrawal) in windows.items():
        if any(isinstance(v, float) and math.isnan(v) for v in (onset, withdrawal)):
            continue
        used += 1
        jan1 = pd.Timestamp(year=int(year), month=1, day=1)
        season = rain[jan1 + pd.Timedelta(days=int(onset) - 1): jan1 + pd.Timedelta(days=int(withdrawal) - 1)]
        dry, months, i = (season < rain_day_mm).to_numpy(), set(), 0
        while i < len(dry):
            if not dry[i]:
                i += 1
                continue
            j = i
            while j < len(dry) and dry[j]:
                j += 1
            if j - i >= min_run:
                months.update(season.index[i:j].month)
            i = j
        for m in months:
            hits[m - 1] += 1
    return [round(float(h) / used, 2) if used else None for h in hits]


def level(power, era5, minimum):
    """2 if both datasets reach `minimum`, 1 if only one does, 0 if neither (a missing value counts as no)."""
    return sum(1 for v in (power, era5) if v is not None and v >= minimum)


def build():
    out = {
        "definitions": {
            "hot_month": f"at least {HOT_DAYS_MIN} days a month above {HOT_TMAX_C} C, averaged over 1981-2025",
            "dry_spell_month": (f"in at least {int(DRY_SHARE_MIN * 100)}% of years a dry run of {DRY_RUN_DAYS}+ days "
                                f"(rain under {RAIN_DAY_MM} mm a day) inside the monsoon overlaps the month"),
            "frost_night": f"minimum temperature at or below {FROST_TMIN_C} C",
            "level": "2 = both NASA POWER and ERA5 reach the threshold, 1 = only one does (they disagree), 0 = neither",
            "months": "calendar order, index 0 = January",
        },
        "points": {},
    }
    for point in POINTS:
        hot, dry, frost = {}, {}, {}
        for source, yearly_file in (("power", "features_yearly.csv"), ("era5", "features_yearly_era5.csv")):
            df = load_daily(point, source)
            n_years = df.index.year.nunique()
            hot[source] = hot_days_per_month(df["T2M_MAX"], HOT_TMAX_C, n_years)
            frost[source] = frost_days_per_year(df["T2M_MIN"], FROST_TMIN_C, n_years)
            yearly = pd.read_csv(OUT / yearly_file)
            yearly = yearly[yearly.point == point]
            windows = {int(r.year): (r.onset_doy, r.withdrawal_doy) for r in yearly.itertuples()}
            dry[source] = monsoon_dry_share(df["PRECTOTCORR"], windows)
        out["points"][point] = {
            "hot_days": hot,
            "heat_level": [level(hot["power"][m], hot["era5"][m], HOT_DAYS_MIN) for m in range(12)],
            "dry_spell_share": dry,
            "dry_spell_level": [level(dry["power"][m], dry["era5"][m], DRY_SHARE_MIN) for m in range(12)],
            "frost_days_per_year": frost,
        }
    return out


if __name__ == "__main__":
    result = build()
    (OUT / "season_risk.json").write_text(json.dumps(result, indent=1))
    for p, v in result["points"].items():
        print(p, "heat", v["heat_level"], "dry", v["dry_spell_level"], "frost", v["frost_days_per_year"])
