# Crop profile sheet

Table: [`data/crops.csv`](../data/crops.csv). One row per crop used in the four strategies, plus two cover-crop options (sunn hemp, horse gram) and a fallow baseline.

**These are published, generalised figures, not measurements from these farms. Every strategy built on them needs local review by a farmer, KVK or agronomist.**

## Validity rule

- **valid**: the source was opened and the number was read there.
- **unverified**: the number comes from a search summary, from general agronomy knowledge, or is a judgement. The `unverified_fields` column lists these per crop. `ratings` in that column means all the low/medium/high columns.

## Columns

| Column | Meaning | Feeds |
|---|---|---|
| `sow_start`, `sow_end` | Normal rainfed sowing window (MM-DD) | Bare-field windows, timeline |
| `duration_days_min/max` | Sowing to harvest | Bare-field windows |
| `water_need_mm_min/max` | Crop water need over the season | Water saving, water balance |
| `kc_mid`, `kc_end` | FAO-56 crop coefficients (mid and late season) | Evapotranspiration explainer |
| `water_need` | low / medium / high rating | Water saving priority, water constraint |
| `drought_tolerance` | low / medium / high rating | Vulnerable seasons |
| `sensitive_stage` | Stage most hurt by a dry spell | Vulnerable seasons |
| `heat_threshold_c` | Daily max temperature that harms flowering | Heat-stress days from POWER |
| `legume`, `n_fix_kg_ha_min/max`, `n_fixation` | Nitrogen fixing | Nitrogen priority |
| `ground_cover`, `residue` | Soil cover while growing, residue left after | Erosion, organic matter priorities |
| `fodder_value` | Use as animal feed | Forage priority |
| `equipment` | basic, or needs a sprayer | Equipment constraint |

Harvest dates are not stored. The engine derives them as sowing date plus duration.
Market income is not here. It comes from `data/processed/mandi_monthly.csv` and `data/msp.csv`.

## Sources and validity per field

| Field | Crops | Source | Validity |
|---|---|---|---|
| Sowing window | soybean, cotton, pigeon pea, kharif sorghum, chickpea | ICAR-CRIDA Agriculture Contingency Plan, District Akola, section 1.12 (rainfed rows) | valid |
| Sowing window | rabi sorghum | General practice (mid Sep to mid Oct); not in the CRIDA table | unverified |
| Sowing window | horse gram | Vikaspedia package of practices (late Aug to Nov), via search summary | unverified |
| Sowing window | sunn hemp | Not found for a post-soybean slot. See gaps | missing |
| Duration | cotton 180-195, sorghum 120-130 | FAO Irrigation Water Management Training Manual 3, ch. 2 | valid |
| Duration | soybean min 85 | FAO-56 Table 11, tropics row | valid |
| Duration | soybean max 110 | Typical for local varieties; FAO manual's global 135-150 does not fit (see checks) | unverified |
| Duration | chickpea, pigeon pea, sunn hemp, horse gram | ICRISAT / CRIDA / Tropical Forages via search summaries, and general practice | unverified |
| Water need (mm) | cotton 700-1300, soybean 450-700, sorghum 450-650 | FAO Training Manual 3, ch. 2 | valid |
| Water need (mm) | chickpea 200-300 | ICRISAT literature via search summary | unverified |
| Water need (mm) | horse gram 400-800 | Sources conflict (400-800, 640-750, ~800) | unverified |
| Water need (mm) | pigeon pea, sunn hemp | No figure found | missing |
| Kc mid, Kc end | soybean, cotton, chickpea, sorghum | FAO-56 Table 12 | valid |
| Kc | pigeon pea, sunn hemp, horse gram | Not listed in FAO-56 | missing |
| N fixation (kg/ha) | chickpea 23-97, pigeon pea 4-200 | CGIAR source via search summary. ICRISAT Patancheru estimate for pigeon pea: about 69 per season | unverified |
| N fixation (kg/ha) | sunn hemp 150-165 at 60 days | Tropical Forages via search summary | unverified |
| N fixation (kg/ha) | soybean, horse gram | Not looked up; rating only | missing |
| Heat threshold | all | General agronomy knowledge, not looked up | unverified |
| Sensitive stage | all | General agronomy knowledge, not looked up | unverified |
| All low/medium/high ratings | all | Judgement from the numbers above | unverified |

Links:
- ICAR-CRIDA contingency plan, Akola: https://icar-crida.res.in/CP/Maharastra/PDKV,%20Akola/Akola.pdf
- FAO-56, chapter 6 (Tables 11 and 12): https://www.fao.org/4/x0490e/x0490e0b.htm
- FAO Training Manual 3, chapter 2: https://www.fao.org/4/s2022e/s2022e02.htm
- Tropical Forages, Crotalaria juncea: https://tropicalforages.info/text/entities/crotalaria_juncea.htm
- Vikaspedia, horse gram: https://www.vikaspedia.in/agriculture/crop-production/package-of-practices/pulses/horse-gram

## Local context from the Akola contingency plan (valid)

- NARP zone "Central Maharashtra Plateau" covers Akola, Buldhana and Washim together, so the Akola sowing windows are used for all three points.
- South-west monsoon: normal onset week 24 (11-17 June), cessation week 40 (1-7 October). Normal rainfall 711.6 mm June-September, 825.3 mm a year.
- Drought, flood, hail and heat wave are listed as occasional. Frost is listed as none (relevant to the frost-risk explainer).
- Soils: deep black 46.5%, shallow black 43.5%, medium deep black 9.9% (Akola figures include Washim).

## Checks against our own data

- **Rainfall agrees.** POWER 1981-2025 mean for the Akola point: 877 mm a year, 740 mm June-September (plan: 825 and 712). Buldhana 835 / 700, Washim 885 / 746.
- **Soybean then chickpea only works with short-duration soybean.** Sown 15 June-15 July, an 85-110 day soybean is off the field by mid-September to early November, close to the 1-15 October rainfed chickpea window. FAO's global 135-150 days would miss it. Late-sown soybean leaves no room for chickpea: flag as a risk on strategy 1.
- **Chickpea heat threshold needs review.** POWER mean daily maximum at Akola is 33.8 C in February and 37.7 C in March. With a 32 C threshold, most of February counts as heat stress, so either the threshold or the assumed flowering period needs a local check.

## Gaps and risks needing local review

1. Sunn hemp has no sowing window for a slot after soybean. It is normally a monsoon-season green manure; whether it establishes on residual moisture in October here is unknown.
2. Rabi sorghum and horse gram sowing windows are not from a Vidarbha source.
3. Pigeon pea has no water-need or Kc figure. Its rating is a judgement.
4. All heat thresholds, sensitive stages and low/medium/high ratings are unverified.
5. Durations depend on variety. The table gives ranges, not a variety recommendation.
6. Cotton is rated `sprayer` for equipment as a judgement (pest pressure); confirm.
