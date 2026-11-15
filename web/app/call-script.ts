// The Hindi script for the voice call, and the matching of what the farmer says to an answer.
import type { PictogramId } from "./pictograms";

// All Hindi text here was drafted by Claude and has NOT been reviewed by a native speaker.
// Marathi will be a second file with the same shape, after a native speaker reviews it.

export type Option = {
  value: string; // the value the engine expects (see api/main.py)
  label: string; // shown and read aloud
  pics: PictogramId[]; // pictures shown on the tile, left to right (the farmers cannot read)
  words: string[]; // spoken words that pick this option
  weak?: string[]; // only used when no strong word matched (shared words like "soybean")
};

export type Step = {
  id: "location" | "rotation" | "water_source" | "priority1" | "priority2" | "water_level" | "equipment" | "market";
  question: string;
  options: (answers: Answers) => Option[];
};

export type Answers = Partial<Record<Step["id"], string>>;

export const SCRIPT = {
  title: "फ़ील्ड शिफ़्ट",
  tagline: "खेत के लिए सलाह। बस एक बार छुइए और बोलिए।",
  start: "सलाह के लिए छुइए",
  useForm: "या फ़ॉर्म भरकर देखें",
  end: "बातचीत ख़त्म",
  again: "नई बातचीत",
  back: "वापस",
  greeting: "नमस्ते। मैं आपके खेत के लिए कुछ सवाल पूछूँगी। बोलकर जवाब दीजिए, या तस्वीर छू दीजिए।",
  notUnderstood: "माफ़ कीजिए, समझ नहीं आया। फिर से बोलिए, या तस्वीर छुइए।",
  closing: "धन्यवाद। आपके जवाब मिल गए। अब मैं नतीजे दिखाती हूँ। बातचीत पूरी हुई।",
  speaking: "सुनिए…",
  listening: "आपकी बारी — बोलिए",
  tapOnly: "तस्वीर छुइए",
  noMic: "माइक्रोफ़ोन की इजाज़त नहीं मिली। तस्वीर छुकर जवाब दीजिए।",
};

const LOCATIONS: Option[] = [
  { value: "akola", label: "अकोला", pics: ["pin"], words: ["अकोला", "akola"] },
  { value: "buldhana", label: "बुलढाणा", pics: ["pin"], words: ["बुलढाणा", "बुलढाना", "बुलडाना", "बुलढ़ाणा", "buldhana", "buldana"] },
  { value: "washim", label: "वाशिम", pics: ["pin"], words: ["वाशिम", "वाशीम", "washim", "vashim"] },
];

const ROTATIONS: Option[] = [
  { value: "soybean_fallow", label: "सोयाबीन, फिर खेत खाली", pics: ["soybean", "then", "bare"], words: ["खाली", "fallow", "empty"], weak: ["सोयाबीन", "soybean"] },
  { value: "cotton", label: "कपास", pics: ["cotton"], words: ["कपास", "cotton"] },
  { value: "soybean_chickpea", label: "सोयाबीन, फिर चना", pics: ["soybean", "then", "chickpea"], words: ["चना", "चने", "chana", "chickpea"] },
];

const WATER_SOURCES: Option[] = [
  { value: "rainfed", label: "सिर्फ़ बारिश", pics: ["rain"], words: ["बारिश", "बरसात", "वर्षा", "rain"] },
  { value: "well", label: "कुआँ या बोरवेल", pics: ["well"], words: ["कुआँ", "कुआं", "बोरवेल", "borewell", "well"] },
  { value: "canal_tank", label: "नहर या तालाब", pics: ["canal"], words: ["नहर", "तालाब", "canal", "tank"] },
];

const PRIORITIES: Option[] = [
  { value: "water_saving", label: "पानी बचाना", pics: ["water_saving"], words: ["पानी", "water"] },
  { value: "forage", label: "जानवरों का चारा", pics: ["forage"], words: ["चारा", "जानवर", "fodder", "forage"] },
  { value: "nitrogen", label: "कम खाद", pics: ["nitrogen"], words: ["खाद", "यूरिया", "नाइट्रोजन", "fertiliser", "fertilizer"] },
  { value: "erosion", label: "मिट्टी का बहना रोकना", pics: ["erosion"], words: ["कटाव", "बहना", "बह", "बहती", "बहाव", "erosion"] },
  { value: "organic_matter", label: "मिट्टी की सेहत", pics: ["organic_matter"], words: ["सेहत", "जैविक", "organic"], weak: ["मिट्टी"] },
  { value: "market_income", label: "अच्छा दाम", pics: ["market_income"], words: ["दाम", "भाव", "कीमत", "आमदनी", "income", "price"] },
];

const NONE: Option = { value: "", label: "कोई नहीं", pics: ["none"], words: ["नहीं", "नही", "कोई नहीं", "none", "no"] };

const LEVELS: Option[] = [
  { value: "low", label: "कम", pics: ["level1"], words: ["कम", "low"] },
  { value: "medium", label: "ठीक-ठाक", pics: ["level2"], words: ["ठीक", "मध्यम", "मीडियम", "medium"] },
  { value: "high", label: "ज़्यादा", pics: ["level3"], words: ["ज़्यादा", "ज्यादा", "अधिक", "high"] },
];

const EQUIPMENT: Option[] = [
  { value: "sprayer", label: "हाँ", pics: ["yes"], words: ["हाँ", "हां", "हा", "जी", "है", "yes"] },
  { value: "basic", label: "नहीं", pics: ["no"], words: ["नहीं", "नही", "ना", "no"] },
];

const MARKETS: Option[] = [
  { value: "mandi", label: "मंडी में", pics: ["mandi"], words: ["मंडी", "mandi"] },
  { value: "buyer", label: "पास के ख़रीदार को", pics: ["buyer"], words: ["ख़रीदार", "खरीदार", "व्यापारी", "buyer"] },
  { value: "own_use", label: "अपने इस्तेमाल के लिए", pics: ["own_use"], words: ["अपने", "घर", "खुद", "own"] },
];

export const STEPS: Step[] = [
  { id: "location", question: "आपका खेत किस ज़िले में है?", options: () => LOCATIONS },
  { id: "rotation", question: "अभी आप खेत में क्या बोते हैं?", options: () => ROTATIONS },
  { id: "water_source", question: "आपके खेत में पानी कहाँ से आता है?", options: () => WATER_SOURCES },
  { id: "priority1", question: "आपके लिए सबसे ज़रूरी क्या है?", options: () => PRIORITIES },
  {
    id: "priority2",
    question: "कोई दूसरी ज़रूरी बात? नहीं हो तो नहीं बोलिए।",
    options: (a) => [...PRIORITIES.filter((p) => p.value !== a.priority1), NONE],
  },
  { id: "water_level", question: "खेत के लिए पानी कितना मिल सकता है?", options: () => LEVELS },
  { id: "equipment", question: "क्या आपके पास स्प्रेयर या बुवाई की मशीन है?", options: () => EQUIPMENT },
  { id: "market", question: "आप अपनी फ़सल कहाँ बेचते हैं?", options: () => MARKETS },
];

const ORDINALS: string[][] = [
  ["पहला", "पहली", "एक", "1", "one", "first"],
  ["दूसरा", "दूसरी", "दो", "2", "two", "second"],
  ["तीसरा", "तीसरी", "तीन", "3", "three", "third"],
  ["चौथा", "चौथी", "चार", "4", "four", "fourth"],
];

// A word of 1-2 characters must be a whole word ("ना", "no"); longer words can sit inside a word.
function hits(tokens: string[], text: string, word: string): boolean {
  return word.length <= 2 ? tokens.includes(word) : text.includes(word);
}

/** What did the farmer pick? The longest matching spoken word wins; null if nothing matched. */
export function matchOption(transcript: string, options: Option[]): Option | null {
  const text = transcript.toLowerCase().replace(/[।.,?!]/g, " ").replace(/\s+/g, " ").trim();
  const tokens = text.split(" ");
  const best = (pick: (o: Option) => string[] | undefined) => {
    let found: Option | null = null;
    let len = 0;
    for (const o of options) {
      for (const w of pick(o) ?? []) {
        if (hits(tokens, text, w) && w.length > len) {
          found = o;
          len = w.length;
        }
      }
    }
    return found;
  };
  const byWord = best((o) => o.words) ?? best((o) => o.weak);
  if (byWord) return byWord;
  const ordinal = ORDINALS.findIndex((set) => set.some((w) => tokens.includes(w)));
  return ordinal >= 0 && ordinal < options.length ? options[ordinal] : null;
}
