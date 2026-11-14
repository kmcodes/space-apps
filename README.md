# Space Apps

Workspace for NASA Space Apps Challenge 2026 (14–15 Nov).

## Field Shift: Adapting Farms with NASA Data

Decision-support tool that helps a rainfed farmer in Vidarbha, Maharashtra explore crop-rotation strategies that protect soil and water under changing weather. It compares 4 strategies (existing rotation + 3 alternatives) with cited NASA evidence, and always shows information gaps and risks needing local review. It supports, never replaces, farmer and agronomist judgment.

- Challenge: https://www.spaceappschallenge.org/2026/challenges/adapting-farms-with-nasa-data/
- Start plan: [START.md](START.md)

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
