"""Sample manually downloaded SoilGrids GeoTIFFs (data/raw/soilgrids/) at each point.

Files were downloaded by hand from soilgrids.org (Download tool, 2x2 deg tile,
mean, 250 m) because the REST API was down on 14 Nov 2026.
Pixel value 0 = masked (built-up / no data), so we use the nearest pixel that is
valid in every layer and record its distance from the requested point.

Units after conversion: clay/sand/silt %, pH, SOC stock t/ha (0-30 cm).
Output: data/processed/soil.csv   (source = SoilGrids web download, manual)
"""
import csv
from pathlib import Path

import numpy as np
import rasterio

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data/raw/soilgrids"
DEPTHS = ["0-5", "5-15", "15-30"]
SCALE = {"clay": 10, "sand": 10, "ph": 10}  # g/kg -> %, pH x10 -> pH


def main():
    files = sorted(RAW.glob("*.tif"))
    arrs = {f.stem: rasterio.open(f) for f in files}
    first = next(iter(arrs.values()))
    data = {k: v.read(1) for k, v in arrs.items()}
    valid = np.all([a > 0 for a in data.values()], axis=0)
    rows, cols = np.nonzero(valid)
    xs, ys = first.transform * (cols + 0.5, rows + 0.5)
    xs, ys = np.array(xs), np.array(ys)

    pts = list(csv.DictReader(open(ROOT / "data/points.csv")))
    out = []
    for p in pts:
        lat, lon = float(p["lat"]), float(p["lon"])
        d = np.hypot((xs - lon) * np.cos(np.radians(lat)), ys - lat) * 111.0
        i = d.argmin()
        r, c = rows[i], cols[i]
        meta = [p["name"], round(float(ys[i]), 4), round(float(xs[i]), 4), round(float(d[i]), 2)]
        for depth in DEPTHS:
            clay = data[f"clay_{depth}"][r, c] / 10
            sand = data[f"sand_{depth}"][r, c] / 10
            ph = data[f"ph_{depth}"][r, c] / 10
            out.append(meta + [depth, "clay_pct", round(float(clay), 1)])
            out.append(meta + [depth, "sand_pct", round(float(sand), 1)])
            out.append(meta + [depth, "silt_pct", round(float(100 - clay - sand), 1)])
            out.append(meta + [depth, "ph", round(float(ph), 1)])
        out.append(meta + ["0-30", "soc_stock_t_ha", float(data["soc_0-30"][r, c])])

    path = ROOT / "data/processed/soil.csv"
    with open(path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["point", "sample_lat", "sample_lon", "dist_from_point_km",
                    "depth_cm", "property", "value"])
        w.writerows(out)
    print("wrote", path, len(out), "rows")


if __name__ == "__main__":
    main()
