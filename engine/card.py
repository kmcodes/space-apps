"""Template evidence cards (no LLM in this version). Five sections, always including a local-review risk."""
LABEL = {"water_fit": "water fit", "timing_fit": "sowing and harvest timing", "bare_days": "keeping the field covered",
         "nitrogen": "nitrogen from legumes", "forage": "fodder value", "market": "price signal"}
REVIEW = "This is a hypothesis for local review by a farmer, KVK or agronomist, not a prescription."
RISK_FLAGS = {
    "onset_after_window": "In some years the monsoon starts after this crop's sowing window closes.",
    "heat_exposure": "The crop cycle can run into the pre-monsoon heat (after mid-March).",
}


def build_card(strategy_id, comps, weights, evidence_lines, constraints, crops):
    contribution = {k: weights[k] * comps[k].score for k in weights if comps[k].status == "ok"}
    top = sorted(contribution, key=contribution.get, reverse=True)[:2]
    why = ("Suggested mainly because of " + " and ".join(LABEL[k] for k in top) + ".") if top else \
          "Not enough scored information to say why."
    benefits = [f"{LABEL[k].capitalize()}: strong ({comps[k].score:.0f}/100)"
                for k, r in comps.items() if r.status == "ok" and r.score >= 70]
    gaps = []
    for k, r in comps.items():
        if r.status == "missing":
            gaps.append(f"{LABEL[k].capitalize()} could not be scored: {r.detail.get('reason', 'input missing')}")
        elif r.status == "ok" and r.validity == "unverified":
            gaps.append(f"{LABEL[k].capitalize()} relies on unverified inputs or a proxy")
    risks = [REVIEW]
    if constraints.get("equipment") == "basic":
        for c in crops:
            if c.equipment == "sprayer":
                risks.append(f"{c.name} usually needs a sprayer; you said you have basic equipment.")
    for flag in comps.get("timing_fit").detail.get("flags", []) if "timing_fit" in comps and comps["timing_fit"].status == "ok" else []:
        if flag in RISK_FLAGS:
            risks.append(RISK_FLAGS[flag])
    return {"why_suggested": why, "evidence": [e["claim"] for e in evidence_lines], "benefits": benefits,
            "gaps": gaps, "risks_for_local_review": risks}
