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


def _timing_inputs_unverified(crop):
    return any(f.startswith("sow_") or f.startswith("duration") for f in crop.unverified)


def timing_fit(crop, yf):
    """Sowing date from monsoon onset and the crop's window; penalties for late onset, long delay, and
    a crop cycle running into the pre-monsoon heat. All penalty sizes live in config (assumptions)."""
    if crop.role == "baseline":
        return Result(None, "na", "valid", {"reason": "not applicable to fallow"})
    if crop.sow_start_doy is None or crop.sow_end_doy is None or crop.duration_mid is None:
        return _missing("sowing window or duration is blank")
    flags = []
    penalty = 0.0
    if crop.season == "kharif":
        onset = yf["onset_doy"]
        if math.isnan(onset):  # the onset rule found no onset this year: treat as after the window
            flags.append("no_onset_found")
            onset = crop.sow_end_doy + 1
        if onset > crop.sow_end_doy:
            flags.append("onset_after_window")
            penalty += config.LATE_ONSET_PENALTY
        sow = min(max(onset, crop.sow_start_doy), crop.sow_end_doy)
        delay = sow - crop.sow_start_doy
        penalty += min(config.SOWING_DELAY_CAP, max(0, delay - config.SOWING_DELAY_FREE_DAYS) * config.SOWING_DELAY_PER_DAY)
    else:
        sow = crop.sow_start_doy
    harvest = sow + crop.duration_mid
    heat_limit = config.DAYS_IN_YEAR + config.HEAT_SEASON_START_DOY
    if harvest > heat_limit:
        flags.append("heat_exposure")
        penalty += min(config.HEAT_EXPOSURE_CAP, (harvest - heat_limit) * config.HEAT_EXPOSURE_PER_DAY)
    validity = "unverified" if _timing_inputs_unverified(crop) else "degraded"
    return Result(max(0.0, 100.0 - penalty), "ok", validity,
                  {"sow_doy": sow, "harvest_doy": harvest, "flags": flags})


def bare_days(intervals, validity="degraded"):
    """Days in the year with no crop in the ground. intervals = [(sow_doy, harvest_doy), ...]; may wrap the new year."""
    covered = set()
    for start, end in intervals:
        for d in range(int(start), int(end)):
            covered.add(d % config.DAYS_IN_YEAR)
    bare = config.DAYS_IN_YEAR - len(covered)
    return Result(100.0 * (1 - bare / config.DAYS_IN_YEAR), "ok", validity,
                  {"covered_days": len(covered), "bare_days": bare})
