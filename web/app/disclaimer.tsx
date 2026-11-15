"use client";

// The "supports, does not replace" bar, fixed to the bottom of every screen, in the language the switch shows.
// START.md requires it to be visible at all times. The Hindi is machine-drafted and needs a native speaker's review.

import type { ReactNode } from "react";
import { useLang, type L } from "./lang";

export const DISCLAIMER: L = {
  hi: "यह परामर्श उपकरण किसानों और स्थानीय कृषि विशेषज्ञों की समझ का सहारा है, उसकी जगह नहीं।",
  en: "This tool supports, and does not replace, the judgement of farmers and local agricultural experts.",
};

// `notes`: optional one-line announcements (for example "no Hindi voice on this phone"), shown as white strips just above
// the bar so they never cover the buttons.
export default function Disclaimer({ notes = [] }: { notes?: { icon: ReactNode; text: string }[] }) {
  const { lang } = useLang();
  return (
    <div className="fixed inset-x-0 bottom-0 z-10">
      {notes.map((n) => (
        <p
          key={n.text}
          role="status"
          className="flex items-center justify-center gap-2 border-t-2 border-forest bg-paper px-4 py-1.5 text-center text-sm font-semibold text-forest"
          lang={lang}
        >
          <span aria-hidden className="shrink-0">{n.icon}</span>
          <span className="min-w-0">{n.text}</span>
        </p>
      ))}
      <p className="bg-forest px-4 py-2.5 text-center text-sm font-semibold text-white" lang={lang}>
        {DISCLAIMER[lang]}
      </p>
    </div>
  );
}

const ICON = "h-5 w-5";
export const SpeakerOffIcon = () => (
  <svg viewBox="0 0 24 24" className={ICON} fill="none" stroke="currentColor" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round">
    <path d="M4 10v4h4l5 4V6L8 10z" />
    <path d="M17 9l5 6M22 9l-5 6" />
  </svg>
);
export const MicOffIcon = () => (
  <svg viewBox="0 0 24 24" className={ICON} fill="none" stroke="currentColor" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round">
    <rect x="9" y="3" width="6" height="11" rx="3" />
    <path d="M5.5 11a6.5 6.5 0 0 0 13 0M12 17.5V21M3 3l18 18" />
  </svg>
);
