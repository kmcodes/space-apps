"use client";

// The app's language: Hindi (the default, the farmers' language) or English. One switch at the top of every screen.
// The choice is remembered in the browser. English text was drafted by Claude to match the Hindi, one string for one string.

import { createContext, useContext, useEffect, useState, type ReactNode } from "react";

export type Lang = "hi" | "en";
export type L = Record<Lang, string>; // a string in both languages

const KEY = "field-shift-lang";

const LangContext = createContext<{ lang: Lang; setLang: (l: Lang) => void }>({ lang: "hi", setLang: () => {} });

export function LangProvider({ children }: { children: ReactNode }) {
  // Hindi first, so the server and the first browser render agree; a saved choice is applied right after.
  const [lang, setLangState] = useState<Lang>("hi");

  useEffect(() => {
    try {
      const saved = window.localStorage.getItem(KEY);
      // eslint-disable-next-line react-hooks/set-state-in-effect
      if (saved === "en" || saved === "hi") setLangState(saved);
    } catch {
      // Storage can be blocked (private window); the choice then lasts until the page closes.
    }
  }, []);

  function setLang(l: Lang) {
    setLangState(l);
    try {
      window.localStorage.setItem(KEY, l);
    } catch {
      // ignore
    }
  }

  return <LangContext.Provider value={{ lang, setLang }}>{children}</LangContext.Provider>;
}

export const useLang = () => useContext(LangContext);

/** The switch at the top of every screen. Each name is written in its own language so anyone can find theirs. */
export function LangToggle() {
  const { lang, setLang } = useLang();
  const choices: { id: Lang; label: string; tag: string }[] = [
    { id: "hi", label: "हिन्दी", tag: "hi" },
    { id: "en", label: "English", tag: "en" },
  ];
  return (
    <div className="mx-auto flex w-full max-w-xl justify-end px-4 pt-3">
      <div role="group" aria-label="Language / भाषा" className="flex overflow-hidden rounded-field border-2 border-forest text-base font-bold">
        {choices.map((c) => (
          <button
            key={c.id}
            type="button"
            lang={c.tag}
            aria-pressed={lang === c.id}
            onClick={() => setLang(c.id)}
            className={`px-3 py-1 ${lang === c.id ? "bg-forest text-white" : "bg-paper text-forest"}`}
          >
            {c.label}
          </button>
        ))}
      </div>
    </div>
  );
}
