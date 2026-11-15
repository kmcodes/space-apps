"""Seasonal water need of pigeon pea at Akola: the numbers behind water_need_mm_min/max in data/crops.csv.

Crop water need = sum over the season of (crop coefficient Kc x reference evapotranspiration ETo).

* Kc is MEASURED: PDKV Akola lysimeter study, mean of kharif 2022 and 2023 (Phase IX and Phase X reports of the
  MahaPOCRA project "Determination of Crop Coefficients for Major Crops by Lysimetric Studies"):
  initial 0.53, development 0.81, mid-season 1.10, late 0.79, over stages of 24, 52, 58 and 46 days (180 days).
* ETo is DERIVED by us from NASA POWER daily weather at the Akola point, 1981-2025. POWER has no wind, so the
  FAO-56 Penman-Monteith uses the default 2 m/s wind. Hargreaves-Samani (temperature only) is the cross-check.

The report itself gives taluka-wise totals only in appendices that were not in the PDF we could open, so this is our
own estimate, not a published figure. It is flagged `water_need_mm` in `unverified_fields` for that reason.

Run:  python -m pipeline.pigeon_pea_water_need
"""

import math

import numpy as np
import pandas as pd

LAT = 20.70          # the Akola point
ELEVATION_M = 280.0  # assumption: about 280 m
STAGES = [(24, 0.53), (52, 0.81), (58, 1.10), (46, 0.79)]  # (days, Kc)
SOW_DOY = 175        # 24 June: the PDKV lysimeter was sown on 24 June 2022 and 30 June 2023


def load_power(path="data/processed/power_akola.csv") -> pd.DataFrame:
    df = pd.read_csv(path, parse_dates=["date"])
    df["year"] = df["date"].dt.year
    return df


def _extraterrestrial_radiation(doy: np.ndarray) -> np.ndarray:
    phi = math.radians(LAT)
    dr = 1 + 0.033 * np.cos(2 * np.pi * doy / 365)
    decl = 0.409 * np.sin(2 * np.pi * doy / 365 - 1.39)
    ws = np.arccos(-np.tan(phi) * np.tan(decl))
    return (24 * 60 / np.pi) * 0.0820 * dr * (ws * np.sin(phi) * np.sin(decl) + np.cos(phi) * np.cos(decl) * np.sin(ws))


def _sat_vapour_pressure(t):
    return 0.6108 * np.exp(17.27 * t / (t + 237.3))


def eto_penman_monteith(df: pd.DataFrame) -> np.ndarray:
    """FAO-56 daily ETo (mm/day), wind fixed at 2 m/s. Needs solar radiation, so it is NaN before 1984."""
    ra = _extraterrestrial_radiation(df["date"].dt.day_of_year.values)
    tmax, tmin, tmean, rh = df["T2M_MAX"].values, df["T2M_MIN"].values, df["T2M"].values, df["RH2M"].values
    rs = df["ALLSKY_SFC_SW_DWN"].values
    es = (_sat_vapour_pressure(tmax) + _sat_vapour_pressure(tmin)) / 2
    ea = rh / 100 * es
    rso = (0.75 + 2e-5 * ELEVATION_M) * ra
    rn = 0.77 * rs - 4.903e-9 * (((tmax + 273.16) ** 4 + (tmin + 273.16) ** 4) / 2) * (0.34 - 0.14 * np.sqrt(ea)) * (
        1.35 * np.clip(rs / rso, 0.3, 1.0) - 0.35
    )
    pressure = 101.3 * ((293 - 0.0065 * ELEVATION_M) / 293) ** 5.26
    gamma = 0.000665 * pressure
    delta = 4098 * _sat_vapour_pressure(tmean) / (tmean + 237.3) ** 2
    u2 = 2.0
    return (0.408 * delta * rn + gamma * 900 / (tmean + 273) * u2 * (es - ea)) / (delta + gamma * (1 + 0.34 * u2))


def eto_hargreaves(df: pd.DataFrame) -> np.ndarray:
    """Hargreaves-Samani daily ETo (mm/day) from temperature only."""
    ra = _extraterrestrial_radiation(df["date"].dt.day_of_year.values)
    spread = np.clip(df["T2M_MAX"].values - df["T2M_MIN"].values, 0, None)
    return 0.0023 * (df["T2M"].values + 17.8) * np.sqrt(spread) * ra * 0.408


def seasonal_need(df: pd.DataFrame, eto: np.ndarray, sow_doy: int = SOW_DOY) -> np.ndarray:
    """Season total (mm) for each year with a full, complete season, sown on sow_doy."""
    kc = np.concatenate([np.full(days, k) for days, k in STAGES])
    out = []
    for year in sorted(df["year"].unique()):
        daily = eto[(df["year"] == year).values]
        season = daily[sow_doy - 1 : sow_doy - 1 + len(kc)]
        if len(season) == len(kc) and not np.isnan(season).any():
            out.append(float((season * kc).sum()))
    return np.array(out)


def summary(df: pd.DataFrame | None = None) -> dict:
    df = load_power() if df is None else df
    result = {}
    for name, eto in (("penman_monteith", eto_penman_monteith(df)), ("hargreaves", eto_hargreaves(df))):
        need = seasonal_need(df, eto)
        result[name] = {"years": len(need), "mean": need.mean(), "p25": np.percentile(need, 25), "p75": np.percentile(need, 75)}
    return result


if __name__ == "__main__":
    s = summary()
    for name, v in s.items():
        print(f"{name:16s} years={v['years']} mean={v['mean']:.0f} mm  p25={v['p25']:.0f}  p75={v['p75']:.0f}")
    lo = round(s["penman_monteith"]["p25"], -1)
    hi = round(s["hargreaves"]["p75"], -1)
    print(f"water_need_mm_min/max = {lo:.0f} / {hi:.0f}  (Penman-Monteith lower quartile to Hargreaves upper quartile)")
