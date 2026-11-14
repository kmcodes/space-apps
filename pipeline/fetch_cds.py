"""Pull ERA5-Land monthly means from the Copernicus CDS for each point in data/points.csv.

Needs a CDS account + token in ~/.cdsapirc (NOT in the repo), and the dataset licence
accepted on its CDS page. Verify dataset id / variable names against the live CDS docs.

Raw NetCDF -> data/raw/cds_era5land_monthly_<name>.nc (gitignored)

Usage:  .venv\\Scripts\\python pipeline\\fetch_cds.py [name ...]   (default: all points)
"""
import csv
import sys
from pathlib import Path

import cdsapi

ROOT = Path(__file__).resolve().parent.parent
DATASET = "reanalysis-era5-land-monthly-means"
VARIABLES = [
    "volumetric_soil_water_layer_1",   # 0-7 cm soil moisture
    "volumetric_soil_water_layer_2",   # 7-28 cm soil moisture
    "total_precipitation",
    "total_evaporation",               # evapotranspiration (water-balance explainer)
    "2m_temperature",
]
YEARS = [str(y) for y in range(1981, 2026)]   # same baseline as POWER (1981+)
HALF_BOX = 0.1                                 # degrees around the point (~ one 9 km grid cell)


def main():
    wanted = set(sys.argv[1:])
    with open(ROOT / "data/points.csv") as f:
        points = [p for p in csv.DictReader(f) if not wanted or p["name"] in wanted]
    (ROOT / "data/raw").mkdir(parents=True, exist_ok=True)
    client = cdsapi.Client()
    for p in points:
        out = ROOT / f"data/raw/cds_era5land_monthly_{p['name']}.nc"
        if out.exists():
            print(f"skip {p['name']} (already downloaded)")
            continue
        lat, lon = float(p["lat"]), float(p["lon"])
        print(f"requesting {p['name']} ... (queued on CDS, may take a while)", flush=True)
        client.retrieve(DATASET, {
            "product_type": "monthly_averaged_reanalysis",
            "variable": VARIABLES,
            "year": YEARS,
            "month": [f"{m:02d}" for m in range(1, 13)],
            "time": "00:00",
            "area": [lat + HALF_BOX, lon - HALF_BOX, lat - HALF_BOX, lon + HALF_BOX],  # N, W, S, E
            "data_format": "netcdf",
            "download_format": "unarchived",
        }, str(out))
        print(f"saved {out.name}")


if __name__ == "__main__":
    main()
