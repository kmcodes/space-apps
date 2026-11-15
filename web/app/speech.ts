// Browser speech output shared by the call and the results screens (Web Speech API, standing in for Sarvam).
// The app speaks as a woman ("दिखाती हूँ"), so pick a female Hindi voice when the device has a choice.
// Voices do not report gender; these are the common names (Google Hindi, Microsoft Kalpana, Apple Lekha).

const MALE_VOICE = /hemant|ravi|madhur|prabhat|\bmale\b/i;
const FEMALE_VOICE = /female|kalpana|swara|lekha|google/i;

export function pickHindiVoice(synth: SpeechSynthesis): SpeechSynthesisVoice | undefined {
  const hindi = synth.getVoices().filter((v) => v.lang.toLowerCase().startsWith("hi"));
  return hindi.find((v) => FEMALE_VOICE.test(v.name)) ?? hindi.find((v) => !MALE_VOICE.test(v.name)) ?? hindi[0];
}

// Some browsers never report that speech ended: no Hindi voice on the device, a stalled engine, a background tab.
// Anything waiting on "ended" would hang for ever (the call never reached the results). So `done` also fires
// if speech has not started within 2.5 s, or has run far longer than the text needs. It fires only once.
export function guardUtterance(u: SpeechSynthesisUtterance, text: string, done: () => void) {
  let finished = false;
  let startTimer: ReturnType<typeof setTimeout> | undefined;
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
  startTimer = setTimeout(finish, 2500);
}

let current = 0; // bumped on every speak or stop, so a cancelled utterance never fires its callback

export function stopSpeech() {
  current++;
  if (typeof window !== "undefined") window.speechSynthesis?.cancel();
}

export function speakHindi(text: string, onEnd?: () => void) {
  const synth = window.speechSynthesis;
  stopSpeech();
  const mine = current;
  if (!synth) {
    onEnd?.();
    return;
  }
  const u = new SpeechSynthesisUtterance(text);
  u.lang = "hi-IN";
  const voice = pickHindiVoice(synth);
  if (voice) u.voice = voice;
  guardUtterance(u, text, () => {
    if (mine === current) onEnd?.();
  });
  synth.speak(u);
}
