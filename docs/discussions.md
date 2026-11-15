# Discussions

Open points for Kartik and Amrita to settle. Add new topics at the bottom with a date.

## Review of `docs/ENGINE_DESIGN.md` (Amrita, 14 Nov 2026, 17:15)

Checked against the data files in the repo. The design follows every rule in `START.md`. Seven issues, all still open as of commit `092d4a7`.

| # | Issue | Why it matters | Suggested fix |
|---|---|---|---|
| 1 | **Blank values are not handled.** The design covers `unverified` inputs but says nothing about missing ones. | Pigeon pea and sunn hemp have no water-need figure, so `water_fit` cannot be computed for them. Soybean and horse gram have no nitrogen number, so they would score zero even though both are legumes. | A missing input gives no score for that component. Its weight is shared among the others, and the gap is listed on the card. Blank must never mean zero. |
| 2 | **Nitrogen uses the midpoint of the range.** | Pigeon pea's range is 4-200 kg/ha, so its midpoint (102) beats chickpea's (60) only because the range is wider. | Use the low/medium/high `n_fixation` rating, which every legume in `crops.csv` has. |
| 3 | **Sensitive stages are text in the crop sheet.** | `heat_risk` and `dry_spell_risk` need day numbers, such as "days 40 to 70 after sowing". The sheet only says "flowering and pod fill". | Amrita adds start-day and end-day columns to `data/crops.csv`. |
| 4 | **How crops combine into one strategy score is not defined.** | S1 has two crops in sequence. S2 has two at the same time. S3 offers sorghum, sunn hemp or horse gram, and it is unclear whether that is one strategy or three. | Average across the year for sequences. Show S3 with one default crop and the other two as variants. **Needs a decision.** |
| 5 | **The priority boost is uneven.** | With `forage` as first priority, forage only rises from 4% to about 9% of the score. With `water_saving`, the water components reach about 52%. Picking forage would barely change the ranking, so the design's own test (changing priority changes the ranking) could fail. | Give the first priority a fixed share of the total, such as 40%, in place of the 2.5x multiplier. |
| 6 | **Confidence will be grey for every strategy.** | Seven of the twelve components rest only on unverified crop values. Every strategy would show low confidence, so the indicator tells the farmer nothing. | Verify the few crop fields that carry the most weight: heat thresholds, stage timing, chickpea water need. Amrita's sheet. |
| 7 | **The market score compares price with MSP.** | Price per quintal is not income without yield, and cotton and soybean yield very different amounts per hectare. Washim cotton, which falls back to MSP because it has no price data, would also look perfectly stable. | Call it a "price signal" and say so on the card, or add typical district yields. Flag every MSP fallback. |

### Smaller points

- **Duplicate strategies.** If the farmer already grows soybean then chickpea, S0 and S1 are identical. The design only covers the cotton case.
- **Sowing date per year.** The design does not say which date inside the sowing window the engine uses each year. Suggestion: the monsoon onset if it falls inside the window, otherwise the window's end with a flag.

### Location: GPS coordinates versus our data

Location is now any lat/lon (section 2b), but all our data is precomputed for three fixed points: POWER, features, soil, NDVI and mandi prices. Soil came from manually downloaded tiles and NDVI from the AppEEARS queue, so neither can be fetched live for a new point. Mandi prices are keyed by district. The design does not say what the engine does with a point that is not one of the three.

Suggestion: snap any location to the nearest of our three points, say so on the card, and treat GPS as a way to choose the preset.

`START.md` still lists location as a choice of three districts, so it now disagrees with the design.

### Heat risk after the ERA5 cross-check

Heat-day counts differ by up to five times between POWER and ERA5. `heat_risk` would then rest on a disputed weather number and an unverified crop threshold at the same time. This makes issue 6 more pressing.

### Scope

As of 17:10 on Saturday, `engine/`, `api/`, `web/` and `voice/` are empty. Proposed first version:

- Three preset locations only. GPS and the map pin come later.
- Five components: `water_fit`, `timing_fit`, `bare_days`, `nitrogen`, `market`.
- English text cards from templates. No LLM and no voice yet.
- Goal: `/compare` returns four scored strategies with evidence lines for Akola tonight.

### Suggested answers to the design's questions (section 11)

1. **Weights:** fine as a start, with the boost changed as in issue 5.
2. **Cost-based margin:** skip it.
3. **Own use:** set the market weight to zero and share it out.
4. **Cotton baseline:** cotton alone, with S2 as "add pigeon pea".
5. **Irrigated farms:** show them, with the caveat that irrigation data is missing.
6. **Scenario slider:** cut for now.
7. **Language:** Hindi for the demo is fine. No Marathi reviewer identified yet.
8. **Who drives which file:** to agree.

## Review of engine v0 code (Amrita, 15 Nov 2026, 10:10)

Reviewed at commit `c31270d`. Requirements installed in a fresh `.venv`, all 134 tests pass, and `Engine.compare` returns four scored strategies for every input tried (Akola and Washim; default, forage, water saving with low water, market income, nitrogen; current rotation cotton). Run directly, not through a live server.

### Status of the seven design issues

| # | Issue | Status |
|---|---|---|
| 1 | Blank values scored as zero | Fixed. Blank is a gap, and a strategy below 70% coverage is not ranked. |
| 2 | Nitrogen from range midpoint | Fixed. Uses the rating. |
| 3 | Sensitive stages as day numbers | Not needed yet. Heat and dry-spell scoring are not in v0. |
| 4 | Combining crops into a strategy | Fixed (sequence, mixed, variants). |
| 5 | Uneven priority boost | Fixed. First priority gets a fixed 40%. Forage as priority now puts S3 first. |
| 6 | Confidence grey everywhere | **Open, and it happened.** S1, S2 and S3 show confidence 0.0 for every input tried. |
| 7 | Market score as income | Fixed. Renamed price signal; MSP-only is a gap. |

### New problems

**1. Leaving the field empty can beat growing a second crop (serious).**
In a sequence, nitrogen, forage and market are averaged over the days a crop is in the ground (`score.py`, `_combine(..., "mean", days)`), so fallow days are ignored.

| Akola, default inputs | nitrogen | forage | market |
|---|---|---|---|
| S0 soybean then fallow | 60.0 | 25.0 | 38.9 |
| S1 soybean then chickpea | 60.0 | 25.0 | 32.0 |

Adding chickpea gives no nitrogen benefit and lowers the price signal. With `market_income` as the priority the ranking is S0, S1, S3, S2: the existing soybean-then-fallow rotation comes first. Suggested fix: average benefits over the whole year (divide by 365), so empty days count as zero. Needs a decision.

**2. Variants skip the coverage rule.**
`score_variants` returns a total with no coverage check, and the response carries only `total_score`.

| S3 variant (Akola, default) | total | coverage | missing |
|---|---|---|---|
| sorghum_rabi (default) | 62.5 | 1.00 | none |
| sunn_hemp | 54.4 | 0.25 | water_fit, timing_fit, market, bare_days |
| horse_gram | 77.7 | 0.80 | market |

Horse gram shows the highest number in the whole response while it has no price data, and its duration in `crops.csv` is probably too short (see `docs/crop_gap_research.md` section 3). Suggested fix: apply `MIN_COVERAGE` to variants and return `data_coverage` and `incomplete` for each.

**3. `water_source` is accepted by the API but never used by the engine.** A farmer with a well gets the same result as a rainfed one.

**4. Water and timing barely separate the strategies.** In the median year almost every strategy scores 98-100 on `water_fit` and `timing_fit`. Only cotton alone differs (water 74.9). Most of the ranking comes from bare days, the price signal and the unverified ratings.

**5. Cards.**
- Dates appear as "day 166 of the year"; a farmer needs "15 June".
- The gaps list repeats "relies on unverified inputs or a proxy" once per component, with no detail on which input.
- Risks are one generic sentence. The S1 card does not say it needs a short-duration soybean, which `docs/crop_sheet.md` flags as the main risk.

**6. Small.** README says 129 tests; there are 134. In Washim, S2 is ranked on 73% coverage with both water and market missing, just above the 70% line.

### Market inputs behind those scores (Akola, last 12 months)

| Crop | Median price (Rs/q) | MSP (Rs/q) | Ratio | Score |
|---|---|---|---|---|
| soybean | 6,120 | 5,708 | 1.07 | 38.9 |
| chickpea | 5,692 | 5,875 | 0.97 | 25.1 |
| cotton | 8,010 | 8,267 | 0.97 | 25.6 |
| pigeon pea | 7,514 | 8,450 | 0.89 | 12.6 |
| sorghum | 2,428 | 4,023 | 0.60 | 0.0 |

### Crop sheet follow-up (Amrita)

`docs/crop_gap_research.md` gives verified values that conflict with `data/crops.csv`: chickpea heat threshold 35 C (sheet 32), horse gram duration 120-180 days (sheet 85-110), sunn hemp nitrogen 50-60 kg/ha (sheet 150-165). To be merged into the sheet, which also starts on issue 6. Not done yet.

## Deployment: decisions needed (Amrita, 15 Nov 2026, 10:35)

The web app in `web/` runs locally against the API (see `web/README.md`). Nothing is deployed. Two decisions for Kartik:

1. **Whose Vercel account hosts the web app?** Kartik owns the GitHub repo, so importing it from his account gives a redeploy on every push. The alternative is Amrita deploying from her PC with the Vercel command-line tool.
2. **Where does the engine API run?** The docs name Vercel for the PWA but no host for the Python API. It needs a public HTTPS address before the deployed web app can work. One option is Render's free tier, which runs FastAPI from the repo but sleeps when idle, so the first request after a pause can take up to a minute.

Things to settle with the API host:

- `requirements.txt` includes `earthaccess` and `pytest`, which the API does not need at run time. A slimmer requirements file for the host would install faster.
- `ALLOWED_ORIGINS` should be set to the web app's address. The default is open.
- The usage log and `/admin/stats` need their token set on the host.

Also from the web build: `water_source` is collected on the form and sent, but the engine ignores it (engine review, problem 3).

## Month timeline under every year bar (Amrita, 15 Nov 2026, evening)

Amrita asked for an x-axis timeline on the results. Added in `web/app/results.tsx` (`MonthAxis`, Kartik's file, changed by Amrita for his review) and `MONTH_HI_SHORT` in `web/app/results-script.ts`: a tick per month (thicker at the start of kharif, rabi and summer) and all twelve short Hindi month names, June first, coloured by season. The same timeline sits under the full bar on the one-choice screen and under each small bar in the choices list. The short month names are machine-drafted and need a native speaker's check.

Also noticed: `npm run lint` fails on `web/app/speech.ts` line 18 (`startTimer` should be `const`). Not changed.
