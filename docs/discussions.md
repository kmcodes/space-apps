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
