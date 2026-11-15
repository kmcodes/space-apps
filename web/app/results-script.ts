// What the results page says and shows, built only from the engine's structured output.
// Nothing here invents a number or a claim: every sentence is a template tied to an engine field
// (component status, calendar, risk text), and no scores are spoken or shown (docs/VOICE_APP_PLAN.md).
// All Hindi text was drafted by Claude and has NOT been reviewed by a native speaker.

import type { PictogramId } from "./pictograms";

export type Component = { score: number | null; status: string; validity: string; weight: number };
export type CalendarEntry = { crop: string; sow_doy: number; harvest_doy: number };
export type Evidence = { claim: string; dataset?: string; period?: string; resolution?: string; validity: string };
export type Strategy = {
  id: string;
  name: string;
  kind: string; // "sequence" | "mixed" | "single"
  crops: string[];
  duplicate_of: string | null;
  calendar?: CalendarEntry[];
  components: Record<string, Component>;
  evidence: Evidence[];
  incomplete: boolean;
  card: { gaps: string[]; risks_for_local_review: string[] };
};
export type SeasonRisk = { heat_level: number[]; dry_spell_level: number[]; frost_days_per_year: { power: number; era5: number } };
export type Result = {
  served: boolean;
  reason?: string;
  ranking: string[];
  tied_with_top: string[];
  strategies: Strategy[];
  site_evidence: Evidence[];
  location?: { nearest: string };
  season_risk?: SeasonRisk; // calendar order, index 0 = January
};

export const RESULTS = {
  loading: "रुकिए, तरीके देखे जा रहे हैं…",
  waking: "इंजन जाग रहा है, इसमें एक मिनट लग सकता है। थोड़ा रुकिए…",
  error: "इंजन से जवाब नहीं मिला। फिर से कोशिश कीजिए।",
  retry: "फिर से कोशिश करें",
  title: "आपके खेत के लिए तरीके",
  where: "आपकी जगह",
  outOfArea: "इस जगह के लिए हमारे पास अभी जानकारी नहीं है। हम अभी अकोला, बुलढाणा और वाशिम के लिए काम करते हैं। नई बातचीत में ज़िला चुनिए।",
  replay: "फिर सुनिए",
  again: "नई बातचीत",
  back: "वापस",
  current: "आप अभी यही करते हैं",
  notRanked: "पूरी जानकारी नहीं",
  tapHint: "किसी तरीके को छुइए",
  forExperts: "विशेषज्ञों के लिए: स्रोत और जाँच",
  // The two rows are the two kinds of advice: what was checked, and what is an estimate.
  good: "जाँचा हुआ सुझाव",
  unknown: "अनुमानित सुझाव",
  estimate: "अनुमानित सुझाव",
  verifiedAdvice: "जाँचा हुआ सुझाव",
  estimateNote: "ये आँकड़ों से लगाए अनुमान हैं, पक्की बात नहीं।",
  noneChecked: "अभी इस तरीके की कोई बात पूरी तरह जाँची हुई नहीं है।",
  estimateGood: "आँकड़ों से अच्छा लगता है, पर अभी जाँचा नहीं",
  expert: "विशेषज्ञ से पूछिए",
  vulnerable: "नाज़ुक समय",
  learn: "समझिए",
  learnTitle: "ये बातें क्या हैं?",
  kharif: "खरीफ",
  rabi: "रबी",
  summer: "गर्मी",
  disclaimer: "यह औज़ार किसानों और स्थानीय कृषि विशेषज्ञों की समझ का सहारा है, उसकी जगह नहीं।",
  suggestion: "यह सुझाव है, आदेश नहीं। कृषि विज्ञान केंद्र या कृषि अधिकारी से पूछिए।",
};

const CROP_HI: Record<string, string> = {
  soybean: "सोयाबीन",
  chickpea: "चना",
  cotton: "कपास",
  pigeon_pea: "तुअर",
  sorghum_rabi: "ज्वार",
  sunn_hemp: "सनई",
  horse_gram: "कुलथी",
  fallow: "खाली खेत",
};

const CROP_PIC: Record<string, PictogramId> = {
  soybean: "soybean",
  chickpea: "chickpea",
  cotton: "cotton",
  pigeon_pea: "pigeon_pea",
  sorghum_rabi: "sorghum",
  fallow: "bare",
};

const cropName = (c: string) => CROP_HI[c] ?? c;
const cropPic = (c: string): PictogramId => CROP_PIC[c] ?? "bare";

/** "सोयाबीन, फिर चना" / "कपास और तुअर साथ-साथ" / "कपास". */
export function strategyName(s: Strategy): string {
  const names = s.crops.map(cropName);
  if (s.kind === "mixed") return `${names.join(" और ")} साथ-साथ`;
  return names.join(", फिर ");
}

/** Pictures for one strategy: crops in order, with an arrow between a sequence or a plus between a mixed crop. */
export function strategyPics(s: Strategy): PictogramId[] {
  return picsFor(s.crops, s.kind === "mixed" ? "plus" : "then");
}

export function picsFor(crops: string[], joiner: PictogramId): PictogramId[] {
  const out: PictogramId[] = [];
  crops.forEach((c, i) => {
    if (i) out.push(joiner);
    out.push(cropPic(c));
  });
  return out;
}

/** The choices to show, best first. A rotation identical to the current one is shown once, marked as current. */
export type Choice = { strategy: Strategy; top: boolean; current: boolean };

export function choices(result: Result): Choice[] {
  const alias = (id: string) => result.strategies.find((s) => s.id === id)?.duplicate_of ?? id;
  const visible = result.strategies.filter((s) => !s.duplicate_of);
  const currentId = alias("S0"); // S0 is what the farmer does now; if it equals S1, S1 carries the mark
  const top = new Set(result.tied_with_top.map(alias));
  const place = (s: Strategy) => {
    if (s.incomplete) return 99;
    const i = result.ranking.findIndex((id) => alias(id) === s.id);
    return i < 0 ? 98 : i;
  };
  return [...visible]
    .sort((a, b) => place(a) - place(b))
    .map((s) => ({ strategy: s, top: top.has(s.id) && !s.incomplete, current: s.id === currentId }));
}

// ---- The year bar: June to May, so kharif and rabi each form one block ----

const MONTH_DAYS = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31];
const MONTH_OF_DAY: number[] = MONTH_DAYS.flatMap((n, m) => Array<number>(n).fill(m)); // day 0..364 -> month 0..11
export const YEAR_ORDER = [5, 6, 7, 8, 9, 10, 11, 0, 1, 2, 3, 4]; // Jun..Dec, Jan..May
export const SEASONS = [
  { key: "kharif", from: 0, length: 5 }, // Jun to Oct
  { key: "rabi", from: 5, length: 5 }, // Nov to Mar
  { key: "summer", from: 10, length: 2 }, // Apr to May
] as const;

/** For each of the 12 months (June first): the crop in the ground for at least half the month. Empty = bare field.
 *  Only a mixed crop (an intercrop) can show two crops in one month; in a sequence the main crop of that month wins. */
export function yearBar(calendar: CalendarEntry[] = [], mixed = false): string[][] {
  const days: Record<string, number[]> = {};
  for (const e of calendar) {
    const counts = (days[e.crop] ??= Array<number>(12).fill(0));
    for (let d = e.sow_doy; d < e.harvest_doy; d++) counts[MONTH_OF_DAY[(d - 1) % 365]]++;
  }
  return YEAR_ORDER.map((m) => {
    const here = Object.keys(days)
      .filter((c) => days[c][m] >= MONTH_DAYS[m] / 2)
      .sort((a, b) => days[b][m] - days[a][m]);
    return mixed ? here : here.slice(0, 1);
  });
}

export type Run = { start: number; length: number; crops: string[] };

/** Consecutive months with the same crops, so each stretch gets one picture. */
export function runs(bar: string[][]): Run[] {
  const out: Run[] = [];
  bar.forEach((crops, i) => {
    const last = out[out.length - 1];
    if (last && last.crops.join("+") === crops.join("+")) last.length++;
    else out.push({ start: i, length: 1, crops });
  });
  return out;
}

// ---- The three picture rows on a detail screen ----

const GOOD_HI: Record<string, string> = {
  water_fit: "बारिश फ़सल के पानी की ज़रूरत से अच्छा मेल खाती है",
  timing_fit: "बुवाई और कटाई का समय ठीक बैठता है",
  bare_days: "खेत ज़्यादा दिन फ़सल से ढका रहता है",
  nitrogen: "मिट्टी में नाइट्रोजन बढ़ती है, खाद कम लगती है",
  forage: "जानवरों के लिए चारा मिलता है",
  market: "बाज़ार भाव का संकेत अच्छा है",
};

const UNSURE_HI: Record<string, string> = {
  water_fit: "पानी का मेल",
  timing_fit: "बुवाई-कटाई का समय",
  bare_days: "खेत कितने दिन ढका रहेगा",
  nitrogen: "नाइट्रोजन का फ़ायदा",
  forage: "चारे की मात्रा",
  market: "बाज़ार भाव",
};

export const AREA_SCALE_HI = "मौसम का डेटा पूरे इलाके का है, आपके अपने खेत का नहीं।";

/** "Verified" only when every part of the score is complete and its inputs are checked (validity "valid").
    Any missing, degraded or unverified input makes it an estimate. Today the crop sheet is mostly unverified, so it is an estimate. */
export function adviceKind(s: Strategy): "estimate" | "verified" {
  const parts = Object.values(s.components);
  const allChecked = parts.length > 0 && parts.every((c) => c.status === "ok" && c.validity === "valid");
  return allChecked && !s.incomplete ? "verified" : "estimate";
}

export function adviceLabel(kinds: Array<"estimate" | "verified">): string {
  return kinds.length > 0 && kinds.every((k) => k === "verified") ? RESULTS.verifiedAdvice : RESULTS.estimate;
}

const isGood = (c: Component) => c.status === "ok" && (c.score ?? 0) >= 70; // the engine's own "strong" line
const isChecked = (c: Component) => c.status === "ok" && c.validity === "valid";

/** Row "जाँचा हुआ सुझाव": only parts whose inputs are checked (validity "valid"). A high score on an unchecked
    input is not a confirmed fact, so it goes in the estimate row instead. Today the crop sheet is mostly
    unverified, so this row usually says that nothing is fully checked yet. */
export function goodLines(s: Strategy): string[] {
  const lines = Object.entries(s.components)
    .filter(([, c]) => isChecked(c))
    .map(([k, c]) => (isGood(c) ? GOOD_HI[k] : UNSURE_HI[k] ? `${UNSURE_HI[k]}: जाँचा हुआ है, पर इसमें कमी है` : ""))
    .filter(Boolean);
  return lines.length ? lines : [RESULTS.noneChecked];
}

/** Row "अनुमानित सुझाव": what looks good by the numbers but is not checked, the parts not checked or missing,
    and the area-scale weather. */
export function unknownLines(s: Strategy): string[] {
  const entries = Object.entries(s.components).filter(([, c]) => !isChecked(c));
  const estGood = entries.filter(([, c]) => isGood(c)).map(([k]) => GOOD_HI[k]).filter(Boolean);
  const unsure = entries.filter(([, c]) => !isGood(c)).map(([k]) => UNSURE_HI[k]).filter(Boolean);
  const lines: string[] = [];
  if (s.incomplete) lines.push("इस तरीके को पूरा आँका नहीं जा सका, क्योंकि कुछ जानकारी नहीं मिली।");
  estGood.forEach((l, i) => lines.push(i === 0 ? `${RESULTS.estimateGood}: ${l}` : l));
  if (unsure.length) lines.push(`इनके आँकड़े हमने अभी जाँचे नहीं हैं: ${unsure.join(", ")}।`);
  lines.push(AREA_SCALE_HI);
  return lines;
}

// The engine's risk sentences (engine/card.py), matched exactly, mapped to Hindi. Anything unmatched is skipped,
// and the general "ask an expert" line below always covers it.
const RISK_HI: [string, string][] = [
  ["In some years the monsoon starts after this crop's sowing window closes.", "कुछ सालों में मानसून इस फ़सल की बुवाई का समय निकलने के बाद आता है।"],
  ["The crop cycle can run into the pre-monsoon heat (after mid-March).", "फ़सल मार्च के बीच के बाद की गर्मी तक पहुँच सकती है।"],
  ["In some years no clear monsoon start was found in the weather record.", "कुछ सालों में मौसम के रिकॉर्ड में मानसून की साफ़ शुरुआत नहीं मिली।"],
  ["In late years the first crop can finish after the next crop's sowing window closes.", "देर वाले सालों में अगली फ़सल की बुवाई का समय निकल सकता है।"],
];

export function expertLines(s: Strategy): string[] {
  const lines = [RESULTS.suggestion];
  for (const risk of s.card.risks_for_local_review) {
    if (risk.includes("usually needs a sprayer")) lines.push("इस फ़सल में आम तौर पर स्प्रेयर चाहिए, और आपके पास नहीं है।");
    const hit = RISK_HI.find(([en]) => en === risk);
    if (hit) lines.push(hit[1]);
  }
  return lines;
}

const DISTRICT_HI: Record<string, string> = { akola: "अकोला", buldhana: "बुलढाणा", washim: "वाशिम" };

/** "वाशिम के पास": the district whose weather and satellite data stand in for the farm. */
export function nearestPhrase(result: Result): string | null {
  const d = result.location?.nearest;
  return d ? `${DISTRICT_HI[d] ?? d} के पास` : null;
}

/** Spoken when the results arrive: where, how many ways, which is best, the main caution. */
export function summarySpeech(list: Choice[], where?: string | null): string {
  const ranked = list.filter((c) => !c.strategy.incomplete);
  const top = ranked.filter((c) => c.top).map((c) => strategyName(c.strategy));
  const kind = adviceLabel(ranked.map((c) => adviceKind(c.strategy)));
  const parts = [...(where ? [`आपकी जगह ${where} है।`] : []), `आपके खेत के लिए ${list.length} तरीके देखे।`, `यह ${kind} है। ${kind === RESULTS.estimate ? RESULTS.estimateNote : ""}`.trim()];
  if (top.length === 1) parts.push(`सबसे अच्छा लगा: ${top[0]}।`);
  else if (top.length > 1) parts.push(`ये लगभग बराबर अच्छे लगे: ${top.join(" और ")}।`);
  else parts.push("इस बार कोई साफ़ सबसे अच्छा तरीका नहीं मिला।");
  parts.push(RESULTS.suggestion, RESULTS.disclaimer, "किसी तरीके को छुकर और जानिए। शब्द समझने के लिए समझिए छुइए।");
  return parts.join(" ");
}

// ---- Vulnerable seasons: heat, dry spells inside the monsoon, and frost (engine: season_risk) ----

const MONTH_HI = ["जून", "जुलाई", "अगस्त", "सितंबर", "अक्टूबर", "नवंबर", "दिसंबर", "जनवरी", "फ़रवरी", "मार्च", "अप्रैल", "मई"];

/** Short month names for the timeline under every year bar (June first). Machine-drafted, needs a native speaker's check. */
export const MONTH_HI_SHORT = ["जून", "जुला", "अग", "सित", "अक्टू", "नव", "दिस", "जन", "फ़र", "मार्च", "अप्रै", "मई"];

/** Re-order a January-first list to June-first, the order of the year bar. */
export const fromJune = <T,>(calendar: T[]): T[] => YEAR_ORDER.map((m) => calendar[m]);

/** Months (June-first positions) as Hindi text: "अप्रैल से मई और जून". */
export function monthRanges(positions: number[]): string {
  const parts: string[] = [];
  let i = 0;
  while (i < positions.length) {
    let j = i;
    while (j + 1 < positions.length && positions[j + 1] === positions[j] + 1) j++;
    parts.push(j > i ? `${MONTH_HI[positions[i]]} से ${MONTH_HI[positions[j]]}` : MONTH_HI[positions[i]]);
    i = j + 1;
  }
  return parts.join(" और ");
}

export type RiskRun = { start: number; length: number; level: number };

/** Consecutive risky months with the same level (2 = both datasets agree, 1 = they disagree). */
export function riskRuns(levels: number[]): RiskRun[] {
  const out: RiskRun[] = [];
  levels.forEach((level, i) => {
    if (!level) return;
    const last = out[out.length - 1];
    if (last && last.level === level && last.start + last.length === i) last.length++;
    else out.push({ start: i, length: 1, level });
  });
  return out;
}

/** When this strategy's crop is in the ground during a hot or dry-spell month, plus the frost finding. */
export function vulnerableLines(s: Strategy, risk: SeasonRisk): string[] {
  const inGround = yearBar(s.calendar, s.kind === "mixed").map((c) => c.length > 0);
  const heat = fromJune(risk.heat_level);
  const dry = fromJune(risk.dry_spell_level);
  const pick = (levels: number[]) => levels.map((l, i) => (l > 0 ? i : -1)).filter((i) => i >= 0);
  const lines: string[] = [];

  const hot = pick(heat);
  const hotIn = hot.filter((i) => inGround[i]);
  if (hot.length) {
    lines.push(
      hotIn.length
        ? `${monthRanges(hotIn)} में महीने के कई दिन 38 डिग्री से ज़्यादा गर्मी पड़ती है, और तब फ़सल खेत में रहती है।`
        : `गर्मी वाले महीनों (${monthRanges(hot)}) में इस तरीके की फ़सल खेत में नहीं रहती।`,
    );
    if (hotIn.some((i) => heat[i] === 1)) lines.push("कुछ महीनों की गर्मी के बारे में NASA और ERA5 के आँकड़े एकमत नहीं हैं, इसलिए वहाँ अंदाज़ा पक्का नहीं है।");
  }

  const dryMonths = pick(dry);
  const dryIn = dryMonths.filter((i) => inGround[i]);
  if (dryMonths.length) {
    lines.push(
      dryIn.length
        ? `${monthRanges(dryIn)} में बारिश के बीच दस दिन या उससे ज़्यादा लंबा सूखा अंतराल कई सालों में आता है, और तब फ़सल खेत में होती है।`
        : `बारिश के बीच सूखे अंतराल वाले महीनों (${monthRanges(dryMonths)}) में इस तरीके की फ़सल खेत में नहीं है।`,
    );
  }

  lines.push(
    risk.frost_days_per_year.power === 0 && risk.frost_days_per_year.era5 === 0
      ? "पाला: 1981 से 2025 के आँकड़ों में पाले की रात नहीं मिली।"
      : "पाला: आँकड़ों में पाले की कुछ रातें मिलीं। अपने इलाके के विशेषज्ञ से पूछिए।",
  );
  lines.push(AREA_SCALE_HI);
  return lines;
}

// ---- "समझिए": plain explanations of the terms the brief asks for, plus satellite versus ground ----

export type Explainer = { key: string; title: string; pics: PictogramId[]; text: string };

export function explainers(risk?: SeasonRisk): Explainer[] {
  const frostFound = risk && (risk.frost_days_per_year.power > 0 || risk.frost_days_per_year.era5 > 0);
  const frostData = !risk
    ? ""
    : frostFound
      ? " 1981 से 2025 के आँकड़ों में कुछ पाले की रातें मिलीं।"
      : " 1981 से 2025 के आँकड़ों में इन तीनों जगहों पर पाले की रात नहीं मिली।";
  return [
    {
      key: "et",
      title: "वाष्पोत्सर्जन",
      pics: ["et"],
      text: "पौधे की पत्तियों और मिट्टी से पानी भाप बनकर उड़ता है, इसे वाष्पोत्सर्जन कहते हैं। गर्मी, धूप और हवा में यह बढ़ता है। फ़सल को कितना पानी चाहिए, यह इसी से तय होता है। इसलिए गर्मी में फ़सल ज़्यादा प्यासी होती है।",
    },
    {
      key: "soil_moisture",
      title: "मिट्टी की नमी का फ़र्क",
      pics: ["soil_moisture"],
      text: "सामान्य साल के मुकाबले मिट्टी में नमी कितनी कम या ज़्यादा है, इसे मिट्टी की नमी का फ़र्क कहते हैं। नमी सामान्य से कम हो तो यह सूखे का संकेत है। हम NASA के आँकड़ों से जड़ों के पास की नमी देखते हैं।",
    },
    {
      key: "ndvi",
      title: "हरापन (NDVI)",
      pics: ["ndvi"],
      text: "उपग्रह से खेत की हरियाली मापी जाती है, इसे NDVI कहते हैं। हरापन ज़्यादा हो तो खेत में फ़सल है, कम हो तो खेत खाली या सूखा है। हम इससे देखते हैं कि साल में खेत कब खाली रहता है।",
    },
    {
      key: "frost",
      title: "पाला",
      pics: ["snow"],
      text: `बहुत ठंडी रात में पौधों पर बर्फ़ जम जाना पाला है। इससे फ़सल जल सकती है।${frostData} यह इलाके का आँकड़ा है, आपके खेत का नहीं।`,
    },
    {
      key: "balance",
      title: "पानी का हिसाब",
      pics: ["balance"],
      text: "बारिश से जितना पानी मिला और फ़सल ने जितना इस्तेमाल किया, इन दोनों का मिलान पानी का हिसाब है। बारिश फ़सल की ज़रूरत से कम हो तो कमी रहती है, और तब सिंचाई या नमी बचाने की ज़रूरत पड़ती है।",
    },
    {
      key: "satellite",
      title: "उपग्रह और ज़मीन",
      pics: ["satellite", "plus", "farmer"],
      text: "उपग्रह ऊपर से बड़े इलाके की तस्वीर देता है, पर आपका अपना खेत अलग से नहीं देखता। हमारा मौसम का आँकड़ा लगभग पचास किलोमीटर के इलाके का है, और हरापन ढाई सौ मीटर के टुकड़े का। आपका खेत असल में कैसा है, यह आप और आपके कृषि अधिकारी जानते हैं। इसलिए दोनों को साथ मिलाकर देखिए।",
    },
  ];
}
