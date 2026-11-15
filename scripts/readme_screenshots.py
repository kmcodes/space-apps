"""Phone-size screenshots of the app flow for README.md, saved to docs/screenshots/flow/.

Drives Chrome (or Edge) with Playwright: walks the voice call by tapping the picture tiles, with the demo answers
from docs/DEMO_SCRIPT.md, in Hindi, then shows English, and a phone outside our area.

Two things are faked so the pictures are the same on every machine, and neither changes what the app draws:
  * speech: the page is given a Hindi and an English voice and a speaker that "finishes" after a moment, so the
    "listen" and "speak" states appear in order (a headless browser has no voices);
  * the Next.js development badge is hidden.
The satellite map (Google's embed) is NOT photographed: the main run has no location, so the call asks the district.

Run from the repo root, with the engine API and the web app running:
    pip install playwright
    python scripts/readme_screenshots.py [app url] [--channel chrome|msedge]
Default app url: http://localhost:3000. Default channel: chrome.
"""

import argparse
from pathlib import Path

from playwright.sync_api import sync_playwright

OUT = Path(__file__).resolve().parent.parent / "docs" / "screenshots" / "flow"
BANGALORE = {"latitude": 12.9716, "longitude": 77.5946}
TILE_WAIT_MS = 90_000

# The demo answers, by tile label, in the order the call asks (with no location the first question is the district).
ANSWERS = [
    ("03-district", "अकोला"),
    ("04-rotation", "सोयाबीन, फिर खेत खाली"),
    ("05-water-source", "सिर्फ़ बारिश"),
    ("06-priority-1", "पानी बचाना"),
    ("07-priority-2", "जानवरों का चारा"),
    ("08-water-level", "कम"),
    ("09-equipment", "नहीं"),
    ("10-market", "मंडी में"),
]

# A page with a Hindi and an English voice, and a speaker that starts and ends on its own.
FAKE_SPEECH = """
// The fake voices are plain objects, which a real utterance would refuse; let it ignore the voice it is given.
Object.defineProperty(SpeechSynthesisUtterance.prototype, 'voice', { configurable: true, get() { return null; }, set() {} });
Object.defineProperty(window, 'speechSynthesis', { configurable: true, value: {
  getVoices: () => [{ lang: 'hi-IN', name: 'Google हिन्दी', default: true }, { lang: 'en-IN', name: 'Google English India' }],
  speak: (u) => setTimeout(() => { u.onstart && u.onstart({}); setTimeout(() => u.onend && u.onend({}), 1500); }, 50),
  cancel: () => {}, addEventListener: () => {}, removeEventListener: () => {}, paused: false, speaking: false, pending: false,
}});
document.addEventListener('DOMContentLoaded', () => {
  const s = document.createElement('style');
  s.textContent = 'nextjs-portal { display: none !important }';
  document.head.appendChild(s);
});
"""


def shot(page, name, full=True):
    if full:
        # On a phone the disclaimer bar is fixed to the bottom of the screen; in a full-page image it would float
        # mid-page, so for the capture only it is placed at the end of the page.
        page.add_style_tag(content="p.fixed, div.fixed { position: static !important; }")
    page.screenshot(path=str(OUT / f"{name}.png"), full_page=full)
    print("saved", name, flush=True)


def tile(page, label):
    return page.locator("ul button", has_text=label).first


def new_page(browser, geolocation=None):
    ctx = browser.new_context(
        viewport={"width": 390, "height": 844}, device_scale_factor=2, is_mobile=True, has_touch=True, locale="hi-IN",
        geolocation=geolocation, permissions=["geolocation"] if geolocation else [],
    )
    ctx.add_init_script(FAKE_SPEECH)
    return ctx, ctx.new_page()


def answer_all(page, answers=ANSWERS, names=True):
    for name, label in answers:
        t = tile(page, label)
        t.wait_for(timeout=TILE_WAIT_MS)
        page.wait_for_timeout(700)  # let the question settle
        if names:
            shot(page, name)
        t.click()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("url", nargs="?", default="http://localhost:3000")
    ap.add_argument("--channel", default="chrome")
    args = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)

    with sync_playwright() as p:
        browser = p.chromium.launch(channel=args.channel, headless=True)

        # --- Hindi, no location: the call asks the district first --------------------------------------------
        ctx, page = new_page(browser)
        page.goto(args.url, wait_until="networkidle")
        page.wait_for_timeout(1500)
        shot(page, "01-home", full=False)

        page.get_by_role("button", name="English").click()
        page.wait_for_timeout(500)
        shot(page, "02-home-english", full=False)
        page.get_by_role("button", name="हिन्दी").click()
        page.wait_for_timeout(500)

        page.get_by_role("button", name="बोलने के लिए छुइए").click()  # start the call
        answer_all(page)
        page.get_by_text("किसी तरीके को छुइए").wait_for(timeout=180_000)  # the engine may need to wake
        page.wait_for_timeout(1500)
        shot(page, "11-results")

        page.locator("ul li button").first.click()  # the top choice
        page.wait_for_timeout(1500)
        shot(page, "12-one-choice")

        # The screen opens one row at a time: the estimates first (the heart of the advice labels), then the sensitive months.
        page.locator("ol button", has_text="अनुमानित सुझाव").first.click()
        page.wait_for_timeout(500)
        shot(page, "13-estimate-row")
        page.locator("ol button", has_text="नाज़ुक समय").first.click()
        page.wait_for_timeout(500)
        shot(page, "14-sensitive-months")

        page.get_by_text("विशेषज्ञों के लिए", exact=False).first.click()
        page.wait_for_timeout(800)
        shot(page, "15-for-experts")

        page.get_by_role("button", name="वापस").first.click()
        page.wait_for_timeout(800)
        page.get_by_text("समझिए", exact=False).first.click()
        page.wait_for_timeout(1200)
        shot(page, "16-explained")
        page.get_by_role("button", name="वापस").first.click()
        page.wait_for_timeout(800)

        # The same screens in English
        page.get_by_role("button", name="English").click()
        page.wait_for_timeout(800)
        shot(page, "17-results-english")
        page.locator("ul li button").first.click()
        page.wait_for_timeout(1200)
        shot(page, "18-one-choice-english")
        ctx.close()

        # --- A phone in Bangalore: outside our area -----------------------------------------------------------
        ctx, page = new_page(browser, geolocation=BANGALORE)
        page.goto(args.url, wait_until="networkidle")
        page.wait_for_timeout(1000)
        page.get_by_role("button", name="बोलने के लिए छुइए").click()
        t = tile(page, "अकोला")
        t.wait_for(timeout=TILE_WAIT_MS)
        page.wait_for_timeout(800)
        shot(page, "19-outside-our-area")
        t.click()
        answer_all(page, answers=ANSWERS[1:], names=False)  # the district was just chosen
        page.get_by_text("उदाहरण (आपका खेत नहीं)", exact=False).wait_for(timeout=180_000)
        page.wait_for_timeout(1500)
        shot(page, "20-example-results", full=False)
        ctx.close()
        browser.close()


if __name__ == "__main__":
    main()
