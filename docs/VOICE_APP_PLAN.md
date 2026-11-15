# Voice app plan (front end)

Decisions from Amrita's review of the screen mock-ups, 15 Nov 2026. This replaces the form-first screen in `web/app/field-shift.tsx` as the main experience. Read this before working on `web/`.

## The users

Farmers in Vidarbha who may not read. Everything important is said aloud. Anything drawn must need little or no reading.

## How the app works

1. **One tap starts a conversation.** The farmer taps the microphone once and says something like "सुझाव चाहिए".
2. **Then it behaves like a phone call, not a walkie-talkie.** The microphone stays open. The app detects when the farmer stops speaking, replies by voice, and listens again. No button press per answer. The farmer can interrupt while the app is speaking.
3. **The app asks for what the engine needs**, one question at a time, by voice. Picture choices appear under each question as a tap fallback.
4. **Location** comes from phone GPS with a map pin to confirm (see `docs/ENGINE_DESIGN.md` section 2b).
5. **Results are a page plus speech.** The app speaks the top options and the main risk, and shows the picture version.
6. **The app closes the conversation** by saying it is over. A red end button lets the farmer end it at any time.

## Questions the app asks

| Engine input | How it is asked |
|---|---|
| Current rotation | Spoken; picture choices for the three listed rotations |
| Water source | Rain / well / canal, with pictures |
| Priority (one, optional second) | Spoken; picture choices |
| Water availability | Low / medium / high |
| Equipment | **Yes or no:** "क्या आपके पास स्प्रेयर या बुवाई की मशीन है?" (not "औज़ार साधारण", which was unclear) |
| Where they sell | Mandi / nearby buyer / own use |

## Results screens (for non-readers)

- **No scores on screen.** Choices are ordered best first; the top ones get a thumbs-up mark.
- **The year bar always shows all 12 months**, and the blocks are grouped so the **kharif** and **rabi** seasons are clearly visible (for example a band or divider marking each season). Green month = crop in the ground, with a crop picture. Brown month = empty field.
- **One choice per detail screen:** the year bar, then three tappable picture rows that speak when tapped: what is good, what we do not know, what to ask an expert.
- **Sources and validity flags** (required by the brief) sit behind a small "for experts" link, for a KVK officer or a judge.
- Crop pictures: real drawings or photos of soybean, chickpea, cotton, pigeon pea and sorghum are still needed. Icons are placeholders.

## Crops

- For the hackathon, only the listed rotations in `engine/strategies.py`.
- After the hackathon: if a farmer names a crop that is not in the system, the app says so ("this crop is not in our system yet; it can be added later") and offers the nearest listed choice.
- Known gap: green gram (moong) is widely grown in Akola (about 44,000 ha in the ICAR-CRIDA district plan) and is not in the list.

## Build order

1. **Now: look and feel of the call screen**, using the browser's built-in speech (Web Speech API) as a stand-in for Sarvam. Testing the conversation flow is a separate step, done later.
2. Results screens with the season-grouped year bar.
3. Swap the stand-in for Sarvam speech-to-text and text-to-speech once there is an account and key.
4. Hindi text in per-language files; Marathi later, after a native speaker reviews it.

The current form becomes the "answer by tapping" fallback, not the main screen.

## Deferred on purpose

- **Visual style refresh.** The current look (`web/DESIGN.md`) is clean but reads old-fashioned. Fix it at the end, not now.
- Flow testing, deployment (see `docs/discussions.md`), offline cache.

## Open technical questions

- Echo: the microphone must not pick up the app's own voice from the speaker. Browser echo cancellation is untested with speech playing.
- Whether Sarvam offers streaming speech-to-text. If not, audio is cut at each pause and sent in pieces, adding a short delay.
- All Hindi text so far was drafted by Claude and is unreviewed.
