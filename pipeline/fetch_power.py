"""Pull NASA POWER daily point data for each point in data/points.csv.

Raw JSON -> data/raw/power_<name>.json (gitignored)
Clean CSV -> data/processed/power_<name>.csv (-999 -> blank)
"""
import csv
import json
import time
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PARAMS = "T2M,T2M_MAX,T2M_MIN,PRECTOTCORR,RH2M,GWETTOP,GWETROOT,ALLSKY_SFC_SW_DWN"
START, END = "19810101", "20251231"
URL = "https://power.larc.nasa.gov/api/temporal/daily/point"


def fetch(lat, lon):
    q = urllib.parse.urlencode({
        "parameters": PARAMS, "community": "AG", "latitude": lat,
        "longitude": lon, "start": START, "end": END, "format": "JSON",
    })
    with urllib.request.urlopen(f"{URL}?{q}", timeout=300) as r:
        return json.load(r)


def main():
    (ROOT / "data/raw").mkdir(parents=True, exist_ok=True)
    (ROOT / "data/processed").mkdir(parents=True, exist_ok=True)
    with open(ROOT / "data/points.csv") as f:
        points = list(csv.DictReader(f))
    for p in points:
        name = p["name"]
        print(f"fetching {name} ...", flush=True)
        data = fetch(p["lat"], p["lon"])
        (ROOT / f"data/raw/power_{name}.json").write_text(json.dumps(data))
        series = data["properties"]["parameter"]
        names = list(series)
        dates = sorted(next(iter(series.values())))
        with open(ROOT / f"data/processed/power_{name}.csv", "w", newline="") as f:
            w = csv.writer(f)
            w.writerow(["date"] + names)
            for d in dates:
                row = []
                for n in names:
                    v = series[n].get(d)
                    row.append("" if v is None or v == -999 else v)
                w.writerow([f"{d[:4]}-{d[4:6]}-{d[6:]}"] + row)
        time.sleep(2)


if __name__ == "__main__":
    main()
