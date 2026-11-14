"""ERA5 monthly means (rain, 2 m temperature) at each point, 1981-2025.

Independent cross-check for NASA POWER trends. Needs ~/.cdsapirc and an accepted
ERA5 licence. One small CDS request covers all three points; values are
bilinearly interpolated from the 0.25 deg grid to each point.

Raw -> data/raw/era5_monthly.nc (gitignored)
Out -> data/processed/era5_monthly.csv  (point, date, rain_mm_month, t2m_c)
"""
import calendar
import csv
import os
from pathlib import Path

import cdsapi
import xarray as xr

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data/raw/era5_monthly.nc"


def to_rows(nc_path, pts):
    """Interpolate an ERA5 monthly-means netCDF to each point.
    Returns [point, date, rain_mm_month, t2m_c]. tp in monthly means is the mean
    daily total in metres, so mm/month = tp * 1000 * days_in_month."""
    ds = xr.open_dataset(nc_path)
    tname = "valid_time" if "valid_time" in ds.coords else "time"
    rows = []
    for p in pts:
        s = ds.interp(latitude=float(p["lat"]), longitude=float(p["lon"]), method="linear")
        for t in s[tname].values:
            d = s.sel({tname: t})
            ts = str(t)[:10]
            y, m = int(ts[:4]), int(ts[5:7])
            rain = float(d["tp"]) * 1000 * calendar.monthrange(y, m)[1]
            rows.append([p["name"], ts, round(rain, 1), round(float(d["t2m"]) - 273.15, 2)])
    return rows


def main():
    pts = list(csv.DictReader(open(ROOT / "data/points.csv")))
    lats = [float(p["lat"]) for p in pts]
    lons = [float(p["lon"]) for p in pts]
    area = [max(lats) + 0.3, min(lons) - 0.3, min(lats) - 0.3, max(lons) + 0.3]  # N, W, S, E
    RAW.parent.mkdir(parents=True, exist_ok=True)
    existing = os.environ.get("ERA5_REQUEST_ID")  # reuse a queued CDS request instead of resubmitting
    if existing and not RAW.exists():
        remote = cdsapi.Client().client.get_remote(existing)
        remote.download(str(RAW))
    if not RAW.exists():
        cdsapi.Client().retrieve(
            "reanalysis-era5-single-levels-monthly-means",
            {
                "product_type": "monthly_averaged_reanalysis",
                "variable": ["total_precipitation", "2m_temperature"],
                "year": [str(y) for y in range(1981, 2026)],
                "month": [f"{m:02d}" for m in range(1, 13)],
                "time": "00:00",
                "area": area,
                "data_format": "netcdf",
                "download_format": "unarchived",
            },
            str(RAW),
        )
    rows = to_rows(RAW, pts)
    out = ROOT / "data/processed/era5_monthly.csv"
    with open(out, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["point", "date", "rain_mm_month", "t2m_c"])
        w.writerows(rows)
    print("wrote", out, len(rows), "rows")


if __name__ == "__main__":
    main()
