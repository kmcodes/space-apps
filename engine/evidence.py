"""Evidence lines: every number shown to a user is one of these, with dataset, period, resolution and validity.

Numbers in `claim` come only from the engine's computed detail, so a later text-rewriting step can be
checked against them.
"""
VALIDITY_REASON = {
    "valid": "",
    "degraded": "gridded weather (about 50 km) cannot see field-level differences",
    "unverified": "relies on crop-sheet values marked unverified, or on a proxy; needs local review",
}
CROP_SHEET = {"dataset": "Crop profile sheet (data/crops.csv; ICAR-CRIDA, FAO and other published sources)",
              "period": "n/a", "resolution": "crop level, not field level"}
MARKET = {"dataset": "Agmarknet mandi prices via data.gov.in, and MSP", "period": "last 12 months",
          "resolution": "district markets"}


def _claim(name, r):
    d, s = r.detail, r.score
    if name == "water_fit":
        if "rain_mm" in d:
            return (f"June-September rain is about {d['rain_mm']:.0f} mm against a crop need of about {d['need_mm']:.0f} mm "
                    f"({d.get('kind', '')})").replace(" ()", "")
        if "wet_days" in d:
            return (f"About {d['wet_days']:.0f} days with a moist root zone in Oct-Dec against about {d['days_needed']} days "
                    f"wanted (a proxy, not a water balance)")
    if name == "timing_fit" and "sow_doy" in d:
        flags = ", ".join(d.get("flags", [])) or "no timing problems"
        return f"Sowing around day {d['sow_doy']:.0f} and harvest around day {d['harvest_doy']:.0f} of the year ({flags})"
    if name == "bare_days" and "bare_days" in d:
        return f"About {d['bare_days']} days a year with no crop in the field ({d['covered_days']} days covered)"
    if name == "market" and "ratio" in d:
        return (f"Recent mandi price about Rs {d['price_rs_per_quintal']:.0f} per quintal against an MSP of "
                f"Rs {d['msp_rs_per_quintal']:.0f} ({d['months']} months, price swings {100 * d['volatility']:.0f}%)")
    return f"{name.replace('_', ' ')} score {s:.0f} out of 100"


def describe(name, result, ctx):
    if result.status == "na":
        return None
    if name in ("water_fit", "timing_fit"):
        source = ctx["weather"]
    elif name == "market":
        source = MARKET
    elif name == "bare_days":
        source = {**ctx["weather"], "dataset": ctx["weather"]["dataset"] + " (onset) and crop calendar; NDVI cross-check"}
    else:
        source = CROP_SHEET
    line = {"dataset": source["dataset"], "period": source["period"], "resolution": source["resolution"],
            "validity": result.validity, "validity_reason": VALIDITY_REASON[result.validity], "used_in": [name]}
    if result.status == "missing":
        return {**line, "claim": f"{name.replace('_', ' ')} could not be scored", "value": None,
                "gap": result.detail.get("reason", "input missing")}
    gap = "" if result.validity == "valid" else VALIDITY_REASON[result.validity]
    return {**line, "claim": _claim(name, result), "value": round(result.score, 1), "gap": gap}
