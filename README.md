# Field Shift

Built for the NASA Space Apps Challenge 2026 (14–15 Nov), challenge [Adapting Farms with NASA Data](https://www.spaceappschallenge.org/2026/challenges/adapting-farms-with-nasa-data/).

A decision-support tool for a rainfed farmer in Vidarbha, Maharashtra (Akola, Buldhana, Washim). The farmer answers a few questions and the tool compares four ways of using the field through the year, showing for each one why it was suggested, the evidence, the benefits, what is not known, and what to check with a local expert.

**It supports, and does not replace, the judgement of farmers and local agricultural experts.** Every suggestion is a hypothesis for local review. Data is point and regional (weather about 25–50 km, satellite 250 m), not field-level.

The app is built for farmers who may not read: a voice call in Hindi, picture answers, and results that are spoken and shown as pictures. Team: Kartik and Amrita (working agreement in [CLAUDE.md](CLAUDE.md)).

## What it does

1. **A voice call.** One tap starts a conversation in Hindi, or in English: a switch at the top of every screen changes the whole app (questions, spoken text, results). The app first checks the farm location: if the phone gives one, it shows a satellite map with a red pin and asks "is this your farm?"; if not (or the answer is no), it asks the district. Then it asks seven more questions aloud (current rotation, water source, one or two priorities, water available, equipment, where they sell), reads each option while its picture lights up, and listens. Every answer can also be tapped.
2. **An engine compares four rotations.** Your current one, soybean then chickpea, cotton with pigeon pea, and soybean then sorghum (or a cover crop). Each is scored by transparent rules from weather, satellite greenness, soil and market data. The farmer's priority sets the weights, and the weights are shown.
3. **Results for non-readers.** Choices are ordered best first with a thumbs-up on the top ones and no scores. Each choice has a 12-month year bar (June to May, kharif and rabi grouped; green is a crop in the ground, dark is a bare field) and three picture rows that speak when tapped: the checked advice (जाँचा हुआ सुझाव), the estimates (अनुमानित सुझाव), the sensitive months, and what to ask an expert. Every choice carries a badge, "अनुमानित सुझाव" (estimated suggestion), until all its inputs are checked; today none are, so every suggestion is labelled an estimate. Sources and validity flags sit behind a "for experts" link.

Rules we kept: no strategy is shown without its gaps and risks; every evidence line cites its dataset, period and a validity flag (valid, degraded, unverified); a missing input is never scored as zero and a data gap never flatters a strategy; where two datasets disagree we show the range and do not pick one.

## Live

- App: https://field-shift-opal.vercel.app (open on an Android phone in Chrome for voice)
- Engine API: https://space-apps-dzma.onrender.com (`/health`, `/docs`)

The API sleeps after about 15 minutes idle. Open `/health` a minute before a demo.

## Run it

You need Python 3.11 or newer (we use 3.14) and Node.js 20 or newer.

```bash
# engine API (from the repo root)
python3 -m venv .venv && .venv/bin/pip install -r requirements-dev.txt   # requirements.txt alone is enough to run the API
.venv/bin/python -m pytest                                   # 146 tests
.venv/bin/uvicorn api.main:app --port 8000                   # docs at http://127.0.0.1:8000/docs

# web app (second terminal)
cd web && npm install && npm run dev                         # http://localhost:3000
```

On Windows use `.venv\Scripts\python` in place of `.venv/bin/python`. Details for the web app: [web/README.md](web/README.md).

Try the API without the app:

```bash
curl -s localhost:8000/compare -H 'content-type: application/json' \
  -d '{"location":"akola","priorities":["water_saving"],"constraints":{"water_availability":"low"}}'
```

### Settings

| Variable | Where | What it does |
|---|---|---|
| `NEXT_PUBLIC_API_URL` | web | Address of the engine API. Default `http://127.0.0.1:8000`. Read at build time. |
| `ALLOWED_ORIGINS` | API | Comma-separated web addresses allowed to call the API. Default is open, fine for a demo only. |
| `ADMIN_TOKEN` | API | Turns on `GET /admin/stats` (send it as the `x-admin-token` header). Unset means the route is off. |
| `USAGE_LOG` | API | Where the anonymous usage log goes. Default `data/usage.jsonl`. |

The usage log has one line per `/compare` call: time, district, rotation, water source, priorities, whether it was served, and latency. It stores no coordinates and no identity.

To try the app on a phone on the same Wi-Fi, run the API with `--host 0.0.0.0`, start the web app with `NEXT_PUBLIC_API_URL` set to your computer's address, and open that address on the phone. The microphone and the phone's location only work on HTTPS (or localhost), so voice answers need a deployed or tunnelled build. Tapping works on plain HTTP.

## Data used

**NASA data**

| Data | Used for |
|---|---|
| NASA POWER, daily 1981–2025 (temperature, rain, soil wetness, humidity, solar radiation) | Rain and water fit, monsoon onset and withdrawal, dry spells, heat days |
| MODIS MOD13Q1.061 NDVI (250 m, 16-day, 2015–2025) via NASA AppEEARS | Bare-field windows and crop seasons seen from space |

NASA SMAP soil moisture was searched in the catalogue but is not used.

**Non-NASA data**

| Data | Used for |
|---|---|
| ISRIC SoilGrids (clay, sand, pH, soil carbon) | Soil context |
| ERA5 reanalysis (Copernicus/ECMWF) through Open-Meteo, CC BY 4.0 | Independent cross-check of POWER |
| Agmarknet mandi prices via data.gov.in, and announced minimum support prices | Market score |
| Crop parameters: FAO-56, FAO Irrigation Water Management Training Manual 3, ICAR-CRIDA Akola contingency plan, ICRISAT, FAO ECOCROP | Crop sheet (`data/crops.csv`); each value is marked valid or unverified |

Every number in the crop sheet is marked **valid** (the source was opened and the number read) or **unverified**. See [docs/crop_sheet.md](docs/crop_sheet.md) and [docs/crop_gap_research.md](docs/crop_gap_research.md).

### How the vulnerable months are decided

`pipeline/season_risk.py` reads the daily POWER and ERA5 files and writes `data/processed/season_risk.json`, which the engine returns with `/compare`. The thresholds are our own and are shown to users:

- **Hot month:** on average at least 10 days a month above 38 °C (1981–2025).
- **Dry-spell month:** in at least 4 years in 10, a dry run of 10 or more days (under 2.5 mm of rain a day) inside that year's monsoon, from onset to withdrawal, overlaps the month.
- **Frost night:** a minimum temperature of 2 °C or below.
- A month is marked **solid** when both datasets reach the threshold and **dashed** when only one does. Result: April and May are hot in both, March only in POWER; August has long dry spells in both, September in one; no frost night in either dataset at any of the three points.

The "नाज़ुक समय" row says when a choice's crop is in the ground during those months. It does not know each crop's most sensitive stage in days (the crop sheet only has it as text and mostly unverified), so it does not claim to.

### What we found when we cross-checked

- POWER and ERA5 agree that rain has risen over 1981–2025 and on monsoon withdrawal and the length of dry spells.
- They disagree on temperature trend and on how many days are above 40 °C in March–May. We show a range and do not claim a trend.

## How it is built

```
data/        raw pulls (gitignored) and processed tables
pipeline/    fetch and feature derivation (Python)
engine/      transparent rule scorer; every tunable number is in engine/config.py
api/         POST /compare, GET /health, GET /admin/stats
web/         Next.js PWA: voice call, picture questions, results
voice/       reserved for the Sarvam speech integration (empty for now)
docs/        design, crop sheet, data quality, plans
tests/       146 tests, written first
```

- Engine design and the rules behind every score: [docs/ENGINE_DESIGN.md](docs/ENGINE_DESIGN.md).
- Voice app plan and who it is for: [docs/VOICE_APP_PLAN.md](docs/VOICE_APP_PLAN.md).
- Colours, type and layout: [web/DESIGN.md](web/DESIGN.md).
- Open decisions and engine review: [docs/discussions.md](docs/discussions.md).

## Status

Honest list of what works and what does not yet.

| Brief item | State |
|---|---|
| At least three strategies, including the current rotation | Done: four |
| Per strategy: why, evidence, benefits, gaps, risks | Done (spoken and shown; sources behind "for experts") |
| Bare-field windows | Done (year bar) |
| Vulnerable seasons | Done: hot and dry-spell months drawn under the year bar, a spoken "नाज़ुक समय" row per choice, and the frost finding |
| Farmer priorities and constraints as inputs | Done |
| Explainers (evapotranspiration, soil-moisture anomaly, NDVI, frost risk, water balance) | Done: the "समझिए" screen, each one spoken |
| Satellite versus ground data explained | Done: the last row of "समझिए" |
| Uncertainty and where local validation is needed | Done |
| Timeline | Done (year bar) |
| Map of the farm location | Done: phone location, satellite map with a pin, farmer confirms; district tiles if the phone gives no location |
| Scenario slider | Not built |

Not done yet:

- **The map is Google's keyless embed**, which is not an official, supported product, and the browser sends the farm's coordinates (rounded to about 100 m) to Google when it loads. Phone location needs HTTPS. Without a map, the app still works from the district tiles.
- **Speech is the browser's built-in Hindi**, not Sarvam. It works best in Chrome or Edge on Android. Sarvam speech-to-text and text-to-speech is planned and needs an account and key.
- **Deployment.** Live since 15 Nov 2026: app at https://field-shift-opal.vercel.app, engine API at https://space-apps-dzma.onrender.com (free tier: it sleeps when idle, so the first request can take about 30 seconds). They redeploy after a push only while the watcher script runs on Amrita's PC; see `web/README.md`.
- **All Hindi text is machine-drafted and has not been reviewed by a native speaker, and the English text is drafted the same way.** Marathi, the real language of the region, waits for a native reviewer.
- **Crop pictures are drawn placeholders.** Real drawings or photos are needed.
- **The engine ignores the water source** the farmer gives (see the engine review in docs/discussions.md).
- **No language model writes any text.** Evidence cards and the Hindi sentences are templates filled from engine fields, so no number is invented.

## Limits to keep in mind

Weather is area-scale, satellite pixels are 250 m and mixed, rain is reanalysis and not gauge data, the water proxy for rabi crops is rough, and all penalties in the scoring are our own assumptions, written down in `engine/config.py`. Treat the output as a conversation starter for a local expert.
