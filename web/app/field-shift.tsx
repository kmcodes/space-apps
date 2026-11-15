"use client";

import { useEffect, useState } from "react";

// Where the engine API runs. Set NEXT_PUBLIC_API_URL for a deployed build.
const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8000";

export const DISCLAIMER =
  "This tool supports, and does not replace, the judgement of farmers and local agricultural experts.";

const LOCATIONS = [
  ["akola", "Akola"],
  ["buldhana", "Buldhana"],
  ["washim", "Washim"],
];
const ROTATIONS = [
  ["soybean_fallow", "Soybean, then the field stays empty"],
  ["cotton", "Cotton"],
  ["soybean_chickpea", "Soybean, then chickpea"],
];
const WATER_SOURCES = [
  ["rainfed", "Rain only"],
  ["well", "Well or borewell"],
  ["canal_tank", "Canal or tank"],
];
const PRIORITIES = [
  ["water_saving", "Saving water"],
  ["forage", "Feed for animals"],
  ["nitrogen", "Less fertiliser (nitrogen fixing)"],
  ["erosion", "Less soil washing away"],
  ["organic_matter", "Healthier soil"],
  ["market_income", "Selling price"],
];
const WATER_LEVELS = [
  ["low", "Low"],
  ["medium", "Medium"],
  ["high", "High"],
];
const EQUIPMENT = [
  ["basic", "Basic tools"],
  ["sprayer", "Has a seeder or sprayer"],
];
const MARKETS = [
  ["mandi", "Sell at the local mandi"],
  ["buyer", "Sell to a nearby buyer"],
  ["own_use", "Own use"],
];
const COMPONENT_LABELS: Record<string, string> = {
  water_fit: "Water fit",
  timing_fit: "Sowing and harvest timing",
  bare_days: "Field kept covered",
  nitrogen: "Nitrogen from legumes",
  forage: "Feed for animals",
  market: "Price signal",
};
const CROP_LABELS: Record<string, string> = {
  soybean: "Soybean",
  cotton: "Cotton",
  chickpea: "Chickpea",
  pigeon_pea: "Pigeon pea",
  sorghum_rabi: "Winter sorghum",
  sorghum_kharif: "Sorghum",
  sunn_hemp: "Sunn hemp",
  horse_gram: "Horse gram",
  fallow: "Empty field",
};
const CONFIDENCE_TEXT: Record<string, string> = {
  green: "Inputs well supported",
  yellow: "Inputs partly supported",
  grey: "Inputs mostly unverified",
};
const VALIDITY_TEXT: Record<string, string> = {
  valid: "Checked source",
  degraded: "Coarse data",
  unverified: "Unverified input",
};
const MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
const MONTH_STARTS = [1, 32, 60, 91, 121, 152, 182, 213, 244, 274, 305, 335]; // day of year, non-leap
const YEAR = 365;

type Component = { score: number | null; status: string; validity: string; weight: number };
type Evidence = { claim: string; dataset?: string; period?: string; resolution?: string; validity: string };
type CalendarEntry = { crop: string; sow_doy: number; harvest_doy: number };
type Strategy = {
  id: string;
  name: string;
  crops: string[];
  note: string;
  duplicate_of: string | null;
  calendar?: CalendarEntry[];
  total_score: number;
  score_band: [number, number];
  confidence_label: string;
  components: Record<string, Component>;
  evidence: Evidence[];
  data_coverage: number;
  incomplete: boolean;
  card: {
    why_suggested: string;
    benefits: string[];
    gaps: string[];
    risks_for_local_review: string[];
  };
  variants: Record<string, { total_score: number | null }>;
};
type Result = {
  served: boolean;
  reason?: string;
  ranking: string[];
  tied_with_top: string[];
  weights_used: Record<string, number>;
  strategies: Strategy[];
  site_evidence: Evidence[];
  monsoon?: { onset_doy: number; withdrawal_doy: number };
};

function dateOf(doy: number) {
  const d = ((Math.round(doy) - 1) % YEAR) + 1;
  let m = 11;
  while (MONTH_STARTS[m] > d) m--;
  return `${d - MONTH_STARTS[m] + 1} ${MONTHS[m]}`;
}

// A crop that runs past 31 December is drawn as two pieces.
function pieces(entry: CalendarEntry) {
  const start = entry.sow_doy;
  const end = entry.harvest_doy;
  return end <= YEAR ? [[start, end]] : [[start, YEAR], [1, end - YEAR]];
}

function coveredDays(calendar: CalendarEntry[]) {
  const days = new Set<number>();
  for (const c of calendar) for (let d = c.sow_doy; d < c.harvest_doy; d++) days.add(d % YEAR);
  return days.size;
}

function overlaps(calendar: CalendarEntry[]) {
  return calendar.some((a, i) => calendar.some((b, j) => i < j && a.sow_doy < b.harvest_doy && b.sow_doy < a.harvest_doy));
}

const pct = (days: number) => `${(100 * days) / YEAR}%`;

/* The year board: one strip per rotation on a shared January to December axis.
   Dark = bare soil, green = a crop in the ground, blue band = the monsoon. */
function YearBoard({ strategies, monsoon }: { strategies: Strategy[]; monsoon?: Result["monsoon"] }) {
  return (
    <section aria-labelledby="year-heading" className="border-t-2 border-soil pt-3">
      <h2 id="year-heading" className="narrow text-xl font-bold">
        The field through the year
      </h2>
      <p className="mt-1 text-sm text-soil-soft">
        Green is a crop in the ground. Dark is bare soil.
        {monsoon && ` The blue band is the usual monsoon, about ${dateOf(monsoon.onset_doy)} to ${dateOf(monsoon.withdrawal_doy)}.`}
      </p>

      <div className="relative mt-3">
        {monsoon && (
          <div
            aria-hidden
            className="absolute inset-y-0 bg-monsoon-wash"
            style={{ left: pct(monsoon.onset_doy - 1), width: pct(monsoon.withdrawal_doy - monsoon.onset_doy) }}
          />
        )}
        <div aria-hidden className="relative grid grid-cols-12 text-center text-[0.7rem] font-medium text-soil-soft">
          {MONTHS.map((m) => (
            <span key={m} className="border-l border-rule first:border-l-0">
              {m[0]}
            </span>
          ))}
        </div>

        <ol className="relative mt-1 space-y-3 pb-1">
          {strategies.map((s) => {
            const calendar = s.calendar ?? [];
            const lanes = overlaps(calendar);
            const bare = YEAR - coveredDays(calendar);
            return (
              <li key={s.id}>
                <div className="flex items-baseline justify-between gap-2 text-sm">
                  <span className="font-semibold">{s.name}</span>
                  <span className="narrow shrink-0 font-semibold tabular-nums">{bare} days bare</span>
                </div>
                <div
                  role="img"
                  aria-label={`${s.name}: ${calendar.map((c) => `${CROP_LABELS[c.crop] ?? c.crop} from ${dateOf(c.sow_doy)} to ${dateOf(c.harvest_doy)}`).join("; ")}. ${bare} days with bare soil.`}
                  className="relative mt-1 h-7 overflow-hidden rounded-field bg-soil"
                >
                  {calendar.map((c, lane) =>
                    pieces(c).map(([start, end], i) => (
                      <div
                        key={`${c.crop}-${i}`}
                        className="absolute border-x border-limewash bg-crop"
                        style={{
                          left: pct(start - 1),
                          width: pct(end - start),
                          top: lanes ? `${(100 * lane) / calendar.length}%` : 0,
                          height: lanes ? `${100 / calendar.length}%` : "100%",
                        }}
                      />
                    )),
                  )}
                </div>
                <p className="mt-1 text-xs text-soil-soft">
                  {calendar.length
                    ? calendar.map((c) => `${CROP_LABELS[c.crop] ?? c.crop} ${dateOf(c.sow_doy)} to ${dateOf(c.harvest_doy)}`).join(", ")
                    : "No crop dates available"}
                </p>
              </li>
            );
          })}
        </ol>
      </div>
      <p className="mt-2 text-xs text-soil-soft">
        Dates are for a typical year from area weather and published crop durations, not for one field.
      </p>
    </section>
  );
}

function Field(props: { label: string; value: string; options: string[][]; onChange: (v: string) => void; allowEmpty?: string }) {
  return (
    <label className="block text-sm font-semibold">
      {props.label}
      <select
        className="mt-1 block w-full rounded-field border border-soil-soft bg-paper px-3 py-2.5 text-base font-normal text-soil"
        value={props.value}
        onChange={(e) => props.onChange(e.target.value)}
      >
        {props.allowEmpty !== undefined && <option value="">{props.allowEmpty}</option>}
        {props.options.map(([value, label]) => (
          <option key={value} value={value}>
            {label}
          </option>
        ))}
      </select>
    </label>
  );
}

function Bars({ rows, unit }: { rows: [string, number | null][]; unit: string }) {
  return (
    <dl className="mt-2 space-y-1.5">
      {rows.map(([key, value]) => (
        <div key={key} className="grid grid-cols-[10.5rem_1fr_3.25rem] items-center gap-2 text-sm">
          <dt>{COMPONENT_LABELS[key] ?? key}</dt>
          <dd className="h-1.5 bg-rule">{value !== null && <div className="h-full bg-soil" style={{ width: `${value}%` }} />}</dd>
          <dd className="narrow text-right font-semibold tabular-nums">{value === null ? "no data" : `${value.toFixed(0)}${unit}`}</dd>
        </div>
      ))}
    </dl>
  );
}

function EvidenceLine({ e }: { e: Evidence }) {
  const source = [e.dataset && `Source: ${e.dataset}`, e.period && e.period !== "n/a" && `Period: ${e.period}`, e.resolution && `Scale: ${e.resolution}`]
    .filter(Boolean)
    .join(". ");
  return (
    <li>
      <p className="text-sm">{e.claim}</p>
      <p className="mt-0.5 text-xs text-soil-soft">
        <span className="mr-1.5 border border-soil-soft px-1 font-semibold text-soil">{VALIDITY_TEXT[e.validity] ?? e.validity}</span>
        {source}
      </p>
    </li>
  );
}

function Notes({ title, items, tone }: { title: string; items: string[]; tone: "unknown" | "risk" }) {
  if (!items.length) return null;
  return (
    <div className={tone === "unknown" ? "border-l-4 border-turmeric bg-turmeric-wash p-3" : "border-l-4 border-almanac p-3"}>
      <h4 className="text-sm font-bold">{title}</h4>
      <ul className="mt-1 list-disc space-y-1 pl-5 text-sm">
        {items.map((item, i) => (
          <li key={i}>{item}</li>
        ))}
      </ul>
    </div>
  );
}

function StrategySection({ s, standing }: { s: Strategy; standing: string }) {
  const variants = Object.entries(s.variants);
  return (
    <article className="border-t-2 border-soil pt-3">
      <div className="flex items-start justify-between gap-3">
        <div>
          <h3 className="narrow text-xl font-bold leading-tight">{s.name}</h3>
          <p className={`mt-0.5 text-sm font-semibold ${s.incomplete ? "text-almanac" : "text-soil-soft"}`}>
            {standing}
            {s.id === "S0" && " (what you do now)"}
          </p>
        </div>
        <p className="shrink-0 text-right">
          <span className="narrow block text-4xl font-extrabold leading-none tabular-nums">{s.total_score.toFixed(0)}</span>
          <span className="text-xs text-soil-soft">
            out of 100, {s.score_band[0].toFixed(0)} to {s.score_band[1].toFixed(0)} across years
          </span>
        </p>
      </div>

      <p className="mt-2 text-sm">{s.card.why_suggested}</p>
      {s.duplicate_of && <p className="mt-1 text-sm">This is the same rotation as your current one.</p>}
      {s.note && <p className="mt-1 text-sm text-soil-soft">{s.note}</p>}
      <p className="mt-1 text-sm text-soil-soft">
        {CONFIDENCE_TEXT[s.confidence_label] ?? s.confidence_label}. Scored on {(s.data_coverage * 100).toFixed(0)}% of the data that
        matters to you.
      </p>

      <Bars rows={Object.entries(s.components).map(([k, c]) => [k, c.score])} unit="" />

      <div className="mt-3 space-y-2">
        <Notes title="What we do not know" items={s.card.gaps} tone="unknown" />
        <Notes title="Check with a local expert" items={s.card.risks_for_local_review} tone="risk" />
      </div>

      {variants.length > 0 && (
        <p className="mt-3 text-sm">
          <span className="font-semibold">Other second crops, scored on less data: </span>
          {variants.map(([crop, v]) => `${CROP_LABELS[crop] ?? crop} ${v.total_score === null ? "no score" : v.total_score.toFixed(0)}`).join(", ")}
        </p>
      )}

      <details className="mt-3">
        <summary className="cursor-pointer text-sm font-semibold text-monsoon underline underline-offset-2">Evidence and benefits</summary>
        {s.card.benefits.length > 0 && (
          <ul className="mt-2 list-disc space-y-1 pl-5 text-sm">
            {s.card.benefits.map((b, i) => (
              <li key={i}>{b}</li>
            ))}
          </ul>
        )}
        <ul className="mt-2 space-y-2.5">
          {s.evidence.map((e, i) => (
            <EvidenceLine key={i} e={e} />
          ))}
        </ul>
      </details>
    </article>
  );
}

// Answers handed over by the voice call. When given, the comparison runs on load.
export type Initial = Partial<{
  location: string;
  rotation: string;
  water_source: string;
  priority1: string;
  priority2: string;
  water_level: string;
  equipment: string;
  market: string;
  lat: number; // from the phone, rounded to about 100 m
  lon: number;
  example?: boolean; // the farmer is outside our area and picked a district to see an example
}>;

export default function FieldShift({ initial }: { initial?: Initial } = {}) {
  const [location, setLocation] = useState(initial?.location ?? "akola");
  const [rotation, setRotation] = useState(initial?.rotation ?? "soybean_fallow");
  const [waterSource, setWaterSource] = useState(initial?.water_source ?? "rainfed");
  const [priority1, setPriority1] = useState(initial?.priority1 ?? "water_saving");
  const [priority2, setPriority2] = useState(initial?.priority2 ?? "");
  const [waterLevel, setWaterLevel] = useState(initial?.water_level ?? "low");
  const [equipment, setEquipment] = useState(initial?.equipment ?? "basic");
  const [market, setMarket] = useState(initial?.market ?? "mandi");
  const [result, setResult] = useState<Result | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  function compare(e: React.FormEvent) {
    e.preventDefault();
    void run();
  }

  async function run() {
    setLoading(true);
    setError("");
    try {
      const res = await fetch(`${API_URL}/compare`, {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({
          location,
          current_rotation: rotation,
          water_source: waterSource,
          priorities: [priority1, priority2].filter((p, i, all) => p && all.indexOf(p) === i),
          constraints: { water_availability: waterLevel, equipment, market },
        }),
      });
      if (!res.ok) throw new Error(`The engine answered with an error (${res.status}).`);
      setResult(await res.json());
    } catch (err) {
      setResult(null);
      setError(err instanceof TypeError ? "Could not reach the engine. Check that it is running." : String((err as Error).message));
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    if (initial) void run();
    // Runs once on load; the call hands over complete answers.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const served = result?.served ? result : null;
  const ranked = served
    ? [...served.strategies].sort((a, b) => {
        const ra = served.ranking.indexOf(a.id);
        const rb = served.ranking.indexOf(b.id);
        return (ra < 0 ? 99 : ra) - (rb < 0 ? 99 : rb);
      })
    : [];
  const tie = served ? served.tied_with_top.length > 1 : false;

  function standing(s: Strategy) {
    if (!served) return "";
    if (s.incomplete) return "Not ranked: too little data";
    if (tie && served.tied_with_top.includes(s.id)) return "Joint top";
    return `Rank ${served.ranking.indexOf(s.id) + 1} of ${served.ranking.length}`;
  }

  return (
    <div className="mx-auto w-full max-w-xl flex-1 px-4 pb-24 pt-5">
      <header>
        <h1 className="narrow text-4xl font-extrabold leading-none">Field Shift</h1>
        <p className="mt-2 text-base text-soil-soft">
          Four ways to use your field through the year, with the evidence and the unknowns for each.
        </p>
      </header>

      <form onSubmit={compare} className="mt-5 space-y-3.5 border-t-2 border-soil pt-4">
        <Field label="Where is your farm?" value={location} options={LOCATIONS} onChange={setLocation} />
        <Field label="What do you grow now?" value={rotation} options={ROTATIONS} onChange={setRotation} />
        <Field label="Where does your water come from?" value={waterSource} options={WATER_SOURCES} onChange={setWaterSource} />
        <Field label="What matters most to you?" value={priority1} options={PRIORITIES} onChange={setPriority1} />
        <Field
          label="Second priority (optional)"
          value={priority2}
          options={PRIORITIES.filter(([v]) => v !== priority1)}
          onChange={setPriority2}
          allowEmpty="None"
        />
        <Field label="How much water is available?" value={waterLevel} options={WATER_LEVELS} onChange={setWaterLevel} />
        <Field label="Equipment" value={equipment} options={EQUIPMENT} onChange={setEquipment} />
        <Field label="Where do you sell?" value={market} options={MARKETS} onChange={setMarket} />
        <button
          type="submit"
          disabled={loading}
          className="w-full rounded-field bg-monsoon px-4 py-3 text-lg font-bold text-white disabled:opacity-60"
        >
          {loading ? "Comparing…" : "Compare rotations"}
        </button>
      </form>

      {error && (
        <p role="alert" className="mt-4 border-l-4 border-almanac p-3 text-sm font-semibold text-almanac">
          {error}
        </p>
      )}
      {result && !result.served && <p className="mt-4 border-l-4 border-turmeric bg-turmeric-wash p-3 text-sm">{result.reason}</p>}

      {served && (
        <div className="mt-7 space-y-7" aria-live="polite">
          <YearBoard strategies={ranked} monsoon={served.monsoon} />

          {tie && (
            <p className="border-l-4 border-turmeric bg-turmeric-wash p-3 text-sm font-semibold">
              No clear winner: {served.tied_with_top.length} rotations score within a few points of each other.
            </p>
          )}

          {ranked.map((s) => (
            <StrategySection key={s.id} s={s} standing={standing(s)} />
          ))}

          <section className="border-t-2 border-soil pt-3">
            <h2 className="narrow text-xl font-bold">How your answers set the weights</h2>
            <Bars rows={Object.entries(served.weights_used)} unit="%" />
          </section>

          <section className="border-t-2 border-soil pt-3">
            <h2 className="narrow text-xl font-bold">About your area</h2>
            <p className="mt-1 text-sm text-soil-soft">Satellite and weather data cover a wide area, not one field.</p>
            <ul className="mt-2 space-y-2.5">
              {served.site_evidence.map((e, i) => (
                <EvidenceLine key={i} e={e} />
              ))}
            </ul>
          </section>
        </div>
      )}

      <p className="fixed inset-x-0 bottom-0 bg-turmeric px-4 py-2.5 text-center text-sm font-semibold text-soil">{DISCLAIMER}</p>
    </div>
  );
}
