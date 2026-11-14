# Crop sheet gaps: candidate values from other sources

Written 14 Nov 2026 (Kartik's Claude). Candidate values for blanks and unverified fields in `data/crops.csv`. **This file does not change `crops.csv`.** Amrita owns the sheet and decides what to merge.

## Status labels (same rule as `docs/crop_sheet.md`)

- **VERIFIED**: the source page was opened and the number was read there. Quote given.
- **SEARCH-SUMMARY**: seen only in a search-result snippet. Treat as `unverified`.
- **NOT FOUND**: no usable source found. Leave blank; the engine treats blank as a gap, never zero.

## 1. Blanks that now have a verified candidate

| Crop | Field | Candidate | Status | Source and quote |
|---|---|---|---|---|
| soybean | n_fix_kg_ha | 73-288 (shoot ureides) or 147-337 (root ureides) | VERIFIED, but Australian field data | Herridge 1982, Plant Physiology 70:7-11, abstract: "seasonal N(2) fixation for soybeans at the seven locations ranged from 73 to 288 kilograms per hectare N". https://hero.epa.gov/reference/11590334 . Seven sites in NW New South Wales; Vidarbha rainfed yields are lower, so expect less. Do not use as a Vidarbha figure without a caveat |
| sunn_hemp | n_fix_kg_ha | 50-60 within 60-90 days; 60 as green manure | VERIFIED | Feedipedia: "can fix about 50-60 kg N/ha within 60-90 days of cultivation. It provides 60 kg N/ha to the soil when it is used as green manure." https://www.feedipedia.org/node/313 |
| sunn_hemp | water need | rainfall as low as 200 mm a year; irrigation "necessary for maximum growth and nitrogen fixation (minimum of 25 mm of water/week)" | VERIFIED (rainfall, weekly water); seasonal mm not given | Feedipedia, same page. Over about 8-9 weeks to green-manure stage, 25 mm/week would be about 200-225 mm (my arithmetic, not a source figure) |
| sunn_hemp | duration | ploughed in about 2 months after sowing at flowering; 60-160 day crop cycle | VERIFIED | Feedipedia ("ploughed in 2 months after sowing when the plants begin to flower"); ECOCROP id 801 crop cycle 60-160 |
| sunn_hemp | season, sowing | "As a green manure, sunn hemp is mainly grown during the rainy season." Also: "grown in kharif in the northern states ... raised in rabi also" in southern regions | VERIFIED, no Vidarbha window | Feedipedia; indiaagronet https://indiaagronet.com/indiaagronet/crop%20info/sunnhemp.htm |
| horse_gram | water, season | rainfall 380-900 mm, drought-hardy; "grown on residual moisture in the dry season, (e.g. after a rice crop)" | VERIFIED | ECHO plant sheet https://api.echocommunity.org/pdf/en/8d75d448-9c82-4e8c-926d-fbc53eef9797/horse-gram.pdf |
| horse_gram | duration | pasture in 40-50 days; "in 120-180 days the seed is mature" | VERIFIED | ECHO, same page. **Conflicts with the sheet's 85 days** (see section 3) |
| chickpea | heat threshold | **35 C** during flowering and podding | VERIFIED | Gaur et al. 2013, ICRISAT: "suffers heavy yield losses when exposed to heat stress at the reproductive (flowering and podding) stage ... A temperature of 35 °C was found to be critical in differentiating heat-tolerant and heat-sensitive genotypes in chickpea under field conditions." http://oar.icrisat.org/7264/ |
| chickpea | sensitive stage | flowering and podding (reproductive stage) | VERIFIED (stage, not day numbers) | Same abstract: "Heat stress during the reproductive phase adversely affects pollen viability, fertilization, pod set, and seed development" |

## 2. ECOCROP table for all seven crops (one consistent source)

FAO ECOCROP datasheets, opened and read. Same fields for every crop, so useful as a consistent fallback where `water_need_mm` is blank.

| Crop | ECOCROP id | Temp optimal (C) | Temp absolute (C) | Annual rain optimal (mm) | Annual rain absolute (mm) | Crop cycle (days) |
|---|---|---|---|---|---|---|
| soybean (Glycine max) | 1150 | 20-33 | 10-38 | 600-1500 | 450-1800 | 75-180 |
| cotton (Gossypium hirsutum) | 1160 | 22-36 | 15-42 | 750-1200 | 450-1500 | 150-200 |
| chickpea (Cicer arietinum) | 2479 | 15-29 | 7-35 | 600-1000 | 300-1800 | 90-180 |
| pigeon pea (Cajanus cajan) | 576 | 18-38 | 10-45 | 600-1500 | 400-4000 | 90-365 |
| sorghum (Sorghum bicolor) | 48747 | 22-35 | 8-40 | 400-600 | 300-700 | 90-300 |
| horse gram (Macrotyloma uniflorum) | 1399 | 20-28 | 17-35 | 500-1200 | 300-4300 | 40-180 |
| sunn hemp (Crotalaria juncea) | 801 | 20-30 | 4-40 | 500-1500 | 200-4300 | 60-160 |

URL pattern: `https://ecocrop.apps.fao.org/ecocrop/srv/en/dataSheet?id=<id>`.

**How to read it (my understanding, verify):**
- The page does not say whether the temperature range is daily maximum or growing-season mean. As far as I know, ECOCROP-based models treat it as mean temperature. So using the **absolute maximum** as `heat_threshold_c` is a rough proxy, not a measured damage threshold. For chickpea it matches ICRISAT's 35 C, which is reassuring.
- Annual rainfall is a screening range, not a seasonal water requirement. It is a different quantity from `water_need_mm` and must be labelled so.
- Local annual rain is about 810-950 mm (POWER and ERA5 medians). Sorghum's ECOCROP absolute maximum is 700 mm, yet sorghum is widely grown here, so ECOCROP is too coarse to rule crops out. Use it as a hint only.
- A search result noted FAO says the ECOCROP database was discontinued around 2015 (snippet only, not checked). The figures are still citable but old.

## 3. Conflicts with the current sheet (please review)

| Item | Sheet says | New source says | Suggestion |
|---|---|---|---|
| Chickpea heat threshold | 32 C (per `docs/crop_sheet.md` checks) | 35 C critical in the field (ICRISAT, VERIFIED) | Change to 35 and mark VERIFIED. With 32 C most of February counts as heat stress |
| Horse gram duration | 85 days (unverified) | 120-180 days to mature seed; 40-50 days for pasture (ECHO) | Fix duration. A 120+ day crop sown after soybean runs well past February and into the hot season, which changes its fit |
| Sunn hemp N fixation | 150-165 kg/ha at 60 days (Tropical Forages, search summary) | 50-60 kg/ha within 60-90 days; 60 as green manure (Feedipedia, VERIFIED) | Show a range 50-165 and flag the conflict, or use the verified 50-60 |
| Chickpea duration | unverified | ECOCROP 90-180 (VERIFIED, broad) | Mark partly supported; ICRISAT typical figures would narrow it |

## 4. What the sources say about strategy S3 (important)

- **Sunn hemp after soybean on residual moisture is not supported by what I read.** Feedipedia says it needs a minimum of 25 mm of water a week for full growth and nitrogen fixation, and is mainly a rainy-season green manure. indiaagronet says "a minimum of 40cm of rainfall distributed in not less than 50 rainy days during the growing season is a primary requisite" (that page is about fibre sunn hemp). An October sowing in rainfed Vidarbha has neither. Treat sunn hemp as a flagged "unproven in this slot" variant.
- **Horse gram fits the residual-moisture slot better** (ECHO: grown on residual moisture in the dry season; drought-hardy). But its 120-180 day duration and 20-28 C optimal range need checking against the Vidarbha Feb-May heat.
- This supports Amrita's suggestion to make rabi sorghum the default S3 crop, with the other two as variants.

## 5. Still missing (NOT FOUND or SEARCH-SUMMARY only)

| Crop | Field | What I found | Handling |
|---|---|---|---|
| pigeon pea | water_need_mm, kc_mid, kc_end | ECOCROP gives annual rainfall only (600-1500 optimal). No seasonal mm or Kc. Search snippet: "average rainfall for growing pigeon pea ranges from 600 to 650 mm" (farmpedia.org, not opened) | Leave blank. Engine uses the ECOCROP rainfall range as a labelled proxy |
| sunn hemp | kc, sowing window for Vidarbha, sensitive stage | none | Leave blank |
| sunn hemp | water need | "400-500 mm of irrigation" for fibre crop (ScienceDirect snippet only) | SEARCH-SUMMARY, unverified |
| horse gram | kc, heat sensitive stage | none | Leave blank. ECOCROP optimal 20-28 C, absolute max 35 C |
| horse gram | n_fix_kg_ha | ECHO says only that it fixes nitrogen. A commercial site snippet says 50-80 kg/ha (organicmandya.com) | SEARCH-SUMMARY, weak source, unverified. Use the rating only |
| soybean | net nitrogen | A review snippet says biological fixation met "50-60% of soybean N demand" and "in most situations the amount of N fixed was not sufficient to replace N export" (Salvagiotti et al. 2008, ScienceDirect, blocked to my reader) | SEARCH-SUMMARY. Suggests soybean's net N benefit to the next crop is small even though it is a legume |
| all crops | sensitive-stage day numbers | none | See next section |
| rabi sorghum | sowing window | none | still unverified |

## 6. Suggestions for the sheet and engine

1. **Sensitive-stage windows (Amrita's issue 3):** FAO-56 Table 11 gives stage lengths (initial, development, mid, late) for each crop. Amrita already opened FAO-56 for Kc. Define the sensitive window as the **mid-season stage** (flowering and pod fill) in days after sowing, which is verifiable and consistent. For chickpea ICRISAT confirms the reproductive stage is the heat-sensitive one.
2. **New columns** that make every crop comparable: `ecocrop_temp_opt_min/max`, `ecocrop_temp_abs_min/max`, `ecocrop_rain_opt_min/max`, `ecocrop_rain_abs_min/max`, `ecocrop_cycle_min/max`, with `heat_threshold_source` saying "ECOCROP absolute max (proxy)" or "ICRISAT field study".
3. **Heat risk confidence:** a cited heat threshold removes one reason `heat_risk` was grey. The weather side is still disputed between POWER and ERA5, so keep the range display.
4. **Do not use the Australian soybean number as a Vidarbha value.** If an ICAR or ICRISAT figure for rainfed Indian soybean can be found, use that.

## 7. Next research round (not done)

- FAO-56 Table 11 stage lengths for the five crops that have them (Amrita has the page open already).
- Pigeon pea seasonal water use (ICRISAT or ICAR).
- A Vidarbha or Maharashtra source for rabi sorghum sowing and for any post-soybean cover crop (KVK or PDKV Akola).
- An Indian soybean N-fixation figure.
