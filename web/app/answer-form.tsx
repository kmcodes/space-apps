"use client";

// "Tap to fill the form": the same questions as the voice call, as a form, for people who prefer to read and choose.
// Questions and choices come from the call script (call-script.ts), so they follow the language switch and always match
// the call. On submit the answers go to the same results page as the call (results.tsx).

import { useState } from "react";
import { STEPS, SCRIPTS, type Answers } from "./call-script";
import { useLang } from "./lang";

// The answers handed to the results page, from the call or from this form.
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

// The form has no map, so "is the red mark your farm?" is left out and the district is asked directly.
const FORM_STEPS = STEPS.filter((s) => s.id !== "farm");

// A sensible first choice for each question, so the form can be sent at once.
const DEFAULTS: Answers = {
  location: "akola",
  rotation: "soybean_fallow",
  water_source: "rainfed",
  priority1: "water_saving",
  priority2: "",
  water_level: "low",
  equipment: "basic",
  market: "mandi",
};

export default function AnswerForm({ onSubmit }: { onSubmit: (answers: Initial) => void }) {
  const { lang } = useLang();
  const S = SCRIPTS[lang];
  const [answers, setAnswers] = useState<Answers>(DEFAULTS);

  function set(id: string, value: string) {
    const next = { ...answers, [id]: value };
    if (id === "priority1" && next.priority2 === value) next.priority2 = ""; // the second priority cannot repeat the first
    setAnswers(next);
  }

  function submit(e: React.FormEvent) {
    e.preventDefault();
    const { location, rotation, water_source, priority1, priority2, water_level, equipment, market } = answers;
    onSubmit({ location, rotation, water_source, priority1, priority2, water_level, equipment, market });
  }

  return (
    <form onSubmit={submit} className="mx-auto w-full max-w-xl flex-1 px-4 pb-28 pt-4">
      <h1 className="narrow text-3xl font-extrabold leading-normal" lang={lang}>
        {S.formTitle}
      </h1>
      <div className="mt-4 space-y-4 border-t-2 border-soil pt-4">
        {FORM_STEPS.map((step) => (
          <label key={step.id} className="block text-lg font-semibold leading-normal" lang={lang}>
            {step.question[lang]}
            <select
              className="mt-1 block w-full rounded-field border-2 border-soil bg-paper px-3 py-3 text-lg font-normal text-soil"
              value={answers[step.id] ?? ""}
              onChange={(e) => set(step.id, e.target.value)}
              lang={lang}
            >
              {step.options(answers).map((o) => (
                <option key={o.value || "none"} value={o.value}>
                  {o.label[lang]}
                </option>
              ))}
            </select>
          </label>
        ))}
      </div>
      <button
        type="submit"
        className="mt-6 w-full rounded-field border-[3px] border-action bg-action px-4 py-3.5 text-2xl font-extrabold leading-normal text-white"
        lang={lang}
      >
        <span className="narrow">{S.formSubmit}</span>
      </button>
    </form>
  );
}
