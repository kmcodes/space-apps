"use client";

// The voice call: one tap starts it, the app asks one question at a time aloud and listens for the answer.
// Picture buttons under each question are the tap fallback. Browser speech (Web Speech API) stands in for Sarvam.
// When the questions are done, the answers go to <FieldShift>, which calls the engine and shows the results.

import { useEffect, useRef, useState } from "react";
import AnswerForm, { type Initial } from "./answer-form";
import Disclaimer from "./disclaimer";
import { SCRIPTS, STEPS, matchOption, type Answers, type Option } from "./call-script";
import { isServed } from "./coverage";
import { useLang } from "./lang";
import { FormIcon, MicIcon, Pictogram, SpeakerIcon } from "./pictograms";
import Results from "./results";
import { guardUtterance, pickVoice, speechLang } from "./speech";
import { wakeApi } from "./wake-api";

type Phase = "home" | "call" | "results" | "form";
type Status = "speaking" | "listening" | "tap";

// The browser's speech recognition is not in TypeScript's DOM types.
interface Recognition {
  lang: string;
  continuous: boolean;
  interimResults: boolean;
  onresult: ((e: { results: ArrayLike<ArrayLike<{ transcript: string }>> }) => void) | null;
  onerror: ((e: { error: string }) => void) | null;
  onend: (() => void) | null;
  start(): void;
  abort(): void;
}
type RecognitionCtor = new () => Recognition;

function recognitionCtor(): RecognitionCtor | null {
  const w = window as unknown as { SpeechRecognition?: RecognitionCtor; webkitSpeechRecognition?: RecognitionCtor };
  return w.SpeechRecognition ?? w.webkitSpeechRecognition ?? null;
}

// Jan to Dec for a soybean then chickpea field: crop in the ground except the bare Mar to May window.
const YEAR_PICTURE = [true, true, false, false, false, true, true, true, true, true, true, true];


export default function VoiceCall() {
  const [phase, setPhase] = useState<Phase>("home");
  const [idx, setIdx] = useState(0);
  const [answers, setAnswers] = useState<Answers>({});
  const [status, setStatus] = useState<Status>("speaking");
  const [reading, setReading] = useState(-1); // which tile is being read aloud right now
  // The tile just chosen (by tap or by voice): outlined in green with a tick for a moment before the next question.
  const [picked, setPicked] = useState<string | null>(null);
  const pickedRef = useRef<string | null>(null);
  const [notice, setNotice] = useState("");
  // Found out after load (browser only), so the first render matches the server.
  const [canListen, setCanListen] = useState(true);
  const [voices, setVoices] = useState<{ hi: boolean; en: boolean } | null>(null); // does the device have a voice for each language?
  const [coords, setCoords] = useState<{ lat: number; lon: number } | null>(null); // the phone's location, if it gave one
  const [final, setFinal] = useState<Initial | null>(null); // the answers handed to the results page
  // The farm question needs the map. Until the greeting is done and the map has loaded, no question or buttons are shown.
  const [intro, setIntro] = useState(true);
  const [mapReady, setMapReady] = useState(false);
  const mapReadyRef = useRef(false);
  const mapTimer = useRef<number | undefined>(undefined);
  const mapWaiting = useRef(false); // the call is at the farm question and waiting for the map
  const outsideRef = useRef(false); // the phone's location is outside the area we cover: no map, ask the district

  const run = useRef(0); // bumped to cancel any speech or listening still in flight
  const idxRef = useRef(0);
  const answersRef = useRef<Answers>({});
  const recRef = useRef<Recognition | null>(null);
  const silences = useRef(0);
  const coordsRef = useRef<{ lat: number; lon: number } | null>(null);
  const geo = useRef<"pending" | "ok" | "none">("none");
  const { lang } = useLang();
  const langRef = useRef(lang); // read by speech and listening callbacks, which outlive a render
  const S = SCRIPTS[lang]; // the script for rendering; callbacks use SCRIPTS[langRef.current]

  useEffect(() => {
    wakeApi(); // the API host may be asleep; start waking it now
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setCanListen(recognitionCtor() !== null);
    const synth = window.speechSynthesis;
    if (!synth) {
      setVoices({ hi: false, en: false });
      return;
    }
    const check = () => {
      const all = synth.getVoices();
      if (all.length) setVoices({ hi: all.some((v) => v.lang.toLowerCase().startsWith("hi")), en: all.some((v) => v.lang.toLowerCase().startsWith("en")) });
    };
    check();
    synth.addEventListener("voiceschanged", check);
    return () => {
      synth.removeEventListener("voiceschanged", check);
      // run is a counter, not a DOM node, so the value at cleanup time is the one we want.
      // eslint-disable-next-line react-hooks/exhaustive-deps
      run.current++;
      recRef.current?.abort();
      synth.cancel();
    };
  }, []);

  // Keep the speech callbacks' language current. If the language is switched during a call, say the question again
  // in the new language (or, before any answer, restart the call so the greeting is in it too).
  const langSeen = useRef(false);
  useEffect(() => {
    langRef.current = lang;
    if (!langSeen.current) {
      langSeen.current = true;
      return;
    }
    if (phase !== "call") return;
    stopAudio();
    if (Object.keys(answersRef.current).length === 0) start();
    else ask(idxRef.current);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [lang]);

  function stopAudio() {
    run.current++;
    recRef.current?.abort();
    recRef.current = null;
    window.speechSynthesis?.cancel();
  }

  function speak(text: string, then?: () => void) {
    const synth = window.speechSynthesis;
    const token = run.current;
    if (!synth) {
      then?.();
      return;
    }
    synth.cancel();
    const u = new SpeechSynthesisUtterance(text);
    u.lang = speechLang(langRef.current);
    const voice = pickVoice(synth, langRef.current);
    if (voice) u.voice = voice;
    guardUtterance(u, text, () => {
      if (token === run.current) then?.();
    });
    synth.speak(u);
  }

  function listen() {
    const Ctor = recognitionCtor();
    const token = run.current;
    if (!Ctor) {
      setStatus("tap");
      return;
    }
    const rec = new Ctor();
    rec.lang = speechLang(langRef.current);
    rec.continuous = false;
    rec.interimResults = false;
    let heard = false;
    let blocked = false;
    rec.onresult = (e) => {
      heard = true;
      if (token !== run.current) return;
      const text = Array.from(e.results)
        .map((r) => r[0].transcript)
        .join(" ");
      const step = STEPS[idxRef.current];
      const option = matchOption(text, step.options(answersRef.current));
      if (option) choose(option);
      else {
        silences.current = 0;
        setStatus("speaking");
        speak(SCRIPTS[langRef.current].notUnderstood, listen);
      }
    };
    rec.onerror = (e) => {
      if (token !== run.current) return;
      if (e.error === "not-allowed" || e.error === "service-not-allowed") {
        blocked = true;
        setNotice("noMic");
        setStatus("tap");
      }
    };
    rec.onend = () => {
      if (token !== run.current || heard || blocked) return;
      // The farmer said nothing. Listen once more, then wait for a tap or the microphone button.
      silences.current++;
      if (silences.current >= 2) setStatus("tap");
      else listen();
    };
    recRef.current = rec;
    setStatus("listening");
    try {
      rec.start();
    } catch {
      setStatus("tap");
    }
  }

  function ask(i: number) {
    idxRef.current = i;
    setIdx(i);
    silences.current = 0;
    setStatus("speaking");
    setReading(-1);
    pickedRef.current = null;
    setPicked(null);
    setIntro(false);
    const step = STEPS[i];
    if (step.id === "farm" && coordsRef.current && !mapReadyRef.current) {
      // Show the map's frame with a placeholder and say nothing yet. If the map does not load in time, fall back to
      // the district question, the same as when the phone gives no location.
      const waitToken = run.current;
      mapWaiting.current = true;
      window.clearTimeout(mapTimer.current);
      mapTimer.current = window.setTimeout(() => {
        if (waitToken !== run.current || mapReadyRef.current) return;
        mapWaiting.current = false;
        coordsRef.current = null;
        setCoords(null);
        ask(1);
      }, MAP_WAIT_MS);
      return;
    }
    const labels = step.options(answersRef.current).map((o) => o.label[langRef.current]);
    const token = run.current;
    // Read-along: the farmer hears each option while its picture lights up, so picture and word get linked.
    const readFrom = (n: number) => {
      if (token !== run.current) return;
      if (n >= labels.length) {
        setReading(-1);
        listen();
        return;
      }
      setReading(n);
      speak(labels[n], () => readFrom(n + 1));
    };
    speak(step.question[langRef.current], () => readFrom(0));
  }

  const MAP_WAIT_MS = 8000; // how long to wait for the map before asking the district instead
  const PICK_HOLD_MS = 700; // long enough to see which tile was taken, short enough not to feel slow

  function choose(option: Option) {
    if (pickedRef.current !== null) return; // one answer per question; ignore a second tap while it is shown
    stopAudio();
    setReading(-1);
    pickedRef.current = option.value;
    setPicked(option.value);
    const token = run.current;
    window.setTimeout(() => {
      if (token === run.current) advance(option); // not if the call was ended meanwhile
    }, PICK_HOLD_MS);
  }

  function advance(option: Option) {
    const i = idxRef.current;
    const next = { ...answersRef.current, [STEPS[i].id]: option.value };
    answersRef.current = next;
    setAnswers(next);
    setNotice((n) => (n === "outside" ? "" : n)); // the "outside our area" line was for the district question
    // "Yes, that is my farm" makes the district question unnecessary; "no" falls back to the district tiles.
    const nextIdx = STEPS[i].id === "farm" ? (option.value === "yes" ? i + 2 : i + 1) : i + 1;
    if (nextIdx < STEPS.length) ask(nextIdx);
    else {
      const { farm, ...rest } = next;
      setFinal(farm === "yes" && coordsRef.current ? { ...rest, location: undefined, ...coordsRef.current } : { ...rest, ...(outsideRef.current ? { example: true } : {}) });
      setStatus("speaking");
      speak(SCRIPTS[langRef.current].closing, () => setPhase("results"));
    }
  }

  // The map frame finished loading. If the call is already waiting at the farm question, ask it now;
  // if the greeting is still being spoken, begin() will ask it when the greeting ends.
  function onMapLoad() {
    if (mapReadyRef.current) return;
    mapReadyRef.current = true;
    setMapReady(true);
    window.clearTimeout(mapTimer.current);
    if (mapWaiting.current) {
      mapWaiting.current = false;
      ask(0);
    }
  }

  // Once the greeting is done: if the phone gave a location, confirm it on a map; otherwise ask the district.
  // The location prompt may still be open, so wait a little for it.
  function begin(waited = 0) {
    const token = run.current;
    if (geo.current === "pending" && waited < 10000) {
      setTimeout(() => token === run.current && begin(waited + 300), 300);
      return;
    }
    if (outsideRef.current) {
      setNotice("outside");
      speak(SCRIPTS[langRef.current].outside, () => ask(1));
      return;
    }
    ask(coordsRef.current ? 0 : 1);
  }

  function start() {
    stopAudio();
    wakeApi(); // no-op if the page already pinged a moment ago
    answersRef.current = {};
    setAnswers({});
    setNotice("");
    outsideRef.current = false;
    setPhase("call");
    setIdx(0);
    idxRef.current = 0;
    setStatus("speaking");
    setFinal(null);
    setIntro(true);
    window.clearTimeout(mapTimer.current);
    mapWaiting.current = false;
    mapReadyRef.current = false;
    setMapReady(false);
    coordsRef.current = null;
    setCoords(null);
    geo.current = "none";
    // Geolocation only works on HTTPS or localhost. Elsewhere the call simply asks the district.
    if (window.isSecureContext && navigator.geolocation) {
      geo.current = "pending";
      navigator.geolocation.getCurrentPosition(
        (p) => {
          // Rounded to about 100 m: the engine's data is far coarser than that, and less is stored or sent.
          const lat = Math.round(p.coords.latitude * 1000) / 1000;
          const lon = Math.round(p.coords.longitude * 1000) / 1000;
          if (!isServed(lat, lon)) {
            // Outside the area we cover: say so now, skip the map and ask the district instead, to show an example.
            outsideRef.current = true;
            geo.current = "none";
            return;
          }
          coordsRef.current = { lat, lon };
          setCoords(coordsRef.current);
          geo.current = "ok";
        },
        () => {
          geo.current = "none";
        },
        { timeout: 12000, maximumAge: 60000 },
      );
    }
    speak(SCRIPTS[langRef.current].greeting, () => begin());
  }

  function end() {
    stopAudio();
    setReading(-1);
    setPhase("home");
  }

  function leave(to: Phase) {
    stopAudio();
    setPhase(to);
  }

  if (phase === "results" && final) return <Results answers={final} onRestart={() => leave("home")} />;

  if (phase === "form") {
    return (
      <>
        <div className="mx-auto w-full max-w-xl px-4 pt-3">
          <button onClick={() => leave("home")} className="rounded-field border-2 border-soil px-3 py-1.5 text-base font-bold" lang={lang}>
            {S.back}
          </button>
        </div>
        <AnswerForm
          onSubmit={(a) => {
            setFinal(a);
            setPhase("results"); // the same results page as the voice call
          }}
        />
        <Disclaimer />
      </>
    );
  }

  if (phase === "home") {
    return (
      <main className="mx-auto flex w-full max-w-xl flex-1 flex-col px-4 pb-24 pt-8">
        <h1 className="narrow text-5xl font-extrabold leading-none" lang={lang}>
          {S.title}
        </h1>
        <p className="mt-3 text-xl text-soil-soft" lang={lang}>
          {S.tagline}
        </p>
        {/* The year strip is this app's signature: green = crop in the ground, dark = bare field, blue band = monsoon.
            Here it is only a picture of what the app is about, so it has no text. */}
        <div className="mt-8" aria-hidden>
          <div className="grid grid-cols-12 gap-px">
            <span className="col-span-4 col-start-6 h-2 bg-monsoon" />
          </div>
          <div className="mt-1 grid grid-cols-12 gap-px">
            {YEAR_PICTURE.map((crop, m) => (
              <span key={m} className={`h-12 ${crop ? "bg-crop" : "bg-soil"}`} />
            ))}
          </div>
          <div className="mt-3 flex items-center justify-center gap-2">
            <Pictogram id="soybean" className="h-10 w-10" />
            <Pictogram id="then" className="h-5 w-5" />
            <Pictogram id="chickpea" className="h-10 w-10" />
            <Pictogram id="then" className="h-5 w-5" />
            <Pictogram id="bare" className="h-10 w-10" />
          </div>
        </div>

        {/* Two buttons of one type (same shape, size, text and icon), each label on one line.
            Speaking is the main action, so it is filled; the form is the same button outlined. */}
        <button
          onClick={start}
          className="mt-8 flex w-full items-center gap-3 rounded-field border-[3px] border-monsoon bg-monsoon px-4 py-3.5 text-left text-white"
        >
          <MicIcon className="h-8 w-8 shrink-0" />
          <span className="narrow min-w-0 flex-1 whitespace-nowrap py-1 text-2xl font-extrabold leading-normal" lang={lang}>
            {S.start}
          </span>
          {/* Static sound bars: this button talks. */}
          <span aria-hidden className="flex h-8 shrink-0 items-center gap-1">
            {[10, 20, 28, 16, 10].map((h, i) => (
              <span key={i} className="w-1 rounded-full bg-white/80" style={{ height: h }} />
            ))}
          </span>
        </button>
        <button
          onClick={() => leave("form")}
          className="mt-3 flex w-full items-center gap-3 rounded-field border-[3px] border-monsoon bg-paper px-4 py-3.5 text-left text-monsoon"
        >
          <FormIcon className="h-8 w-8 shrink-0" />
          <span className="narrow min-w-0 flex-1 whitespace-nowrap py-1 text-2xl font-extrabold leading-normal" lang={lang}>
            {S.useForm}
          </span>
        </button>
        {voices && !voices[lang] && (
          <p className="mt-6 border-l-4 border-turmeric bg-turmeric-wash p-3 text-sm">
            This device has no {lang === "hi" ? "Hindi" : "English"} voice, so the questions will be shown but not spoken.
          </p>
        )}
        {!canListen && (
          <p className="mt-3 border-l-4 border-turmeric bg-turmeric-wash p-3 text-sm">
            This browser cannot listen to speech. You can still answer by tapping the pictures. Chrome or Edge on Android work best.
          </p>
        )}
        <Disclaimer />
      </main>
    );
  }

  const step = STEPS[idx];
  const options = step.options(answers);
  const waitingMap = step.id === "farm" && !!coords && !mapReady; // the map is on its way: show its frame, not the question
  const hideQuestion = intro || waitingMap;
  const statusText = status === "speaking" ? S.speaking : status === "listening" ? S.listening : S.tapOnly;
  const canTapToSpeak = status === "tap" && canListen && !notice && !hideQuestion;

  return (
    <main className="mx-auto flex w-full max-w-xl flex-1 flex-col px-4 pb-24 pt-3">
      <div className="flex items-center gap-4">
        {/* One segment per question, like the year strip: answered, current, to come. No numbers, nothing to read. */}
        <div className="flex flex-1 gap-1" aria-hidden>
          {STEPS.map((st, i) => (
            <span key={st.id} className={`h-2 flex-1 ${i < idx ? "bg-soil" : i === idx ? "bg-monsoon" : "bg-rule"}`} />
          ))}
        </div>
        <button onClick={end} className="flex items-center gap-2 rounded-field bg-almanac px-3 py-2 text-base font-bold text-white" lang={lang}>
          <svg aria-hidden viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2.4} strokeLinecap="round" className="h-4 w-4">
            <path d="M6 6l12 12M18 6L6 18" />
          </svg>
          {S.end}
        </button>
      </div>

      {/* The mic or speaker shows whose turn it is. When the app is waiting for a tap, this is the "speak again" button. */}
      {!waitingMap && (
      <button
        onClick={canTapToSpeak ? listen : undefined}
        disabled={!canTapToSpeak}
        role="status"
        aria-live="polite"
        className="mt-6 flex items-center gap-4 self-start text-left"
      >
        <span
          className={`flex h-16 w-16 shrink-0 items-center justify-center rounded-field ${
            status === "listening" ? "bg-monsoon text-white" : status === "speaking" ? "bg-soil text-white" : "border-2 border-monsoon text-monsoon"
          }`}
        >
          {status === "speaking" ? <SpeakerIcon className="h-8 w-8" /> : <MicIcon className="h-8 w-8" />}
        </span>
        <span className="narrow text-xl font-bold text-soil-soft" lang={lang}>
          {statusText}
        </span>
      </button>
      )}

      {!hideQuestion && (
        <h2 className="narrow mt-4 text-3xl font-extrabold leading-tight" lang={lang}>
          {step.question[lang]}
        </h2>
      )}

      {notice && (
        <p className="mt-3 border-l-4 border-almanac p-3 text-sm font-semibold text-almanac" lang={lang}>
          {notice === "noMic" ? S.noMic : notice === "outside" ? S.outside : notice}
        </p>
      )}

      {step.id === "farm" && coords && (
        <>
          {/* Google's keyless embed, satellite view. The browser sends these coordinates to Google when it loads.
              The frame keeps its space from the start; a placeholder fills it until the map has loaded. */}
          <div className="relative mt-4 h-64 w-full overflow-hidden rounded-field border-2 border-soil bg-paper">
            {!mapReady && (
              <div role="status" className="absolute inset-0 flex animate-pulse flex-col items-center justify-center gap-2 bg-rule/40">
                <Pictogram id="pin" className="h-14 w-14" />
                <span className="narrow text-lg font-bold text-soil-soft" lang={lang}>
                  {S.mapLoading}
                </span>
              </div>
            )}
            <iframe
              title="map"
              className={`absolute inset-0 h-full w-full ${mapReady ? "" : "opacity-0"}`}
              referrerPolicy="no-referrer"
              sandbox="allow-scripts allow-same-origin"
              onLoad={onMapLoad}
              src={`https://www.google.com/maps?q=${coords.lat},${coords.lon}&z=16&t=k&output=embed`}
            />
          </div>
          {mapReady && (
            <p className="mt-1 text-sm text-soil-soft" lang={lang}>
              {S.mapNote}
            </p>
          )}
        </>
      )}

      {!intro && (
      <ul className={`mt-5 grid grid-cols-2 gap-3 ${waitingMap ? "opacity-40" : ""}`}>
        {options.map((o, i) => (
          <li key={o.value || "none"} className="last:odd:col-span-2">
            <button
              onClick={() => choose(o)}
              disabled={waitingMap}
              aria-pressed={picked === o.value}
              className={`relative flex h-full min-h-44 w-full flex-col items-center justify-center gap-3 rounded-field text-center ${
                picked === o.value
                  ? "border-[6px] border-crop bg-crop/15 p-2 outline outline-4 outline-offset-2 outline-crop"
                  : picked !== null
                    ? "border-2 border-soil bg-paper p-3 opacity-40"
                    : reading === i
                      ? "border-4 border-monsoon bg-monsoon-wash p-2.5"
                      : "border-2 border-soil bg-paper p-3"
              }`}
            >
              {picked === o.value && (
                <span aria-hidden className="absolute right-1.5 top-1.5 flex h-9 w-9 items-center justify-center rounded-full bg-crop text-white">
                  <svg viewBox="0 0 24 24" className="h-6 w-6" fill="none" stroke="currentColor" strokeWidth="3.5" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M5 12.5l4.5 4.5L19 7.5" />
                  </svg>
                </span>
              )}
              <span className="flex items-center justify-center gap-1">
                {o.pics.map((id, k) => (
                  <Pictogram key={k} id={id} className={id === "then" ? "h-5 w-5" : o.pics.length > 1 ? "h-12 w-12" : "h-20 w-20"} />
                ))}
              </span>
              <span className="narrow text-lg font-bold leading-tight" lang={lang}>
                {o.label[lang]}
              </span>
            </button>
          </li>
        ))}
      </ul>
      )}
      <Disclaimer />
    </main>
  );
}
