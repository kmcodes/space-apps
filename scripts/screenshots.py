"""Phone-size screenshots of every screen of the live app, for the project page and README.

Drives Microsoft Edge (already on Windows) with Playwright, walks the voice call by tapping the picture tiles,
and saves PNGs to docs/screenshots/. Location is set to Akola, as in docs/DEMO_SCRIPT.md. A fake microphone is
granted (it hears silence), so every answer is a tap.

Run from the repo root:  .venv\\Scripts\\python scripts\\screenshots.py [app url]
Needs: pip install playwright (in the venv). Open the API's /health first so it is awake.
"""
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

URL = sys.argv[1] if len(sys.argv) > 1 else "https://field-shift-opal.vercel.app"
OUT = Path(__file__).resolve().parent.parent / "docs" / "screenshots"
AKOLA = {"latitude": 20.700, "longitude": 77.008}
# The demo answers (docs/DEMO_SCRIPT.md), by tile label, in the order the call asks.
ANSWERS = ["हाँ, यही है", "सोयाबीन, फिर खेत खाली", "सिर्फ़ बारिश", "पानी बचाना", "जानवरों का चारा", "कम", "नहीं", "मंडी में"]
TILE_WAIT_MS = 60000


def shot(page, name, full=True):
    path = OUT / f"{name}.png"
    if full:
        # On a phone the disclaimer bar is fixed to the bottom of the screen; in a full-page image it would float
        # mid-page over the content, so for the capture only it is placed at the end of the page instead.
        page.add_style_tag(content="p.fixed, div.fixed { position: static !important; }")
    page.screenshot(path=str(path), full_page=full)
    print("saved", path.name, flush=True)


def tile(page, label):
    return page.locator("ul button", has_text=label).first


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        browser = p.chromium.launch(channel="msedge", headless=True, args=[
            "--use-fake-ui-for-media-stream", "--use-fake-device-for-media-stream"])  # a fake microphone
        ctx = browser.new_context(
            viewport={"width": 390, "height": 844}, device_scale_factor=2, is_mobile=True, has_touch=True,
            locale="hi-IN", geolocation=AKOLA, permissions=["geolocation", "microphone"],
        )
        # hide the Next.js development badge when run against a local dev server
        ctx.add_init_script("document.addEventListener('DOMContentLoaded', () => { const s = document.createElement('style'); s.textContent = 'nextjs-portal { display: none !important }'; document.head.appendChild(s); });")
        page = ctx.new_page()
        page.goto(URL, wait_until="networkidle")
        page.wait_for_timeout(1500)
        shot(page, "01-start", full=False)

        page.get_by_role("button", name="बोलने के लिए दबाइए").click()  # one tap starts the call
        for i, label in enumerate(ANSWERS):
            t = tile(page, label)
            t.wait_for(timeout=TILE_WAIT_MS)
            page.wait_for_timeout(1200)  # let the map or pictures settle
            shot(page, f"{i + 2:02d}-question-{i + 1}")
            t.click()
            if i == 1:  # show once what a chosen tile looks like
                page.wait_for_timeout(150)
                shot(page, f"{i + 2:02d}b-option-selected")

        page.get_by_text("किसी तरीके को छुइए").wait_for(timeout=180000)  # engine may need to wake
        page.wait_for_timeout(1500)
        shot(page, "10-results-list")

        page.locator("ul li button").first.click()  # the top choice
        page.wait_for_timeout(1500)
        shot(page, "11-one-choice")

        page.get_by_text("विशेषज्ञों के लिए", exact=False).first.click()
        page.wait_for_timeout(1000)
        shot(page, "12-for-experts")

        page.get_by_role("button", name="वापस").first.click()
        page.wait_for_timeout(1000)
        page.get_by_text("समझिए", exact=False).first.click()
        page.wait_for_timeout(1500)
        shot(page, "13-explainers")

        # "Tap to fill the form": a fresh page, the form, then the same results it opens
        page = ctx.new_page()
        page.goto(URL, wait_until="networkidle")
        page.wait_for_timeout(1000)
        page.get_by_role("button", name="फ़ॉर्म भरने के लिए दबाइए").click()
        page.wait_for_timeout(1000)
        shot(page, "14-form")
        browser.close()


if __name__ == "__main__":
    main()
