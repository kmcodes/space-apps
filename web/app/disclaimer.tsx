"use client";

// The "supports, does not replace" bar, fixed to the bottom of every screen, in the language the switch shows.
// START.md requires it to be visible at all times. The Hindi is machine-drafted and needs a native speaker's review.

import { useLang, type L } from "./lang";

export const DISCLAIMER: L = {
  hi: "यह परामर्श उपकरण किसानों और स्थानीय कृषि विशेषज्ञों की समझ का सहारा है, उसकी जगह नहीं।",
  en: "This tool supports, and does not replace, the judgement of farmers and local agricultural experts.",
};

export default function Disclaimer() {
  const { lang } = useLang();
  return (
    <p className="fixed inset-x-0 bottom-0 z-10 bg-forest px-4 py-2.5 text-center text-sm font-semibold text-white" lang={lang}>
      {DISCLAIMER[lang]}
    </p>
  );
}
