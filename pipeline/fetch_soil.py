"""SoilGrids 2.0 point values for each point in data/points.csv.

REST API only. On 14 Nov 2026 the API returned 503. The raster fallbacks were
tested and rejected: the files.isric.org VRT returned nodata (-32768) at all 3
points, and the maps.isric.org WCS returned 71/72 zero pixels. Do not trust
those paths. This script fails loudly and writes nothing if REST is down.
Output: data/processed/soil.csv  (real units, mean value)
"""
import csv
import json
import time
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PROPS = ["sand", "silt", "clay", "soc", "phh2o", "bdod", "cec"]
DEPTHS = ["0-5cm", "5-15cm", "15-30cm", "30-60cm"]
# SoilGrids stores integers; divide by factor to get conventional units
FACTOR = {"sand": 10, "silt": 10, "clay": 10, "soc": 10, "phh2o": 10, "bdod": 100, "cec": 10}
UNITS = {"sand": "%", "silt": "%", "clay": "%", "soc": "g/kg", "phh2o": "pH", "bdod": "kg/dm3", "cec": "cmol(c)/kg"}


def rest(lat, lon):
    q = [("lon", lon), ("lat", lat), ("value", "mean")]
    q += [("property", p) for p in PROPS] + [("depth", d) for d in DEPTHS]
    url = "https://rest.isric.org/soilgrids/v2.0/properties/query?" + urllib.parse.urlencode(q)
    with urllib.request.urlopen(url, timeout=120) as r:
        data = json.load(r)
    out = {}
    for layer in data["properties"]["layers"]:
        p = layer["name"]
        for d in layer["depths"]:
            v = d["values"]["mean"]
            out[(p, d["label"].replace(" ", "").replace("cm", "cm"))] = None if v is None else v / FACTOR[p]
    return out


def main():
    with open(ROOT / "data/points.csv") as f:
        pts = list(csv.DictReader(f))
    rows = []
    for p in pts:
        for attempt in range(5):
            try:
                vals = rest(p["lat"], p["lon"])
                break
            except Exception as e:
                print(f"{p['name']}: attempt {attempt + 1} failed ({e})", flush=True)
                time.sleep(15)
        else:
            raise SystemExit("SoilGrids REST unavailable; nothing written")
        print("done", p["name"], flush=True)
        for (prop, depth), v in vals.items():
            rows.append([p["name"], prop, depth, "" if v is None else round(v, 3), UNITS[prop], "SoilGrids REST"])
        time.sleep(13)
    out = ROOT / "data/processed/soil.csv"
    with open(out, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["point", "property", "depth", "mean", "unit", "source"])
        w.writerows(rows)
    print("wrote", out)


if __name__ == "__main__":
    main()
