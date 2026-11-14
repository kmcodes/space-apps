"""ERA5 daily rain and temperature via Open-Meteo's archive API (backup for the slow Copernicus CDS queue).

Open-Meteo serves ERA5 reanalysis (ECMWF/Copernicus, 0.25 deg) through its own API: no account, no queue.
Privacy: coordinates are rounded to 0.01 deg (~1 km) before being sent to the third-party service;
ERA5's grid is ~25-30 km so nothing is lost.
Attribution: weather data by Open-Meteo.com (CC BY 4.0), based on ERA5 (Copernicus Climate Change Service / ECMWF).

Out: data/processed/era5_daily_openmeteo.csv  (point, date, rain_mm, t2m_mean_c, t2m_max_c, t2m_min_c)
"""
import csv
import json
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
URL = "https://archive-api.open-meteo.com/v1/archive"


CHUNKS = [("1981-01-01", "1990-12-31"), ("1991-01-01", "2000-12-31"), ("2001-01-01", "2010-12-31"),
          ("2011-01-01", "2020-12-31"), ("2021-01-01", "2025-12-31")]


def fetch(lat, lon, start, end):
    q = urllib.parse.urlencode({
        "latitude": round(float(lat), 2), "longitude": round(float(lon), 2),
        "start_date": start, "end_date": end,
        "daily": "precipitation_sum,temperature_2m_mean,temperature_2m_max,temperature_2m_min",
        "models": "era5", "timezone": "Asia/Kolkata",
    })
    for attempt in range(6):
        try:
            with urllib.request.urlopen(f"{URL}?{q}", timeout=120) as r:
                return json.load(r)
        except urllib.error.HTTPError as e:
            if e.code != 429:
                raise
            print("  rate limited (429), waiting 65 s", flush=True)
            time.sleep(65)
    raise SystemExit("Open-Meteo still rate limiting; try again later")


def main():
    pts = list(csv.DictReader(open(ROOT / "data/points.csv")))
    rows = []
    for p in pts:
        for start, end in CHUNKS:
            d = fetch(p["lat"], p["lon"], start, end)
            dd = d["daily"]
            for i, t in enumerate(dd["time"]):
                rows.append([p["name"], t, dd["precipitation_sum"][i], dd["temperature_2m_mean"][i],
                             dd["temperature_2m_max"][i], dd["temperature_2m_min"][i]])
            print(p["name"], start[:4], "-", end[:4], "grid", d.get("latitude"), d.get("longitude"), flush=True)
            time.sleep(15)
    out = ROOT / "data/processed/era5_daily_openmeteo.csv"
    with open(out, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["point", "date", "rain_mm", "t2m_mean_c", "t2m_max_c", "t2m_min_c"])
        w.writerows(rows)
    print("wrote", out, len(rows), "rows")


if __name__ == "__main__":
    main()
