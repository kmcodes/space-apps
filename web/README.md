# Field Shift web app (PWA)

Next.js 16 app. One screen: the farmer's inputs, then the four rotation cards from the engine's `POST /compare`.

## Run locally

Needs Node.js. Start the engine API first, from the repo root:

```
.venv\Scripts\python -m uvicorn api.main:app --port 8000
```

Then, in `web/`:

```
npm install
npm run dev
```

Open http://localhost:3000.

## Settings

`NEXT_PUBLIC_API_URL` is the address of the engine API. Default: `http://127.0.0.1:8000`. Set it in the hosting environment for a deployed build.

## Files

- `app/field-shift.tsx`: the form and the result cards (client component).
- `app/manifest.ts`, `public/icon.svg`: make the site installable to a phone's home screen.
- `app/layout.tsx`, `app/globals.css`: page shell and base styles.

## Not built yet

- GPS and the map pin. Location is a choice of the three presets.
- Voice (Sarvam) and Hindi text. All text is English and lives in `app/field-shift.tsx`.
- Offline cache (service worker).
- PNG icons. The manifest has an SVG icon only; some phones want 192 and 512 px PNGs to offer install.
