"use client";

import { useState } from "react";

// Where the engine API runs. Set NEXT_PUBLIC_API_URL for a deployed build.
const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8000";

const DISCLAIMER =
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
  soybean: "soybean",
  cotton: "cotton",
  chickpea: "chickpea",
  pigeon_pea: "pigeon pea",
  sorghum_rabi: "winter sorghum",
  sorghum_kharif: "sorghum",
  sunn_hemp: "sunn hemp",
  horse_gram: "horse gram",
  fallow: "empty field",
};
const CONFIDENCE_TEXT: Record<string, string> = {
  green: "Well supported",
  yellow: "Partly supported",
  grey: "Mostly unverified inputs",
};
const CONFIDENCE_STYLE: Record<string, string> = {
  green: "bg-emerald-100 text-emerald-900",
  yellow: "bg-amber-100 text-amber-900",
  grey: "bg-stone-200 text-stone-700",
};
const VALIDITY_STYLE: Record<string, string> = {
  valid: "bg-emerald-100 text-emerald-900",
  degraded: "bg-amber-100 text-amber-900",
  unverified: "bg-stone-200 text-stone-700",
};

type Component = { score: number | null; status: string; validity: string; weight: number };
type Evidence = {
  claim: string;
  dataset?: string;
  period?: string;
  resolution?: string;
  validity: string;
  gap?: string;
  topic?: string;
};
type Strategy = {
  id: string;
  name: string;
  crops: string[];
  note: string;
  duplicate_of: string | null;
  total_score: number;
  score_band: [number, number];
  rank_stability: number;
  confidence_label: string;
  components: Record<string, Component>;
  evidence: Evidence[];
  data_coverage: number;
  incomplete: boolean;
  card: {
    why_suggested: string;
    evidence: string[];
    benefits: string[];
    gaps: string[];
    risks_for_local_review: string[];
  };
  variants: Record<string, { total_score: number | null }>;
};
type Result = {
  served: boolean;
  reason?: string;
  location: { nearest: string | null; distance_km: number };
  ranking: string[];
  tied_with_top: string[];
  weights_used: Record<string, number>;
  strategies: Strategy[];
  site_evidence: Evidence[];
};

function Select(props: {
  label: string;
  value: string;
  options: string[][];
  onChange: (v: string) => void;
  allowEmpty?: string;
}) {
  return (
    <label className="block text-sm font-medium text-stone-800">
      {props.label}
      <select
        className="mt-1 block w-full rounded-lg border border-stone-300 bg-white px-3 py-2.5 text-base text-stone-900"
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

function ValidityTag({ validity }: { validity: string }) {
  return (
    <span className={`rounded px-1.5 py-0.5 text-xs font-medium ${VALIDITY_STYLE[validity] ?? VALIDITY_STYLE.unverified}`}>
      {validity}
    </span>
  );
}

function EvidenceLine({ e }: { e: Evidence }) {
  return (
    <li className="border-l-2 border-stone-300 pl-3">
      <p className="text-sm text-stone-900">{e.claim}</p>
      <p className="mt-1 flex flex-wrap items-center gap-x-2 gap-y-1 text-xs text-stone-600">
        <ValidityTag validity={e.validity} />
        {[e.dataset, e.period, e.resolution].filter(Boolean).join(" · ")}
      </p>
    </li>
  );
}

function List({ title, items }: { title: string; items: string[] }) {
  if (!items.length) return null;
  return (
    <div>
      <h4 className="text-sm font-semibold text-stone-900">{title}</h4>
      <ul className="mt-1 list-disc space-y-1 pl-5 text-sm text-stone-800">
        {items.map((item, i) => (
          <li key={i}>{item}</li>
        ))}
      </ul>
    </div>
  );
}

function StrategyCard({ s, rank, tied }: { s: Strategy; rank: number | null; tied: boolean }) {
  const crops = s.crops.map((c) => CROP_LABELS[c] ?? c).join(s.id === "S2" ? " with " : ", then ");
  const variants = Object.entries(s.variants);
  return (
    <article className="rounded-xl border border-stone-300 bg-white p-4 shadow-sm">
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="text-xs font-semibold uppercase tracking-wide text-emerald-800">
            {s.incomplete ? "Not ranked: too little data" : tied ? "Joint top" : rank ? `Rank ${rank}` : ""}
            {s.id === "S0" ? " · what you do now" : ""}
          </p>
          <h3 className="mt-0.5 text-lg font-semibold text-stone-900">{s.name}</h3>
          <p className="text-sm text-stone-600">{crops}</p>
        </div>
        <div className="shrink-0 text-right">
          <p className="text-2xl font-bold tabular-nums text-stone-900">{s.total_score.toFixed(0)}</p>
          <p className="text-xs text-stone-600">
            {s.score_band[0].toFixed(0)} to {s.score_band[1].toFixed(0)} across years
          </p>
        </div>
      </div>

      <p className="mt-2 flex flex-wrap items-center gap-2 text-xs">
        <span className={`rounded px-2 py-0.5 font-medium ${CONFIDENCE_STYLE[s.confidence_label]}`}>
          {CONFIDENCE_TEXT[s.confidence_label] ?? s.confidence_label}
        </span>
        <span className="text-stone-600">Scored on {(s.data_coverage * 100).toFixed(0)}% of the data that matters to you</span>
      </p>
      {s.duplicate_of && (
        <p className="mt-2 text-sm text-stone-700">This is the same rotation as your current one.</p>
      )}
      {s.note && <p className="mt-2 text-sm text-stone-700">{s.note}</p>}
      <p className="mt-2 text-sm text-stone-800">{s.card.why_suggested}</p>

      <dl className="mt-3 space-y-1.5">
        {Object.entries(s.components).map(([key, c]) => (
          <div key={key} className="grid grid-cols-[9.5rem_1fr_2.5rem] items-center gap-2 text-xs">
            <dt className="text-stone-700">{COMPONENT_LABELS[key] ?? key}</dt>
            <dd className="h-2 overflow-hidden rounded bg-stone-200">
              {c.score !== null && <div className="h-full bg-emerald-700" style={{ width: `${c.score}%` }} />}
            </dd>
            <dd className="text-right tabular-nums text-stone-800">{c.score === null ? "no data" : c.score.toFixed(0)}</dd>
          </div>
        ))}
      </dl>

      <div className="mt-3 space-y-3">
        <List title="What we do not know" items={s.card.gaps} />
        <List title="Check with a local expert" items={s.card.risks_for_local_review} />
      </div>

      <details className="mt-3">
        <summary className="cursor-pointer text-sm font-medium text-emerald-900">Evidence and benefits</summary>
        <div className="mt-2 space-y-3">
          <List title="Benefits" items={s.card.benefits} />
          <ul className="space-y-2">
            {s.evidence.map((e, i) => (
              <EvidenceLine key={i} e={e} />
            ))}
          </ul>
        </div>
      </details>

      {variants.length > 0 && (
        <div className="mt-3 rounded-lg bg-stone-100 p-3 text-sm text-stone-800">
          <p className="font-medium">Other second crops (scored on less data)</p>
          <ul className="mt-1 space-y-0.5">
            {variants.map(([crop, v]) => (
              <li key={crop}>
                {CROP_LABELS[crop] ?? crop}: {v.total_score === null ? "no score" : v.total_score.toFixed(0)}
              </li>
            ))}
          </ul>
        </div>
      )}
    </article>
  );
}

export default function FieldShift() {
  const [location, setLocation] = useState("akola");
  const [rotation, setRotation] = useState("soybean_fallow");
  const [waterSource, setWaterSource] = useState("rainfed");
  const [priority1, setPriority1] = useState("water_saving");
  const [priority2, setPriority2] = useState("");
  const [waterLevel, setWaterLevel] = useState("low");
  const [equipment, setEquipment] = useState("basic");
  const [market, setMarket] = useState("mandi");
  const [result, setResult] = useState<Result | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function compare(e: React.FormEvent) {
    e.preventDefault();
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

  const ranked = result?.served
    ? [...result.strategies].sort((a, b) => {
        const ra = result.ranking.indexOf(a.id);
        const rb = result.ranking.indexOf(b.id);
        return (ra < 0 ? 99 : ra) - (rb < 0 ? 99 : rb);
      })
    : [];
  const tie = result?.served && result.tied_with_top.length > 1;

  return (
    <div className="mx-auto w-full max-w-xl flex-1 px-4 pb-28 pt-6">
      <header>
        <h1 className="text-2xl font-bold text-stone-900">Field Shift</h1>
        <p className="mt-1 text-sm text-stone-700">
          Compare four ways to use your field through the year, with the evidence and the unknowns for each.
        </p>
      </header>

      <form onSubmit={compare} className="mt-5 space-y-4 rounded-xl border border-stone-300 bg-white p-4 shadow-sm">
        <Select label="Where is your farm?" value={location} options={LOCATIONS} onChange={setLocation} />
        <Select label="What do you grow now?" value={rotation} options={ROTATIONS} onChange={setRotation} />
        <Select label="Where does your water come from?" value={waterSource} options={WATER_SOURCES} onChange={setWaterSource} />
        <Select label="What matters most to you?" value={priority1} options={PRIORITIES} onChange={setPriority1} />
        <Select
          label="Second priority (optional)"
          value={priority2}
          options={PRIORITIES.filter(([v]) => v !== priority1)}
          onChange={setPriority2}
          allowEmpty="None"
        />
        <Select label="How much water is available?" value={waterLevel} options={WATER_LEVELS} onChange={setWaterLevel} />
        <Select label="Equipment" value={equipment} options={EQUIPMENT} onChange={setEquipment} />
        <Select label="Where do you sell?" value={market} options={MARKETS} onChange={setMarket} />
        <button
          type="submit"
          disabled={loading}
          className="w-full rounded-lg bg-emerald-800 px-4 py-3 text-base font-semibold text-white disabled:opacity-60"
        >
          {loading ? "Comparing…" : "Compare rotations"}
        </button>
      </form>

      {error && (
        <p role="alert" className="mt-4 rounded-lg border border-red-300 bg-red-50 p-3 text-sm text-red-900">
          {error}
        </p>
      )}

      {result && !result.served && (
        <p className="mt-4 rounded-lg border border-amber-300 bg-amber-50 p-3 text-sm text-amber-900">{result.reason}</p>
      )}

      {result?.served && (
        <section className="mt-6 space-y-4" aria-live="polite">
          {tie && (
            <p className="rounded-lg border border-amber-300 bg-amber-50 p-3 text-sm text-amber-900">
              No clear winner: {result.tied_with_top.length} rotations score within a few points of each other.
            </p>
          )}

          <div className="rounded-xl border border-stone-300 bg-white p-4 shadow-sm">
            <h2 className="text-base font-semibold text-stone-900">How your answers set the weights</h2>
            <dl className="mt-2 space-y-1.5">
              {Object.entries(result.weights_used).map(([key, w]) => (
                <div key={key} className="grid grid-cols-[9.5rem_1fr_2.5rem] items-center gap-2 text-xs">
                  <dt className="text-stone-700">{COMPONENT_LABELS[key] ?? key}</dt>
                  <dd className="h-2 overflow-hidden rounded bg-stone-200">
                    <div className="h-full bg-stone-600" style={{ width: `${w}%` }} />
                  </dd>
                  <dd className="text-right tabular-nums text-stone-800">{w.toFixed(0)}%</dd>
                </div>
              ))}
            </dl>
          </div>

          {ranked.map((s) => {
            const rank = result.ranking.indexOf(s.id);
            return (
              <StrategyCard
                key={s.id}
                s={s}
                rank={rank < 0 ? null : rank + 1}
                tied={Boolean(tie) && result.tied_with_top.includes(s.id)}
              />
            );
          })}

          <div className="rounded-xl border border-stone-300 bg-white p-4 shadow-sm">
            <h2 className="text-base font-semibold text-stone-900">About your area</h2>
            <p className="mt-1 text-xs text-stone-600">
              Satellite and weather data cover a wide area, not one field. Each line shows its source.
            </p>
            <ul className="mt-3 space-y-3">
              {result.site_evidence.map((e, i) => (
                <EvidenceLine key={i} e={e} />
              ))}
            </ul>
          </div>
        </section>
      )}

      <p className="fixed inset-x-0 bottom-0 border-t border-amber-300 bg-amber-100 px-4 py-2.5 text-center text-xs font-medium text-amber-950">
        {DISCLAIMER}
      </p>
    </div>
  );
}
