"use client";

// The results for a farmer who may not read (docs/VOICE_APP_PLAN.md):
// - a list of choices, best first, with a thumbs-up on the top ones and no scores;
// - for one choice: the 12-month year bar (kharif and rabi grouped), then three picture rows that speak when tapped;
// - sources and validity flags sit behind a small "for experts" link.

import { useEffect, useState } from "react";
import { DISCLAIMER, type Initial } from "./field-shift";
import { Pictogram, SpeakerIcon, type PictogramId } from "./pictograms";
import { speakHindi, stopSpeech } from "./speech";
import {
  MONTH_HI_SHORT,
  RESULTS,
  SEASONS,
  choices,
  expertLines,
  explainers,
  fromJune,
  adviceKind,
  adviceLabel,
  goodLines,
  picsFor,
  riskRuns,
  runs,
  strategyName,
  strategyPics,
  nearestPhrase,
  summarySpeech,
  unknownLines,
  vulnerableLines,
  yearBar,
  type Choice,
  type Result,
  type SeasonRisk,
  type Strategy,
} from "./results-script";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8000";
// Retries for a sleeping API host: wait this long before each try (the first is immediate). About 25 s of waiting
// between tries, plus each try may itself wait up to ATTEMPT_TIMEOUT_MS while the host wakes.
const RETRY_DELAYS_MS = [0, 3000, 8000, 15000];
const ATTEMPT_TIMEOUT_MS = 45000;

type Row = "good" | "unknown" | "vulnerable" | "expert";

function Pics({ pics, className }: { pics: PictogramId[]; className: string }) {
  return (
    <span className="flex items-center gap-1" aria-hidden>
      {pics.map((id, i) => (
        <Pictogram key={i} id={id} className={id === "then" || id === "plus" ? "h-5 w-5" : className} />
      ))}
    </span>
  );
}

/* Twelve months, June first, so the kharif block and the rabi block each sit together.
   Green = a crop in the ground, dark = bare field. The compact version has no pictures. */
/* Under the year bar: the months the climate record marks as hot, and as having long dry spells inside the monsoon.
   Solid = both NASA POWER and ERA5 agree; dashed = only one of them does. */
function RiskRows({ risk }: { risk: SeasonRisk }) {
  const rows = [
    { key: "heat", pic: "hot", levels: fromJune(risk.heat_level) },
    { key: "dry", pic: "dry", levels: fromJune(risk.dry_spell_level) },
  ] as const;
  return (
    <>
      {rows
        .filter((r) => r.levels.some((l) => l > 0))
        .map((r) => (
          <div key={r.key} className="mt-1 grid grid-cols-12">
            {riskRuns(r.levels).map((run) => (
              <div
                key={run.start}
                style={{ gridColumn: `${run.start + 1} / span ${run.length}` }}
                className={`flex items-center justify-center border-2 border-almanac py-1 ${run.level === 2 ? "bg-almanac/15" : "border-dashed"}`}
              >
                <Pictogram id={r.pic} className="h-7 w-7" />
              </div>
            ))}
          </div>
        ))}
    </>
  );
}

/* The x axis: a tick per month (thicker where kharif, rabi and summer start) and every month's name, June first.
   Names take their season's colour so they tie to the season blocks above. Same timeline under every bar. */
const SEASON_START = new Set<number>(SEASONS.map((se) => se.from));
const SEASON_TEXT: Record<string, string> = { kharif: "text-monsoon", rabi: "text-[#7a5a00]", summer: "text-soil-soft" };
const seasonOf = (i: number) => SEASONS.find((se) => i >= se.from && i < se.from + se.length)!.key;

function MonthAxis({ full }: { full?: boolean }) {
  return (
    <div className="mt-1">
      <div className="grid grid-cols-12 border-t-2 border-soil">
        {MONTH_HI_SHORT.map((m, i) => (
          <span key={m} className={`border-l border-soil ${SEASON_START.has(i) ? "h-2 border-l-[3px]" : "h-1"}`} />
        ))}
      </div>
      <div className="grid grid-cols-12" lang="hi">
        {MONTH_HI_SHORT.map((m, i) => (
          <span
            key={m}
            className={`narrow min-w-0 text-center font-semibold leading-tight ${full ? "text-xs" : "text-[0.65rem]"} ${SEASON_TEXT[seasonOf(i)]}`}
          >
            {m}
          </span>
        ))}
      </div>
    </div>
  );
}

function YearBar({ s, full, risk }: { s: Strategy; full?: boolean; risk?: SeasonRisk }) {
  const bar = yearBar(s.calendar, s.kind === "mixed");
  const gap = (i: number) => (i === 4 || i === 9 ? "border-r-[6px] border-limewash" : "");
  return (
    <div aria-hidden>
      {full && (
        <div className="grid grid-cols-12">
          {SEASONS.map((se, i) => (
            <div
              key={se.key}
              style={{ gridColumn: `${se.from + 1} / span ${se.length}` }}
              className={`flex flex-col items-center justify-end pb-1 ${i < 2 ? "border-r-[6px] border-limewash" : ""} ${
                se.key === "kharif" ? "bg-monsoon-wash" : se.key === "rabi" ? "bg-turmeric-wash" : "bg-rule"
              }`}
            >
              {se.key !== "summer" && <Pictogram id={se.key === "kharif" ? "rain" : "sun"} className="h-8 w-8" />}
              <span className="narrow text-sm font-bold" lang="hi">
                {RESULTS[se.key]}
              </span>
            </div>
          ))}
        </div>
      )}
      <div className={`grid grid-cols-12 ${full ? "mt-1" : ""}`}>
        {bar.map((crops, i) => (
          <span key={i} className={`${full ? "h-10" : "h-3.5"} ${crops.length ? "bg-crop" : "bg-soil"} ${gap(i)}`} />
        ))}
      </div>
      {full && (
        <div className="mt-1 grid grid-cols-12">
          {runs(bar).map((r) => (
            <div key={r.start} style={{ gridColumn: `${r.start + 1} / span ${r.length}` }} className="flex min-w-0 items-center justify-center">
              <Pics pics={r.crops.length ? picsFor(r.crops, "plus") : ["bare"]} className="h-8 w-8 min-w-0 shrink" />
            </div>
          ))}
        </div>
      )}
      {full && risk && <RiskRows risk={risk} />}
      <MonthAxis full={full} />
    </div>
  );
}

/** Says how far to trust the advice: an estimate from the numbers, or checked. Shown on the list and on every choice. */
function AdviceBadge({ label, note }: { label: string; note?: boolean }) {
  return (
    <p className="mt-2 flex items-center gap-2 text-lg font-bold text-soil" lang="hi">
      <span className="flex items-center gap-1.5 rounded-field border-2 border-dashed border-soil px-2.5 py-1">
        <Pictogram id="unknown" className="h-5 w-5" />
        {label}
      </span>
      {note && label === RESULTS.estimate && <span className="text-base font-semibold text-soil-soft">{RESULTS.estimateNote}</span>}
    </p>
  );
}

function Disclaimer() {
  return <p className="fixed inset-x-0 bottom-0 z-10 bg-turmeric px-4 py-2.5 text-center text-sm font-semibold text-soil">{DISCLAIMER}</p>;
}

function Detail({ c, risk, onBack }: { c: Choice; risk?: SeasonRisk; onBack: () => void }) {
  const s = c.strategy;
  const [open, setOpen] = useState<Row | null>(null);
  const [speaking, setSpeaking] = useState<Row | null>(null);
  const name = strategyName(s);
  const rows: { key: Row; label: string; icon: PictogramId; lines: string[] }[] = [
    { key: "good", label: RESULTS.good, icon: "yes", lines: goodLines(s) }, // a tick = checked; the thumbs-up is kept for "best choice"
    { key: "unknown", label: RESULTS.unknown, icon: "unknown", lines: unknownLines(s) },
    ...(risk ? [{ key: "vulnerable" as const, label: RESULTS.vulnerable, icon: "warning" as const, lines: vulnerableLines(s, risk) }] : []),
    { key: "expert", label: RESULTS.expert, icon: "expert", lines: expertLines(s) },
  ];

  useEffect(() => {
    speakHindi(`${name}। यह ${adviceLabel([adviceKind(s)])} है। छुकर सुनिए: ${rows.map((r) => r.label).join(", ")}।`);
    return stopSpeech;
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [name]);

  function tap(r: (typeof rows)[number]) {
    setOpen(r.key);
    setSpeaking(r.key);
    speakHindi(`${r.label}। ${r.lines.join(" ")}`, () => setSpeaking(null));
  }

  return (
    <main className="mx-auto flex w-full max-w-xl flex-1 flex-col px-4 pb-24 pt-3">
      <button
        onClick={() => {
          stopSpeech();
          onBack();
        }}
        className="flex items-center gap-1 self-start rounded-field border-2 border-soil px-3 py-1.5 text-base font-bold"
        lang="hi"
      >
        <svg aria-hidden viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2.4} strokeLinecap="round" strokeLinejoin="round" className="h-4 w-4">
          <path d="M15 5l-7 7 7 7" />
        </svg>
        {RESULTS.back}
      </button>

      <div className="mt-5 flex items-center gap-3">
        {c.top && <Pictogram id="thumbs_up" className="h-14 w-14 shrink-0" />}
        <div>
          <Pics pics={strategyPics(s)} className="h-12 w-12" />
          <h2 className="narrow mt-1 text-3xl font-extrabold leading-tight" lang="hi">
            {name}
          </h2>
          {c.current && (
            <p className="text-base font-semibold text-soil-soft" lang="hi">
              {RESULTS.current}
            </p>
          )}
          <AdviceBadge label={adviceLabel([adviceKind(s)])} />
        </div>
      </div>

      <div className="mt-5">
        <YearBar s={s} full risk={risk} />
      </div>

      <ol className="mt-6 border-t-2 border-soil">
        {rows.map((r) => (
          <li key={r.key} className="border-b border-rule">
            <button onClick={() => tap(r)} className="flex min-h-24 w-full items-center gap-4 py-3 text-left">
              <span className="flex h-16 w-16 shrink-0 items-center justify-center rounded-field border-2 border-soil bg-paper p-1.5">
                <Pictogram id={r.icon} />
              </span>
              <span className="narrow flex-1 text-2xl font-bold leading-tight" lang="hi">
                {r.label}
              </span>
              <SpeakerIcon className={`h-7 w-7 shrink-0 ${speaking === r.key ? "text-monsoon" : "text-soil-soft"}`} />
            </button>
            {open === r.key && (
              <ul className="space-y-1.5 pb-4 pl-5 pr-2 text-lg" lang="hi">
                {r.lines.map((l, i) => (
                  <li key={i} className="border-l-4 border-rule pl-3">
                    {l}
                  </li>
                ))}
              </ul>
            )}
          </li>
        ))}
      </ol>

      <details className="mt-5">
        <summary className="cursor-pointer text-sm font-semibold text-monsoon underline underline-offset-2" lang="hi">
          {RESULTS.forExperts}
        </summary>
        <ul className="mt-2 space-y-2.5 text-sm">
          {s.evidence.map((e, i) => (
            <li key={i} className="border-l-4 border-rule pl-3">
              <p>{e.claim}</p>
              <p className="text-soil-soft">
                Source: {e.dataset ?? "not given"}. Period: {e.period ?? "not given"}. Check status: {e.validity}.
              </p>
            </li>
          ))}
        </ul>
      </details>
      <Disclaimer />
    </main>
  );
}

function Learn({ risk, onBack }: { risk?: SeasonRisk; onBack: () => void }) {
  const [open, setOpen] = useState<string | null>(null);
  const [speaking, setSpeaking] = useState<string | null>(null);
  const items = explainers(risk);

  useEffect(() => {
    speakHindi(`${RESULTS.learnTitle} किसी तस्वीर को छुकर सुनिए।`);
    return stopSpeech;
  }, []);

  return (
    <main className="mx-auto flex w-full max-w-xl flex-1 flex-col px-4 pb-24 pt-3">
      <button
        onClick={() => {
          stopSpeech();
          onBack();
        }}
        className="flex items-center gap-1 self-start rounded-field border-2 border-soil px-3 py-1.5 text-base font-bold"
        lang="hi"
      >
        <svg aria-hidden viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2.4} strokeLinecap="round" strokeLinejoin="round" className="h-4 w-4">
          <path d="M15 5l-7 7 7 7" />
        </svg>
        {RESULTS.back}
      </button>
      <h1 className="narrow mt-6 text-3xl font-extrabold leading-tight" lang="hi">
        {RESULTS.learnTitle}
      </h1>
      <ol className="mt-5 border-t-2 border-soil">
        {items.map((e) => (
          <li key={e.key} className="border-b border-rule">
            <button
              onClick={() => {
                setOpen(e.key);
                setSpeaking(e.key);
                speakHindi(`${e.title}। ${e.text}`, () => setSpeaking(null));
              }}
              className="flex min-h-24 w-full items-center gap-4 py-3 text-left"
            >
              <span className="flex h-16 min-w-16 shrink-0 items-center justify-center gap-1 rounded-field border-2 border-soil bg-paper p-1.5">
                {e.pics.map((id, i) => (
                  <Pictogram key={i} id={id} className={id === "plus" ? "h-4 w-4" : e.pics.length > 1 ? "h-8 w-8" : "h-full w-full"} />
                ))}
              </span>
              <span className="narrow flex-1 text-2xl font-bold leading-tight" lang="hi">
                {e.title}
              </span>
              <SpeakerIcon className={`h-7 w-7 shrink-0 ${speaking === e.key ? "text-monsoon" : "text-soil-soft"}`} />
            </button>
            {open === e.key && (
              <p className="border-l-4 border-rule pb-4 pl-3 pr-2 text-lg" lang="hi">
                {e.text}
              </p>
            )}
          </li>
        ))}
      </ol>
      <Disclaimer />
    </main>
  );
}

export default function Results({ answers, onRestart }: { answers: Initial; onRestart: () => void }) {
  const [result, setResult] = useState<Result | null>(null);
  const [failed, setFailed] = useState(false);
  const [attempt, setAttempt] = useState(0);
  const [selected, setSelected] = useState<string | null>(null);
  const [learn, setLearn] = useState(false);

  const [waking, setWaking] = useState(false);

  useEffect(() => {
    let alive = true;
    let controller: AbortController | null = null; // the attempt in flight, so leaving the page cancels it
    const body = JSON.stringify({
      location: answers.location,
      lat: answers.lat,
      lon: answers.lon,
      current_rotation: answers.rotation,
      water_source: answers.water_source,
      priorities: [answers.priority1, answers.priority2].filter((p, i, all) => p && all.indexOf(p) === i),
      constraints: { water_availability: answers.water_level, equipment: answers.equipment, market: answers.market },
    });
    (async () => {
      // The free API host sleeps when idle and takes up to about a minute to wake, so retry quietly before giving up.
      // Network errors, time-outs and 5xx answers are retried; a 4xx means the request itself is wrong, so it is not.
      for (let i = 0; i < RETRY_DELAYS_MS.length; i++) {
        if (i > 0) {
          if (i === 1 && alive) {
            setWaking(true);
            speakHindi(RESULTS.waking);
          }
          await new Promise((r) => setTimeout(r, RETRY_DELAYS_MS[i]));
        }
        if (!alive) return;
        const attemptController = new AbortController();
        controller = attemptController;
        const timer = setTimeout(() => attemptController.abort(), ATTEMPT_TIMEOUT_MS);
        try {
          const res = await fetch(`${API_URL}/compare`, {
            method: "POST",
            headers: { "content-type": "application/json" },
            body,
            signal: attemptController.signal,
          });
          if (res.status >= 400 && res.status < 500) break; // not worth retrying
          if (!res.ok) continue;
          const data: Result = await res.json();
          if (!alive) return;
          setWaking(false);
          setResult(data);
          speakHindi(data.served ? summarySpeech(choices(data), nearestPhrase(data)) : RESULTS.outOfArea);
          return;
        } catch {
          if (!alive) return;
        } finally {
          clearTimeout(timer);
        }
      }
      if (alive) {
        setWaking(false);
        setFailed(true);
      }
    })();
    return () => {
      alive = false;
      controller?.abort();
      stopSpeech();
    };
  }, [answers, attempt]);

  const list = result?.served ? choices(result) : [];
  const chosen = list.find((c) => c.strategy.id === selected);

  if (learn) return <Learn risk={result?.season_risk} onBack={() => setLearn(false)} />;
  if (chosen) return <Detail c={chosen} risk={result?.season_risk} onBack={() => setSelected(null)} />;

  return (
    <main className="mx-auto flex w-full max-w-xl flex-1 flex-col px-4 pb-24 pt-3">
      <div className="flex items-center justify-between gap-3">
        <button
          onClick={() => {
            stopSpeech();
            onRestart();
          }}
          className="rounded-field border-2 border-soil px-3 py-1.5 text-base font-bold"
          lang="hi"
        >
          {RESULTS.again}
        </button>
        {result?.served && (
          <button
            onClick={() => speakHindi(summarySpeech(list, result ? nearestPhrase(result) : null))}
            className="flex items-center gap-2 rounded-field border-2 border-monsoon px-3 py-1.5 text-base font-bold text-monsoon"
            lang="hi"
          >
            <SpeakerIcon className="h-5 w-5" />
            {RESULTS.replay}
          </button>
        )}
      </div>

      <h1 className="narrow mt-6 text-3xl font-extrabold leading-tight" lang="hi">
        {RESULTS.title}
      </h1>

      {result?.served && nearestPhrase(result) && (
        <p className="mt-1 flex items-center gap-2 text-lg font-semibold text-soil-soft" lang="hi">
          <Pictogram id="pin" className="h-6 w-6" />
          {RESULTS.where}: {nearestPhrase(result)}
        </p>
      )}

      {result?.served && <AdviceBadge label={adviceLabel(list.filter((c) => !c.strategy.incomplete).map((c) => adviceKind(c.strategy)))} note />}

      {!result && !failed && (
        <p className="mt-6 text-xl font-semibold text-soil-soft" lang="hi" role="status">
          {waking ? RESULTS.waking : RESULTS.loading}
        </p>
      )}
      {failed && (
        <div className="mt-6 border-l-4 border-almanac p-3" role="alert">
          <p className="text-lg font-semibold text-almanac" lang="hi">
            {RESULTS.error}
          </p>
          <button
            onClick={() => {
              setFailed(false);
              setAttempt((n) => n + 1);
            }}
            className="mt-3 rounded-field border-2 border-almanac px-3 py-1.5 text-base font-bold text-almanac"
            lang="hi"
          >
            {RESULTS.retry}
          </button>
        </div>
      )}
      {result && !result.served && (
        <div className="mt-6 border-l-4 border-turmeric bg-turmeric-wash p-3">
          <p className="text-lg font-semibold" lang="hi">
            {RESULTS.outOfArea}
          </p>
          <p className="mt-2 text-sm text-soil-soft">{result.reason}</p>
        </div>
      )}

      {list.length > 0 && (
        <>
          <p className="mt-2 text-lg text-soil-soft" lang="hi">
            {RESULTS.tapHint}
          </p>
          <ul className="mt-4 space-y-3">
            {list.map((c) => (
              <li key={c.strategy.id}>
                <button
                  onClick={() => setSelected(c.strategy.id)}
                  className={`flex w-full items-center gap-3 rounded-field bg-paper text-left ${c.top ? "border-4 border-soil p-2.5" : "border-2 border-soil p-3"}`}
                >
                  <span className="flex h-14 w-14 shrink-0 items-center justify-center">
                    {c.top ? (
                      <Pictogram id="thumbs_up" />
                    ) : c.strategy.incomplete ? (
                      <Pictogram id="unknown" />
                    ) : null}
                  </span>
                  <span className="min-w-0 flex-1">
                    <Pics pics={strategyPics(c.strategy)} className="h-10 w-10" />
                    <span className="narrow mt-1 block text-xl font-bold leading-tight" lang="hi">
                      {strategyName(c.strategy)}
                    </span>
                    {(c.current || c.strategy.incomplete) && (
                      <span className="block text-sm font-semibold text-soil-soft" lang="hi">
                        {c.strategy.incomplete ? RESULTS.notRanked : RESULTS.current}
                      </span>
                    )}
                    <span className="mt-2 block">
                      <YearBar s={c.strategy} />
                    </span>
                  </span>
                </button>
              </li>
            ))}
          </ul>
          <button
            onClick={() => {
              stopSpeech();
              setLearn(true);
            }}
            className="mt-5 flex w-full items-center gap-4 border-y-2 border-soil py-4 text-left"
          >
            <span className="flex h-14 w-14 shrink-0 items-center justify-center">
              <Pictogram id="unknown" />
            </span>
            <span className="narrow flex-1 text-2xl font-bold" lang="hi">
              {RESULTS.learn}
            </span>
          </button>
        </>
      )}
      <Disclaimer />
    </main>
  );
}
