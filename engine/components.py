"""Component scores, 0-100. Pure functions.

Every function returns a Result. status:
  'ok'      score is a real number (a legitimate 0 is still 'ok')
  'missing' an input is blank or unknown: score is None, the gap is reported. Never zero.
  'na'      component does not apply to this crop (e.g. water fit of fallow)
validity: 'valid' | 'degraded' | 'unverified' (worst input wins).
"""
import math
from dataclasses import dataclass, field

from . import config


@dataclass(frozen=True)
class Result:
    score: float | None
    status: str
    validity: str = "unverified"
    detail: dict = field(default_factory=dict)


def _missing(reason):
    return Result(None, "missing", "unverified", {"reason": reason})


def _rating(value, unverified, name):
    if value is None:
        return _missing(f"{name} rating is blank")
    validity = "unverified" if "ratings" in unverified else "valid"
    return Result(float(config.RATING_SCORE[value]), "ok", validity, {"rating": value})


def nitrogen(crop):
    return _rating(crop.n_fixation, crop.unverified, "n_fixation")


def forage(crop):
    return _rating(crop.fodder_value, crop.unverified, "fodder_value")


def water_fit(crop, yf):
    if crop.role == "baseline":
        return Result(None, "na", "valid", {"reason": "not applicable to fallow"})
    if crop.season is None:
        return _missing("season is unknown")
    if crop.season == "kharif":
        need = crop.water_need_mid
        if need is None:
            return _missing("water_need_mm is blank")
        score = min(100.0, 100.0 * yf["kharif_rain_mm"] / need)
        validity = "unverified" if "water_need_mm" in crop.unverified else "degraded"
        return Result(score, "ok", validity, {"kind": "kharif rain / need", "rain_mm": yf["kharif_rain_mm"], "need_mm": need})
    # rabi: proxy from wet root-zone days
    wet = yf.get("wet_root_days_oct_dec")
    if wet is None or (isinstance(wet, float) and math.isnan(wet)):
        return _missing("no soil-wetness data for this source")
    if crop.water_need is None:
        return _missing("water_need rating is blank")
    needed = config.RABI_WET_DAYS_NEEDED[crop.water_need]
    return Result(min(100.0, 100.0 * wet / needed), "ok", "unverified",
                  {"kind": "proxy: wet root-zone days Oct-Dec / days wanted", "wet_days": wet, "days_needed": needed})
