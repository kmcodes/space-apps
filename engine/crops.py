"""Load the crop sheet (data/crops.csv).

Rule: a blank cell becomes None. Blank never means zero; the engine treats None as a gap.
"""
import csv
from dataclasses import dataclass
from datetime import date


def mmdd_to_doy(s):
    """'06-15' -> day of year in a non-leap year; blank -> None."""
    if not s:
        return None
    month, day = s.split("-")
    return date(2001, int(month), int(day)).timetuple().tm_yday


def _num(s):
    return float(s) if s not in ("", None) else None


def _text(s):
    return s if s else None


@dataclass(frozen=True)
class Crop:
    name: str
    role: str | None
    season: str | None
    sow_start_doy: int | None
    sow_end_doy: int | None
    duration_min: float | None
    duration_max: float | None
    water_need_mm_min: float | None
    water_need_mm_max: float | None
    water_need: str | None
    legume: bool | None
    n_fixation: str | None
    ground_cover: str | None
    residue: str | None
    fodder_value: str | None
    equipment: str | None
    unverified: frozenset

    @property
    def duration_mid(self):
        if self.duration_min is None or self.duration_max is None:
            return None
        return (self.duration_min + self.duration_max) / 2

    @property
    def water_need_mid(self):
        if self.water_need_mm_min is None or self.water_need_mm_max is None:
            return None
        return (self.water_need_mm_min + self.water_need_mm_max) / 2


def load_crops(path):
    out = {}
    with open(path) as f:
        for r in csv.DictReader(f):
            legume = {"yes": True, "no": False}.get(r["legume"])
            out[r["crop"]] = Crop(
                name=r["crop"], role=_text(r["role"]), season=_text(r["season"]),
                sow_start_doy=mmdd_to_doy(r["sow_start"]), sow_end_doy=mmdd_to_doy(r["sow_end"]),
                duration_min=_num(r["duration_days_min"]), duration_max=_num(r["duration_days_max"]),
                water_need_mm_min=_num(r["water_need_mm_min"]), water_need_mm_max=_num(r["water_need_mm_max"]),
                water_need=_text(r["water_need"]), legume=legume, n_fixation=_text(r["n_fixation"]),
                ground_cover=_text(r["ground_cover"]), residue=_text(r["residue"]),
                fodder_value=_text(r["fodder_value"]), equipment=_text(r["equipment"]),
                unverified=frozenset(x for x in r["unverified_fields"].split(";") if x),
            )
    return out
