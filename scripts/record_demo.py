"""Records the 30-second demo video of the app (docs/DEMO_SCRIPT.md) as docs/demo/field-shift-demo.mp4.

What you get: a phone-sized screen recording of the voice call, in English, with a tap marker, the app's OWN voice as the only
sound, and captions in a strip under the phone screen, on a dark portrait canvas (1080x1920).

How it works
  1. Playwright drives Chrome in a 780x1688 window and records the page. The page is zoomed to double size, so the layout is
     exactly a 390x844 phone's (the app has no width breakpoints) but the recording is sharp: Playwright records at the
     window's size, and a real 2x pixel ratio is not recorded. Chrome is started WITHOUT Playwright's default "disable
     extensions" switches, because Chrome's Google voices need them off.
  2. At the same time PipeWire (pw-record) records what the computer plays, which is the app's voice. Keep the computer quiet
     while it runs (no notifications, music or calls), because everything that is played is recorded.
  3. ffmpeg keeps the parts that matter (jump cuts, so the whole call fits in under 30 seconds), joins the sound to the same
     parts, adds the captions and writes the MP4.

--silent is for testing: Chrome stays muted, nothing is recorded or played, and the video has no sound track. The picture,
the timing and the captions are the same, so it is safe to run while others are working.

If the app's screens or wording change, edit LABELS and STEPS below (they are the only places that name on-screen text).

Needs: pip install playwright and `playwright install ffmpeg` (Playwright's own video encoder), the installed Chrome, ffmpeg
and (unless --silent) pw-record and wpctl (PipeWire). The engine API and the web app must be running (default
http://localhost:3000); open the API's /health first so it is awake. Linux with PipeWire. On another system, record the phone
yourself and caption it with docs/demo_captions.srt (see docs/DEMO_SCRIPT.md).

    python scripts/record_demo.py [app url] [--channel chrome] [--headed] [--silent]
"""

import argparse
import re
import signal
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "docs" / "demo"
MAX_SECONDS = 29.5  # the official limit is 30 seconds; stay under it

# Everything on screen that the script looks for, in one place (English, because the video is recorded in English).
LABELS = {
    "start": "Tap to speak",           # the button that starts the call
    "results": "Touch an option",      # a line that is on the results list and nowhere else
    "estimate": "Estimated advice",    # the row opened on one option
    "hindi": "हिन्दी",                  # the language switch, to show the Hindi screen at the end
    "language_key": "field-shift-lang",  # the browser storage key that holds the chosen language
}
# (the tile to tap, seconds to show its question first). The first few are readable; the rest go by quickly.
STEPS = [("Akola", 0.9), ("Soybean, then empty field", 1.0), ("Rain only", 0.9), ("Save water", 0.9),
         ("Fodder for animals", 0.4), ("Low", 0.3), ("No", 0.3), ("At the mandi", 0.3)]

# English as the language, a visible tap marker, and no development badge. The voice is left alone: it is the real one.
INIT = """
localStorage.setItem('%(language_key)s', 'en');
document.addEventListener('DOMContentLoaded', () => {
  const s = document.createElement('style');
  s.textContent = `html { zoom: 2 } nextjs-portal { display: none !important }
    .tap-mark { position: fixed; z-index: 99999; width: 56px; height: 56px; margin: -28px 0 0 -28px; border-radius: 50%%;
      border: 4px solid #1f5fa8; background: rgba(31,95,168,.25); pointer-events: none; animation: tapmark .7s ease-out forwards; }
    @keyframes tapmark { from { transform: scale(.4); opacity: 1 } to { transform: scale(1.5); opacity: 0 } }`;
  document.head.appendChild(s);
});
document.addEventListener('pointerdown', (e) => {
  // The page is zoomed 2x, so a position in window pixels is half that in page pixels.
  const d = document.createElement('div'); d.className = 'tap-mark'; d.style.left = (e.clientX / 2) + 'px'; d.style.top = (e.clientY / 2) + 'px';
  document.body.appendChild(d); setTimeout(() => d.remove(), 800);
}, true);
""" % LABELS


def srt_time(t):
    t = max(0.0, t)
    ms = min(999, int(round((t % 1) * 1000)))
    return f"{int(t // 3600):02d}:{int(t % 3600 // 60):02d}:{int(t % 60):02d},{ms:03d}"


def default_sink_id():
    """The PipeWire id of the default output (marked with *), whose monitor is what the computer plays."""
    status = subprocess.run(["wpctl", "status"], capture_output=True, text=True, check=True).stdout
    sinks = status.split("Sinks:")[1].split("Sources:")[0]
    m = re.search(r"\*\s+(\d+)\.", sinks)
    if not m:
        sys.exit("no default audio output found (wpctl status)")
    return m.group(1)


def record(url, channel, headed, silent):
    OUT.mkdir(parents=True, exist_ok=True)
    raw = OUT / "raw"
    raw.mkdir(exist_ok=True)
    for old in list(raw.glob("*.webm")) + list(raw.glob("*.wav")):
        old.unlink()
    wav = None if silent else raw / "sound.wav"
    rec, t_audio = None, time.monotonic()
    if wav:
        rec = subprocess.Popen(["pw-record", "--target", default_sink_id(), "-P", "stream.capture.sink=true", "--rate", "48000", "--channels", "2", str(wav)])
        t_audio = time.monotonic()
        time.sleep(0.6)
    try:
        video, marks, t_page = _record_page(url, channel, headed, silent, raw)
    finally:
        # Always stop the audio recorder, even after an error, or it keeps running.
        if rec is not None and rec.poll() is None:
            rec.send_signal(signal.SIGINT)
            try:
                rec.wait(timeout=10)
            except subprocess.TimeoutExpired:
                rec.kill()
    return video, wav, marks, t_page - t_audio  # the sound file starts this much before the page


def _record_page(url, channel, headed, silent, raw):
    from playwright.sync_api import sync_playwright

    marks = {}
    # Chrome's Google voices need extensions on. Muting is kept only for --silent.
    ignore = ["--disable-extensions", "--disable-component-extensions-with-background-pages"] + ([] if silent else ["--mute-audio"])
    with sync_playwright() as p:
        browser = p.chromium.launch(channel=channel, headless=not headed, ignore_default_args=ignore)
        ctx = browser.new_context(
            viewport={"width": 780, "height": 1688}, device_scale_factor=1, is_mobile=True, has_touch=True, locale="en-IN",
            record_video_dir=str(raw), record_video_size={"width": 780, "height": 1688},
        )
        ctx.add_init_script(INIT)
        t_page = time.monotonic()
        page = ctx.new_page()
        now = lambda: time.monotonic() - t_page  # noqa: E731

        def need(what, locator, timeout=30000):
            """Wait for something on screen; say plainly which label to fix in LABELS or STEPS if it never shows."""
            try:
                locator.wait_for(timeout=timeout)
            except Exception:
                sys.exit(f"the screen never showed {what!r}: the app's wording may have changed; edit LABELS or STEPS in this script")

        page.goto(url, wait_until="networkidle")
        start_button = page.get_by_role("button", name=LABELS["start"])
        need(LABELS["start"], start_button)
        n_voices = page.evaluate("async () => { await new Promise(r => setTimeout(r, 1500)); return speechSynthesis.getVoices().length; }")
        if n_voices == 0:
            sys.exit("Chrome has no voices here: try --headed, or check that Chrome's Google voices are installed")
        marks["home"] = now()
        page.wait_for_timeout(1600)  # the home screen for a moment

        marks["tap_start"] = now()
        start_button.click()

        previous = ""
        for i, (label, hold) in enumerate(STEPS):
            # Wait until the heading has changed, so a tile of the question just answered (still on screen for a moment
            # after the tap) is never tapped by mistake.
            try:
                page.wait_for_function("prev => { const h = document.querySelector('h2'); return !!h && h.textContent !== prev; }", arg=previous, timeout=30000)
            except Exception:
                sys.exit(f"no new question appeared before {label!r}: the question order or wording may have changed; edit STEPS")
            tile = page.locator("ul button", has_text=label).first
            need(label, tile)
            previous = page.locator("h2").first.text_content()
            if i == 0:
                marks["q1_visible"] = now()
            page.wait_for_timeout(int(hold * 1000))
            if i == 0:
                marks["first_answer"] = now()
            tile.click()
        marks["last_tap"] = now()
        need(LABELS["results"], page.get_by_text(LABELS["results"]), timeout=120000)
        marks["results"] = now()
        page.wait_for_timeout(4400)  # the results list while the summary starts to be read

        marks["tap_option"] = now()
        page.locator("ul li button").first.click()
        page.wait_for_timeout(1700)
        marks["tap_estimate"] = now()
        row = page.locator("ol button", has_text=LABELS["estimate"]).first
        need(LABELS["estimate"], row)
        row.click()
        page.wait_for_timeout(3300)

        marks["tap_hindi"] = now()
        page.get_by_role("button", name=LABELS["hindi"]).click()
        page.wait_for_timeout(2500)
        marks["end"] = now()
        video = page.video.path()
        ctx.close()
        browser.close()
    return Path(video), marks, t_page


def plan(m):
    """The parts to keep, as (start, end) in page time: a jump-cut edit of the whole call."""
    return [
        (m["home"], m["tap_start"] + 2.8),                 # home screen, the tap, the start of the greeting
        (m["q1_visible"] - 0.3, m["last_tap"] + 0.9),      # the questions, answered one after another
        (m["results"] - 0.2, m["results"] + 4.2),          # the results list, summary starting
        (m["tap_option"] - 0.3, m["tap_estimate"] + 3.0),  # one option, then the "estimated advice" row
        (m["tap_hindi"] - 0.2, m["end"]),                  # the same screen in Hindi
    ]


def captions(parts, m):
    """Captions timed on the EDITED video: where each part starts is the sum of the parts before it.
    Returns (list of (start, end, text), total length)."""
    starts, t = [], 0.0
    for a, b in parts:
        starts.append(t)
        t += b - a
    total = t

    def edited(page_time):
        for (a, b), s in zip(parts, starts):
            if a <= page_time <= b:
                return s + (page_time - a)
        raise ValueError(f"{page_time} is not inside a kept part")

    e_tap = edited(m["tap_start"])
    e_first = edited(m["first_answer"])
    return [
        (0.0, e_tap, "Field Shift: voice advice for rainfed farmers\nTeam Kartik and Amrita\nNASA Space Apps 2026: Adapting Farms with NASA Data"),
        (e_tap, e_first, "1. One tap starts a call.\nThe app asks the questions aloud."),
        (e_first, starts[2], "2. Answer by voice or by touching a picture.\nEight short questions."),
        (starts[2], starts[3], "3. Four ways to use the field through the year,\nfrom 45 years of NASA POWER weather\nand MODIS satellite data."),
        (starts[3], starts[4], "4. Each colour is a crop, black is an empty field.\nEvery suggestion says what is not checked."),
        (starts[4], total - 2.0, "Hindi and English."),
        (total - 2.0, total, "Supports, does not replace, local experts.\nNext: all of India, more crops, orchards."),
    ], total


def write_srt(caps):
    lines = [f"{i}\n{srt_time(a)} --> {srt_time(b)}\n{text}\n" for i, (a, b, text) in enumerate(caps, 1)]
    path = OUT / "captions.srt"
    path.write_text("\n".join(lines), encoding="utf8")
    return path


def compose(video, wav, delta, parts, srt, out):
    """Cut and join the parts, put the phone screen on a dark canvas, add the captions (and the sound, if there is any)."""
    n = len(parts)
    vparts = "".join(f"[0:v]trim=start={a:.3f}:end={b:.3f},setpts=PTS-STARTPTS[v{i}];" for i, (a, b) in enumerate(parts))
    vin = "".join(f"[v{i}]" for i in range(n))
    style = "FontName=DejaVu Sans,FontSize=7,Bold=1,PrimaryColour=&H00FFFFFF,BorderStyle=1,Outline=0,Shadow=0,Alignment=2,MarginV=12,MarginL=8,MarginR=8"
    fc = (
        vparts + f"{vin}concat=n={n}:v=1:a=0[vv];"
        "[vv]scale=-2:1500,format=yuv420p[app];color=c=0x2b2320:s=1080x1920:r=30[bg];"
        "[bg][app]overlay=(W-w)/2:70:shortest=1[v];"
        f"[v]subtitles='{srt.as_posix()}':original_size=1080x1920:force_style='{style}'[out]"
    )
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-i", str(video)]
    if wav is not None:
        aparts = "".join(
            f"[1:a]atrim=start={a + delta:.3f}:end={b + delta:.3f},asetpts=PTS-STARTPTS,afade=t=in:d=0.03,afade=t=out:st={max(0, b - a - 0.05):.3f}:d=0.05[a{i}];"
            for i, (a, b) in enumerate(parts)
        )
        ain = "".join(f"[a{i}]" for i in range(n))
        fc = aparts + f"{ain}concat=n={n}:v=0:a=1,loudnorm=I=-16:TP=-1.5[aa];" + fc
        cmd += ["-i", str(wav)]
    cmd += ["-filter_complex", fc, "-map", "[out]"]
    cmd += ["-map", "[aa]", "-c:a", "aac", "-b:a", "128k"] if wav is not None else ["-an"]
    cmd += ["-r", "30", "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p", "-movflags", "+faststart", "-t", f"{MAX_SECONDS}", str(out)]
    subprocess.run(cmd, check=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("url", nargs="?", default="http://localhost:3000")
    ap.add_argument("--channel", default="chrome")
    ap.add_argument("--headed", action="store_true", help="show the Chrome window while recording")
    ap.add_argument("--silent", action="store_true", help="test run: no sound is played or recorded")
    args = ap.parse_args()
    video, wav, marks, delta = record(args.url, args.channel, args.headed, args.silent)
    parts = plan(marks)
    caps, total = captions(parts, marks)
    srt = write_srt(caps)
    out = OUT / ("field-shift-demo-silent-test.mp4" if args.silent else "field-shift-demo.mp4")
    compose(video, wav, delta, parts, srt, out)
    print("marks", {k: round(v, 1) for k, v in marks.items()})
    print("parts", [(round(a, 1), round(b, 1)) for a, b in parts])
    print("edited length", round(total, 1), "s ->", out)
    if total > MAX_SECONDS:
        print("WARNING: longer than", MAX_SECONDS, "s; the video was cut at that length. Shorten the holds in STEPS.")


if __name__ == "__main__":
    sys.exit(main())
