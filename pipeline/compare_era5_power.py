"""Cross-check NASA POWER against ERA5 (Open-Meteo copy) at each point.

Questions answered:
 1. Do they agree on the level of rain and temperature? (bias, correlation)
 2. Do they agree on the *trends* (the surprising POWER rainfall rise, no warming)?
Out: data/processed/era5_vs_power.json (+ printed table)
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data/processed"


def trend(series):
    y = series.index.values.astype(float)
    v = series.values.astype(float)
    ok = ~np.isnan(v)
    slope = stats.theilslopes(v[ok], y[ok])[0] * 10
    tau, p = stats.kendalltau(y[ok], v[ok])
    return {"per_decade": round(float(slope), 2), "p": round(float(p), 4), "significant": bool(p < 0.05)}


def annual(df, col, how, months=None):
    d = df if months is None else df[df.index.month.isin(months)]
    g = d[col].groupby(d.index.year)
    return (g.sum() if how == "sum" else g.mean())


def main():
    pts = pd.read_csv(ROOT / "data/points.csv")["name"].tolist()
    era = pd.read_csv(OUT / "era5_daily_openmeteo.csv", parse_dates=["date"])
    res = {}
    for p in pts:
        pw = pd.read_csv(OUT / f"power_{p}.csv", parse_dates=["date"], index_col="date")
        er = era[era.point == p].set_index("date").drop(columns="point")
        both = pw[["PRECTOTCORR", "T2M", "T2M_MAX"]].join(er[["rain_mm", "t2m_mean_c", "t2m_max_c"]], how="inner").dropna()
        r = {"days_compared": int(len(both))}
        r["daily_rain_corr"] = round(float(both.PRECTOTCORR.corr(both.rain_mm)), 3)
        mon = both.resample("MS").agg({"PRECTOTCORR": "sum", "rain_mm": "sum", "T2M": "mean", "t2m_mean_c": "mean"})
        r["monthly_rain_corr"] = round(float(mon.PRECTOTCORR.corr(mon.rain_mm)), 3)
        r["monthly_temp_corr"] = round(float(mon.T2M.corr(mon.t2m_mean_c)), 3)
        r["mean_annual_rain_mm"] = {"power": round(float(annual(both, "PRECTOTCORR", "sum").mean()), 0),
                                    "era5": round(float(annual(both, "rain_mm", "sum").mean()), 0)}
        r["mean_temp_c"] = {"power": round(float(both.T2M.mean()), 2), "era5": round(float(both.t2m_mean_c.mean()), 2)}
        r["mean_tmax_mar_may_c"] = {
            "power": round(float(both[both.index.month.isin([3, 4, 5])].T2M_MAX.mean()), 2),
            "era5": round(float(both[both.index.month.isin([3, 4, 5])].t2m_max_c.mean()), 2)}
        tr = {}
        for name, pcol, ecol, how, months in [
            ("annual_rain_mm", "PRECTOTCORR", "rain_mm", "sum", None),
            ("kharif_rain_mm", "PRECTOTCORR", "rain_mm", "sum", [6, 7, 8, 9]),
            ("t2m_mean_annual", "T2M", "t2m_mean_c", "mean", None),
            ("tmax_mean_mar_may", "T2M_MAX", "t2m_max_c", "mean", [3, 4, 5]),
        ]:
            tr[name] = {"power": trend(annual(both, pcol, how, months)), "era5": trend(annual(both, ecol, how, months))}
            a, b = tr[name]["power"], tr[name]["era5"]
            tr[name]["agree"] = bool(np.sign(a["per_decade"]) == np.sign(b["per_decade"]) and a["significant"] == b["significant"])
        r["trend_per_decade"] = tr
        base = both[(both.index.year >= 1981) & (both.index.year <= 2010)]
        rec = both[both.index.year >= 2016]
        r["kharif_rain_baseline_vs_recent_mm"] = {
            "power": [round(float(annual(base, "PRECTOTCORR", "sum", [6, 7, 8, 9]).mean())), round(float(annual(rec, "PRECTOTCORR", "sum", [6, 7, 8, 9]).mean()))],
            "era5": [round(float(annual(base, "rain_mm", "sum", [6, 7, 8, 9]).mean())), round(float(annual(rec, "rain_mm", "sum", [6, 7, 8, 9]).mean()))]}
        res[p] = r
    (OUT / "era5_vs_power.json").write_text(json.dumps(res, indent=2))
    for p, r in res.items():
        print("==", p, "| days", r["days_compared"], "| corr daily/monthly rain", r["daily_rain_corr"], r["monthly_rain_corr"], "| temp monthly corr", r["monthly_temp_corr"])
        print("   mean annual rain mm", r["mean_annual_rain_mm"], "| mean T", r["mean_temp_c"], "| Tmax Mar-May", r["mean_tmax_mar_may_c"])
        print("   kharif rain 1981-2010 vs 2016+", r["kharif_rain_baseline_vs_recent_mm"])
        for k, v in r["trend_per_decade"].items():
            f = lambda x: f"{x['per_decade']:+.2f}{'*' if x['significant'] else ''}"
            print(f"   trend/decade {k}: POWER {f(v['power'])}  ERA5 {f(v['era5'])}  agree={v['agree']}")


if __name__ == "__main__":
    main()
