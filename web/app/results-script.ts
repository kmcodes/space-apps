// What the results page says and shows, built only from the engine's structured output.
// Nothing here invents a number or a claim: every sentence is a template tied to an engine field
// (component status, calendar, risk text), and no scores are spoken or shown (docs/VOICE_APP_PLAN.md).
// All Hindi text was drafted by Claude and has NOT been reviewed by a native speaker. The English is a plain
// one-for-one version of the Hindi. Where the engine already writes an English sentence (the risk lines), English shows it as is.

import type { Lang } from "./lang";
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

const RESULTS_HI = {
  loading: "रुकिए, तरीके देखे जा रहे हैं…",
  waking: "इंजन जाग रहा है, इसमें एक मिनट लग सकता है। थोड़ा रुकिए…",
  error: "इंजन से जवाब नहीं मिला। फिर से कोशिश कीजिए।",
  retry: "फिर से कोशिश करें",
  title: "आपके खेत के लिए तरीके",
  where: "आपकी जगह",
  outOfArea: "इस जगह के लिए हमारे पास अभी जानकारी नहीं है। हम अभी अकोला, बुलढाणा और वाशिम के लिए काम करते हैं।",
  exampleHint: "उदाहरण देखने के लिए ज़िला छुइए।",
  exampleLabel: "उदाहरण (आपका खेत नहीं)",
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
  disclaimer: "यह परामर्श उपकरण किसानों और स्थानीय कृषि विशेषज्ञों की समझ का सहारा है, उसकी जगह नहीं।",
  suggestion: "यह सुझाव है, आदेश नहीं। कृषि विज्ञान केंद्र या कृषि अधिकारी से पूछिए।",
  // Spoken sentences and sentence pieces
  detailIntro: (name: string, kind: string, labels: string) => `${name}। यह ${kind} है। छुकर सुनिए: ${labels}।`,
  learnIntro: (title: string) => `${title} किसी तस्वीर को छुकर सुनिए।`,
  rowSpeech: (label: string, lines: string[]) => `${label}। ${lines.join(" ")}`,
  incompleteLine: "इस तरीके को पूरा आँका नहीं जा सका, क्योंकि कुछ जानकारी नहीं मिली।",
  checkedButWeak: (name: string) => `${name}: जाँचा हुआ है, पर इसमें कमी है`,
  notCheckedList: (names: string) => `इनके आँकड़े हमने अभी जाँचे नहीं हैं: ${names}।`,
  areaScale: "मौसम का डेटा पूरे इलाके का है, आपके अपने खेत का नहीं।",
  nearPhrase: (district: string) => `${district} के पास`,
  mixedName: (names: string[]) => `${names.join(" और ")} साथ-साथ`,
  thenName: (names: string[]) => names.join(", फिर "),
  sayWhere: (where: string) => `आपकी जगह ${where} है।`,
  sayExample: (district: string) => `ये ${district} के उदाहरण हैं, आपके अपने खेत के नहीं।`,
  sayCount: (n: number) => `आपके खेत के लिए ${n} तरीके देखे।`,
  sayKind: (kind: string) => `यह ${kind} है।`,
  sayBest: (name: string) => `सबसे अच्छा लगा: ${name}।`,
  sayTied: (names: string[]) => `ये लगभग बराबर अच्छे लगे: ${names.join(" और ")}।`,
  sayNoBest: "इस बार कोई साफ़ सबसे अच्छा तरीका नहीं मिला।",
  sayMore: "किसी तरीके को छुकर और जानिए। शब्द समझने के लिए समझिए छुइए।",
  sprayerRisk: "इस फ़सल में आम तौर पर स्प्रेयर चाहिए, और आपके पास नहीं है।",
};

const lowerAfterFirst = (name: string, i: number) => (i === 0 ? name : name.charAt(0).toLowerCase() + name.slice(1));

const RESULTS_EN: typeof RESULTS_HI = {
  loading: "Please wait, looking at the options…",
  waking: "The engine is waking up. This can take a minute. Please wait…",
  error: "No answer from the engine. Please try again.",
  retry: "Try again",
  title: "Options for your farm",
  where: "Your location",
  outOfArea: "We do not have information for this place yet. For now we work only for Akola, Buldhana and Washim.",
  exampleHint: "Touch a district to see an example.",
  exampleLabel: "Example (not your farm)",
  replay: "Listen again",
  again: "New call",
  back: "Back",
  current: "What you do now",
  notRanked: "Information incomplete",
  tapHint: "Touch an option",
  forExperts: "For experts: sources and checks",
  good: "Checked advice",
  unknown: "Estimated advice",
  estimate: "Estimated advice",
  verifiedAdvice: "Checked advice",
  estimateNote: "These are estimates from the numbers, not certain facts.",
  noneChecked: "Nothing about this option is fully checked yet.",
  estimateGood: "Looks good by the numbers, but not checked yet",
  expert: "Ask an expert",
  vulnerable: "Sensitive times",
  learn: "Explained",
  learnTitle: "What do these mean?",
  kharif: "Kharif",
  rabi: "Rabi",
  summer: "Summer",
  disclaimer: "This tool is a support for the understanding of farmers and local agricultural experts. It does not replace it.",
  suggestion: "This is a suggestion, not an order. Ask the Krishi Vigyan Kendra or an agriculture officer.",
  detailIntro: (name, kind, labels) => `${name}. This is ${kind.toLowerCase()}. Touch to listen: ${labels}.`,
  learnIntro: (title) => `${title} Touch a picture to listen.`,
  rowSpeech: (label, lines) => `${label}. ${lines.join(" ")}`,
  incompleteLine: "This option could not be fully assessed, because some information was missing.",
  checkedButWeak: (name) => `${name}: checked, but this is weak`,
  notCheckedList: (names) => `We have not checked the figures for these yet: ${names}.`,
  areaScale: "The weather data is for the whole area, not for your own field.",
  nearPhrase: (district) => `near ${district}`,
  // Only the first crop starts with a capital: "Soybean, then sorghum (jowar)".
  mixedName: (names) => `${names.map(lowerAfterFirst).join(" and ")} together`,
  thenName: (names) => names.map(lowerAfterFirst).join(", then "),
  sayWhere: (where) => `Your location is ${where}.`,
  sayExample: (district) => `These are examples for ${district}, not for your own farm.`,
  sayCount: (n) => `I looked at ${n} options for your farm.`,
  sayKind: (kind) => `This is ${kind.toLowerCase()}.`,
  sayBest: (name) => `Looks best: ${name}.`,
  sayTied: (names) => `These look about equally good: ${names.join(" and ")}.`,
  sayNoBest: "This time there is no clear best option.",
  sayMore: "Touch an option to learn more. To understand the words, touch Explained.",
  sprayerRisk: "This crop usually needs a sprayer, and you do not have one.",
};

/** The text of the results screens in this language. */
export const resultsText = (lang: Lang) => (lang === "en" ? RESULTS_EN : RESULTS_HI);
export type ResultsText = ReturnType<typeof resultsText>;

const CROP_NAMES: Record<Lang, Record<string, string>> = {
  hi: {
    soybean: "सोयाबीन",
    chickpea: "चना",
    cotton: "कपास",
    pigeon_pea: "तुअर",
    sorghum_rabi: "ज्वार",
    sunn_hemp: "सनई",
    horse_gram: "कुलथी",
    fallow: "खाली खेत",
  },
  en: {
    soybean: "Soybean",
    chickpea: "Chickpea",
    cotton: "Cotton",
    pigeon_pea: "Pigeon pea (tur)",
    sorghum_rabi: "Sorghum (jowar)",
    sunn_hemp: "Sunn hemp",
    horse_gram: "Horse gram",
    fallow: "Empty field",
  },
};

const CROP_PIC: Record<string, PictogramId> = {
  soybean: "soybean",
  chickpea: "chickpea",
  cotton: "cotton",
  pigeon_pea: "pigeon_pea",
  sorghum_rabi: "sorghum",
  fallow: "bare",
};

const cropName = (c: string, lang: Lang) => CROP_NAMES[lang][c] ?? c;
const cropPic = (c: string): PictogramId => CROP_PIC[c] ?? "bare";

/** "सोयाबीन, फिर चना" / "कपास और तुअर साथ-साथ" / "कपास", or in English "Soybean, then chickpea" / "Cotton and Pigeon pea together". */
export function strategyName(s: Strategy, lang: Lang): string {
  const names = s.crops.map((c) => cropName(c, lang));
  const t = resultsText(lang);
  return s.kind === "mixed" ? t.mixedName(names) : t.thenName(names);
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

// ---- The picture rows on a detail screen ----

const GOOD: Record<Lang, Record<string, string>> = {
  hi: {
    water_fit: "बारिश फ़सल के पानी की ज़रूरत से अच्छा मेल खाती है",
    timing_fit: "बुवाई और कटाई का समय ठीक बैठता है",
    bare_days: "खेत ज़्यादा दिन फ़सल से ढका रहता है",
    nitrogen: "मिट्टी में नाइट्रोजन बढ़ती है, खाद कम लगती है",
    forage: "जानवरों के लिए चारा मिलता है",
    market: "बाज़ार भाव का संकेत अच्छा है",
  },
  en: {
    water_fit: "Rain matches the crop's water need well",
    timing_fit: "Sowing and harvest timing fits",
    bare_days: "The field stays covered with a crop for more days",
    nitrogen: "Nitrogen in the soil increases, so less fertiliser is needed",
    forage: "Gives fodder for animals",
    market: "The market price signal is good",
  },
};

const UNSURE: Record<Lang, Record<string, string>> = {
  hi: {
    water_fit: "पानी का मेल",
    timing_fit: "बुवाई-कटाई का समय",
    bare_days: "खेत कितने दिन ढका रहेगा",
    nitrogen: "नाइट्रोजन का फ़ायदा",
    forage: "चारे की मात्रा",
    market: "बाज़ार भाव",
  },
  en: {
    water_fit: "water match",
    timing_fit: "sowing and harvest timing",
    bare_days: "how many days the field stays covered",
    nitrogen: "nitrogen benefit",
    forage: "amount of fodder",
    market: "market price",
  },
};

export const areaScale = (lang: Lang) => resultsText(lang).areaScale;

/** "Verified" only when every part of the score is complete and its inputs are checked (validity "valid").
    Any missing, degraded or unverified input makes it an estimate. Today the crop sheet is mostly unverified, so it is an estimate. */
export function adviceKind(s: Strategy): "estimate" | "verified" {
  const parts = Object.values(s.components);
  const allChecked = parts.length > 0 && parts.every((c) => c.status === "ok" && c.validity === "valid");
  return allChecked && !s.incomplete ? "verified" : "estimate";
}

export function adviceLabel(kinds: Array<"estimate" | "verified">, lang: Lang): string {
  const t = resultsText(lang);
  return kinds.length > 0 && kinds.every((k) => k === "verified") ? t.verifiedAdvice : t.estimate;
}

const isGood = (c: Component) => c.status === "ok" && (c.score ?? 0) >= 70; // the engine's own "strong" line
const isChecked = (c: Component) => c.status === "ok" && c.validity === "valid";

/** Row "checked advice" (जाँचा हुआ सुझाव): only parts whose inputs are checked (validity "valid"). A high score on an
    unchecked input is not a confirmed fact, so it goes in the estimate row instead. Today the crop sheet is mostly
    unverified, so this row usually says that nothing is fully checked yet. */
export function goodLines(s: Strategy, lang: Lang): string[] {
  const t = resultsText(lang);
  const lines = Object.entries(s.components)
    .filter(([, c]) => isChecked(c))
    .map(([k, c]) => (isGood(c) ? GOOD[lang][k] : UNSURE[lang][k] ? t.checkedButWeak(UNSURE[lang][k]) : ""))
    .filter(Boolean);
  return lines.length ? lines : [t.noneChecked];
}

/** Row "estimated advice" (अनुमानित सुझाव): what looks good by the numbers but is not checked, the parts not checked
    or missing, and the area-scale weather. */
export function unknownLines(s: Strategy, lang: Lang): string[] {
  const t = resultsText(lang);
  const entries = Object.entries(s.components).filter(([, c]) => !isChecked(c));
  const estGood = entries.filter(([, c]) => isGood(c)).map(([k]) => GOOD[lang][k]).filter(Boolean);
  const unsure = entries.filter(([, c]) => !isGood(c)).map(([k]) => UNSURE[lang][k]).filter(Boolean);
  const lines: string[] = [];
  if (s.incomplete) lines.push(t.incompleteLine);
  estGood.forEach((l, i) => lines.push(i === 0 ? `${t.estimateGood}: ${l}` : l));
  if (unsure.length) lines.push(t.notCheckedList(unsure.join(", ")));
  lines.push(t.areaScale);
  return lines;
}

// The engine's risk sentences (engine/card.py), matched exactly, mapped to Hindi. Anything unmatched is skipped,
// and the general "ask an expert" line below always covers it. In English the engine's own sentence is shown as it is.
const RISK_HI: [string, string][] = [
  ["In some years the monsoon starts after this crop's sowing window closes.", "कुछ सालों में मानसून इस फ़सल की बुवाई का समय निकलने के बाद आता है।"],
  ["The crop cycle can run into the pre-monsoon heat (after mid-March).", "फ़सल मार्च के बीच के बाद की गर्मी तक पहुँच सकती है।"],
  ["In some years no clear monsoon start was found in the weather record.", "कुछ सालों में मौसम के रिकॉर्ड में मानसून की साफ़ शुरुआत नहीं मिली।"],
  ["In late years the first crop can finish after the next crop's sowing window closes.", "देर वाले सालों में अगली फ़सल की बुवाई का समय निकल सकता है।"],
];

export function expertLines(s: Strategy, lang: Lang): string[] {
  const t = resultsText(lang);
  const lines = [t.suggestion];
  for (const risk of s.card.risks_for_local_review) {
    if (lang === "en") {
      lines.push(risk);
      continue;
    }
    if (risk.includes("usually needs a sprayer")) lines.push(t.sprayerRisk);
    const hit = RISK_HI.find(([en]) => en === risk);
    if (hit) lines.push(hit[1]);
  }
  return lines;
}

const DISTRICTS: Record<Lang, Record<string, string>> = {
  hi: { akola: "अकोला", buldhana: "बुलढाणा", washim: "वाशिम" },
  en: { akola: "Akola", buldhana: "Buldhana", washim: "Washim" },
};

/** The districts the farmer can pick when their own place is outside our area. */
export const DISTRICT_IDS = ["akola", "buldhana", "washim"] as const;
export const districtLabel = (id: string, lang: Lang) => DISTRICTS[lang][id] ?? id;

/** "वाशिम" / "Washim": the district the results are for. */
export function districtName(result: Result, lang: Lang): string | null {
  const d = result.location?.nearest;
  return d ? districtLabel(d, lang) : null;
}

/** "वाशिम के पास" / "near Washim": the district whose weather and satellite data stand in for the farm. */
export function nearestPhrase(result: Result, lang: Lang): string | null {
  const d = result.location?.nearest;
  return d ? resultsText(lang).nearPhrase(DISTRICTS[lang][d] ?? d) : null;
}

/** Spoken when the results arrive: where, how many ways, which is best, the main caution. */
/** `exampleFor` is the district name when the farmer is outside our area and picked a district: say so, not "your location". */
export function summarySpeech(list: Choice[], where: string | null | undefined, lang: Lang, exampleFor?: string | null): string {
  const t = resultsText(lang);
  const ranked = list.filter((c) => !c.strategy.incomplete);
  const top = ranked.filter((c) => c.top).map((c) => strategyName(c.strategy, lang));
  const kind = adviceLabel(ranked.map((c) => adviceKind(c.strategy)), lang);
  const place = exampleFor ? [t.sayExample(exampleFor)] : where ? [t.sayWhere(where)] : [];
  const parts = [...place, t.sayCount(list.length), `${t.sayKind(kind)} ${kind === t.estimate ? t.estimateNote : ""}`.trim()];
  if (top.length === 1) parts.push(t.sayBest(top[0]));
  else if (top.length > 1) parts.push(t.sayTied(top));
  else parts.push(t.sayNoBest);
  parts.push(t.suggestion, t.disclaimer, t.sayMore);
  return parts.join(" ");
}

// ---- Vulnerable seasons: heat, dry spells inside the monsoon, and frost (engine: season_risk) ----

const MONTHS: Record<Lang, string[]> = {
  hi: ["जून", "जुलाई", "अगस्त", "सितंबर", "अक्टूबर", "नवंबर", "दिसंबर", "जनवरी", "फ़रवरी", "मार्च", "अप्रैल", "मई"],
  en: ["June", "July", "August", "September", "October", "November", "December", "January", "February", "March", "April", "May"],
};

/** Short month names for the timeline under every year bar (June first). Machine-drafted, needs a native speaker's check. */
const MONTHS_SHORT: Record<Lang, string[]> = {
  hi: ["जून", "जुला", "अग", "सित", "अक्टू", "नव", "दिस", "जन", "फ़र", "मार्च", "अप्रै", "मई"],
  en: ["Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec", "Jan", "Feb", "Mar", "Apr", "May"],
};
export const monthShort = (lang: Lang) => MONTHS_SHORT[lang];

/** Re-order a January-first list to June-first, the order of the year bar. */
export const fromJune = <T,>(calendar: T[]): T[] => YEAR_ORDER.map((m) => calendar[m]);

/** Months (June-first positions) as text: "अप्रैल से मई और जून" / "April to May and June". */
export function monthRanges(positions: number[], lang: Lang): string {
  const names = MONTHS[lang];
  const to = lang === "en" ? "to" : "से";
  const and = lang === "en" ? " and " : " और ";
  const parts: string[] = [];
  let i = 0;
  while (i < positions.length) {
    let j = i;
    while (j + 1 < positions.length && positions[j + 1] === positions[j] + 1) j++;
    parts.push(j > i ? `${names[positions[i]]} ${to} ${names[positions[j]]}` : names[positions[i]]);
    i = j + 1;
  }
  return parts.join(and);
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

const VULNERABLE: Record<
  Lang,
  {
    hotIn: (months: string) => string;
    hotOut: (months: string) => string;
    hotDisagree: string;
    dryIn: (months: string) => string;
    dryOut: (months: string) => string;
    frostNone: string;
    frostSome: string;
  }
> = {
  hi: {
    hotIn: (m) => `${m} में महीने के कई दिन 38 डिग्री से ज़्यादा गर्मी पड़ती है, और तब फ़सल खेत में रहती है।`,
    hotOut: (m) => `गर्मी वाले महीनों (${m}) में इस तरीके की फ़सल खेत में नहीं रहती।`,
    hotDisagree: "कुछ महीनों की गर्मी के बारे में NASA और ERA5 के आँकड़े एकमत नहीं हैं, इसलिए वहाँ अंदाज़ा पक्का नहीं है।",
    dryIn: (m) => `${m} में बारिश के बीच दस दिन या उससे ज़्यादा लंबा सूखा अंतराल कई सालों में आता है, और तब फ़सल खेत में होती है।`,
    dryOut: (m) => `बारिश के बीच सूखे अंतराल वाले महीनों (${m}) में इस तरीके की फ़सल खेत में नहीं है।`,
    frostNone: "पाला: 1981 से 2025 के आँकड़ों में पाले की रात नहीं मिली।",
    frostSome: "पाला: आँकड़ों में पाले की कुछ रातें मिलीं। अपने इलाके के विशेषज्ञ से पूछिए।",
  },
  en: {
    hotIn: (m) => `In ${m}, many days of the month are hotter than 38 degrees, and the crop is in the field then.`,
    hotOut: (m) => `The crop of this option is not in the field in the hot months (${m}).`,
    hotDisagree: "For some months, the NASA and ERA5 data do not agree about the heat, so the estimate there is less certain.",
    dryIn: (m) => `In ${m}, in many years there is a dry gap of ten days or more between rains, and the crop is in the field then.`,
    dryOut: (m) => `The crop of this option is not in the field in the months with dry gaps between rains (${m}).`,
    frostNone: "Frost: no frost night was found in the 1981 to 2025 data.",
    frostSome: "Frost: some frost nights were found in the data. Ask an expert in your area.",
  },
};

/** When this strategy's crop is in the ground during a hot or dry-spell month, plus the frost finding. */
export function vulnerableLines(s: Strategy, risk: SeasonRisk, lang: Lang): string[] {
  const v = VULNERABLE[lang];
  const inGround = yearBar(s.calendar, s.kind === "mixed").map((c) => c.length > 0);
  const heat = fromJune(risk.heat_level);
  const dry = fromJune(risk.dry_spell_level);
  const pick = (levels: number[]) => levels.map((l, i) => (l > 0 ? i : -1)).filter((i) => i >= 0);
  const lines: string[] = [];

  const hot = pick(heat);
  const hotIn = hot.filter((i) => inGround[i]);
  if (hot.length) {
    lines.push(hotIn.length ? v.hotIn(monthRanges(hotIn, lang)) : v.hotOut(monthRanges(hot, lang)));
    if (hotIn.some((i) => heat[i] === 1)) lines.push(v.hotDisagree);
  }

  const dryMonths = pick(dry);
  const dryIn = dryMonths.filter((i) => inGround[i]);
  if (dryMonths.length) {
    lines.push(dryIn.length ? v.dryIn(monthRanges(dryIn, lang)) : v.dryOut(monthRanges(dryMonths, lang)));
  }

  lines.push(risk.frost_days_per_year.power === 0 && risk.frost_days_per_year.era5 === 0 ? v.frostNone : v.frostSome);
  lines.push(resultsText(lang).areaScale);
  return lines;
}

// ---- "समझिए" / "Explained": plain explanations of the terms the brief asks for, plus satellite versus ground ----

export type Explainer = { key: string; title: string; pics: PictogramId[]; text: string };

const EXPLAINERS: Record<Lang, Record<"et" | "soil_moisture" | "ndvi" | "balance" | "satellite" | "other_crops", { title: string; text: string }> & { frostTitle: string; frost: (data: string) => string; frostFound: string; frostNone: string }> = {
  hi: {
    et: {
      title: "वाष्पोत्सर्जन",
      text: "पौधे की पत्तियों और मिट्टी से पानी भाप बनकर उड़ता है, इसे वाष्पोत्सर्जन कहते हैं। गर्मी, धूप और हवा में यह बढ़ता है। फ़सल को कितना पानी चाहिए, यह इसी से तय होता है। इसलिए गर्मी में फ़सल ज़्यादा प्यासी होती है।",
    },
    soil_moisture: {
      title: "मिट्टी की नमी का फ़र्क",
      text: "सामान्य साल के मुकाबले मिट्टी में नमी कितनी कम या ज़्यादा है, इसे मिट्टी की नमी का फ़र्क कहते हैं। नमी सामान्य से कम हो तो यह सूखे का संकेत है। हम NASA के आँकड़ों से जड़ों के पास की नमी देखते हैं।",
    },
    ndvi: {
      title: "हरापन (NDVI)",
      text: "उपग्रह से खेत की हरियाली मापी जाती है, इसे NDVI कहते हैं। हरापन ज़्यादा हो तो खेत में फ़सल है, कम हो तो खेत खाली या सूखा है। हम इससे देखते हैं कि साल में खेत कब खाली रहता है।",
    },
    balance: {
      title: "पानी का हिसाब",
      text: "बारिश से जितना पानी मिला और फ़सल ने जितना इस्तेमाल किया, इन दोनों का मिलान पानी का हिसाब है। बारिश फ़सल की ज़रूरत से कम हो तो कमी रहती है, और तब सिंचाई या नमी बचाने की ज़रूरत पड़ती है।",
    },
    satellite: {
      title: "उपग्रह और ज़मीन",
      text: "उपग्रह ऊपर से बड़े इलाके की तस्वीर देता है, पर आपका अपना खेत अलग से नहीं देखता। हमारा मौसम का आँकड़ा लगभग पचास किलोमीटर के इलाके का है, और हरापन ढाई सौ मीटर के टुकड़े का। आपका खेत असल में कैसा है, यह आप और आपके कृषि अधिकारी जानते हैं। इसलिए दोनों को साथ मिलाकर देखिए।",
    },
    other_crops: {
      title: "दूसरी फ़सलें",
      text: "सोयाबीन के बाद ज्वार के अलावा हमने सनई और कुलथी भी जाँचीं। इनके बारे में भरोसेमंद जानकारी अभी कम है, जैसे बुवाई का सही समय और मंडी के दाम, इसलिए इन्हें अभी विकल्प के रूप में नहीं दिखाते। जानकारी पक्की होने पर इन्हें जोड़ेंगे। अपने कृषि अधिकारी से इनके बारे में पूछ सकते हैं।",
    },
    frostTitle: "पाला",
    frost: (data) => `बहुत ठंडी रात में पौधों पर बर्फ़ जम जाना पाला है। इससे फ़सल जल सकती है।${data} यह इलाके का आँकड़ा है, आपके खेत का नहीं।`,
    frostFound: " 1981 से 2025 के आँकड़ों में कुछ पाले की रातें मिलीं।",
    frostNone: " 1981 से 2025 के आँकड़ों में इन तीनों जगहों पर पाले की रात नहीं मिली।",
  },
  en: {
    et: {
      title: "Evapotranspiration",
      text: "Water evaporates from the leaves of plants and from the soil. This loss is called evapotranspiration. It rises with heat, sunshine and wind. It decides how much water a crop needs. That is why a crop is thirstier in hot weather.",
    },
    soil_moisture: {
      title: "Soil moisture anomaly",
      text: "How much more or less moisture the soil has than in a normal year is called the soil moisture anomaly. Moisture below normal is a sign of drought. We use NASA data to look at the moisture near the roots.",
    },
    ndvi: {
      title: "Greenness (NDVI)",
      text: "A satellite measures how green a field is. This is called NDVI. High greenness means there is a crop in the field. Low greenness means the field is empty or dry. We use it to see when the field is empty during the year.",
    },
    balance: {
      title: "Water balance",
      text: "Matching the water that the rain gave against the water that the crop used is the water balance. When the rain is less than the crop needs, there is a shortage, and then irrigation or saving moisture is needed.",
    },
    satellite: {
      title: "Satellite and ground",
      text: "A satellite gives a picture of a large area from above, but it does not see your own field separately. Our weather figure is for an area of about fifty kilometres, and the greenness is for a patch of two hundred and fifty metres. How your field really is, you and your agriculture officer know. So look at both together.",
    },
    other_crops: {
      title: "Other crops",
      text: "Besides sorghum after soybean, we also looked at sunn hemp and horse gram. There is not yet enough reliable information about them, such as the right sowing time and mandi prices, so we do not show them as options for now. We will add them when the information is firmer. You can ask your agriculture officer about them.",
    },
    frostTitle: "Frost",
    frost: (data) => `On a very cold night, ice can form on plants. This is frost. It can burn a crop.${data} This is a figure for the area, not for your field.`,
    frostFound: " Some frost nights were found in the 1981 to 2025 data.",
    frostNone: " No frost night was found at these three places in the 1981 to 2025 data.",
  },
};

export function explainers(risk: SeasonRisk | undefined, lang: Lang): Explainer[] {
  const e = EXPLAINERS[lang];
  const frostFound = risk && (risk.frost_days_per_year.power > 0 || risk.frost_days_per_year.era5 > 0);
  const frostData = !risk ? "" : frostFound ? e.frostFound : e.frostNone;
  return [
    { key: "et", title: e.et.title, pics: ["et"], text: e.et.text },
    { key: "soil_moisture", title: e.soil_moisture.title, pics: ["soil_moisture"], text: e.soil_moisture.text },
    { key: "ndvi", title: e.ndvi.title, pics: ["ndvi"], text: e.ndvi.text },
    { key: "frost", title: e.frostTitle, pics: ["snow"], text: e.frost(frostData) },
    { key: "balance", title: e.balance.title, pics: ["balance"], text: e.balance.text },
    { key: "satellite", title: e.satellite.title, pics: ["satellite", "plus", "farmer"], text: e.satellite.text },
    // Sunn hemp and horse gram are scored by the engine (S3 variants) but not shown as options: their data is too thin.
    { key: "other_crops", title: e.other_crops.title, pics: ["unknown"], text: e.other_crops.text },
  ];
}
