# Space Apps

Workspace for NASA Space Apps Challenge 2026 (14–15 Nov).

## Field Shift: Adapting Farms with NASA Data

Decision-support tool that helps a rainfed farmer in Vidarbha, Maharashtra explore crop-rotation strategies that protect soil and water under changing weather. It compares 4 strategies (existing rotation + 3 alternatives) with cited NASA evidence, and always shows information gaps and risks needing local review. It supports, never replaces, farmer and agronomist judgment.

- Challenge: https://www.spaceappschallenge.org/2026/challenges/adapting-farms-with-nasa-data/
- Start plan: [START.md](START.md)

## Run the engine

```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
.venv/bin/python -m pytest                              # 129 tests
.venv/bin/uvicorn api.main:app --reload                 # http://127.0.0.1:8000/docs
curl -s localhost:8000/compare -H 'content-type: application/json' \
  -d '{"location":"akola","priorities":["water_saving"],"constraints":{"water_availability":"low"}}'
```

Design: `docs/ENGINE_DESIGN.md`. Every tunable number is in `engine/config.py`.

## Layout (built during the event)

```
data/        raw pulls (gitignored) + processed tables
pipeline/    fetch + feature derivation (Python)
engine/      transparent rule scorer
api/         POST /compare
web/         dashboard
voice/       Hindi voice flow
docs/        notes, data quality, crop sheet
```

## Status

Team: Kartik + Amrita. Working agreement in [CLAUDE.md](CLAUDE.md).

Planning done. Build starts 14 Nov 09:00 local.
