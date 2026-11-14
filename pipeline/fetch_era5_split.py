"""ERA5 monthly means in small per-decade CDS requests (fallback for a slow queue).

Same data as fetch_era5.py (rain, 2 m temperature, 1981-2025, interpolated to the
points in data/points.csv) but split into 5 small requests that can be run in
parallel and shared across machines/accounts.

  python pipeline/fetch_era5_split.py --dry-run            # show the 5 requests
  python pipeline/fetch_era5_split.py                      # submit and fetch all parts
  python pipeline/fetch_era5_split.py --parts 4 5          # only parts 4 and 5
  python pipeline/fetch_era5_split.py --merge              # build era5_monthly.csv

Each finished part is written to data/processed/era5_parts/era5_<start>_<end>.csv
(tiny, safe to commit) so two people can each fetch some parts and share by git.
Needs ~/.cdsapirc for the account running it, and the ERA5 licence accepted.
"""
import argparse
import csv
import sys
import time
from pathlib import Path

import cdsapi

sys.path.insert(0, str(Path(__file__).resolve().parent))
from fetch_era5 import to_rows  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = ROOT / "data/raw/era5_parts"
OUT_DIR = ROOT / "data/processed/era5_parts"
PARTS = [(1981, 1990), (1991, 2000), (2001, 2010), (2011, 2020), (2021, 2025)]
DATASET = "reanalysis-era5-single-levels-monthly-means"


def points():
    return list(csv.DictReader(open(ROOT / "data/points.csv")))


def request(y0, y1, pts):
    lats = [float(p["lat"]) for p in pts]
    lons = [float(p["lon"]) for p in pts]
    return {
        "product_type": "monthly_averaged_reanalysis",
        "variable": ["total_precipitation", "2m_temperature"],
        "year": [str(y) for y in range(y0, y1 + 1)],
        "month": [f"{m:02d}" for m in range(1, 13)],
        "time": "00:00",
        "area": [max(lats) + 0.3, min(lons) - 0.3, min(lats) - 0.3, max(lons) + 0.3],
        "data_format": "netcdf",
        "download_format": "unarchived",
    }


def merge():
    rows = []
    for y0, y1 in PARTS:
        f = OUT_DIR / f"era5_{y0}_{y1}.csv"
        if not f.exists():
            sys.exit(f"missing part {f.name}; fetch it first")
        rows += list(csv.reader(open(f)))[1:]
    rows.sort(key=lambda r: (r[0], r[1]))
    out = ROOT / "data/processed/era5_monthly.csv"
    with open(out, "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["point", "date", "rain_mm_month", "t2m_c"])
        w.writerows(rows)
    print("merged", len(rows), "rows ->", out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--parts", type=int, nargs="*", help="part numbers 1-5 (default all)")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--merge", action="store_true")
    a = ap.parse_args()
    if a.merge:
        return merge()
    pts = points()
    chosen = [(i, PARTS[i - 1]) for i in (a.parts or range(1, len(PARTS) + 1))]
    if a.dry_run:
        for i, (y0, y1) in chosen:
            print(i, y0, y1, request(y0, y1, pts)["area"])
        return
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    client = cdsapi.Client().client
    pending = {}
    for i, (y0, y1) in chosen:  # submit all first so they queue in parallel
        out_csv = OUT_DIR / f"era5_{y0}_{y1}.csv"
        if out_csv.exists():
            print(f"part {i} {y0}-{y1}: already done")
            continue
        remote = client.submit(DATASET, request(y0, y1, pts))
        print(f"part {i} {y0}-{y1}: submitted {remote.request_id}", flush=True)
        pending[i] = (y0, y1, remote)
    while pending:
        for i, (y0, y1, remote) in list(pending.items()):
            remote.update()
            st = remote.status
            if st == "successful":
                nc = RAW_DIR / f"era5_{y0}_{y1}.nc"
                remote.download(str(nc))
                with open(OUT_DIR / f"era5_{y0}_{y1}.csv", "w", newline="") as fh:
                    w = csv.writer(fh)
                    w.writerow(["point", "date", "rain_mm_month", "t2m_c"])
                    w.writerows(to_rows(nc, pts))
                print(f"part {i} {y0}-{y1}: done", flush=True)
                del pending[i]
            elif st == "failed":
                print(f"part {i} {y0}-{y1}: FAILED", flush=True)
                del pending[i]
        if pending:
            print("waiting:", {i: v[2].status for i, v in pending.items()}, flush=True)
            time.sleep(60)
    print("all parts finished. Merge with: --merge (needs all 5 part CSVs)")


if __name__ == "__main__":
    main()
