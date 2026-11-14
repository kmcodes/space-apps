# Engine design (DRAFT for Kartik + Amrita to review before any code)

Status: draft, 14 Nov 2026. Nothing here is built. All weights and thresholds are **starting values** to argue about. Anything marked **[unverified]** comes from the crop sheet's unverified fields or from our own judgement.

## 1. What the engine does

Given a farmer's location, current rotation, water source, priority and constraints, it scores **4 rotation strategies** from NASA-derived evidence plus soil, crop and price data, and returns for each: why suggested, evidence, benefits, information gaps, risks needing local review. It supports, never replaces, local judgement.

Anti-goals (a failure even if it runs): an invented number; a strategy shown without its gaps and risks; an evidence line without dataset + period + validity; a score that cannot be traced to inputs.

## 2. Inputs

**Farmer inputs** (from the dashboard or voice flow)

| Input | Values |
|---|---|
| location | lat/lon of the plot (from phone GPS or a map pin). Districts akola, buldhana, washim remain as presets that fill in our three farm points |
| current rotation | soybean_fallow (default), cotton, soybean_chickpea, ... |
| water source | rainfed, well, canal_tank |
| priority (1, optional 2nd) | water_saving, forage, nitrogen, erosion, organic_matter, market_income |
| constraints | water_availability low/medium/high; equipment basic/sprayer; market_preference mandi/buyer/own_use |

**Data** (all already in the repo)

| File | Gives |
|---|---|
| `data/processed/features_yearly.csv`, `features_summary.json` | per year: onset, withdrawal, kharif rain, dry spells, heat days, post-monsoon root wetness, cold and frost days (POWER, 1981-2025) |
| `data/processed/power_<point>.csv` | daily weather, for stage-window calculations |
| `data/processed/ndvi.csv` | MODIS NDVI, 2015-2025, bare window and winter greenness |
| `data/processed/soil.csv` | clay, sand, silt, pH, SOC stock per point |
| `data/crops.csv` | per-crop traits and validity flags (Amrita's sheet) |
| `data/processed/mandi_monthly.csv`, `data/msp.csv` | prices and MSP |

## 2b. Input flow: voice inside the mobile app, location from the phone

The voice is an interface **inside the mobile app, which is a PWA** (installable web app, no native build), not a phone call. So the app can read the phone's location in the same session.

1. Farmer opens the app and taps the mic. Mic permission is requested (tied to the tap).
2. Voice agent (Hindi in the demo, see 6b) asks what it needs: crop, water source, priority, constraints.
3. Agent says, in effect, "sir, ek baar aapke mobile pe location approve kijiye". The app requests location permission and reads GPS with the browser Geolocation API (needs HTTPS; the PWA is served from Vercel).
4. **Accuracy check.** The API returns an accuracy radius. If it is worse than about 250 m, ask the farmer to step outside or place the pin on the map.
5. **Map confirm.** Show a satellite map centred on the reading. The farmer drags or taps the pin onto their field. This also catches a wrong GPS reading and a farmer who is not at the plot.
6. The engine receives lat/lon and returns the cards; the agent speaks the top three and the key risk.

**Phone call (optional, later, not in scope now):** the same engine could be reached by a phone call using Sarvam STT/TTS, but a call has no GPS. The farmer would have to say a village or taluka name, or we send an SMS link that opens the PWA and shares location. That is more complex, so it stays out of the first version.

**Fallbacks** (only if GPS is denied, off or inaccurate): tap a pin on the map; say or type a village or taluka name (geocoded, then confirmed on the map); or choose a district preset. Each fallback changes the evidence line labels (resolution) and the confidence, never the claims.

**Privacy:** nothing is stored by default. Coordinates stay in memory for the session. For outside services (NASA POWER, geocoder) send coordinates rounded to about 1 km, since POWER's cell is about 50 km anyway. Say this in the consent text, in the app's language.

**PWA notes:** installable to the home screen; the mic and location prompts must be tested in installed (standalone) mode as well as in the browser, on Android Chrome and on iOS Safari (iOS can behave differently, verify). Voice needs internet, so the pre-recorded demo fallback stays. Cache the explainer text and last result for flaky rural connections.

**To verify at build time:** that the Sarvam STT/TTS calls work inside the same page as the Geolocation prompt, handles mic and location permissions cleanly on a real Android phone, and supports Hindi now and Marathi later. Demo on a real phone, not a laptop: desktop browsers often return Wi-Fi/IP locations that are kilometres off.

## 2c. Coverage: which GPS points we can serve (tiles and snapping)

Measured 14 Nov 2026. The downloaded soil tile covers **208 km east-west by 221 km north-south (about 46,000 km2), at 250 m pixels** (lon 76.058-78.058, lat 19.75-21.75). All three presets are inside it.

| Layer | What we have | For a GPS point |
|---|---|---|
| Soil (SoilGrids) | the tile above | sampled at the point itself, **plot-scale (250 m)**, anywhere in the tile |
| Weather features (POWER, ERA5) | computed at 3 points; grids are ~25-50 km | snapped to the nearest preset |
| NDVI (MODIS) | 3 points (a region-wide area request is possible later) | snapped to the nearest preset |
| Mandi prices | by district | nearest preset's district markets |
| Crop windows (CRIDA) | one zone covering Akola, Buldhana, Washim | applies inside that zone only |

The presets cover little of the tile: within 10 km of a preset is 2% of it, 25 km is 12%, 50 km is 37%, 100 km is 78%. The farthest point is 166 km from a preset.

**Rule for now (data-driven, so adding tiles later needs no code change):**
1. A **tile registry** lists each covered tile (bounds, resolution, source). Adding a tile later means adding one entry and its data.
2. A point is **served** if it is inside the soil tile **and** within `MAX_SNAP_KM` (default 50 km) of a preset. Inside the tile but farther than that: "outside the areas we have built data for yet (Akola, Washim, Buldhana)".
3. Every result states the **distance to the nearest preset** and each layer's level: "your spot (250 m)" for soil, "area (snapped, N km away)" for the rest. Evidence lines carry that resolution.
4. A snapped layer more than 25 km from its preset is marked `degraded`.
5. Product version later: more tiles, a region-wide NDVI raster, and weather fetched live for any point; the 50 km limit then goes away.

## 3. The four strategies (defined as data, not code)

| id | name | crops and timing |
|---|---|---|
| S0 | Existing | farmer's current rotation (default soybean then fallow) |
| S1 | Soybean then chickpea | soybean sown 15 Jun-15 Jul, chickpea sown 1-15 Oct |
| S2 | Cotton + pigeon pea intercrop | both sown 15 Jun-10 Jul |
| S3 | Soybean then sorghum / cover crop | sorghum (rabi) or sunn hemp / horse gram after soybean |

Each strategy is a list of (crop, role, sow window, duration) rows from `crops.csv`. Harvest = sowing + duration. The engine always shows all four. A strategy that fails a hard check is shown with a red flag and the reason, never hidden (the brief asks to compare at least three).

## 4. Scoring pipeline

Per strategy, per year (1981-2025), compute component scores 0-100, then combine with weights. Running it for every historical year gives a distribution, which becomes the uncertainty (section 7).

### 4.1 Components (each traceable to named inputs)

| Component | How it is computed | Inputs | Validity of inputs |
|---|---|---|---|
| `water_fit` | available water / crop need. Kharif crops: seasonal rain from onset vs `water_need_mm`. Rabi crops: residual moisture proxy (`wet_root_days_oct_dec`, `post_monsoon_gwetroot_mean`) scaled by clay (water-holding), vs a low rabi need | POWER, soil, crops | POWER degraded (50 km); GWETROOT is a modelled index; chickpea/sorghum need figures partly unverified |
| `timing_fit` | does the sowing window fall after onset and does harvest land before the heat season. Uses onset and withdrawal distribution and the crop's duration | POWER, crops | degraded |
| `heat_risk` (inverted) | days with `T2M_MAX` above `heat_threshold_c` inside the crop's sensitive stage window | POWER daily, crops | thresholds **unverified** |
| `dry_spell_risk` (inverted) | whether a dry run of 10+ days overlaps the sensitive stage | POWER daily, crops | stage windows **unverified** |
| `bare_days` (inverted) | days per year with no crop between harvest and next sowing, from the crop calendar. Cross-checked against NDVI Apr-May low | crops, NDVI | NDVI valid but 250 m mixed pixel |
| `nitrogen` | midpoint of `n_fix_kg_ha` range, scaled 0-100 | crops | mostly unverified |
| `erosion_cover` | `ground_cover` and `residue` ratings plus bare days | crops | ratings unverified |
| `organic_matter` | `residue` rating, cover, with soil SOC as context only | crops, soil | ratings unverified |
| `forage` | `fodder_value` rating | crops | unverified |
| `market` | recent modal price vs MSP, and price spread (min-max) as volatility | mandi, msp | prices valid; price is a proxy, **no cost data so no margin** |
| `pest_break` | rule: legume after cereal/oilseed, or deep-rooted legume with cotton, scores high; same family repeated scores low | crops | judgement, **unverified** |
| `equipment_fit` | `equipment` field vs farmer's equipment | crops | judgement |

Components that rely only on unverified inputs still score, but their evidence lines carry the `unverified` flag and lower the strategy's confidence.

### 4.2 Weights from priority and constraints (draft numbers)

Base weights (balanced farmer): `water_fit` 20, `timing_fit` 10, `heat_risk` 10, `dry_spell_risk` 10, `market` 10, `bare_days` 8, `nitrogen` 6, `erosion_cover` 6, `organic_matter` 6, `forage` 4, `pest_break` 6, `equipment_fit` 4 (sum 100).

Priority multiplier on the matching components, then renormalise to 100:

| Priority | Boosts (x2.5 first priority, x1.5 second) |
|---|---|
| water_saving | `water_fit`, `dry_spell_risk` |
| forage | `forage` |
| nitrogen | `nitrogen`, `pest_break` |
| erosion | `erosion_cover`, `bare_days` |
| organic_matter | `organic_matter`, `bare_days` |
| market_income | `market` |

Constraints:
- water_availability = low: `water_fit` weight x1.5 and a **red flag** on any strategy whose crop need exceeds the supply estimate. rainfed implies low for rabi.
- equipment = basic: strategies needing a sprayer get `equipment_fit` 0 and a flag.
- market_preference: adjusts `market` (mandi uses APMC price; own_use sets `market` to forage/food value instead). **[needs your call]**

Total = sum(weight x score) / 100. The exact weights are always shown to the user.

## 5. Evidence lines (the unit everything else is built from)

Every number the app shows is one evidence line:

```json
{
  "claim": "Median monsoon withdrawal is about 5 October",
  "value": "5 Oct (IQR 23 Sep - 15 Oct)",
  "dataset": "NASA POWER daily, AG community",
  "period": "1981-2025",
  "resolution": "~50 km grid, point value",
  "validity": "degraded",
  "validity_reason": "gridded data cannot see field-level differences",
  "used_in": ["timing_fit", "water_fit"],
  "gap": "no field-level rainfall; farmer should confirm local onset"
}
```

**Validity rule:** a line is `valid` only if every input is `valid`; otherwise the worst input wins (`valid` > `degraded` > `unverified`). A strategy's **confidence** is the share of its weighted score backed by `valid` or `degraded` (not `unverified`) lines. Show it as green / yellow / grey.

Known `degraded` or `unverified` items to carry through: POWER at farm scale, POWER rainfall trends (possible data-source change), GWETROOT index, MODIS mixed pixel, all crop ratings and heat thresholds marked unverified, mandi price as an income proxy.

## 6. Evidence card and the LLM

The engine builds the five card sections from templates: **why suggested, evidence, benefits, information gaps, risks needing local review**. An LLM may rewrite them into friendlier language (and later Hindi) but:

1. It receives only the structured output, never raw data.
2. After it responds, extract every number and date from its text; each must exist in the evidence lines (rounding tolerance allowed).
3. If the check fails, discard the LLM text and show the template text. Log the failure.
4. A short fixed disclaimer is appended by code, not by the LLM: "supports, does not replace, local expertise".

## 6b. Language layer (Hindi for the demo, Marathi for production)

The target region (Vidarbha) speaks Marathi. We use **Hindi for the demo** only because neither of us speaks Marathi and we cannot review Marathi text ourselves. Marathi is the production language. The design must make switching a configuration change, not a rewrite:

- The engine is **language-free**. It outputs structured evidence lines, scores and flags. It never contains user-facing sentences.
- All user-facing text lives in per-language files (`engine/i18n/hi.json`, `mr.json`, `en.json`): card templates, explainer text, component names, disclaimer. Keys are shared across languages.
- The narration step takes a `lang` setting. If an LLM rewrites text, the prompt names the language, and the number check (section 6) must handle Devanagari digits as well as Latin digits.
- Voice: **Sarvam AI speech-to-text and text-to-speech**, called from the PWA. Language is set by config. My understanding is that Sarvam covers Hindi and Marathi; verify current language support, latency and pricing before relying on it. There is no phone-agent platform (Bolna is dropped).
- The fixed disclaimer ("supports, does not replace, local expertise") is a reviewed string per language, never machine-written on the fly.
- **Before any production use in Marathi: a native Marathi speaker (ideally a farmer or KVK/agronomy contact) must review every template and the explainers.** Until then Marathi output is labelled unreviewed.
- Crop and technical terms differ by language and region; keep a small glossary per language (for example soybean, chickpea, pigeon pea), also reviewed.

In the pitch we say this plainly: Hindi demo, Marathi production target, same engine, configurable language layer.

## 7. Uncertainty, shown not hidden

- **Per-year scoring:** run the pipeline for each of 45 years. Report median score and a p20-p80 band per strategy.
- **Rank stability:** the share of years each strategy ranks first. If two strategies' bands overlap, say "no clear winner" instead of forcing a rank.
- **Tie rule:** scores within 5 points are shown as a tie.
- **Two-dataset ranges:** weather features are computed from both NASA POWER and ERA5 (`data/processed/features_ranges.json`). Each feature carries the POWER value, the ERA5 value, the range, and an `agree` flag (tolerances are our own choice: 7 days for dates, 10-15% for amounts). Where the datasets disagree (notably days above 40 C in Mar-May, mean Tmax, monsoon onset), the UI shows a range, not one number, and the evidence line is `degraded`.
- **Information gaps** come straight from `missing` and `unverified` crop fields and from every `degraded` dataset, listed per strategy.

## 8. Scenario slider (stretch)

Shift the historical daily series (rain x factor, Tmax + degrees) and rerun the per-year scoring. First version uses user-set sliders. Later, set the defaults from NEX-GDDP-CMIP6 deltas (2040-2060 vs 1995-2014). The slider changes no stored data, only the in-memory run.

## 9. API contract (draft)

`POST /compare`

```json
{
  "location": "akola",
  "current_rotation": "soybean_fallow",
  "water_source": "rainfed",
  "priorities": ["water_saving", "market_income"],
  "constraints": {"water_availability": "low", "equipment": "basic", "market": "mandi"},
  "scenario": {"rain_factor": 1.0, "tmax_shift_c": 0.0}
}
```

Response: for each of 4 strategies: `name`, `total_score`, `score_band` (p20/p80), `rank_stability`, `components` (score, weight, contribution), `confidence`, `card` (five sections), `evidence` (list of evidence lines). Plus top-level `weights_used`, `bare_field_windows`, `vulnerable_seasons`, `disclaimer`.

## 10. Files to build (proposed order)

1. `engine/data.py` load features, crops, soil, ndvi, mandi into typed objects (with validity)
2. `engine/strategies.py` the 4 strategies as data
3. `engine/components.py` one function per component, pure and unit-tested
4. `engine/weights.py` priority and constraint to weights
5. `engine/score.py` per-year scoring, bands, rank stability
6. `engine/evidence.py` evidence lines and validity propagation
7. `engine/card.py` template cards; `engine/narrate.py` LLM rewrite plus number check
8. `api/main.py` `/compare`

**Tests that matter:** changing priority changes the ranking in the expected direction; low water availability penalises high-water crops; an unverified-only component lowers confidence; the number check rejects a text with an invented number; all four strategies are always returned.

## 11. Decisions we need from you two

1. Are the draft weights and the 2.5x / 1.5x priority boost acceptable as a start?
2. Market score: price vs MSP and volatility only, or do we also try a cost-based margin (we have no cost data, so I'd skip it)?
3. For `own_use` market preference, what replaces the market score?
4. S0 baseline when the farmer says "cotton": is it cotton alone, and does S2 then become the "add pigeon pea" comparison?
5. Do we show `water_source = well / canal` farms at all, given our data describes rainfed conditions? Suggest: yes, but `water_fit` uses a higher supply and the card says irrigation data is missing.
6. Scenario slider in scope or cut?
7. Language: confirm Hindi for demo and Marathi as the production target; who can review Marathi text later?
8. Who drives which engine file (see `docs/GIT_WORKFLOW.md` ownership rules)?

## 12. Known weaknesses to state openly

- POWER cannot tell the three farm points apart for weather; only NDVI and soil are 250 m.
- No farm-level data: nothing here knows what a particular field did last season.
- Crop traits are generalised; many are unverified.
- Cross-check against ERA5 (independent reanalysis): both datasets show a significant rainfall rise (about 53-92 mm/decade) but they **disagree on temperature trend** and on **heat-day counts** (days above 40 C in Mar-May differ by up to 5x between datasets). Trends are not used for scoring, and any heat-day figure must be shown as a range with the `degraded` flag.
- Scores rank hypotheses, they do not predict yield or profit.
