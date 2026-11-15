// Pictograms for the voice call. The farmers cannot read, so each answer is a picture first.
// One style: dark soil outline, crop green, monsoon blue, turmeric, on a 48 x 48 grid.
// These are drawn placeholders. Real crop drawings or photos should replace the crop ones (docs/VOICE_APP_PLAN.md).

import type { ReactNode } from "react";

export type PictogramId =
  | "pin"
  | "soybean"
  | "cotton"
  | "chickpea"
  | "bare"
  | "pigeon_pea"
  | "sorghum"
  | "plus"
  | "thumbs_up"
  | "unknown"
  | "expert"
  | "sun"
  | "then"
  | "rain"
  | "well"
  | "canal"
  | "water_saving"
  | "forage"
  | "nitrogen"
  | "erosion"
  | "organic_matter"
  | "market_income"
  | "none"
  | "level1"
  | "level2"
  | "level3"
  | "yes"
  | "no"
  | "mandi"
  | "buyer"
  | "own_use";

function Bars({ n }: { n: number }) {
  return (
    <>
      {[0, 1, 2].map((i) => (
        <rect key={i} x={9 + i * 12} y={40 - (i + 1) * 10} width="8" height={(i + 1) * 10} className={`stroke-soil ${i < n ? "fill-monsoon" : "fill-rule"}`} />
      ))}
    </>
  );
}

const SHAPES: Record<PictogramId, ReactNode> = {
  pin: (
    <>
      <path d="M24 44C16 34 12 28 12 22a12 12 0 0 1 24 0c0 6-4 12-12 22z" className="fill-almanac stroke-soil" />
      <circle cx="24" cy="22" r="4.5" className="fill-paper stroke-soil" />
    </>
  ),
  soybean: (
    <>
      <path d="M24 42V22" className="stroke-soil" />
      <path d="M24 28C16 28 12 22 12 15c8 0 12 5 12 13z" className="fill-crop stroke-soil" />
      <path d="M24 22c8 0 12-6 12-13-8 0-12 5-12 13z" className="fill-crop stroke-soil" />
      <path d="M24 36c-5 0-8 2-9 6 5 0 8-2 9-6z" className="fill-turmeric-wash stroke-soil" />
      <path d="M24 34c5 0 8 2 9 6-5 0-8-2-9-6z" className="fill-turmeric-wash stroke-soil" />
      <path d="M6 42h36" className="stroke-soil" />
    </>
  ),
  cotton: (
    <>
      <path d="M24 42V30" className="stroke-soil" />
      <path d="M15 28h18l-4 7h-10z" className="fill-soil-soft stroke-soil" />
      <circle cx="17" cy="21" r="6" className="fill-paper stroke-soil" />
      <circle cx="31" cy="21" r="6" className="fill-paper stroke-soil" />
      <circle cx="24" cy="14" r="6" className="fill-paper stroke-soil" />
      <path d="M6 42h36" className="stroke-soil" />
    </>
  ),
  chickpea: (
    <>
      <path d="M24 42V26M24 32l-9-9M24 32l9-9" className="stroke-soil" />
      <ellipse cx="15" cy="19" rx="5" ry="6" className="fill-turmeric stroke-soil" />
      <ellipse cx="33" cy="19" rx="5" ry="6" className="fill-turmeric stroke-soil" />
      <path d="M24 26c-5 0-8-3-8-7 5 0 8 3 8 7z" className="fill-crop stroke-soil" />
      <path d="M24 26c5 0 8-3 8-7-5 0-8 3-8 7z" className="fill-crop stroke-soil" />
      <path d="M6 42h36" className="stroke-soil" />
    </>
  ),
  bare: (
    <>
      <rect x="6" y="24" width="36" height="18" className="fill-soil stroke-soil" />
      <path d="M12 30l5 4-3 5M24 28l4 5-4 4M34 31l3 4-2 4" className="stroke-limewash" strokeWidth={1.6} />
    </>
  ),
  pigeon_pea: (
    <>
      <path d="M24 42V14" className="stroke-soil" />
      <path d="M24 35c-7 0-10-3-10-8 7 0 10 3 10 8z" className="fill-crop stroke-soil" />
      <path d="M24 28c7 0 10-3 10-8-7 0-10 3-10 8z" className="fill-crop stroke-soil" />
      <circle cx="17" cy="15" r="3.5" className="fill-turmeric stroke-soil" />
      <circle cx="31" cy="13" r="3.5" className="fill-turmeric stroke-soil" />
      <circle cx="24" cy="8" r="3.5" className="fill-turmeric stroke-soil" />
      <path d="M6 42h36" className="stroke-soil" />
    </>
  ),
  sorghum: (
    <>
      <path d="M24 42V20" className="stroke-soil" />
      <ellipse cx="24" cy="13" rx="6" ry="9" className="fill-soil-soft stroke-soil" />
      <path d="M24 37c-8 0-12-4-14-9M24 32c8 0 12-4 14-9" className="stroke-crop" strokeWidth={3} />
      <path d="M6 42h36" className="stroke-soil" />
    </>
  ),
  plus: <path d="M24 12v24M12 24h24" className="stroke-soil-soft" />,
  thumbs_up: (
    <>
      <path d="M8 22h8v19H8z" className="fill-paper stroke-soil" />
      <path d="M16 24l7-14c3 0 5 2 4 6l-1 6h11c3 0 5 3 4 6l-3 12c-1 3-3 4-5 4H16z" className="fill-crop stroke-soil" />
    </>
  ),
  unknown: (
    <>
      <circle cx="24" cy="24" r="17" className="fill-turmeric-wash stroke-soil" />
      <path d="M18.5 19a5.5 5.5 0 1 1 8.5 4.6c-2 1.3-3 2.4-3 4.9" className="stroke-soil" strokeWidth={3} />
      <path d="M24 35v.5" className="stroke-soil" strokeWidth={3.5} />
    </>
  ),
  expert: (
    <>
      <circle cx="17" cy="17" r="6" className="fill-paper stroke-soil" />
      <path d="M5 41c0-8 5-12 12-12s12 4 12 12z" className="fill-monsoon-wash stroke-soil" />
      <path d="M28 7h15v11h-6l-4 4v-4h-5z" className="fill-paper stroke-soil" />
    </>
  ),
  sun: (
    <>
      <circle cx="24" cy="29" r="8" className="fill-turmeric stroke-soil" />
      <path d="M24 10v6M9 29h6M33 29h6M13.5 18.5l4 4M34.5 18.5l-4 4M6 40h36" className="stroke-soil" />
    </>
  ),
  then: <path d="M8 24h30M30 15l9 9-9 9" className="stroke-soil-soft" />,
  rain: (
    <>
      <path d="M13 28a6 6 0 0 1 1-12 9 9 0 0 1 17 2 5.5 5.5 0 0 1 1 10z" className="fill-monsoon-wash stroke-monsoon" />
      <path d="M16 34l-2 7M25 34l-2 7M34 34l-2 7" className="stroke-monsoon" />
    </>
  ),
  well: (
    <>
      <path d="M12 30h24v13H12z" className="fill-paper stroke-soil" />
      <path d="M12 30a12 4 0 0 1 24 0" className="fill-rule stroke-soil" />
      <path d="M14 30V12M34 30V12M12 12h24M24 12v11" className="stroke-soil" />
      <path d="M20 23h8l-1 7h-6z" className="fill-monsoon stroke-soil" />
    </>
  ),
  canal: (
    <>
      <path d="M6 14q4-4 8 0t8 0t8 0t8 0" className="stroke-monsoon" />
      <path d="M6 23q4-4 8 0t8 0t8 0t8 0" className="stroke-monsoon" />
      <path d="M6 32q4-4 8 0t8 0t8 0t8 0" className="stroke-monsoon" />
      <path d="M4 42h40" className="stroke-soil" />
      <path d="M8 42c0-4 1-6 2-7M12 42c0-3 0-5-1-6" className="stroke-crop" />
      <path d="M38 42c0-4 1-6 2-7M42 42c0-3 0-5-1-6" className="stroke-crop" />
    </>
  ),
  water_saving: (
    <>
      <path d="M24 5C32 15 36 22 36 29a12 12 0 0 1-24 0c0-7 4-14 12-24z" className="fill-monsoon-wash stroke-monsoon" />
      <path d="M18 30l5 5 9-10" className="stroke-soil" strokeWidth={3} />
    </>
  ),
  forage: (
    <>
      <path d="M12 42C12 30 14 22 10 14M20 42C20 28 22 18 22 8M28 42C28 30 26 22 32 11M37 42C37 32 37 26 41 19" className="stroke-crop" strokeWidth={3} />
      <path d="M6 42h36" className="stroke-soil" />
    </>
  ),
  nitrogen: (
    <>
      <path d="M17 8h14l-2 7c6 4 10 10 10 18 0 5-3 9-8 9H17c-5 0-8-4-8-9 0-8 4-14 10-18z" className="fill-paper stroke-soil" />
      <path d="M17 15h14" className="stroke-soil" />
      <path d="M19 37c0-7 4-11 11-11 0 7-4 11-11 11z" className="fill-crop stroke-soil" />
    </>
  ),
  erosion: (
    <>
      <path d="M4 22l40 12v9H4z" className="fill-soil stroke-soil" />
      <path d="M10 17l5 2M21 21l5 2M32 25l5 2" className="stroke-monsoon" strokeWidth={3} />
      <path d="M14 8l-2 5M24 8l-2 5M34 8l-2 5" className="stroke-monsoon" />
    </>
  ),
  organic_matter: (
    <>
      <rect x="6" y="30" width="36" height="12" className="fill-soil stroke-soil" />
      <path d="M24 30V18" className="stroke-soil" />
      <path d="M24 23c-6 0-9-3-9-9 6 0 9 4 9 9z" className="fill-crop stroke-soil" />
      <path d="M24 20c6 0 9-3 9-9-6 0-9 4-9 9z" className="fill-crop stroke-soil" />
    </>
  ),
  market_income: (
    <>
      <circle cx="24" cy="24" r="17" className="fill-turmeric stroke-soil" />
      <text x="24" y="32" textAnchor="middle" fontSize="22" fontWeight="700" className="fill-soil stroke-none">
        ₹
      </text>
    </>
  ),
  none: (
    <>
      <circle cx="24" cy="24" r="16" className="stroke-soil-soft" />
      <path d="M13 35L35 13" className="stroke-almanac" strokeWidth={3} />
    </>
  ),
  level1: <Bars n={1} />,
  level2: <Bars n={2} />,
  level3: <Bars n={3} />,
  yes: (
    <>
      <circle cx="24" cy="24" r="17" className="fill-crop stroke-crop" />
      <path d="M15 25l6 6 12-13" className="stroke-white" strokeWidth={4} />
    </>
  ),
  no: (
    <>
      <circle cx="24" cy="24" r="17" className="fill-almanac stroke-almanac" />
      <path d="M17 17l14 14M31 17L17 31" className="stroke-white" strokeWidth={4} />
    </>
  ),
  mandi: (
    <>
      <path d="M6 17h36l-3 9H9z" className="fill-turmeric stroke-soil" />
      <path d="M10 26v16M38 26v16M6 42h36" className="stroke-soil" />
      <path d="M17 42v-8h14v8z" className="fill-paper stroke-soil" />
    </>
  ),
  buyer: (
    <>
      <path d="M3 17h25v20H3z" className="fill-paper stroke-soil" />
      <path d="M28 24h10l7 7v6H28z" className="fill-paper stroke-soil" />
      <circle cx="13" cy="38" r="4.5" className="fill-soil stroke-soil" />
      <circle cx="37" cy="38" r="4.5" className="fill-soil stroke-soil" />
    </>
  ),
  own_use: (
    <>
      <path d="M6 24L24 9l18 15" className="stroke-soil" />
      <path d="M11 21v21h26V21" className="fill-paper stroke-soil" />
      <path d="M20 42V30h8v12" className="fill-rule stroke-soil" />
    </>
  ),
};

export function Pictogram({ id, className = "h-full w-full" }: { id: PictogramId; className?: string }) {
  return (
    <svg aria-hidden viewBox="0 0 48 48" fill="none" strokeWidth={2.2} strokeLinecap="round" strokeLinejoin="round" className={className}>
      {SHAPES[id]}
    </svg>
  );
}

export function MicIcon({ className }: { className?: string }) {
  return (
    <svg aria-hidden viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round" className={className}>
      <rect x="8.5" y="2.5" width="7" height="12" rx="3.5" fill="currentColor" />
      <path d="M4.5 11.5a7.5 7.5 0 0 0 15 0M12 19v2.5M8.5 21.5h7" />
    </svg>
  );
}

export function SpeakerIcon({ className }: { className?: string }) {
  return (
    <svg aria-hidden viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.8} strokeLinecap="round" strokeLinejoin="round" className={className}>
      <path d="M4 10v4h4l5 4V6L8 10z" />
      <path d="M16.5 9a4 4 0 0 1 0 6M19 6.5a8 8 0 0 1 0 11" />
    </svg>
  );
}
