// Browser speech output shared by the call and the results screens (Web Speech API, standing in for Sarvam).
// The app speaks as a woman ("दिखाती हूँ"), so pick a female voice when the device has a choice, in Hindi or English.
// Voices do not report gender; these are the common names (Google Hindi, Microsoft Kalpana, Apple Lekha, Google UK English Female).

import type { Lang } from "./lang";

const MALE_VOICE = /hemant|ravi|madhur|prabhat|rishi|david|mark|james|\bmale\b/i;
const FEMALE_VOICE = /female|kalpana|swara|lekha|heera|veena|zira|samantha|google/i;

/** The language tag for speaking and for listening: Indian Hindi, or Indian English. */
export const speechLang = (lang: Lang) => (lang === "en" ? "en-IN" : "hi-IN");

/** A voice for this language, preferring a female one, and for English the Indian accent when the device has it. */
export function pickVoice(synth: SpeechSynthesis, lang: Lang): SpeechSynthesisVoice | undefined {
  if (lang === "hi") return pickHindiVoice(synth);
  const english = synth.getVoices().filter((v) => v.lang.toLowerCase().startsWith("en"));
  const indian = english.filter((v) => v.lang.toLowerCase().replace("_", "-") === "en-in");
  const pool = indian.length ? indian : english;
  return pool.find((v) => FEMALE_VOICE.test(v.name)) ?? pool.find((v) => !MALE_VOICE.test(v.name)) ?? pool[0];
}

export function pickHindiVoice(synth: SpeechSynthesis): SpeechSynthesisVoice | undefined {
  const hindi = synth.getVoices().filter((v) => v.lang.toLowerCase().startsWith("hi"));
  return hindi.find((v) => FEMALE_VOICE.test(v.name)) ?? hindi.find((v) => !MALE_VOICE.test(v.name)) ?? hindi[0];
}

// Some browsers never report that speech ended: no Hindi voice on the device, a stalled engine, a background tab.
// Anything waiting on "ended" would hang for ever (the call never reached the results). So `done` also fires
// if speech has not started within 2.5 s, or has run far longer than the text needs. It fires only once.
export function guardUtterance(u: SpeechSynthesisUtterance, text: string, done: () => void) {
  let finished = false;
  let endTimer: ReturnType<typeof setTimeout> | undefined;
  const finish = () => {
    if (finished) return;
    finished = true;
    clearTimeout(startTimer);
    clearTimeout(endTimer);
    done();
  };
  u.onstart = () => {
    clearTimeout(startTimer);
    endTimer = setTimeout(finish, 4000 + text.length * 200);
  };
  u.onend = u.onerror = finish;
  // Declared last but only read inside the callbacks above, which run later, so it is set by then.
  const startTimer = setTimeout(finish, 2500);
}

let current = 0; // bumped on every speak or stop, so a cancelled utterance never fires its callback

export function stopSpeech() {
  current++;
  if (typeof window !== "undefined") window.speechSynthesis?.cancel();
}

export function speakText(text: string, lang: Lang, onEnd?: () => void) {
  const synth = window.speechSynthesis;
  stopSpeech();
  const mine = current;
  if (!synth) {
    onEnd?.();
    return;
  }
  const u = new SpeechSynthesisUtterance(text);
  u.lang = speechLang(lang);
  const voice = pickVoice(synth, lang);
  if (voice) u.voice = voice;
  guardUtterance(u, text, () => {
    if (mine === current) onEnd?.();
  });
  synth.speak(u);
}
