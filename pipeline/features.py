"""Derive agronomic features from NASA POWER daily data (data/processed/power_<point>.csv).

Outputs (data/processed/):
  features_yearly.csv        one row per point x year
  features_monthly_clim.csv  1981-2025 monthly climatology per point
  features_summary.json      medians, trends, recent-vs-baseline, with evidence metadata

All thresholds are named constants below so they can be shown to users and tuned.
Rules are transparent heuristics, not official IMD definitions.
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data/processed"

# ---- thresholds (documented in the log / UI) ----
RAIN_DAY_MM = 2.5            # a "rainy day"
ONSET_WINDOW_DAYS = 5        # onset: >= ONSET_MM over this many days ...
ONSET_MM = 30.0
ONSET_SEARCH_START = (6, 1)  # ... first on/after 1 June
FALSE_ONSET_DRY_DAYS = 10    # ... and no dry run >= this in following 30 days
WITHDRAWAL_DRY_RUN = 15      # withdrawal: first run of this many dry days from 1 Sep
HEAT_T = (35, 38, 40)        # T2M_MAX thresholds, deg C
COLD_LE = 10                 # cold-stress day (T2M_MIN <= 10)
FROST_LE = 2                 # frost-risk day (T2M_MIN <= 2)
SOIL_WET_ROOT = 0.65         # GWETROOT: root-zone wetness well above dry-season floor (~0.59)
DRY_SPELL_MIN = (10, 15)


def runs_of_dry(rain):
    """lengths of consecutive dry-day runs (rain < RAIN_DAY_MM)"""
    out, n = [], 0
    for v in rain:
        if v < RAIN_DAY_MM:
            n += 1
        else:
            if n:
                out.append(n)
            n = 0
    if n:
        out.append(n)
    return out


def find_onset(df_year):
    d = df_year[df_year.index >= pd.Timestamp(df_year.index[0].year, *ONSET_SEARCH_START)]
    rain = d["PRECTOTCORR"].values
    for i in range(len(rain) - ONSET_WINDOW_DAYS - 30):
        if rain[i:i + ONSET_WINDOW_DAYS].sum() >= ONSET_MM:
            nxt = rain[i + ONSET_WINDOW_DAYS:i + ONSET_WINDOW_DAYS + 30]
            if max(runs_of_dry(nxt) or [0]) < FALSE_ONSET_DRY_DAYS:
                return d.index[i]
    return pd.NaT


def find_withdrawal(df_year):
    d = df_year[df_year.index >= pd.Timestamp(df_year.index[0].year, 9, 1)]
    rain = d["PRECTOTCORR"].values
    for i in range(len(rain) - WITHDRAWAL_DRY_RUN):
        if (rain[i:i + WITHDRAWAL_DRY_RUN] < RAIN_DAY_MM).all():
            return d.index[i]
    return pd.NaT


def yearly(point, df):
    rows = []
    for y in range(df.index.year.min(), df.index.year.max() + 1):
        dy = df[df.index.year == y]
        if len(dy) < 360:
            continue
        onset, wd = find_onset(dy), find_withdrawal(dy)
        kh = dy[(dy.index.month >= 6) & (dy.index.month <= 9)]
        start = onset if pd.notna(onset) else pd.Timestamp(y, 6, 1)
        season = dy[(dy.index >= start) & (dy.index <= pd.Timestamp(y, 9, 30))]
        runs = runs_of_dry(season["PRECTOTCORR"].values)
        pre = dy[(dy.index.month >= 3) & (dy.index.month <= 5)]
        khar = dy[(dy.index.month >= 6) & (dy.index.month <= 10)]
        # rabi window Nov(y) - Feb(y+1)
        rabi = df[(df.index >= pd.Timestamp(y, 11, 1)) & (df.index <= pd.Timestamp(y + 1, 2, 28))]
        rabi_ok = len(rabi) >= 115
        post = dy[(dy.index >= pd.Timestamp(y, 10, 15)) & (dy.index <= pd.Timestamp(y, 11, 15))]
        octdec = dy[(dy.index.month >= 10) & (dy.index.month <= 12)]
        winter = rabi[(rabi.index.month == 12) | (rabi.index.month <= 2)] if rabi_ok else rabi.iloc[0:0]
        r = {
            "point": point, "year": y,
            "monsoon_onset": onset.date().isoformat() if pd.notna(onset) else "",
            "onset_doy": onset.day_of_year if pd.notna(onset) else np.nan,
            "monsoon_withdrawal": wd.date().isoformat() if pd.notna(wd) else "",
            "withdrawal_doy": wd.day_of_year if pd.notna(wd) else np.nan,
            "season_length_days": (wd - onset).days if pd.notna(onset) and pd.notna(wd) else np.nan,
            "annual_rain_mm": round(dy["PRECTOTCORR"].sum(), 1),
            "kharif_rain_mm": round(kh["PRECTOTCORR"].sum(), 1),
            "kharif_rainy_days": int((kh["PRECTOTCORR"] >= RAIN_DAY_MM).sum()),
            "longest_dry_spell_days": max(runs or [0]),
            "dry_spells_ge10": sum(1 for x in runs if x >= DRY_SPELL_MIN[0]),
            "dry_spells_ge15": sum(1 for x in runs if x >= DRY_SPELL_MIN[1]),
            "t2m_mean_annual": round(dy["T2M"].mean(), 2),
            "heat_days_gt40_mar_may": int((pre["T2M_MAX"] > 40).sum()),
            "tmax_mean_mar_may": round(pre["T2M_MAX"].mean(), 2),
            "heat_days_gt35_kharif": int((khar["T2M_MAX"] > 35).sum()),
            "heat_days_gt38_kharif": int((khar["T2M_MAX"] > 38).sum()),
            "post_monsoon_gwetroot_mean": round(post["GWETROOT"].mean(), 3),
            "wet_root_days_oct_dec": int((octdec["GWETROOT"] >= SOIL_WET_ROOT).sum()),
            "cold_days_le10_dec_feb": int((winter["T2M_MIN"] <= COLD_LE).sum()) if rabi_ok else np.nan,
            "frost_days_le2_dec_feb": int((winter["T2M_MIN"] <= FROST_LE).sum()) if rabi_ok else np.nan,
        }
        rows.append(r)
    return pd.DataFrame(rows)


def monthly(point, df):
    g = df.groupby(df.index.month)
    nyears = df.index.year.nunique()
    m = pd.DataFrame({
        "t2m": g["T2M"].mean(), "tmax": g["T2M_MAX"].mean(), "tmin": g["T2M_MIN"].mean(),
        "rain_mm": g["PRECTOTCORR"].sum() / nyears,
        "rainy_days": (df["PRECTOTCORR"] >= RAIN_DAY_MM).groupby(df.index.month).sum() / nyears,
        "rh2m": g["RH2M"].mean(), "gwettop": g["GWETTOP"].mean(), "gwetroot": g["GWETROOT"].mean(),
    }).round(3)
    m.insert(0, "month", m.index)
    m.insert(0, "point", point)
    return m.reset_index(drop=True)


def trend(years, vals):
    ok = ~np.isnan(vals)
    y, v = np.array(years)[ok], np.array(vals)[ok]
    if len(v) < 10:
        return None
    slope = stats.theilslopes(v, y)[0]
    tau, p = stats.kendalltau(y, v)
    return {"per_decade": round(float(slope) * 10, 3), "mk_tau": round(float(tau), 3),
            "p_value": round(float(p), 4), "significant_5pct": bool(p < 0.05), "n_years": int(ok.sum())}


def md(doy_series):
    s = doy_series.dropna()
    if s.empty:
        return None
    d = pd.Timestamp(2001, 1, 1) + pd.to_timedelta(float(s.median()) - 1, unit="D")
    q1 = pd.Timestamp(2001, 1, 1) + pd.to_timedelta(float(s.quantile(.25)) - 1, unit="D")
    q3 = pd.Timestamp(2001, 1, 1) + pd.to_timedelta(float(s.quantile(.75)) - 1, unit="D")
    return {"median": d.strftime("%d %b"), "iqr": f"{q1.strftime('%d %b')} - {q3.strftime('%d %b')}"}


def main():
    pts = pd.read_csv(ROOT / "data/points.csv")
    ys, ms, summary = [], [], {}
    for _, p in pts.iterrows():
        df = pd.read_csv(OUT / f"power_{p['name']}.csv", parse_dates=["date"], index_col="date")
        y = yearly(p["name"], df)
        ys.append(y)
        ms.append(monthly(p["name"], df))
        base, recent = y[(y.year >= 1981) & (y.year <= 2010)], y[y.year >= 2016]
        keys = ["annual_rain_mm", "kharif_rain_mm", "t2m_mean_annual", "heat_days_gt40_mar_may",
                "tmax_mean_mar_may", "longest_dry_spell_days", "dry_spells_ge10", "onset_doy",
                "season_length_days", "wet_root_days_oct_dec"]
        summary[p["name"]] = {
            "location": {"lat": float(p["lat"]), "lon": float(p["lon"])},
            "evidence": {"dataset": "NASA POWER daily (AG community)", "period": f"{int(y.year.min())}-{int(y.year.max())}",
                         "resolution": "~0.5 x 0.625 deg grid (about 50 km), point value",
                         "validity": "degraded at farm scale: gridded, cannot see field-level differences"},
            "monsoon_onset": md(y["onset_doy"]),
            "monsoon_withdrawal": md(y["withdrawal_doy"]),
            "median": {k: round(float(y[k].median()), 2) for k in keys},
            "baseline_1981_2010_mean": {k: round(float(base[k].mean()), 2) for k in keys},
            "recent_2016_2025_mean": {k: round(float(recent[k].mean()), 2) for k in keys},
            "trend": {k: trend(y.year.values, y[k].values.astype(float)) for k in keys},
            "false_onset_note": f"onset rule: >= {ONSET_MM} mm in {ONSET_WINDOW_DAYS} days from 1 Jun, no {FALSE_ONSET_DRY_DAYS}-day dry run in next 30 days",
            "gwetroot_note": "POWER GWETROOT is a modelled index with a floor near 0.59; use relative changes only; SMAP is the cross-check",
            "frost_note": "frost days (T2M_MIN <= 2C) in Dec-Feb: total over years = %d" % int(np.nansum(y["frost_days_le2_dec_feb"])),
        }
    pd.concat(ys).to_csv(OUT / "features_yearly.csv", index=False)
    pd.concat(ms).to_csv(OUT / "features_monthly_clim.csv", index=False)
    (OUT / "features_summary.json").write_text(json.dumps(summary, indent=2, default=str))
    print("wrote features_yearly.csv, features_monthly_clim.csv, features_summary.json")


if __name__ == "__main__":
    main()
