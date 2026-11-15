"""compare(request) -> four scored rotation strategies with evidence, uncertainty and cards.

Every strategy is scored for every year in the weather record (1981-2025), so the result carries a median,
a p20-p80 band and the share of years each strategy ranks first. A second weather source (ERA5) is run
the same way as a cross-check. The engine never writes free text from a language model; cards are templates.
"""
import json
import math
from pathlib import Path

import numpy as np
import pandas as pd

from . import config
from .card import build_card
from .components import timing_fit
from .coverage import locate, presets
from .crops import load_crops
from .evidence import describe
from .market import load_market
from .score import (confidence, coverage, confidence_label, rank_stability, score_variants, strategy_components,
                    total_score)
from .strategies import get_strategies
from .weights import BASE_WEIGHTS, compute_weights

ROOT = Path(__file__).resolve().parent.parent
DISCLAIMER = "This tool supports, and does not replace, the judgement of farmers and local agricultural experts."
YEAR_FIELDS = ["kharif_rain_mm", "wet_root_days_oct_dec", "onset_doy", "withdrawal_doy"]
MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


class Engine:
    def __init__(self, crops, power, era5, market, soil, ndvi, ranges, season_risk):
        self.crops, self.power, self.era5, self.market = crops, power, era5, market
        self.soil, self.ndvi, self.ranges = soil, ndvi, ranges
        self.season_risk = season_risk  # months of heat, in-monsoon dry spells and frost (pipeline/season_risk.py)

    @classmethod
    def from_repo(cls, root=ROOT):
        root = Path(root)
        proc = root / "data/processed"
        return cls(
            crops=load_crops(root / "data/crops.csv"),
            power=pd.read_csv(proc / "features_yearly.csv"),
            era5=pd.read_csv(proc / "features_yearly_era5.csv"),
            market=load_market(proc / "mandi_monthly.csv", root / "data/msp.csv"),
            soil=pd.read_csv(proc / "soil.csv"),
            ndvi=pd.read_csv(proc / "ndvi.csv", parse_dates=["date"]),
            ranges=json.loads((proc / "features_ranges.json").read_text()),
            season_risk=json.loads((proc / "season_risk.json").read_text()),
        )

    # ---- helpers ---------------------------------------------------------
    @staticmethod
    def _years(df, point):
        rows = df[df.point == point]
        return [{k: float(r[k]) for k in YEAR_FIELDS} for _, r in rows.iterrows()]

    def _median_year(self, years):
        return {k: float(np.nanmedian([y[k] for y in years])) if not all(math.isnan(y[k]) for y in years) else math.nan
                for k in YEAR_FIELDS}

    def _totals(self, strategy, years, point, priorities, constraints, only=None):
        out = []
        for yf in years:
            comps = strategy_components(strategy, self.crops, yf, self.market, point)
            total, _, _ = total_score(comps, priorities, constraints, only)
            out.append(math.nan if total is None else total)
        return out

    def _site_evidence(self, point, period):
        ev = []
        n = self.ndvi[(self.ndvi.point == point)]
        monthly = n.groupby(n.date.dt.month).ndvi.mean()
        low = monthly.min()
        low_months = [MONTHS[m - 1] for m, v in monthly.items() if v <= low + 0.05]
        ev.append({"topic": "bare_field_window",
                   "claim": f"Greenness is lowest in {', '.join(low_months)} (NDVI about {low:.2f}); fields are typically bare then",
                   "dataset": "NASA MODIS MOD13Q1 NDVI via AppEEARS", "period": "2015-2025",
                   "resolution": "250 m pixel at a farm point (small plots mix inside it)", "validity": "degraded",
                   "validity_reason": "a 250 m pixel averages several small plots", "gap": "confirm with the farmer"})
        s = self.soil[(self.soil.point == point) & (self.soil.depth_cm == "0-5")].set_index("property").value
        ev.append({"topic": "soil",
                   "claim": f"Topsoil is about {s['clay_pct']:.0f}% clay, {s['sand_pct']:.0f}% sand, pH {s['ph']:.1f}",
                   "dataset": "SoilGrids (ISRIC), downloaded by hand from soilgrids.org", "period": "modelled map",
                   "resolution": "250 m", "validity": "degraded",
                   "validity_reason": "a modelled map, not a soil test", "gap": "a soil test would confirm"})
        r = self.ranges[point]
        on, wd, hd = r["onset_doy"], r["withdrawal_doy"], r["heat_days_gt40_mar_may"]
        ev.append({"topic": "monsoon",
                   "claim": (f"The monsoon usually starts between {on['range_dates'][0]} and {on['range_dates'][1]} "
                             f"and ends between {wd['range_dates'][0]} and {wd['range_dates'][1]}"),
                   "dataset": "NASA POWER and ERA5 reanalysis", "period": period, "resolution": "25-50 km grid",
                   "validity": "degraded", "validity_reason": "two datasets differ by a week or more on onset",
                   "gap": "local rain records would confirm"})
        ev.append({"topic": "heat",
                   "claim": (f"Days above 40 C in March-May per year: {hd['range'][0]:.0f} to {hd['range'][1]:.0f} "
                             f"depending on the dataset; the two datasets disagree"),
                   "dataset": "NASA POWER and ERA5 reanalysis", "period": period, "resolution": "25-50 km grid",
                   "validity": "degraded", "validity_reason": "datasets disagree", "gap": "shown as a range on purpose"})
        return ev

    def _card(self, s, comps, weights, evidence, constraints, cov, incomplete):
        card = build_card(s.id, comps, weights, evidence, constraints, [self.crops[c] for c in s.crops])
        if incomplete:
            card["gaps"].insert(0, f"Scored on only {100 * cov:.0f}% of the information that matters for your priorities, "
                                   f"so this strategy is not ranked against the others.")
        return card

    # ---- public ----------------------------------------------------------
    def compare(self, request):
        priorities = request.get("priorities", [])
        constraints = request.get("constraints", {})
        compute_weights(priorities, constraints, tuple(BASE_WEIGHTS))  # validates priorities early
        pts = presets()
        if request.get("location"):
            lat, lon = pts[request["location"]]
        else:
            lat, lon = request["lat"], request["lon"]
        loc = locate(lat, lon)
        location = {"lat": lat, "lon": lon, "nearest": loc.nearest, "distance_km": round(loc.distance_km, 1),
                    "layers": loc.layers}
        if not loc.served:
            return {"served": False, "reason": loc.reason, "location": location, "disclaimer": DISCLAIMER}

        point = loc.nearest
        years_p, years_e = self._years(self.power, point), self._years(self.era5, point)
        yf_med = self._median_year(years_p)
        period = f"{int(self.power[self.power.point == point].year.min())}-{int(self.power[self.power.point == point].year.max())}"
        ctx = {"weather": {"dataset": "NASA POWER daily (AG community)", "period": period,
                           "resolution": "~50 km grid, point value"}}

        strategies = get_strategies(request.get("current_rotation", "soybean_fallow"))
        totals_p = {s.id: self._totals(s, years_p, point, priorities, constraints) for s in strategies}
        yf_med_e = self._median_year(years_e)
        common = {}
        for s in strategies:  # components scored under BOTH sources, so the cross-check compares like with like
            cp = strategy_components(s, self.crops, yf_med, self.market, point)
            ce = strategy_components(s, self.crops, yf_med_e, self.market, point)
            common[s.id] = {k for k in cp if cp[k].status == "ok" and ce[k].status == "ok"}
        totals_e = {s.id: self._totals(s, years_e, point, priorities, constraints, common[s.id]) for s in strategies}
        totals_pc = {s.id: self._totals(s, years_p, point, priorities, constraints, common[s.id]) for s in strategies}
        stability = rank_stability({k: [0 if math.isnan(x) else x for x in v] for k, v in totals_p.items()})

        out = []
        for s in strategies:
            comps = strategy_components(s, self.crops, yf_med, self.market, point)
            _, weights, used = total_score(comps, priorities, constraints)
            tp = np.array(totals_p[s.id], dtype=float)
            te = np.array(totals_e[s.id], dtype=float)
            tpc = np.array(totals_pc[s.id], dtype=float)
            conf = confidence(comps, weights)
            cov = coverage(comps, priorities, constraints)
            incomplete = cov < config.MIN_COVERAGE
            evidence = [e for e in (describe(k, r, ctx) for k, r in comps.items()) if e]
            variants = score_variants(s, self.crops, yf_med, self.market, point, priorities, constraints)
            # When each crop is in the ground in the median year, for the year calendar in the app.
            # Same timing_fit the scores use, so it matches bare_days. harvest_doy may pass 365 (next year).
            calendar = []
            for name in s.crops:
                t = timing_fit(self.crops[name], yf_med)
                if t.status == "ok":
                    calendar.append({"crop": name, "sow_doy": round(t.detail["sow_doy"]),
                                     "harvest_doy": round(t.detail["harvest_doy"])})
            out.append({
                "id": s.id, "name": s.name, "kind": s.kind, "crops": list(s.crops), "note": s.note,
                "duplicate_of": s.duplicate_of, "calendar": calendar,
                "total_score": round(float(np.nanmedian(tp)), 1),
                "score_band": [round(float(np.nanpercentile(tp, 20)), 1), round(float(np.nanpercentile(tp, 80)), 1)],
                "rank_stability": round(stability[s.id], 3),
                "score_by_source": {"power": round(float(np.nanmedian(tp)), 1),
                                    "power_comparable": round(float(np.nanmedian(tpc)), 1),
                                    "era5": None if np.isnan(te).all() else round(float(np.nanmedian(te)), 1),
                                    "note": "era5 and power_comparable use only the components scored under both sources"},
                "confidence": round(conf, 2), "confidence_label": confidence_label(conf),
                "weights": {k: round(v, 1) for k, v in weights.items()},
                "components": {k: {"score": None if r.score is None else round(r.score, 1), "status": r.status,
                                   "validity": r.validity, "weight": round(weights.get(k, 0.0), 1)}
                               for k, r in comps.items()},
                "evidence": evidence,
                "data_coverage": round(cov, 2), "incomplete": incomplete,
                "card": self._card(s, comps, weights, evidence, constraints, cov, incomplete),
                "variants": {v: {"total_score": None if d["total"] is None else round(d["total"], 1)}
                             for v, d in variants.items()},
            })
        totals = {s["id"]: s["total_score"] for s in out if not s["incomplete"]}
        top = max(totals.values()) if totals else 0.0
        return {
            "served": True, "location": location,
            "ranking": sorted(totals, key=totals.get, reverse=True),
            "tied_with_top": [i for i, t in totals.items() if top - t <= config.TIE_POINTS],
            "weights_used": compute_weights(priorities, constraints, tuple(BASE_WEIGHTS)),
            "strategies": out, "site_evidence": self._site_evidence(point, period),
            "season_risk": {**self.season_risk["points"][point], "definitions": self.season_risk["definitions"]},
            "monsoon": {"onset_doy": round(yf_med["onset_doy"]), "withdrawal_doy": round(yf_med["withdrawal_doy"]),
                        "note": "median year, NASA POWER; ERA5 differs by a week or more"},
            "disclaimer": DISCLAIMER, "language": "en",
        }
