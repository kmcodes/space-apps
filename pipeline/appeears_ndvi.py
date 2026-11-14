"""MODIS NDVI (MOD13Q1.061) point extraction via NASA AppEEARS.

Uses Earthdata credentials from ~/.netrc (written by earthaccess login).

  python pipeline/appeears_ndvi.py submit     # submit task, saves task id
  python pipeline/appeears_ndvi.py status     # check task
  python pipeline/appeears_ndvi.py download   # download CSVs to data/raw/appeears/
"""
import base64
import csv
import json
import netrc
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
API = "https://appeears.earthdatacloud.nasa.gov/api"
TASK_FILE = ROOT / "data/raw/appeears_task.json"
OUT = ROOT / "data/raw/appeears"
PRODUCT = "MOD13Q1.061"
LAYERS = ["_250m_16_days_NDVI", "_250m_16_days_EVI",
          "_250m_16_days_pixel_reliability", "_250m_16_days_VI_Quality"]


def call(path, method="GET", token=None, body=None, basic=None, raw=False):
    req = urllib.request.Request(API + path, method=method)
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    if basic:
        req.add_header("Authorization", "Basic " + base64.b64encode(basic.encode()).decode())
    data = None
    if body is not None:
        data = json.dumps(body).encode()
        req.add_header("Content-Type", "application/json")
    with urllib.request.urlopen(req, data=data, timeout=120) as r:
        content = r.read()
    return content if raw else json.loads(content)


def login():
    user, _, pw = netrc.netrc().authenticators("urs.earthdata.nasa.gov")
    return call("/login", "POST", basic=f"{user}:{pw}")["token"]


def submit():
    with open(ROOT / "data/points.csv") as f:
        pts = list(csv.DictReader(f))
    body = {
        "task_type": "point",
        "task_name": "fieldshift_ndvi",
        "params": {
            "dates": [{"startDate": "01-01-2015", "endDate": "12-31-2025"}],
            "layers": [{"product": PRODUCT, "layer": l} for l in LAYERS],
            "coordinates": [{"id": p["name"], "latitude": float(p["lat"]),
                             "longitude": float(p["lon"]), "category": p["name"]}
                            for p in pts],
        },
    }
    res = call("/task", "POST", token=login(), body=body)
    TASK_FILE.parent.mkdir(parents=True, exist_ok=True)
    TASK_FILE.write_text(json.dumps(res))
    print("submitted:", res)


def task_id():
    return json.loads(TASK_FILE.read_text())["task_id"]


def status():
    res = call(f"/task/{task_id()}", token=login())
    print(res.get("status"), res.get("task_id"))
    return res


def download():
    tok = login()
    res = call(f"/task/{task_id()}", token=tok)
    if res.get("status") != "done":
        sys.exit(f"not done yet: {res.get('status')}")
    OUT.mkdir(parents=True, exist_ok=True)
    for f in call(f"/bundle/{task_id()}", token=tok)["files"]:
        name = Path(f["file_name"]).name
        content = call(f"/bundle/{task_id()}/{f['file_id']}", token=tok, raw=True)
        (OUT / name).write_bytes(content)
        print("saved", name, len(content))


if __name__ == "__main__":
    {"submit": submit, "status": status, "download": download}[sys.argv[1]]()
