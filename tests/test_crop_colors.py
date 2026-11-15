"""Every crop in the crop sheet has its own colour on the year bar (web/app/globals.css, --color-crop-<crop>).
Without one a crop would be drawn in no colour, and two crops in one colour would look like one long crop,
which is exactly what the colours are there to prevent. Bare field is black and has no crop colour."""

import csv
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CSS = (ROOT / "web/app/globals.css").read_text(encoding="utf8")
CROPS = [r["crop"] for r in csv.DictReader(open(ROOT / "data/crops.csv", encoding="utf8"))]
COLOURS = dict(re.findall(r"--color-crop-([a-z_]+):\s*(#[0-9a-fA-F]{6})", CSS))


def test_every_crop_in_the_crop_sheet_has_a_colour_except_fallow():
    missing = [c for c in CROPS if c != "fallow" and c not in COLOURS]
    assert missing == []


def test_fallow_has_no_crop_colour_because_a_bare_field_is_black():
    assert "fallow" not in COLOURS


def test_crops_that_can_sit_side_by_side_have_different_colours():
    crops = [c for c in CROPS if c != "fallow"]
    # Sorghum has a kharif and a rabi row in the sheet but is one crop, so it keeps one colour; every other crop is its own.
    families = {("sorghum" if c.startswith("sorghum") else c): COLOURS[c] for c in crops if c in COLOURS}
    assert len(set(v.lower() for v in families.values())) == len(families)
    assert COLOURS["sorghum_kharif"] == COLOURS["sorghum_rabi"]


def test_no_crop_is_drawn_in_the_colour_of_bare_field_or_of_a_risk_marker():
    soil, almanac = "#2b2320", "#b3261e"
    assert all(v.lower() not in (soil, almanac) for v in COLOURS.values())
