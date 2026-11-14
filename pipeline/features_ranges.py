"""Combine POWER and ERA5 features into a range per feature, so the engine and UI can show uncertainty.

For each point and feature: median over 1981-2025 for each dataset, the range between them,
and an agreement flag. A feature is `agree` if the two medians differ by <= tolerance
(dates/lengths in days: absolute; amounts and counts: relative). Otherwise it is `disagree`
and must be displayed as a range with the `degraded` validity flag.

Out: data/processed/features_ranges.json  (+ printed table)
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data/processed"

# feature: (label, kind, tolerance)   kind 'abs' = absolute units, 'rel' = fraction of the mean
FEATURES = {
    "onset_doy": ("monsoon onset (day of year)", "abs", 7),
    "withdrawal_doy": ("monsoon withdrawal (day of year)", "abs", 7),
    "season_length_days": ("rainy season length (days)", "abs", 10),
    "annual_rain_mm": ("annual rain (mm)", "rel", 0.10),
    "kharif_rain_mm": ("Jun-Sep rain (mm)", "rel", 0.10),
    "kharif_rainy_days": ("rainy days Jun-Sep", "rel", 0.15),
    "longest_dry_spell_days": ("longest dry spell in monsoon (days)", "abs", 3),
    "dry_spells_ge10": ("dry spells >= 10 days per year", "abs", 0.5),
    "dry_spells_ge15": ("dry spells >= 15 days per year", "abs", 0.5),
    "heat_days_gt40_mar_may": ("days > 40 C, Mar-May", "rel", 0.15),
    "heat_days_gt35_kharif": ("days > 35 C, Jun-Oct", "rel", 0.15),
    "heat_days_gt38_kharif": ("days > 38 C, Jun-Oct", "rel", 0.15),
    "tmax_mean_mar_may": ("mean Tmax Mar-May (C)", "abs", 1.0),
    "t2m_mean_annual": ("mean temperature (C)", "abs", 0.5),
}
DATE_FEATURES = {"onset_doy", "withdrawal_doy"}


def as_date(doy):
    return (pd.Timestamp(2001, 1, 1) + pd.to_timedelta(float(doy) - 1, unit="D")).strftime("%d %b")


def main():
    a = pd.read_csv(OUT / "features_yearly.csv")
    b = pd.read_csv(OUT / "features_yearly_era5.csv")
    res = {}
    for p in a.point.unique():
        ya, yb = a[a.point == p], b[b.point == p]
        rp = {}
        for k, (label, kind, tol) in FEATURES.items():
            ma, mb = float(ya[k].median()), float(yb[k].median())
            diff = abs(ma - mb)
            limit = tol * ((ma + mb) / 2) if kind == "rel" else tol
            agree = bool(diff <= limit)
            entry = {"label": label, "power": round(ma, 2), "era5": round(mb, 2),
                     "range": [round(min(ma, mb), 2), round(max(ma, mb), 2)],
                     "difference": round(diff, 2), "agree": agree,
                     "validity": "degraded" if agree else "degraded: datasets disagree, show as range"}
            if k in DATE_FEATURES:
                entry["range_dates"] = [as_date(min(ma, mb)), as_date(max(ma, mb))]
            rp[k] = entry
        res[p] = rp
    (OUT / "features_ranges.json").write_text(json.dumps(res, indent=2))
    for p, rp in res.items():
        print(f"== {p}")
        for k, e in rp.items():
            rng = " - ".join(e["range_dates"]) if "range_dates" in e else f"{e['range'][0]} - {e['range'][1]}"
            print(f"   {'ok      ' if e['agree'] else 'DISAGREE'} {e['label']:<38} POWER {e['power']:>8}  ERA5 {e['era5']:>8}  range {rng}")


if __name__ == "__main__":
    main()
