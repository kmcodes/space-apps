# Field Aid design notes

Every screen in `web/` follows this. Change it here first, then in `app/globals.css`.

The app is voice-first: see `docs/VOICE_APP_PLAN.md` for the conversation flow and the screens for non-readers. A style refresh is planned for the end.

Reference used while designing: https://github.com/funboy322/avoid-ai-design (its catalogue as a checklist; its scanner was not run).

## Where the look comes from

- **Subject:** a rainfed farmer in Vidarbha comparing how the field is used across one year. A utility screen, so legibility and density come before decoration.
- **Its world:** deep black cotton soil, the monsoon, mandi rate boards, and the wall calendars and crop calendars that farm offices print.
- **Most distinctive thing:** the year. What separates the rotations is when the field is covered and when it is bare.

## Layout

Lead with the year board: one strip per rotation on a shared January to December axis. Details follow as flat sections divided by a heavy rule, not as floating cards.

## Signature detail

The 12-month field strip: black for bare soil, one colour per crop for what is in the ground, a blue band for the monsoon, and a small legend under the strips. It is the only bold element. Keep everything else quiet.

## Colours

| Token | Value | Role |
|---|---|---|
| `soil` | #2b2320 | Text, heavy rules, bare-soil segments |
| `soil-soft` | #5f5049 | Secondary text |
| `limewash` | #f3f4f1 | Page ground |
| `paper` | #ffffff | Form fields |
| `rule` | #cfd2cc | Light dividers, bar tracks |
| `monsoon` | #1f5fa8 | Monsoon band (as `monsoon-wash`), buttons, links, focus outline |
| `crop` | #3f7d3a | The soybean green; crop-in-the-ground segments only. Not a general accent |
| `crop-soybean`, `crop-chickpea`, `crop-cotton`, `crop-pigeon_pea`, `crop-sorghum_*`, `crop-sunn_hemp`, `crop-horse_gram` | #3f7d3a, #d9a400, #3a9bb5, #d9692b, #7b4fa3, #c2527f, #8a6d3b | One colour per crop on the year bar and its legend (`@theme static` in `globals.css`) |
| `almanac` | #b3261e | Risks, errors, "not ranked" |
| `turmeric` | #f2c230 | Disclaimer banner; `turmeric-wash` behind "what we do not know" |

## Type

One family, Anek Devanagari, because it has Latin and Devanagari in one design: the Hindi and Marathi versions will look like the same product. Its narrow width (class `narrow`) is for headings and figures. Normal width is for reading text.

## Rules

- Sentence case everywhere. No all-caps labels.
- Sources are written as labelled text ("Source: ... Period: ... Scale: ..."), not as dot-separated strings.
- One corner radius (4 px) on fields, buttons and strips. No shadows.
- Score bars are `soil`. The crop colours (`--color-crop-<crop>` in `app/globals.css`) are reserved for crops on the calendar and its legend; each crop keeps one colour on every screen. They differ from bare soil and from the red of the risk markers. Add a colour when you add a crop (`tests/test_crop_colors.py` checks).
- No motion beyond the loading state. Reduced-motion is respected.
- Every interactive element shows a visible focus outline.
- The disclaimer banner is always on screen.

## Update, 15 Nov 2026 night: green start screen (approved by Amrita)

- Start screen (option 3): everything grouped in the middle of a light green page: "नमस्ते 🙏" / "Namaste 🙏", then "आपके लिए खेती के सुझाव" / "Farm suggestions for you" on one line, then "नीचे दिए गए बटनों में से / अपनी पसंद चुनिए।" / "Pick your choice / from the buttons below." on two lines, then the two buttons. The year-bar picture is gone.
- Buttons and anything you can press are green (`action`, #2f6b2b) on every screen. Blue (`monsoon`) is kept only where it means rain or kharif.
- Language switch and the disclaimer bar are dark green (`forest`, #1f4a1c) with white text, on every screen.
- The speak button's sound bars move (`.sound-wave` in globals.css); motion stops when the phone asks for reduced motion.
- Hindi button labels: "बोलने के लिए दबाइए", "फ़ॉर्म भरने के लिए दबाइए".
