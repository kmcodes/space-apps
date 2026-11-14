# How we start

Hackathon: Sat 14 Nov 09:00 → Sun 15 Nov 23:59 local (submission deadline).
Rule: product code (engine, API, dashboard, voice) is written inside this window only. Pre-event work was data exploration and notes.

## Scope in one paragraph

Region Vidarbha (Akola, Buldhana, Washim). Compare 4 rotations per location. Each gets: why suggested, evidence, benefits, information gaps, risks needing local review. Show bare-field windows and crop-vulnerable seasons. Farmer inputs: crop, water source, one priority. Every evidence line cites dataset + period + a validity flag (valid / degraded / unverified). Hindi voice front-end with a pre-recorded fallback.

## Strategies (hypotheses, not prescriptions)

| # | Strategy |
|---|---|
| 0 | Existing: soybean → fallow (or continuous cotton) |
| 1 | Soybean → chickpea (rabi) |
| 2 | Cotton + pigeon pea intercrop |
| 3 | Soybean → sorghum / cover crop |

Drop or swap any strategy we cannot back with a citation (FAO-56, ICAR, ICRISAT).

## Data

| Tier | Source | Role |
|---|---|---|
| Core | NASA POWER (REST, no login) | temp, rain, soil wetness, heat stress, dry spells, monsoon onset |
| Core | MODIS NDVI MOD13Q1 via AppEEARS | bare windows, stress dips |
| Supporting | SoilGrids, crop profile sheet, mandi prices | soil, crop traits, market score |
| Stretch | SMAP SPL3SMP_E | post-monsoon residual moisture |

Skip: ECOSTRESS, Landsat, GEDI, SRTM, GRACE (optional district context only). Verify all parameter names and dataset IDs against live docs.

## First 2 hours (Sat 09:00–11:00)

1. **09:00 Sync (15 min).** Confirm team size, roles, stand-up every 4 h. Read the submission checklist once together. Agree the cut list: farmer confirm/correct, scenario slider, US demo point go first.
2. **09:15 Data check.** Confirm what landed in `data/raw/` (POWER x3, MODIS CSV, SoilGrids x3, crop sheet, mandi table). List gaps. Re-request anything missing now.
3. **09:30 Scaffold.** Create `pipeline/ engine/ api/ web/ voice/`, pick FastAPI + Next.js (default; change only with reason), set env var template (no secrets committed).
4. **09:45 Pipeline.** Load raw data into one weekly/crop-stage table per location. Derive: monsoon onset/withdrawal, heat-stress days, dry-spell counts, post-monsoon moisture curve, NDVI bare windows.
5. **10:30 Engine v0.** Crop profiles × location features × priorities → per-strategy score with component breakdown. Weights visible in output.
6. **11:00 Checkpoint.** `POST /compare` returns 4 scored strategies for one location with evidence lines. If not, cut scope now.

## Build order

Engine → API → dashboard → voice. Voice stays scripted if the Hindi test failed.

## Day plan

| When | Goal |
|---|---|
| Sat 09:00–13:00 | Pipeline + engine + API for 1 location |
| Sat 13:00–19:00 | Dashboard: timeline, 4-way comparison, evidence cards, explainers, disclaimer banner. Extend to 3 locations |
| Sat 19:00–23:00 | LLM evidence-card narration with number check; validity flags |
| Sun 08:00–14:00 | Voice flow + recorded fallback; scenario slider if on track |
| Sun 14:00–20:00 | Polish, deploy, README, data-sources list |
| Sun 20:00–23:00 | Demo video (2 min), project page, submit. Buffer until 23:59 |

## Rules for the build

- LLM narrates only from engine output. Every number it quotes is checked against the engine output. No invented numbers or dataset claims.
- No strategy shown without its gaps and review-needed risks.
- "Supports, does not replace, local expertise" banner always visible.
- No field-level precision claims. Data is point/regional.
- AI-written modules get a second human reviewer before they count as done.
- Demo must work offline from recorded fallback.

## Brief → feature checklist

- [ ] ≥3 strategies incl. existing rotation compared
- [ ] Per strategy: why · evidence · benefits · gaps · risks
- [ ] Bare-field windows shown
- [ ] Vulnerable seasons shown
- [ ] Farmer priorities + constraints as inputs
- [ ] Explainers: evapotranspiration, soil-moisture anomaly, NDVI, frost risk, water balance
- [ ] Satellite vs ground explained
- [ ] Uncertainty and where local validation is needed
- [ ] Optional: map, timeline, overlays, scenario slider

## Submission checklist (confirm against the official guide)

- [ ] Project page on team's Space Apps page
- [ ] Demo video
- [ ] Repo / live link
- [ ] List of NASA data used + non-NASA data (SoilGrids, Agmarknet)
- [ ] Feature-to-brief mapping (checklist above)
- [ ] Submit before Sun 15 Nov 23:59 local

## Open items

1. Team size and roles
2. Earthdata login / AppEEARS status
3. Bolna Hindi voice on the account
4. Agronomist/KVK contact for sanity check
5. Local event rules on pre-written code
6. Scenario slider in scope?
