# Demo video script (2 minutes)

The video replaces the slide deck. It is also the offline fallback for the demo (`START.md`: "Demo must work offline from recorded fallback"). Every claim below is true of what is built today. Anything we cannot claim is listed at the end.

Length: about 230 spoken words at a calm pace, plus the Hindi the app speaks itself.

## Before recording

- **Record online.** The map is Google's embed and needs internet.
- **Use Chrome, at phone width** (DevTools, device toolbar, a phone preset). Record the screen with the app audio on.
- **Set the location to Akola:** DevTools, three-dot menu, More tools, Sensors, Location, custom 20.700 N, 77.008 E. Put a small caption on screen, "demo location: Akola", so nobody thinks it is a real phone fix. A judge's own phone would be outside the region: the app then says so, skips the map and asks for a district, and the results are labelled as an example, not their farm.
- **Check the machine has a Hindi voice.** In Chrome the "Google हिन्दी" voice is usual on Android and Windows; many Linux machines have none. Test one question before recording. If there is no Hindi voice, record on an Android phone instead.
- **Run both servers fresh** and do one full run first, so the engine's cache is warm and results appear in a second or two.
- **Answers to use** (all can be tapped): farm = yes; rotation = soybean then empty field; water = rain only; priority = saving water, second = animal fodder; water available = low; equipment = no; sell = mandi. This gives a clear "soybean then sorghum" top choice and shows the hot-month and dry-spell markers.
- If the microphone works on the take, answer one question by voice ("वाशिम" style short word) so the viewer sees it listens. Otherwise tap, and do not claim live voice recognition in the narration.
- Keep the browser zoom at 100% and hide bookmarks and extensions.
- **Record in Hindi** (the default). The language switch at the top is saved in the browser, so check it says हिन्दी before you start. Restart the API first so it serves the current crop data.

## Script

| Time | On screen | Narration (English) |
|---|---|---|
| 0:00–0:12 | Home screen: the year strip and the two start buttons ("बोलने के लिए छुइए" / Tap to speak, and Tap to fill the form). Slow push in on the strip. | "In Vidarbha, rainfed farmers often leave a field bare for months after soybean. Many of them cannot read. So Field Shift talks." |
| 0:12–0:24 | Cut to a plain map of Vidarbha, or stay on the home screen with a caption: "Akola · Buldhana · Washim · 1981–2025". | "It compares four ways of using one field through the year, using forty-five years of NASA POWER weather and MODIS satellite greenness." |
| 0:24–0:36 | Tap the speak button. The call starts; the map with the red pin and the tick and cross tiles appear. Tap the tick. | "One tap starts a call, in Hindi. The phone shows where the farm is. The farmer confirms the pin." |
| 0:36–0:50 | The question screen: tiles light up one by one as the app reads them. Tap a few answers quickly (cut between them). | "Each question is read aloud while its picture lights up, so a picture and its word are linked. The farmer answers by voice, or by touching." |
| 0:50–1:08 | Results list: thumbs-up on the top choice, no numbers. Tap the top choice: the year bar with kharif and rabi grouped, green and dark months. | "The result is spoken and shown, with no scores. The best choices get a thumbs-up. Each one has a twelve-month bar: green when a crop is in the ground, dark when the field is bare, with kharif and rabi grouped." |
| 1:08–1:22 | Zoom on the thermometer and crossed-out drop markers under the bar, then tap the "नाज़ुक समय" row; its text opens. | "Under it, the hot months and the long dry-spell months from the climate record. A solid mark means both datasets agree." |
| 1:22–1:36 | Tap "अनुमानित सुझाव" and "विशेषज्ञ से पूछिए"; show the text opening and the speaker icon turning blue. Briefly show the "for experts" link. | "Tap a row and it speaks: what is checked, what is only an estimate, and what to ask a local expert. Every choice is labelled an estimate until its inputs are checked. Sources and validity flags sit behind an expert link." |
| 1:36–1:50 | The "समझिए" screen, then a quick cut to the README's cross-check lines (or a caption: "POWER vs ERA5: rain agrees, heat days do not → we show a range"). | "We say what we do not know. We checked NASA POWER against a second dataset, ERA5. They agree that rain is rising, but not on heat days, so we show a range, never one number. Every piece of evidence carries a validity flag." |
| 1:50–2:00 | Back to the home screen; tap the English switch at the top once to show the whole app change language; then the disclaimer banner large on screen; end card with team and repo link. | "Field Shift supports local expertise; it does not replace it. Hindi and English today, Marathi after a native speaker reviews it. Built with NASA POWER and MODIS, plus SoilGrids, ERA5 and mandi prices." |

## Full narration, to read in one go

In Vidarbha, rainfed farmers often leave a field bare for months after soybean. Many of them cannot read. So Field Shift talks.

It compares four ways of using one field through the year, using forty-five years of NASA POWER weather and MODIS satellite greenness.

One tap starts a call, in Hindi. The phone shows where the farm is. The farmer confirms the pin. Each question is read aloud while its picture lights up, so a picture and its word are linked. The farmer answers by voice, or by touching.

The result is spoken and shown, with no scores. The best choices get a thumbs-up. Each one has a twelve-month bar: green when a crop is in the ground, dark when the field is bare, with kharif and rabi grouped. Under it, the hot months and the long dry-spell months from the climate record. A solid mark means both datasets agree.

Tap a row and it speaks: what is checked, what is only an estimate, and what to ask a local expert. Every choice is labelled an estimate until its inputs are checked. Sources and validity flags sit behind an expert link.

We say what we do not know. We checked NASA POWER against a second dataset, ERA5. They agree that rain is rising, but not on heat days, so we show a range, never one number. Every piece of evidence carries a validity flag.

Field Shift supports local expertise; it does not replace it. Hindi and English today, Marathi after a native speaker reviews it. Built with NASA POWER and MODIS, plus SoilGrids, ERA5 and mandi prices.

## Credits on the end card

NASA POWER and MODIS MOD13Q1 (via AppEEARS) · ISRIC SoilGrids · ERA5, Copernicus/ECMWF, through Open-Meteo (CC BY 4.0) · Agmarknet via data.gov.in · FAO, ICAR-CRIDA and ICRISAT for crop values · Team: Kartik and Amrita · Repo: the GitHub link

## Do not say

- That it uses Sarvam. It uses the browser's built-in Hindi speech today.
- That a language model writes any text. Every sentence is a template filled from engine fields.
- That it is live or deployed. Nothing is hosted yet.
- That Marathi works, or that the Hindi or English text has been reviewed by a native speaker. Neither has.
- That any advice is verified. Every choice is labelled "अनुमानित सुझाव" (estimated advice) because the crop inputs are not yet checked in the field. Say "estimate", never "verified" or "validated".
- Anything field-level. The weather is area-scale (about 50 km) and the satellite pixel is 250 m.
- That the crop pictures are final. They are drawn placeholders.
- A score or a percentage for any choice. The app deliberately shows none.

## If something goes wrong on the day

- No Hindi voice or no mic: record on an Android phone in Chrome, or record the screen and add a Hindi voice-over for the app lines.
- The map does not load: tap "no" and show the district tiles instead; say nothing about maps in that take.
- A slow first result: do one throwaway run before recording so the cache is warm.
- Over two minutes: cut the "समझिए" shot first, then the "for experts" link shot.
