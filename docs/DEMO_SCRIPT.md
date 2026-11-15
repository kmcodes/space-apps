# Demo video: 30 seconds, screen recording with captions

**The rule (official 2026 Project Submission Guide and the submission form):** the demo is a video of **30 seconds or less**, or a deck of **7 slides or fewer**. Over the limit means the project is **not eligible for Global Judging**. The link must be public, need no login, and be a full URL (`https://...`).

Other rules from the guide that apply to the video:

- **English.** If anyone speaks another language, the video MUST have English subtitles. Our captions below are written to be those subtitles.
- **No NASA branding.** Do not use the NASA logo, flag or mission marks. Naming the NASA data in text is fine.
- **No person under 18** in any picture, voice or sound.
- **AI disclosure.** The app's voice is machine-generated (the browser's text-to-speech). Say so in the video description (text below).
- The guide suggests this order: who you are, the challenge, the project name, how it works and how NASA data makes it possible, then the future. The captions below follow it.

## What the video is

An explainer of how the app leads a farmer through the call: it **asks a question, waits for the farmer's answer, takes it, and moves on.** It is a captioned screen recording, with no voice-over.

- **The opening is in Hindi, with the app's real voice, uncut.** The greeting, the first question (which district), each picture read aloud, then the "your turn" waiting state, and the farmer's answer. English subtitles give what the Hindi says. This is the only sound in the video.
- **From the second question the call continues in English, silent.** The captions say what the app is doing. A few questions are shown, then the results and one option. Nothing is cut off mid-sentence, because no speech is played after the Hindi opening.
- **A 1.2-second splash** with the app's name opens the video: "Field Aide" in white on the app's dark green. It is also the first frame, so it shows before anyone presses play.
- The judges can try the real thing in the live app we link; the video only explains how it works.

## Shot list (about 29.5 seconds)

| Time | On screen | Caption (English subtitle or explanation) | Sound |
|---|---|---|---|
| 0:00–0:01 | **Splash:** "Field Aide", white on the app's green | none | none |
| 0:01–0:03 | Home screen in Hindi, then the tap on **बोलने के लिए दबाइए** | **Field Aide: voice advice for rainfed farmers.** Team Kartik and Amrita, NASA Space Apps 2026, "Adapting Farms with NASA Data" | none |
| 0:03–0:10 | The call starts: the Hindi greeting | **1. The app greets the farmer, in Hindi:** "Hello. I will ask you a few questions about your farm." | the Hindi greeting |
| 0:10–0:16 | The first question and the three district pictures, each lit as it is read | **2. It asks one question aloud and reads each picture:** "Which district is your farm in?" | the Hindi question and picture names |
| 0:16–0:18 | The "your turn" state (green microphone), then a tap on **अकोला** | **3. Then it waits for the farmer's answer, spoken or touched.** | none |
| 0:18–0:22 | The next question appears; tap **English**; two questions answered by touching pictures | **4. It takes the answer and moves on to the next question** (from here in English). Eight questions in all. | none |
| 0:22–0:25 | The results list: four options, coloured year bars, legend | **5. After the last answer: four ways to use the field through the year,** from 45 years of NASA POWER weather and MODIS satellite data. | none |
| 0:25–0:27 | One option opened, then the **Estimated advice** row | Each colour is a crop, black is an empty field. Every suggestion says what is not checked. | none |
| 0:27–0:29.5 | Same screen | **Supports, does not replace, local experts.** Next: all of India, more crops, orchards. | none |

The times are approximate: the tool measures them from the recording. The captions are in [`docs/demo_captions.srt`](demo_captions.srt).

## Recording it automatically (Linux with PipeWire)

`scripts/record_demo.py` makes the whole video: it drives Chrome at phone size through the call (with a visible tap marker), records the screen, records the app's own voice from the computer's audio output, cuts it down to under 30 seconds, and adds the captions on a dark portrait canvas (1080x1920). Output: `docs/demo/field-aide-demo.mp4`.

```bash
# once: pip install playwright, then: playwright install ffmpeg
# the engine API and the web app must be running; open the API's /health first
python scripts/record_demo.py --silent   # test run: Chrome stays muted, no sound is played or recorded
python scripts/record_demo.py            # the real recording: the app speaks, so keep the computer quiet
```

- The page is shown at exactly a 390x844 phone layout, but zoomed to double size so the recording is sharp.
- Run `--silent` first and look at `docs/demo/field-aide-demo-silent-test.mp4`. Run the real one once you are happy, and listen to it before uploading.
- If the app's wording or screens change, the script stops with a message naming what it could not find. Edit `LABELS` or `STEPS` at the top of the script. `tests/test_record_demo.py` also fails when a label it looks for is gone from the app.
- On another system, record a phone yourself (below) and caption it with `docs/demo_captions.srt`.

## Before recording by hand

- **Start the call in Hindi and let the first question finish, uncut; switch to English from the second question** (the language switch at the top works in the middle of a call). Mute or cut the sound after the Hindi opening, and caption what the app says. Hindi speech needs English subtitles.
- **Record on a phone or a clean window.** Use an Android phone in Chrome, or a Chrome window with a fresh profile and one tab. A normal desktop window shows your other tabs, bookmarks and extensions; the video would show them too.
- **Capture the device's sound.** Use the phone's screen recorder with "media sound" on, or on a computer a recorder that captures system audio (OBS: desktop audio). Do not use a microphone in a room, which adds echo and noise.
- **Warm up the engine.** Open the API's `/health` a minute before, then do one throwaway run so the first answer is fast.
- **Say no to the location prompt**, so the call goes straight to the three district tiles. This also keeps the satellite map (Google's imagery) out of the video.
- **Use these answers:** Akola; soybean then empty field; rain only; save water; fodder as the second goal; low water; no equipment; mandi. The top choice is then soybean then sorghum, with every option ranked.
- **Check the voice.** Run one question first and confirm you hear an English voice.
- Keep the browser at 100% zoom, hide bookmarks, and close notifications.

## Editing down to 30 seconds

1. Record one continuous take, about a minute.
2. Cut the waiting. Speed up any loading to 2x or cut it.
3. Cut between taps, so each question shows for about two seconds.
4. Add the captions (or import `demo_captions.srt`) in large, high-contrast text.
5. Export as MP4. **Check that the length is 30.0 seconds or less**, with no black frames added at the end.

## Hosting

Upload to YouTube as **Unlisted** (a link with no login works) or to Google Drive with "Anyone with the link". Open the link in a private window to check it plays without signing in. Paste the **full** URL, starting with `https://`.

## Video description (paste under the video)

> Field Aide, a project for the NASA Space Apps Challenge 2026 ("Adapting Farms with NASA Data"). A voice and picture assistant for rainfed farmers in Vidarbha, built on NASA POWER weather and MODIS satellite data. Audio: the spoken voice is the browser's built-in machine-generated text-to-speech. Code, text and data scripts were written with AI assistance (Claude Code, Anthropic); no AI model runs inside the product. Code: https://github.com/kmcodes/space-apps

## Do not show or say

- A score or percentage for any option. The app shows none.
- The words "verified" or "validated". Every suggestion is labelled an estimate.
- The satellite map screen (Google's imagery), or a mention that the Hindi has been checked by a native speaker (it has not).
- Anything that claims a result for one field. The data is area-scale.
- Marathi, Sarvam or a language model inside the product. None exists.
- Other tabs, names, emails or notifications on screen.

## If the video is too hard in the time left

A **7-slide deck** is allowed instead (7 slides including the title). Suggested slides: 1. title, team, names, challenge; 2. the problem; 3. the app at a glance (home screen); 4. the questions (picture tiles); 5. the results (coloured year bars, estimate label); 6. how NASA data makes it possible; 7. what is next. The screenshots in `docs/screenshots/flow/` are ready to use. Decks must be in English.
