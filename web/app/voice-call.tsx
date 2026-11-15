"use client";

// The voice call: one tap starts it, the app asks one question at a time aloud and listens for the answer.
// Picture buttons under each question are the tap fallback. Browser speech (Web Speech API) stands in for Sarvam.
// When the questions are done, the answers go to <FieldShift>, which calls the engine and shows the results.

import { useEffect, useRef, useState } from "react";
import FieldShift, { DISCLAIMER, type Initial } from "./field-shift";
import { SCRIPT, STEPS, matchOption, type Answers, type Option } from "./call-script";
import { MicIcon, Pictogram, SpeakerIcon } from "./pictograms";
import Results from "./results";
import { pickHindiVoice } from "./speech";

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

function Disclaimer() {
  return <p className="fixed inset-x-0 bottom-0 z-10 bg-turmeric px-4 py-2.5 text-center text-sm font-semibold text-soil">{DISCLAIMER}</p>;
}

export default function VoiceCall() {
  const [phase, setPhase] = useState<Phase>("home");
  const [idx, setIdx] = useState(0);
  const [answers, setAnswers] = useState<Answers>({});
  const [status, setStatus] = useState<Status>("speaking");
  const [reading, setReading] = useState(-1); // which tile is being read aloud right now
  const [notice, setNotice] = useState("");
  // Found out after load (browser only), so the first render matches the server.
  const [canListen, setCanListen] = useState(true);
  const [hindiVoice, setHindiVoice] = useState<boolean | null>(null);
  const [coords, setCoords] = useState<{ lat: number; lon: number } | null>(null); // the phone's location, if it gave one
  const [final, setFinal] = useState<Initial | null>(null); // the answers handed to the results page

  const run = useRef(0); // bumped to cancel any speech or listening still in flight
  const idxRef = useRef(0);
  const answersRef = useRef<Answers>({});
  const recRef = useRef<Recognition | null>(null);
  const silences = useRef(0);
  const coordsRef = useRef<{ lat: number; lon: number } | null>(null);
  const geo = useRef<"pending" | "ok" | "none">("none");

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setCanListen(recognitionCtor() !== null);
    const synth = window.speechSynthesis;
    if (!synth) {
      setHindiVoice(false);
      return;
    }
    const check = () => {
      const voices = synth.getVoices();
      if (voices.length) setHindiVoice(voices.some((v) => v.lang.toLowerCase().startsWith("hi")));
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
    u.lang = "hi-IN";
    const voice = pickHindiVoice(synth);
    if (voice) u.voice = voice;
    u.onend = u.onerror = () => {
      if (token === run.current) then?.();
    };
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
    rec.lang = "hi-IN";
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
        speak(SCRIPT.notUnderstood, listen);
      }
    };
    rec.onerror = (e) => {
      if (token !== run.current) return;
      if (e.error === "not-allowed" || e.error === "service-not-allowed") {
        blocked = true;
        setNotice(SCRIPT.noMic);
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
    const step = STEPS[i];
    const labels = step.options(answersRef.current).map((o) => o.label);
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
    speak(step.question, () => readFrom(0));
  }

  function choose(option: Option) {
    stopAudio();
    const i = idxRef.current;
    const next = { ...answersRef.current, [STEPS[i].id]: option.value };
    answersRef.current = next;
    setAnswers(next);
    // "Yes, that is my farm" makes the district question unnecessary; "no" falls back to the district tiles.
    const nextIdx = STEPS[i].id === "farm" ? (option.value === "yes" ? i + 2 : i + 1) : i + 1;
    if (nextIdx < STEPS.length) ask(nextIdx);
    else {
      const { farm, ...rest } = next;
      setFinal(farm === "yes" && coordsRef.current ? { ...rest, location: undefined, ...coordsRef.current } : rest);
      setStatus("speaking");
      speak(SCRIPT.closing, () => setPhase("results"));
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
    ask(coordsRef.current ? 0 : 1);
  }

  function start() {
    stopAudio();
    answersRef.current = {};
    setAnswers({});
    setNotice("");
    setPhase("call");
    setIdx(0);
    idxRef.current = 0;
    setStatus("speaking");
    setFinal(null);
    coordsRef.current = null;
    setCoords(null);
    geo.current = "none";
    // Geolocation only works on HTTPS or localhost. Elsewhere the call simply asks the district.
    if (window.isSecureContext && navigator.geolocation) {
      geo.current = "pending";
      navigator.geolocation.getCurrentPosition(
        (p) => {
          // Rounded to about 100 m: the engine's data is far coarser than that, and less is stored or sent.
          coordsRef.current = { lat: Math.round(p.coords.latitude * 1000) / 1000, lon: Math.round(p.coords.longitude * 1000) / 1000 };
          setCoords(coordsRef.current);
          geo.current = "ok";
        },
        () => {
          geo.current = "none";
        },
        { timeout: 12000, maximumAge: 60000 },
      );
    }
    speak(SCRIPT.greeting, () => begin());
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
          <button onClick={() => leave("home")} className="rounded-field border-2 border-soil px-3 py-1.5 text-base font-bold" lang="hi">
            {SCRIPT.back}
          </button>
        </div>
        <FieldShift />
      </>
    );
  }

  if (phase === "home") {
    return (
      <main className="mx-auto flex w-full max-w-xl flex-1 flex-col px-4 pb-24 pt-8">
        <h1 className="narrow text-5xl font-extrabold leading-none" lang="hi">
          {SCRIPT.title}
        </h1>
        <p className="mt-3 text-xl text-soil-soft" lang="hi">
          {SCRIPT.tagline}
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

        <button onClick={start} className="mt-8 flex w-full items-center gap-4 rounded-field bg-monsoon px-5 py-6 text-left text-white">
          <MicIcon className="h-16 w-16 shrink-0" />
          <span className="narrow flex-1 text-3xl font-extrabold leading-tight" lang="hi">
            {SCRIPT.start}
          </span>
          {/* Static sound bars: this button talks. */}
          <span aria-hidden className="flex h-12 shrink-0 items-center gap-1">
            {[16, 32, 48, 28, 18].map((h, i) => (
              <span key={i} className="w-1 rounded-full bg-white/80" style={{ height: h }} />
            ))}
          </span>
        </button>
        <button onClick={() => leave("form")} className="mt-6 self-start text-base font-semibold text-monsoon underline" lang="hi">
          {SCRIPT.useForm}
        </button>
        {hindiVoice === false && (
          <p className="mt-6 border-l-4 border-turmeric bg-turmeric-wash p-3 text-sm">
            This device has no Hindi voice, so the questions will be shown but not spoken.
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
  const statusText = status === "speaking" ? SCRIPT.speaking : status === "listening" ? SCRIPT.listening : SCRIPT.tapOnly;
  const canTapToSpeak = status === "tap" && canListen && !notice;

  return (
    <main className="mx-auto flex w-full max-w-xl flex-1 flex-col px-4 pb-24 pt-3">
      <div className="flex items-center gap-4">
        {/* One segment per question, like the year strip: answered, current, to come. No numbers, nothing to read. */}
        <div className="flex flex-1 gap-1" aria-hidden>
          {STEPS.map((st, i) => (
            <span key={st.id} className={`h-2 flex-1 ${i < idx ? "bg-soil" : i === idx ? "bg-monsoon" : "bg-rule"}`} />
          ))}
        </div>
        <button onClick={end} className="flex items-center gap-2 rounded-field bg-almanac px-3 py-2 text-base font-bold text-white" lang="hi">
          <svg aria-hidden viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2.4} strokeLinecap="round" className="h-4 w-4">
            <path d="M6 6l12 12M18 6L6 18" />
          </svg>
          {SCRIPT.end}
        </button>
      </div>

      {/* The mic or speaker shows whose turn it is. When the app is waiting for a tap, this is the "speak again" button. */}
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
        <span className="narrow text-xl font-bold text-soil-soft" lang="hi">
          {statusText}
        </span>
      </button>

      <h2 className="narrow mt-4 text-3xl font-extrabold leading-tight" lang="hi">
        {step.question}
      </h2>

      {notice && (
        <p className="mt-3 border-l-4 border-almanac p-3 text-sm font-semibold text-almanac" lang="hi">
          {notice}
        </p>
      )}

      {step.id === "farm" && coords && (
        <>
          {/* Google's keyless embed, satellite view. The browser sends these coordinates to Google when it loads. */}
          <iframe
            title="map"
            className="mt-4 h-64 w-full rounded-field border-2 border-soil"
            loading="lazy"
            referrerPolicy="no-referrer"
            sandbox="allow-scripts allow-same-origin"
            src={`https://www.google.com/maps?q=${coords.lat},${coords.lon}&z=16&t=k&output=embed`}
          />
          <p className="mt-1 text-sm text-soil-soft" lang="hi">
            {SCRIPT.mapNote}
          </p>
        </>
      )}

      <ul className="mt-5 grid grid-cols-2 gap-3">
        {options.map((o, i) => (
          <li key={o.value || "none"} className="last:odd:col-span-2">
            <button
              onClick={() => choose(o)}
              className={`flex h-full min-h-44 w-full flex-col items-center justify-center gap-3 rounded-field text-center ${
                reading === i ? "border-4 border-monsoon bg-monsoon-wash p-2.5" : "border-2 border-soil bg-paper p-3"
              }`}
            >
              <span className="flex items-center justify-center gap-1">
                {o.pics.map((id, k) => (
                  <Pictogram key={k} id={id} className={id === "then" ? "h-5 w-5" : o.pics.length > 1 ? "h-12 w-12" : "h-20 w-20"} />
                ))}
              </span>
              <span className="narrow text-lg font-bold leading-tight" lang="hi">
                {o.label}
              </span>
            </button>
          </li>
        ))}
      </ul>
      <Disclaimer />
    </main>
  );
}
