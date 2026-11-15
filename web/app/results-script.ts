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
export type Result = {
  served: boolean;
  reason?: string;
  ranking: string[];
  tied_with_top: string[];
  strategies: Strategy[];
  site_evidence: Evidence[];
  location?: { nearest: string };
};

export const RESULTS = {
  loading: "रुकिए, तरीके देखे जा रहे हैं…",
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
  good: "अच्छी बातें",
  unknown: "जो हमें पता नहीं",
  expert: "विशेषज्ञ से पूछिए",
  noneGood: "इस तरीके में कोई ख़ास अच्छी बात नहीं मिली।",
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

/** Components the engine scored well (score 70 or more, as in the engine's own card). */
export function goodLines(s: Strategy): string[] {
  const lines = Object.entries(s.components)
    .filter(([, c]) => c.status === "ok" && (c.score ?? 0) >= 70)
    .map(([k]) => GOOD_HI[k])
    .filter(Boolean);
  return lines.length ? lines : [RESULTS.noneGood];
}

/** What the engine could not be sure of: missing inputs, unverified inputs or proxies, and the area-scale weather. */
export function unknownLines(s: Strategy): string[] {
  const unsure = Object.entries(s.components)
    .filter(([, c]) => c.status === "missing" || (c.status === "ok" && c.validity === "unverified"))
    .map(([k]) => UNSURE_HI[k])
    .filter(Boolean);
  const lines: string[] = [];
  if (s.incomplete) lines.push("इस तरीके को पूरा आँका नहीं जा सका, क्योंकि कुछ जानकारी नहीं मिली।");
  if (unsure.length) lines.push(`इनकी जानकारी पक्की नहीं है: ${unsure.join(", ")}।`);
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
  const parts = [...(where ? [`आपकी जगह ${where} है।`] : []), `आपके खेत के लिए ${list.length} तरीके देखे।`];
  if (top.length === 1) parts.push(`सबसे अच्छा लगा: ${top[0]}।`);
  else if (top.length > 1) parts.push(`ये लगभग बराबर अच्छे लगे: ${top.join(" और ")}।`);
  else parts.push("इस बार कोई साफ़ सबसे अच्छा तरीका नहीं मिला।");
  parts.push(RESULTS.suggestion, RESULTS.disclaimer, "किसी तरीके को छुकर और जानिए।");
  return parts.join(" ");
}
