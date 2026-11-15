# Submission pack

Text to paste into the Space Apps project page, plus the feature-to-brief mapping and the data lists. Everything here is true of what is built on 15 Nov 2026. Placeholders to fill by hand are marked **[FILL]**.

## Project title

Field Shift

## One-line summary (under 200 characters)

A Hindi voice call for rainfed farmers in Vidarbha that compares four ways to use one field through the year, using NASA POWER weather and MODIS satellite greenness, and shows what is not known.

## Project description (paste into the page)

Many rainfed farmers in Vidarbha, Maharashtra (Akola, Buldhana, Washim) leave a field bare for months after soybean, and many of them cannot read. Field Shift is a decision-support tool built for them.

The farmer taps once and a Hindi voice calls (or an English one: a switch at the top changes the whole app). The phone shows the farm on a satellite map and the farmer confirms the pin. Then the app asks a few questions aloud (current rotation, water source, what matters most, water available, equipment, where they sell). Each option is read while its picture lights up, so the picture and the word are linked. Every question can be answered by voice or by touching.

An engine then compares four ways of using the field through the year: the current rotation, soybean then chickpea, cotton with pigeon pea, and soybean then sorghum or a cover crop. The result is spoken and shown with no scores: the best choices get a thumbs-up, and each has a twelve-month bar (June to May, kharif and rabi grouped) where each crop has its own colour and black means the field is bare, with a small legend under the bars. Hot months and long dry-spell months from the climate record are drawn under the bar. Three picture rows speak when tapped: the checked advice (जाँचा हुआ सुझाव), the estimates (अनुमानित सुझाव), the sensitive months, and what to ask a local expert. Every choice carries a badge, "अनुमानित सुझाव" (estimated suggestion), until all its inputs are checked; today none are, so every suggestion is labelled an estimate. Sources and validity flags sit behind a "for experts" link.

NASA POWER daily weather (1981 to 2025) drives the rain, water, monsoon and heat evidence. MODIS MOD13Q1 NDVI (250 m, 2015 to 2025, from AppEEARS) shows crop seasons and bare-field windows from space. We cross-checked POWER against ERA5: they agree that rain has risen and on dry-spell length, but disagree on heat days and temperature trend, so we show a range and never claim a trend.

We kept strict rules. No strategy is shown without its gaps and risks. Every piece of evidence names its dataset, period and a validity flag. A missing input is never scored as zero. Where two datasets disagree we show both. No language model writes any text: every sentence is a template filled from engine fields, so no number is invented.

Field Shift supports, and does not replace, the judgement of farmers and local agricultural experts. Every suggestion is a hypothesis for local review.

## Links

- Project demo (video of 30 seconds or less, or up to 7 slides; public full URL): **[FILL after upload]**
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
- Crop parameters from FAO-56, FAO Irrigation Water Management Training Manual 3, ICAR-CRIDA Akola contingency plan, the PDKV Akola lysimeter study (MahaPOCRA), ICRISAT and FAO ECOCROP. Each value is marked valid or unverified in `data/crops.csv`.
- Google Maps keyless embed for the satellite map (not an official product; coordinates rounded to about 100 m are sent to Google).

## What is not done (say this plainly)

- Speech uses the browser's built-in Hindi (Chrome on Android works best). Sarvam speech is planned, not built.
- Hosted on free tiers (Vercel and Render): the API sleeps when idle and takes about 30 seconds to wake. Redeploys after a push depend on a watcher script on Amrita's PC.
- All Hindi text is machine-drafted and has not been reviewed by a native speaker. Marathi is not done.
- Crop pictures are drawn placeholders.
- The engine ignores the water source the farmer gives.
- The scenario slider is not built.
- Weather is area-scale (about 25 to 50 km), satellite pixels are 250 m and mixed, rain is reanalysis and not gauge data, and all penalties in the scoring are our own assumptions in `engine/config.py`. Nothing is field-level.

## Use of Super Intelligence (SI): the form's question (paste this answer)

Yes. We used Claude Code (Anthropic), an AI coding assistant, to help write the data pipeline, the rule-based engine, the tests, the web app, the documentation and the first drafts of the Hindi and English text. The team chose the problem and the approach, directed the work, and reviewed it. No AI model runs inside the product: every result comes from rules over NASA POWER, MODIS and other data, and every sentence the app says is a template filled from those results. The app's spoken voice is the browser's built-in text-to-speech, which is machine-generated audio; it is the only audio in the demo video. No images or video were generated by AI. The Hindi and English text has not been checked by a native speaker. **[Confirm this wording with Amrita before submitting.]**

## What the form asks for, and where our answer is

| Form field | Our answer |
|---|---|
| Project name | Field Shift |
| High-level summary | "One-line summary" and "Project description" above |
| Link to final project | The live app, https://field-shift-opal.vercel.app, or the repo, https://github.com/kmcodes/space-apps (full URL, public, no login) |
| Detailed description | "Project description" above, plus the README |
| Use of SI | The answer above |
| NASA data used (at least one is required for a Global Award) | NASA POWER daily weather 1981-2025 and MODIS MOD13Q1 NDVI via AppEEARS. See "Data used" above. |
| Space Agency Partner data and other references | Everything under "Not NASA" in "Data used", plus the code libraries in `requirements.txt` and `web/package.json` |
| Project demo | A video of **30 seconds or less**, or **7 slides or fewer**, at a public full URL. See [DEMO_SCRIPT.md](DEMO_SCRIPT.md). |

All content in the form and in linked materials must be in English. The video may have non-English speech only with English subtitles.

## Before you press submit

- [ ] Demo is **30.0 seconds or less** (or 7 slides or fewer) and the link opens in a private window with no login. Paste the full `https://` URL.
- [ ] Demo has no NASA logo or branding, no person under 18, and no other tabs, names or emails on screen
- [ ] The video description has the audio and AI acknowledgement from [DEMO_SCRIPT.md](DEMO_SCRIPT.md)
- [ ] The SI question is answered with the text above (and confirmed with Amrita)
- [ ] Repo is public and the link works in a private window
- [ ] The live app and engine are redeployed from the latest commit (open `/health` first)
- [ ] README test count and status table still match the code
- [ ] Project page text pasted, every field in English, links filled
- [ ] Team members added on the project page, and everyone is confirmed at the same Local Event
- [ ] Re-read "What is not done" and the "Do not show or say" list in [DEMO_SCRIPT.md](DEMO_SCRIPT.md)
- [ ] Tick the terms and originality boxes, click **Submit for Judging** before **Sunday 15 Nov, 23:59 local time**, and screenshot the confirmation
