"""Pull mandi prices (Agmarknet via data.gov.in) for the districts in data/points.csv.

NON-NASA data - list it in the submission. Source: Ministry of Agriculture and Farmers
Welfare, data.gov.in. Prices are Rs per quintal. Needs DATA_GOV_IN_KEY in .env (gitignored).
The key travels in the URL, so URLs are never printed.

Two modes:

  python pipeline/fetch_mandi.py
      Latest reported day, all commodities
      ("Current Daily Price of Various Commodities from Various Markets (Mandi)").
      Raw JSON  -> data/raw/mandi_maharashtra_<YYYY-MM-DD>.json
      Clean CSV -> data/processed/mandi_prices.csv (appended, de-duplicated)

  python pipeline/fetch_mandi.py history [years]        (default 3)
      Daily prices for the 5 strategy crops over the last N years
      ("Variety-wise Daily Market Prices Data of Commodity").
      Raw JSON  -> data/raw/mandi_history.json
      Clean CSV -> data/processed/mandi_history.csv   (one row per market/variety/grade/day)
                   data/processed/mandi_monthly.csv   (median modal price per point/crop/month)
      Where a point/crop has no rows, the engine falls back to data/msp.csv.
"""
import csv
import json
import statistics
import sys
import time
import urllib.parse
import urllib.request
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
API = "https://api.data.gov.in/resource/"
CURRENT = "9ef84268-d588-465a-a308-a864a43d0070"
HISTORY = "35985678-0d79-46b4-9ed6-6f13308a1d24"
STATE = "Maharashtra"
PAGE = 1000
FIELDS = ["arrival_date", "district", "market", "commodity", "variety", "grade",
          "min_price", "max_price", "modal_price"]
# data.gov.in spellings differ from ours and between the two datasets, so list every variant seen.
ALIASES = {"akola": ["akola"], "buldhana": ["buldhana", "buldana"], "washim": ["washim", "vashim"]}
HIST_DISTRICTS = {"akola": ["Akola"], "buldhana": ["Buldhana"], "washim": ["Washim", "Vashim"]}
CROPS = {
    "soybean": ["Soyabean"],
    "cotton": ["Cotton"],
    "chickpea": ["Bengal Gram(Gram)(Whole)"],
    "pigeon_pea": ["Arhar (Tur/Red Gram)(Whole)", "Red gram/Arhar/Tur(whole)"],
    "sorghum": ["Jowar(Sorghum)"],
}


def read_key():
    for line in (ROOT / ".env").read_text().splitlines():
        if line.startswith("DATA_GOV_IN_KEY="):
            return line.split("=", 1)[1].strip()
    raise SystemExit("DATA_GOV_IN_KEY missing from .env")


def get_page(key, resource, params, offset):
    q = {"api-key": key, "format": "json", "limit": PAGE, "offset": offset}
    q.update(params)
    req = urllib.request.Request(f"{API}{resource}?{urllib.parse.urlencode(q)}",
                                 headers={"User-Agent": "curl/8"})
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


def points():
    with open(ROOT / "data/points.csv") as f:
        return [p["name"] for p in csv.DictReader(f)]


def latest(key):
    wanted = {a: n for n in points() for a in ALIASES.get(n, [n])}
    records, offset = [], 0
    while True:
        page = get_page(key, CURRENT, {"filters[state.keyword]": STATE}, offset)
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
    print(f"{day}: kept {kept} rows for {sorted(set(wanted.values()))}; {len(rows)} rows now in {out.name}")


def history(key, years):
    today = date.today()
    cutoff = today.replace(year=today.year - years).isoformat()
    raw, rows = [], {}
    for point in points():
        for crop, commodities in CROPS.items():
            n = 0
            for district in HIST_DISTRICTS.get(point, [point.title()]):
                for commodity in commodities:
                    params = {"filters[State]": STATE, "filters[District]": district,
                              "filters[Commodity]": commodity, "sort[Arrival_Date]": "desc"}
                    offset = 0
                    while True:          # newest first; stop at the first page that is all too old
                        page = get_page(key, HISTORY, params, offset)
                        recent = [r for r in page["records"] if iso(r["Arrival_Date"]) >= cutoff]
                        raw += recent
                        for r in recent:
                            row = {"point": point, "crop": crop, "arrival_date": iso(r["Arrival_Date"]),
                                   "district": r["District"].strip(), "market": r["Market"].strip(),
                                   "commodity": r["Commodity"].strip(), "variety": r["Variety"].strip(),
                                   "grade": r["Grade"].strip(), "min_price": r["Min_Price"],
                                   "max_price": r["Max_Price"], "modal_price": r["Modal_Price"]}
                            rows[(point, crop, row["arrival_date"], row["market"],
                                  row["variety"], row["grade"])] = row
                        n += len(recent)
                        offset += PAGE
                        if not recent or offset >= int(page["total"]):
                            break
            print(f"{point:9s} {crop:11s} {n:6d} rows since {cutoff}", flush=True)

    (ROOT / "data/raw").mkdir(parents=True, exist_ok=True)
    (ROOT / "data/raw/mandi_history.json").write_text(json.dumps(raw))
    cols = ["point", "crop"] + FIELDS
    with open(ROOT / "data/processed/mandi_history.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        for k in sorted(rows):
            w.writerow(rows[k])

    monthly = {}
    for r in rows.values():
        try:
            price = float(r["modal_price"])
        except (TypeError, ValueError):
            continue
        if price > 0:
            monthly.setdefault((r["point"], r["crop"], r["arrival_date"][:7]), []).append(price)
    with open(ROOT / "data/processed/mandi_monthly.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["point", "crop", "month", "n_prices", "median_modal_price", "min_modal_price", "max_modal_price"])
        for (point, crop, month), v in sorted(monthly.items()):
            w.writerow([point, crop, month, len(v), round(statistics.median(v)), round(min(v)), round(max(v))])
    print(f"{len(rows)} daily rows -> mandi_history.csv; {len(monthly)} point/crop/months -> mandi_monthly.csv")


def main():
    key = read_key()
    if len(sys.argv) > 1 and sys.argv[1] == "history":
        history(key, int(sys.argv[2]) if len(sys.argv) > 2 else 3)
    else:
        latest(key)


if __name__ == "__main__":
    main()
