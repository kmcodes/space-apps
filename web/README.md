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

- `app/field-shift.tsx`: the form, the year board and the rotation sections (client component).
- `DESIGN.md`: colours, type and layout rules. Read before changing any styling.
- `app/manifest.ts`, `public/icon.svg`: make the site installable to a phone's home screen.
- `app/layout.tsx`, `app/globals.css`: page shell and base styles.

## Not built yet

- GPS and the map pin. Location is a choice of the three presets.
- Voice (Sarvam) and Hindi text. All text is English and lives in `app/field-shift.tsx`.
- Offline cache (service worker).
- A way to see the year board for one of the "other second crops".
- PNG icons. The manifest has an SVG icon only; some phones want 192 and 512 px PNGs to offer install.

## Deploying (not done yet)

Waiting on a decision about whose accounts host it. See `docs/discussions.md`.

Web app on Vercel:

1. Import the GitHub repo `kmcodes/space-apps` in Vercel.
2. Set **Root Directory** to `web`. Framework is detected as Next.js; keep the default build settings.
3. Add the environment variable `NEXT_PUBLIC_API_URL` with the public address of the engine API. It is read at build time, so redeploy after changing it.

Engine API (any Python host):

- Start command: `uvicorn api.main:app --host 0.0.0.0 --port $PORT`, run from the repo root so `data/` is found.
- Set `ALLOWED_ORIGINS` to the Vercel address so only the web app can call it.
- The API must be on HTTPS, or the browser blocks calls from the HTTPS web app.
