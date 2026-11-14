"""Combine crop scores into strategy scores (the accepted rules), weight them, and describe confidence.

Rules (Kartik + Amrita, 14 Nov 2026):
 sequence  RISK components (water_fit, timing_fit): the worse crop. BENEFIT components (nitrogen, forage,
           market): average weighted by days in the ground (fallow has none). bare_days: whole year.
 mixed     treated as one crop: water need = main crop + a share of the partner; timing = worse crop;
           nitrogen/forage = the best crop; market = average. bare_days: union.
 variants  S3 shows one default crop; alternatives are scored separately by replacing the last crop.
A crop with a missing value makes the strategy value missing (a gap), never zero.
"""
from dataclasses import replace

from . import config
from .components import Result, bare_days, forage, nitrogen, timing_fit, water_fit
from .validity import worst
from .weights import compute_weights

RISK = ("water_fit", "timing_fit")
BENEFIT = ("nitrogen", "forage", "market")


def _crop_results(crop, yf, market, point):
    return {
        "water_fit": water_fit(crop, yf), "timing_fit": timing_fit(crop, yf),
        "nitrogen": nitrogen(crop), "forage": forage(crop), "market": market.component(point, crop.name),
    }


def _gap(name, crops_missing):
    return Result(None, "missing", "unverified", {"reason": f"{name} is missing for: {', '.join(crops_missing)}"})


def _applicable(name, per_crop):
    return [(c, r[name]) for c, r in per_crop.items() if r[name].status != "na"]


def _combine(name, per_crop, how, weights=None):
    items = _applicable(name, per_crop)
    if not items:
        return Result(None, "na", "valid", {})
    missing = [c for c, r in items if r.status == "missing"]
    if missing:
        return _gap(name, missing)
    validity = worst(*(r.validity for _, r in items))
    scores = [r.score for _, r in items]
    if how == "min":
        score, detail = min(scores), {"worst_crop": min(items, key=lambda it: it[1].score)[0]}
    elif how == "max":
        score, detail = max(scores), {}
    else:  # weighted mean
        w = [(weights or {}).get(c, 1.0) for c, _ in items]
        if sum(w) == 0:
            w = [1.0] * len(items)
        score, detail = sum(a * b for a, b in zip(scores, w)) / sum(w), {}
    return Result(score, "ok", validity, detail)


def _bare(per_crop):
    timings = [r["timing_fit"] for r in per_crop.values()]
    if any(t.status == "missing" for t in timings):
        return _gap("bare_days (needs crop timing)", [c for c, r in per_crop.items() if r["timing_fit"].status == "missing"])
    ok = [t for t in timings if t.status == "ok"]
    intervals = [(t.detail["sow_doy"], t.detail["harvest_doy"]) for t in ok]
    validity = worst("degraded", *(t.validity for t in ok)) if ok else "valid"
    return bare_days(intervals, validity)


def _mixed_water(main, partner, yf):
    for c in (main, partner):
        if c.water_need_mid is None:
            return _gap("water_fit", [c.name])
    need = main.water_need_mid + config.INTERCROP_PARTNER_WATER_SHARE * partner.water_need_mid
    unverified = "water_need_mm" in main.unverified or "water_need_mm" in partner.unverified
    return Result(min(100.0, 100.0 * yf["kharif_rain_mm"] / need), "ok", "unverified" if unverified else "degraded",
                  {"kind": "mixed: main need + partner share", "rain_mm": yf["kharif_rain_mm"], "need_mm": need})


def strategy_components(strategy, crops, yf, market, point):
    chosen = {name: crops[name] for name in strategy.crops}
    per_crop = {name: _crop_results(c, yf, market, point) for name, c in chosen.items()}
    if strategy.kind == "single":
        out = dict(per_crop[strategy.crops[0]])
    elif strategy.kind == "sequence":
        days = {n: (c.duration_mid or 0.0) for n, c in chosen.items()}
        out = {n: _combine(n, per_crop, "min") for n in RISK}
        out.update({n: _combine(n, per_crop, "mean", days) for n in BENEFIT})
    elif strategy.kind == "mixed":
        main, partner = chosen[strategy.crops[0]], chosen[strategy.crops[1]]
        out = {"water_fit": _mixed_water(main, partner, yf), "timing_fit": _combine("timing_fit", per_crop, "min"),
               "nitrogen": _combine("nitrogen", per_crop, "max"), "forage": _combine("forage", per_crop, "max"),
               "market": _combine("market", per_crop, "mean")}
    else:
        raise ValueError(f"unknown strategy kind: {strategy.kind}")
    out["bare_days"] = _bare(per_crop)
    return out


def total_score(components, priorities, constraints):
    used = [k for k, r in components.items() if r.status == "ok"]
    if not used:
        return None, {}, []
    weights = compute_weights(priorities, constraints, used)
    total = sum(weights[k] * components[k].score for k in used) / 100.0
    return total, weights, used


def confidence(components, weights):
    total = sum(weights.values())
    if not total:
        return 0.0
    return sum(w for k, w in weights.items() if components[k].validity != "unverified") / total


def confidence_label(value):
    return "green" if value >= 0.66 else "yellow" if value >= 0.33 else "grey"


def rank_stability(totals_by_strategy):
    ids = list(totals_by_strategy)
    n = len(next(iter(totals_by_strategy.values())))
    share = {i: 0.0 for i in ids}
    for y in range(n):
        best = max(totals_by_strategy[i][y] for i in ids)
        winners = [i for i in ids if totals_by_strategy[i][y] == best]
        for i in winners:
            share[i] += 1.0 / len(winners) / n
    return share


def score_variants(strategy, crops, yf, market, point, priorities, constraints):
    out = {}
    for v in strategy.variants:
        alt = replace(strategy, crops=strategy.crops[:-1] + (v,), variants=())
        comps = strategy_components(alt, crops, yf, market, point)
        total, weights, used = total_score(comps, priorities, constraints)
        out[v] = {"total": total, "components": comps, "weights": weights}
    return out
