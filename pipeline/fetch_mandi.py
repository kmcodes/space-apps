"""Pull current daily mandi prices (Agmarknet via data.gov.in) for Maharashtra,
keep the districts in data/points.csv.

Source: "Current Daily Price of Various Commodities from Various Markets (Mandi)",
Ministry of Agriculture and Farmers Welfare, data.gov.in (NON-NASA data - list it in the submission).
The resource holds only the latest reported day, so run this daily to build a history.

Needs DATA_GOV_IN_KEY in .env (gitignored). The key travels in the URL, so URLs are never printed.

Raw JSON  -> data/raw/mandi_maharashtra_<YYYY-MM-DD>.json (gitignored)
Clean CSV -> data/processed/mandi_prices.csv (appended, de-duplicated; prices in Rs per quintal)
"""
import csv
import json
import time
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RESOURCE = "9ef84268-d588-465a-a308-a864a43d0070"
URL = f"https://api.data.gov.in/resource/{RESOURCE}"
STATE = "Maharashtra"
PAGE = 1000
FIELDS = ["arrival_date", "district", "market", "commodity", "variety", "grade",
          "min_price", "max_price", "modal_price"]
# data.gov.in spellings differ from ours (e.g. Buldana / Vashim), so match loosely.
ALIASES = {"akola": ["akola"], "buldhana": ["buldhana", "buldana"], "washim": ["washim", "vashim"]}


def read_key():
    for line in (ROOT / ".env").read_text().splitlines():
        if line.startswith("DATA_GOV_IN_KEY="):
            return line.split("=", 1)[1].strip()
    raise SystemExit("DATA_GOV_IN_KEY missing from .env")


def get_page(key, offset):
    q = urllib.parse.urlencode({"api-key": key, "format": "json", "limit": PAGE,
                                "offset": offset, "filters[state.keyword]": STATE})
    req = urllib.request.Request(f"{URL}?{q}", headers={"User-Agent": "curl/8"})
    for attempt in range(1, 6):          # the API times out often; retry
        try:
            with urllib.request.urlopen(req, timeout=120) as r:
                return json.load(r)
        except Exception as e:
            print(f"  offset {offset} attempt {attempt} failed: {type(e).__name__}", flush=True)
            time.sleep(5 * attempt)
    raise SystemExit("data.gov.in did not answer after 5 attempts")


def iso(d):                              # 13/11/2026 -> 2026-11-13
    dd, mm, yy = d.split("/")
    return f"{yy}-{mm}-{dd}"


def main():
    key = read_key()
    with open(ROOT / "data/points.csv") as f:
        wanted = {a: p["name"] for p in csv.DictReader(f) for a in ALIASES.get(p["name"], [p["name"]])}
    records, offset = [], 0
    while True:
        page = get_page(key, offset)
        records += page["records"]
        print(f"fetched {len(records)} / {page['total']} {STATE} records", flush=True)
        offset += PAGE
        if not page["records"] or offset >= int(page["total"]):
            break
    if not records:
        raise SystemExit(f"no records returned for {STATE}")

    day = iso(records[0]["arrival_date"])
    (ROOT / "data/raw").mkdir(parents=True, exist_ok=True)
    (ROOT / f"data/raw/mandi_maharashtra_{day}.json").write_text(json.dumps(records))

    out = ROOT / "data/processed/mandi_prices.csv"
    rows = {}
    if out.exists():
        with open(out, newline="") as f:
            for r in csv.DictReader(f):
                rows[tuple(r[k] for k in FIELDS[:6])] = r
    kept = 0
    for r in records:
        point = wanted.get(r["district"].strip().lower())
        if not point:
            continue
        row = {k: r[k].strip() if isinstance(r[k], str) else r[k] for k in FIELDS}
        row["arrival_date"] = iso(r["arrival_date"])
        row["point"] = point
        rows[tuple(str(row[k]) for k in FIELDS[:6])] = row
        kept += 1
    with open(out, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["point"] + FIELDS)
        w.writeheader()
        for k in sorted(rows):
            w.writerow(rows[k])
    districts = sorted({r["district"] for r in records})
    print(f"{day}: kept {kept} rows for {sorted(set(wanted.values()))}; {len(rows)} rows now in {out.name}")
    print(f"districts reporting in {STATE} that day: {len(districts)}")


if __name__ == "__main__":
    main()
