"""Weights from farmer priorities and constraints. Always sums to 100 over the components that have a score.

Rule (Amrita's issue 5): the first priority gets a FIXED 40% of the total, the second 20%; the remainder
follows the base weights. A multiplier would barely move a small component such as forage.
Weights are shown to the user with the results.
"""
from . import config

BASE_WEIGHTS = {"water_fit": 25, "timing_fit": 15, "bare_days": 15, "nitrogen": 15, "forage": 10, "market": 20}

# priority -> components it lifts. Organic matter has no component of its own yet: it uses bare days
# (soil cover) in this version.
PRIORITY_COMPONENTS = {
    "water_saving": ["water_fit"],
    "forage": ["forage"],
    "nitrogen": ["nitrogen"],
    "erosion": ["bare_days"],
    "organic_matter": ["bare_days"],
    "market_income": ["market"],
}
PRIORITY_SHARES = (0.40, 0.20)
LOW_WATER_MULTIPLIER = 1.5


def compute_weights(priorities, constraints, present):
    unknown = [p for p in priorities if p not in PRIORITY_COMPONENTS]
    if unknown:
        raise ValueError(f"unknown priority: {unknown[0]}")
    present = [c for c in BASE_WEIGHTS if c in present]
    own_use = constraints.get("market") == "own_use"

    base = {c: float(BASE_WEIGHTS[c]) for c in present}
    if constraints.get("water_availability") == "low" and "water_fit" in base:
        base["water_fit"] *= LOW_WATER_MULTIPLIER
    if own_use and "market" in base:
        base["market"] = 0.0
    total = sum(base.values())
    base = {c: v / total for c, v in base.items()}

    weights = {c: 0.0 for c in present}
    remaining = 1.0
    seen = []
    for p in priorities:
        if p not in seen:
            seen.append(p)
    for p, share in zip(seen, PRIORITY_SHARES):
        comps = [c for c in PRIORITY_COMPONENTS[p] if c in present and not (own_use and c == "market")]
        if comps:
            remaining -= share
            for c in comps:
                weights[c] += share / len(comps)
    for c in present:
        weights[c] += remaining * base[c]
    return {c: 100.0 * v for c, v in weights.items()}
