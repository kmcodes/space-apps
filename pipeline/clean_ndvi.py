"""Clean AppEEARS MOD13Q1 CSV -> data/processed/ndvi.csv.

Keeps pixel_reliability 0 (good) and 1 (marginal); drops 2 (snow/ice) and 3 (cloudy).
NDVI/EVI arrive already scaled to -0.2..1.
"""
import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "data/raw/appeears/fieldshift-ndvi-MOD13Q1-061-results.csv"
P = "MOD13Q1_061__250m_16_days_"

kept, dropped = [], 0
for r in csv.DictReader(open(SRC)):
    rel = int(float(r[P + "pixel_reliability"]))
    ndvi = r[P + "NDVI"]
    if rel not in (0, 1) or ndvi in ("", "-3000", "-0.3"):
        dropped += 1
        continue
    kept.append([r["ID"], r["Date"], round(float(ndvi), 4), round(float(r[P + "EVI"]), 4), rel])

kept.sort(key=lambda x: (x[0], x[1]))
out = ROOT / "data/processed/ndvi.csv"
with open(out, "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["point", "date", "ndvi", "evi", "reliability"])
    w.writerows(kept)
print(f"kept {len(kept)}, dropped {dropped} -> {out}")
