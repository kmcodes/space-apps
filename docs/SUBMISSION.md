# Submission pack

Text to paste into the Space Apps project page, plus the feature-to-brief mapping and the data lists. Everything here is true of what is built on 15 Nov 2026. Placeholders to fill by hand are marked **[FILL]**.

## Project title

Field Shift

## One-line summary (under 200 characters)

A Hindi voice call for rainfed farmers in Vidarbha that compares four ways to use one field through the year, using NASA POWER weather and MODIS satellite greenness, and shows what is not known.

## Project description (paste into the page)

Many rainfed farmers in Vidarbha, Maharashtra (Akola, Buldhana, Washim) leave a field bare for months after soybean, and many of them cannot read. Field Shift is a decision-support tool built for them.

The farmer taps once and a Hindi voice calls. The phone shows the farm on a satellite map and the farmer confirms the pin. Then the app asks a few questions aloud (current rotation, water source, what matters most, water available, equipment, where they sell). Each option is read while its picture lights up, so the picture and the word are linked. Every question can be answered by voice or by touching.

An engine then compares four ways of using the field through the year: the current rotation, soybean then chickpea, cotton with pigeon pea, and soybean then sorghum or a cover crop. The result is spoken and shown with no scores: the best choices get a thumbs-up, and each has a twelve-month bar (June to May, kharif and rabi grouped) where green means a crop is in the ground and dark means the field is bare. Hot months and long dry-spell months from the climate record are drawn under the bar. Three picture rows speak when tapped: what looks good, what is not yet confirmed, and what to ask a local expert. Every choice carries a badge, "अनुमानित सुझाव" (estimated suggestion), until all its inputs are checked; today none are, so every suggestion is labelled an estimate. Sources and validity flags sit behind a "for experts" link.

NASA POWER daily weather (1981 to 2025) drives the rain, water, monsoon and heat evidence. MODIS MOD13Q1 NDVI (250 m, 2015 to 2025, from AppEEARS) shows crop seasons and bare-field windows from space. We cross-checked POWER against ERA5: they agree that rain has risen and on dry-spell length, but disagree on heat days and temperature trend, so we show a range and never claim a trend.

We kept strict rules. No strategy is shown without its gaps and risks. Every piece of evidence names its dataset, period and a validity flag. A missing input is never scored as zero. Where two datasets disagree we show both. No language model writes any text: every sentence is a template filled from engine fields, so no number is invented.

Field Shift supports, and does not replace, the judgement of farmers and local agricultural experts. Every suggestion is a hypothesis for local review.

## Links

- Demo video: **[FILL after upload]**
- Repository: https://github.com/kmcodes/space-apps (public: it clones without a login, checked 15 Nov)
- Live app: https://field-shift-opal.vercel.app (engine API https://space-apps-dzma.onrender.com; free tier, wakes in about 30 seconds after a quiet spell, so open it a minute before judging)

## Feature-to-brief mapping

| Brief item | Where it is | State |
|---|---|---|
| At least three strategies, including the current rotation | Four strategies, `engine/compare.py` | Done |
| Per strategy: why, evidence, benefits, gaps, risks | Spoken rows and "for experts" evidence in `web/app/results.tsx` | Done |
| Bare-field windows | Year bar, dark months | Done |
| Vulnerable seasons | Hot and dry-spell months under the year bar, "नाज़ुक समय" row, `pipeline/season_risk.py` | Done |
| Farmer priorities and constraints as inputs | Voice call questions | Done |
| Explainers (evapotranspiration, soil-moisture anomaly, NDVI, frost risk, water balance) | "समझिए" screen, each spoken | Done |
| Satellite versus ground data explained | Last row of "समझिए" | Done |
| Uncertainty and where local validation is needed | "We do not know" and "ask an expert" rows | Done |
| Timeline | Year bar | Done |
| Map of the farm location | Phone location, satellite map with pin, farmer confirms | Done |
| Scenario slider | | Not built |

## Data used

**NASA**

- NASA POWER, daily 1981 to 2025: temperature, rain, soil wetness, humidity, solar radiation. Used for rain and water fit, monsoon onset and withdrawal, dry spells, heat days.
- MODIS MOD13Q1.061 NDVI, 250 m, 16-day, 2015 to 2025, via NASA AppEEARS. Used for crop seasons and bare-field windows.
- NASA SMAP soil moisture was searched in the catalogue but is not used.

**Not NASA**

- ISRIC SoilGrids (clay, sand, pH, soil carbon): soil context.
- ERA5 reanalysis (Copernicus/ECMWF) through Open-Meteo, CC BY 4.0: independent cross-check of POWER.
- Agmarknet mandi prices via data.gov.in, and announced minimum support prices: market score.
- Crop parameters from FAO-56, FAO Irrigation Water Management Training Manual 3, ICAR-CRIDA Akola contingency plan, ICRISAT and FAO ECOCROP. Each value is marked valid or unverified in `data/crops.csv`.
- Google Maps keyless embed for the satellite map (not an official product; coordinates rounded to about 100 m are sent to Google).

## What is not done (say this plainly)

- Speech uses the browser's built-in Hindi (Chrome on Android works best). Sarvam speech is planned, not built.
- Hosted on free tiers (Vercel and Render): the API sleeps when idle and takes about 30 seconds to wake. Redeploys after a push depend on a watcher script on Amrita's PC.
- All Hindi text is machine-drafted and has not been reviewed by a native speaker. Marathi is not done.
- Crop pictures are drawn placeholders.
- The engine ignores the water source the farmer gives.
- The scenario slider is not built.
- Weather is area-scale (about 25 to 50 km), satellite pixels are 250 m and mixed, rain is reanalysis and not gauge data, and all penalties in the scoring are our own assumptions in `engine/config.py`. Nothing is field-level.

## How AI was used (answer honestly if the form asks)

Two team members worked with Claude Code (Anthropic) as a coding assistant: it helped write the data pipeline, engine, tests, web app and drafted the Hindi text and docs, and the team reviewed and directed the work. No AI model runs inside the product: results come from rules over data, and every sentence is a template. The Hindi has not been checked by a native speaker. **[FILL: confirm this wording with Amrita, and check the event's rules on AI-assisted and pre-written code, open item 5 in START.md.]**

## Before you press submit

- [ ] Video recorded and uploaded, link pasted above
- [ ] Repo is public (or the visibility the rules ask for) and the link works in a private window
- [ ] README test count and status table still match the code
- [ ] Project page text pasted, links filled
- [ ] Team members added on the project page
- [ ] Re-read "What is not done" and the "do not say" list in `docs/DEMO_SCRIPT.md`
- [ ] Submit before 23:59 local, and screenshot the confirmation
