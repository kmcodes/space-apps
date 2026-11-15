// The script for the voice call in Hindi and English, and the matching of what the farmer says to an answer.
import type { L, Lang } from "./lang";
import type { PictogramId } from "./pictograms";

// All Hindi text here was drafted by Claude and has NOT been reviewed by a native speaker. The English is a
// plain one-for-one version of the Hindi. Marathi will be a third language with the same shape, after a native speaker reviews it.

export type Option = {
  value: string; // the value the engine expects (see api/main.py)
  label: L; // shown and read aloud, in each language
  pics: PictogramId[]; // pictures shown on the tile, left to right (the farmers cannot read)
  words: string[]; // spoken words that pick this option (Hindi and English together: farmers mix them)
  weak?: string[]; // only used when no strong word matched (shared words like "soybean")
};

export type Step = {
  id: "farm" | "location" | "rotation" | "water_source" | "priority1" | "priority2" | "water_level" | "equipment" | "market";
  question: L;
  options: (answers: Answers) => Option[];
};

export type Answers = Partial<Record<Step["id"], string>>;

const SCRIPT_HI = {
  title: "फ़ील्ड एड",
  greeting_title: "नमस्ते",
  taglineLead: "आपके लिए खेती के सुझाव",
  taglineRest: "नीचे दिए गए बटनों में से अपनी पसंद चुनिए।", // one line where it fits, wraps on narrow phones
  start: "बोलने के लिए दबाइए",
  useForm: "फ़ॉर्म भरने के लिए दबाइए",
  end: "बातचीत ख़त्म",
  again: "नई बातचीत",
  back: "वापस",
  greeting: "नमस्ते। मैं आपके खेत के लिए कुछ सवाल पूछूँगी। बोलकर जवाब दीजिए, या तस्वीर छू दीजिए।",
  notUnderstood: "माफ़ कीजिए, समझ नहीं आया। फिर से बोलिए, या तस्वीर छुइए।",
  closing: "धन्यवाद। आपके जवाब मिल गए। अब मैं नतीजे दिखाती हूँ। बातचीत पूरी हुई।",
  speaking: "सुनिए…",
  listening: "आपकी बारी — बोलिए",
  tapOnly: "तस्वीर छुइए",
  mapNote: "लाल निशान आपके फ़ोन की जगह है।",
  mapLoading: "नक्शा खुल रहा है… रुकिए।",
  noMic: "माइक्रोफ़ोन की इजाज़त नहीं मिली। तस्वीर छुकर जवाब दीजिए।",
  noVoice: "इस फ़ोन पर हिंदी आवाज़ नहीं है", // one-line strip above the disclaimer
  noListen: "यह ब्राउज़र आवाज़ नहीं सुन सकता",
  outside: "आपकी जगह अभी हमारे इलाके के बाहर है। उदाहरण देखने के लिए ज़िला चुनिए।",
  formTitle: "अपने खेत के बारे में बताइए",
  formSubmit: "तरीके देखिए",
};

const SCRIPT_EN: typeof SCRIPT_HI = {
  title: "Field Aide",
  greeting_title: "Namaste",
  taglineLead: "Farm suggestions for you",
  taglineRest: "Pick your choice from the buttons below.", // one line where it fits, wraps on narrow phones
  start: "Tap to speak",
  useForm: "Tap to fill the form",
  end: "End call",
  again: "New call",
  back: "Back",
  greeting: "Hello. I will ask you a few questions about your farm. Answer by speaking, or touch a picture.",
  notUnderstood: "Sorry, I did not understand. Please say it again, or touch a picture.",
  closing: "Thank you. I have your answers. Now I will show you the results. The call is finished.",
  speaking: "Listen…",
  listening: "Your turn — speak",
  tapOnly: "Touch a picture",
  mapNote: "The red mark is your phone's location.",
  mapLoading: "Opening the map… please wait.",
  noMic: "Microphone permission was not given. Please answer by touching a picture.",
  noVoice: "No English voice on this phone",
  noListen: "This browser can't hear your voice",
  outside: "Your location is outside our area for now. Choose a district to see an example.",
  formTitle: "Tell us about your farm",
  formSubmit: "Show the options",
};

export const SCRIPTS: Record<Lang, typeof SCRIPT_HI> = { hi: SCRIPT_HI, en: SCRIPT_EN };

// Asked only when the phone gave a location: the map shows a red pin and the farmer confirms it.
// "words" mix Hindi and English on purpose: a farmer may answer in either, and the browser may write either script.
const FARM: Option[] = [
  { value: "yes", label: { hi: "हाँ, यही है", en: "Yes, this is it" }, pics: ["yes"], words: ["हाँ", "हां", "हा", "जी", "है", "यही", "सही", "yes", "yeah", "correct", "right"] },
  { value: "no", label: { hi: "नहीं", en: "No" }, pics: ["no"], words: ["नहीं", "नही", "ना", "गलत", "no", "nope", "wrong"] },
];

const LOCATIONS: Option[] = [
  { value: "akola", label: { hi: "अकोला", en: "Akola" }, pics: ["pin"], words: ["अकोला", "akola"] },
  { value: "buldhana", label: { hi: "बुलढाणा", en: "Buldhana" }, pics: ["pin"], words: ["बुलढाणा", "बुलढाना", "बुलडाना", "बुलढ़ाणा", "buldhana", "buldana", "buldhanaa"] },
  { value: "washim", label: { hi: "वाशिम", en: "Washim" }, pics: ["pin"], words: ["वाशिम", "वाशीम", "washim", "vashim", "washem"] },
];

const ROTATIONS: Option[] = [
  { value: "soybean_fallow", label: { hi: "सोयाबीन, फिर खेत खाली", en: "Soybean, then empty field" }, pics: ["soybean", "then", "bare"], words: ["खाली", "fallow", "empty", "bare", "nothing"], weak: ["सोयाबीन", "soybean", "soyabean", "soya"] },
  { value: "cotton", label: { hi: "कपास", en: "Cotton" }, pics: ["cotton"], words: ["कपास", "cotton"] },
  { value: "soybean_chickpea", label: { hi: "सोयाबीन, फिर चना", en: "Soybean, then chickpea" }, pics: ["soybean", "then", "chickpea"], words: ["चना", "चने", "chana", "chickpea", "chick pea", "gram"] },
];

const WATER_SOURCES: Option[] = [
  { value: "rainfed", label: { hi: "सिर्फ़ बारिश", en: "Rain only" }, pics: ["rain"], words: ["बारिश", "बरसात", "वर्षा", "rain", "rainfed", "monsoon"] },
  { value: "well", label: { hi: "कुआँ या बोरवेल", en: "Well or borewell" }, pics: ["well"], words: ["कुआँ", "कुआं", "बोरवेल", "borewell", "bore well", "well"] },
  { value: "canal_tank", label: { hi: "नहर या तालाब", en: "Canal or pond" }, pics: ["canal"], words: ["नहर", "तालाब", "canal", "tank", "pond", "lake"] },
];

const PRIORITIES: Option[] = [
  { value: "water_saving", label: { hi: "पानी बचाना", en: "Save water" }, pics: ["water_saving"], words: ["पानी", "water"] },
  { value: "forage", label: { hi: "जानवरों का चारा", en: "Fodder for animals" }, pics: ["forage"], words: ["चारा", "जानवर", "fodder", "forage", "animal", "cattle"] },
  { value: "nitrogen", label: { hi: "कम खाद", en: "Less fertiliser" }, pics: ["nitrogen"], words: ["खाद", "यूरिया", "नाइट्रोजन", "fertiliser", "fertilizer", "urea", "nitrogen"] },
  { value: "erosion", label: { hi: "मिट्टी का बहना रोकना", en: "Stop soil washing away" }, pics: ["erosion"], words: ["कटाव", "बहना", "बह", "बहती", "बहाव", "erosion", "washing", "washed"] },
  { value: "organic_matter", label: { hi: "मिट्टी की सेहत", en: "Soil health" }, pics: ["organic_matter"], words: ["सेहत", "जैविक", "organic", "health", "healthy"], weak: ["मिट्टी", "soil"] },
  { value: "market_income", label: { hi: "अच्छा दाम", en: "Better price" }, pics: ["market_income"], words: ["दाम", "भाव", "कीमत", "आमदनी", "income", "price", "money", "profit"] },
];

const NONE: Option = {
  value: "",
  label: { hi: "और कुछ नहीं चाहिए", en: "None" },
  pics: ["none"],
  // "और कुछ नहीं चाहिए" is the label; people will also say just "नहीं" or "कुछ नहीं"
  words: ["और कुछ नहीं", "कुछ नहीं", "कुछ नही", "नहीं चाहिए", "नहीं", "नही", "कोई नहीं", "बस", "none", "no", "nothing", "nobody"],
};

const LEVELS: Option[] = [
  { value: "low", label: { hi: "कम", en: "Low" }, pics: ["level1"], words: ["कम", "low", "little"] },
  { value: "medium", label: { hi: "ठीक-ठाक", en: "Medium" }, pics: ["level2"], words: ["ठीक", "मध्यम", "मीडियम", "medium", "moderate", "average"] },
  { value: "high", label: { hi: "ज़्यादा", en: "High" }, pics: ["level3"], words: ["ज़्यादा", "ज्यादा", "अधिक", "high", "plenty"] },
];

const EQUIPMENT: Option[] = [
  { value: "sprayer", label: { hi: "हाँ", en: "Yes" }, pics: ["yes"], words: ["हाँ", "हां", "हा", "जी", "है", "yes", "yeah", "have"] },
  { value: "basic", label: { hi: "नहीं", en: "No" }, pics: ["no"], words: ["नहीं", "नही", "ना", "no", "nope"] },
];

const MARKETS: Option[] = [
  { value: "mandi", label: { hi: "मंडी में", en: "At the mandi (market yard)" }, pics: ["mandi"], words: ["मंडी", "mandi", "market"] },
  { value: "buyer", label: { hi: "पास के ख़रीदार को", en: "To a nearby buyer" }, pics: ["buyer"], words: ["ख़रीदार", "खरीदार", "व्यापारी", "buyer", "trader", "merchant"] },
  { value: "own_use", label: { hi: "अपने इस्तेमाल के लिए", en: "For my own use" }, pics: ["own_use"], words: ["अपने", "घर", "खुद", "own", "myself", "home", "self"] },
];

export const STEPS: Step[] = [
  { id: "farm", question: { hi: "क्या लाल निशान की जगह आपका खेत है?", en: "Is the red mark the place of your farm?" }, options: () => FARM },
  { id: "location", question: { hi: "आपका खेत किस ज़िले में है?", en: "Which district is your farm in?" }, options: () => LOCATIONS },
  { id: "rotation", question: { hi: "अभी आप खेत में क्या बोते हैं?", en: "What do you grow in the field now?" }, options: () => ROTATIONS },
  { id: "water_source", question: { hi: "आपके खेत में पानी कहाँ से आता है?", en: "Where does the water for your field come from?" }, options: () => WATER_SOURCES },
  { id: "priority1", question: { hi: "आपके लिए सबसे ज़रूरी क्या है?", en: "What matters most to you?" }, options: () => PRIORITIES },
  {
    id: "priority2",
    question: { hi: "कोई दूसरी ज़रूरी बात? नहीं हो तो बोलिए, और कुछ नहीं चाहिए।", en: "Anything else that matters? If not, say no." },
    options: (a) => [...PRIORITIES.filter((p) => p.value !== a.priority1), NONE],
  },
  { id: "water_level", question: { hi: "खेत के लिए पानी कितना मिल सकता है?", en: "How much water can you get for the field?" }, options: () => LEVELS },
  { id: "equipment", question: { hi: "क्या आपके पास स्प्रेयर या बुवाई का कृषि यंत्र है?", en: "Do you have a sprayer or a sowing machine?" }, options: () => EQUIPMENT },
  { id: "market", question: { hi: "आप अपनी फ़सल कहाँ बेचते हैं?", en: "Where do you sell your crop?" }, options: () => MARKETS },
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
