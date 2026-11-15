"""Records the 30-second demo video of the app (docs/DEMO_SCRIPT.md) as docs/demo/field-aide-demo.mp4.

What the video explains: how the app leads a farmer through the call. It asks a question aloud, reads each picture, WAITS for
the farmer's answer (spoken or touched), takes it, and moves on to the next question; after the last answer it shows the options.

What you get: a phone-sized screen recording on a dark portrait canvas (1080x1920) with captions in a strip under the phone.
  * The first question is shown in HINDI with the app's real voice, allowed to finish (the greeting, the question, each picture
    read aloud, then the "your turn" waiting state), subtitled in English. This is the only sound in the video.
  * From the second question the call continues in ENGLISH, silent, with captions that say what the app is doing.
  * A 1.2-second splash with the app's name in white on the app's green opens the video (it is also the first frame).

How it works
  1. Playwright drives Chrome in a 780x1688 window and records the page. The page is zoomed to double size, so the layout is
     exactly a 390x844 phone's (the app has no width breakpoints) but the recording is sharp: Playwright records at the
     window's size, and a real 2x pixel ratio is not recorded. Chrome is started WITHOUT Playwright's default "disable
     extensions" switches, because Chrome's Google voices need them off, and with a fake microphone so the call can wait for an
     answer without a permission message.
  2. At the same time PipeWire (pw-record) records what the computer plays, which is the app's voice. Keep the computer quiet
     while it runs (no notifications, music or calls), because everything that is played is recorded.
  3. A sync mark (a magenta flash and a beep at the same instant) tells the script exactly how the picture and the sound lag the
     page clock, so they stay together after cutting.
  4. ffmpeg keeps the parts that matter (jump cuts), keeps the sound of the Hindi part only, adds the splash and the captions,
     and writes the MP4 (under 30 seconds in all).

--silent is for testing: Chrome stays muted, nothing is recorded or played, and the video has no sound track.

If the app's screens or wording change, edit LABELS, HINDI_STEP and ENGLISH_STEPS below (the only places that name on-screen
text). tests/test_record_demo.py fails if a label the script looks for is no longer in the app.

Needs: pip install playwright and `playwright install ffmpeg` (Playwright's own video encoder), the installed Chrome, ffmpeg
and (unless --silent) pw-record and wpctl (PipeWire). The engine API and the web app must be running (default
http://localhost:3000); open the API's /health first so it is awake. Linux with PipeWire.

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
LEAD = 1.2          # a splash with the app's name opens the video; it is also the first frame, so it shows before anyone presses play
SPLASH_BG = "0x1f4a1c"  # the app's dark green (--color-forest in web/app/globals.css); the name is in white
APP_NAME = "Field Aide"
SPLASH_FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

# Everything on screen that the script looks for, in one place.
LABELS = {
    "start": "बोलने के लिए दबाइए",      # the button that starts the call (the call starts in Hindi)
    "waiting": "आपकी बारी",             # shown while the app waits for the farmer's answer (Hindi)
    "english": "English",               # the language switch, to carry on in English
    "results": "Touch an option",       # a line that is on the results list (English) and nowhere else
    "estimate": "Estimated advice",     # the row opened on one option (English)
    "language_key": "field-shift-lang",  # the browser storage key that holds the chosen language
}
# The first question, in Hindi: (the tile to tap).
HINDI_STEP = "अकोला"
# From the second question, in English: (the tile to tap, seconds to show its question first). The first two are shown on
# screen; the rest are tapped through quickly and cut out of the video.
ENGLISH_STEPS = [("Soybean, then empty field", 0.7), ("Rain only", 0.7), ("Save water", 0.3), ("Fodder for animals", 0.3),
                 ("Low", 0.3), ("No", 0.3), ("At the mandi", 0.3)]
SHOWN_ENGLISH_STEPS = 2  # how many of ENGLISH_STEPS the video shows

# Hindi as the language to begin with, a visible tap marker, and no development badge. The voice is left alone: it is the real one.
INIT = """
localStorage.setItem('%(language_key)s', 'hi');
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

# A sync mark at the start: a one-frame magenta flash and a 1 kHz beep, started in the same instant. The script finds the flash
# in the video and the beep in the sound, which tells it exactly how each lags the page clock (Playwright's video starts about
# a second after the page, and the sound file starts when the recorder does), so picture and sound stay together after cutting.
SYNC_JS = """() => {
  const d = document.createElement('div');
  d.style.cssText = 'position:fixed;inset:0;background:#ff00ff;z-index:999999';
  document.body.appendChild(d);
  try {
    const ctx = new AudioContext(); const o = ctx.createOscillator(); const g = ctx.createGain();
    o.frequency.value = 1000; g.gain.value = 0.5; o.connect(g); g.connect(ctx.destination); o.start(); o.stop(ctx.currentTime + 0.15);
  } catch (e) {}
  setTimeout(() => d.remove(), 300);
}"""


def find_flash(video):
    """When (in video time) the magenta flash first shows: the first frame whose average blue-difference is high."""
    out = subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-t", "20", "-i", str(video), "-vf",
                          "signalstats,metadata=print:key=lavfi.signalstats.UAVG:file=-", "-an", "-f", "null", "-"],
                         capture_output=True, text=True).stdout
    for t, u in re.findall(r"pts_time:([0-9.]+)\s*\n[^\n]*UAVG=([0-9.]+)", out):
        if float(u) > 180:
            return float(t)
    sys.exit("the sync flash is not in the video")


def find_beep(wav):
    """When (in sound-file time) the beep starts: the end of the first silence."""
    err = subprocess.run(["ffmpeg", "-hide_banner", "-i", str(wav), "-af", "silencedetect=n=-35dB:d=0.1", "-f", "null", "-"],
                         capture_output=True, text=True).stderr
    m = re.search(r"silence_end: ([0-9.]+)", err)
    if not m:
        sys.exit("the sync beep is not in the sound (is something else playing, or is the sound muted?)")
    return float(m.group(1))


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
    """Returns the video, the sound (or None), the marks (page time) and how far video and sound lag the page clock."""
    OUT.mkdir(parents=True, exist_ok=True)
    raw = OUT / "raw"
    raw.mkdir(exist_ok=True)
    for old in list(raw.glob("*.webm")) + list(raw.glob("*.wav")):
        old.unlink()
    wav = None if silent else raw / "sound.wav"
    rec = None
    if wav:
        rec = subprocess.Popen(["pw-record", "--target", default_sink_id(), "-P", "stream.capture.sink=true", "--rate", "48000", "--channels", "2", str(wav)])
        time.sleep(0.6)
    try:
        video, marks = _record_page(url, channel, headed, silent, raw)
    finally:
        # Always stop the audio recorder, even after an error, or it keeps running.
        if rec is not None and rec.poll() is None:
            rec.send_signal(signal.SIGINT)
            try:
                rec.wait(timeout=10)
            except subprocess.TimeoutExpired:
                rec.kill()
    dv = find_flash(video) - marks["sync"]                      # video time = page time + dv
    da = (find_beep(wav) - marks["sync"]) if wav else 0.0       # sound time = page time + da
    return video, wav, marks, dv, da


def _record_page(url, channel, headed, silent, raw):
    from playwright.sync_api import sync_playwright

    marks = {}
    # Chrome's Google voices need extensions on. Muting is kept only for --silent.
    ignore = ["--disable-extensions", "--disable-component-extensions-with-background-pages"] + ([] if silent else ["--mute-audio"])
    args = ["--autoplay-policy=no-user-gesture-required", "--use-fake-ui-for-media-stream", "--use-fake-device-for-media-stream"]
    with sync_playwright() as p:
        browser = p.chromium.launch(channel=channel, headless=not headed, ignore_default_args=ignore, args=args)
        ctx = browser.new_context(
            viewport={"width": 780, "height": 1688}, device_scale_factor=1, is_mobile=True, has_touch=True, locale="hi-IN",
            permissions=["microphone"], record_video_dir=str(raw), record_video_size={"width": 780, "height": 1688},
        )
        ctx.add_init_script(INIT)
        t_page = time.monotonic()
        page = ctx.new_page()
        now = lambda: time.monotonic() - t_page  # noqa: E731

        def need(what, locator, timeout=30000):
            """Wait for something on screen; say plainly which label to fix in LABELS or the steps if it never shows."""
            try:
                locator.wait_for(timeout=timeout)
            except Exception:
                sys.exit(f"the screen never showed {what!r}: the app's wording may have changed; edit LABELS or the steps in this script")

        def next_tile(label, previous):
            """The tile for the next question: wait until the heading has changed, so a tile of the question just answered
            (still on screen for a moment after the tap) is never tapped by mistake."""
            try:
                page.wait_for_function("prev => { const h = document.querySelector('h2'); return !!h && h.textContent !== prev; }", arg=previous, timeout=30000)
            except Exception:
                sys.exit(f"no new question appeared before {label!r}: the question order or wording may have changed; edit the steps")
            tile = page.locator("ul button", has_text=label).first
            need(label, tile)
            return tile

        page.goto(url, wait_until="networkidle")
        start_button = page.get_by_role("button", name=LABELS["start"])
        need(LABELS["start"], start_button)
        n_voices = page.evaluate("async () => { await new Promise(r => setTimeout(r, 1500)); return speechSynthesis.getVoices().length; }")
        if n_voices == 0:
            sys.exit("Chrome has no voices here: try --headed, or check that Chrome's Google voices are installed")
        page.evaluate(SYNC_JS)
        marks["sync"] = now()
        page.wait_for_timeout(700)  # the flash and the beep are over before the home screen is used
        marks["home"] = now()
        page.wait_for_timeout(1000)  # the home screen for a moment

        # 1. The call starts in Hindi: the greeting, then the first question read aloud, picture by picture, then the wait.
        marks["tap_start"] = now()
        start_button.click()
        tile = next_tile(HINDI_STEP, "")
        marks["q1_visible"] = now()  # the greeting is over and the first question appears
        need(LABELS["waiting"], page.get_by_text(LABELS["waiting"]), timeout=60000)  # the question and the pictures have been read
        marks["waiting"] = now()
        page.wait_for_timeout(1500)  # the app waiting for the farmer's answer
        marks["first_answer"] = now()
        tile.click()
        previous = page.locator("h2").first.text_content()

        # 2. The next question appears; carry on in English.
        page.wait_for_function("prev => { const h = document.querySelector('h2'); return !!h && h.textContent !== prev; }", arg=previous, timeout=30000)
        page.wait_for_timeout(300)
        marks["tap_english"] = now()
        page.get_by_role("button", name=LABELS["english"]).click()
        previous = ""
        for i, (label, hold) in enumerate(ENGLISH_STEPS):
            try:
                page.wait_for_function("prev => { const h = document.querySelector('h2'); return !!h && /[A-Za-z]/.test(h.textContent) && h.textContent !== prev; }", arg=previous, timeout=30000)
            except Exception:
                sys.exit(f"no English question appeared before {label!r}; edit ENGLISH_STEPS")
            tile = page.locator("ul button", has_text=label).first
            need(label, tile)
            previous = page.locator("h2").first.text_content()
            page.wait_for_timeout(int(hold * 1000))
            tile.click()
            if i == SHOWN_ENGLISH_STEPS - 1:
                marks["english_shown_end"] = now()
        marks["last_tap"] = now()
        need(LABELS["results"], page.get_by_text(LABELS["results"]), timeout=120000)
        marks["results"] = now()
        page.wait_for_timeout(3000)  # the results list

        marks["tap_option"] = now()
        page.locator("ul li button").first.click()
        page.wait_for_timeout(1300)
        marks["tap_estimate"] = now()
        row = page.locator("ol button", has_text=LABELS["estimate"]).first
        need(LABELS["estimate"], row)
        row.click()
        page.wait_for_timeout(3400)
        marks["end"] = now()
        video = page.video.path()
        ctx.close()
        browser.close()
    return Path(video), marks


def plan(m):
    """The parts to keep, as (start, end, with_sound) in page time: a jump-cut edit of the whole call. Only the Hindi opening
    keeps its sound; the English parts are silent and explained by captions. If the cut would run over the limit, the tails of
    the last two parts are shortened a little."""
    parts = [
        [m["home"], m["first_answer"] + 0.8, True],                  # the Hindi opening: greeting, question, pictures, the wait, the answer
        [m["tap_english"] - 0.5, m["english_shown_end"] + 0.8, False],  # the language switch, then two English questions answered
        [m["results"] - 0.2, m["results"] + 2.6, False],             # the results list
        [m["tap_option"] - 0.3, m["tap_estimate"] + 3.4, False],     # one option, then the "estimated advice" row
    ]
    over = sum(b - a for a, b, _ in parts) + LEAD - MAX_SECONDS
    if over > 0:
        cut_last = min(over, 1.2)
        parts[3][1] -= cut_last
        over -= cut_last
    if over > 0:
        parts[2][1] -= min(over, 0.6)
    return [tuple(p) for p in parts]


def captions(parts, m):
    """Captions timed on the EDITED video: where each part starts is the sum of the parts before it, after the LEAD-second splash.
    They explain the call in order: the app asks, reads the pictures, waits for the answer, takes it and moves on.
    Returns (list of (start, end, text), length of the film without the splash)."""
    starts, t = [], 0.0
    for a, b, _ in parts:
        starts.append(t)
        t += b - a
    total = t

    def edited(page_time):
        for (a, b, _), s in zip(parts, starts):
            if a <= page_time <= b:
                return s + (page_time - a)
        raise ValueError(f"{page_time} is not inside a kept part")

    e_tap, e_q1, e_wait, e_first = (edited(m[k]) for k in ("tap_start", "q1_visible", "waiting", "first_answer"))
    e_greet = min(e_tap + 0.9, e_q1 - 0.5)  # the Hindi voice starts a moment after the tap
    caps = [
        (0.0, e_greet, "Field Aide: voice advice for rainfed farmers\nTeam Kartik and Amrita | NASA Space Apps 2026\nAdapting Farms with NASA Data"),
        (e_greet, e_q1, "1. The app greets the farmer, in Hindi:\n“Hello. I will ask you a few questions\nabout your farm.”"),
        (e_q1, e_wait, "2. It asks one question aloud and reads each picture:\n“Which district is your farm in?”"),
        (e_wait, e_first, "3. Then it waits for the farmer's answer,\nspoken or touched."),
        (e_first, starts[2], "4. It takes the answer and moves on to the next question\n(from here in English). Eight questions in all."),
        (starts[2], starts[3], "5. After the last answer: four ways to use the field through the year,\nfrom 45 years of NASA POWER weather and MODIS satellite data."),
        (starts[3], total - 2.2, "Each colour is a crop, black is an empty field.\nEvery suggestion says what is not checked."),
        (total - 2.2, total, "Supports, does not replace, local experts.\nNext: all of India, more crops, orchards."),
    ]
    return [(a + LEAD, b + LEAD, text) for a, b, text in caps], total


def write_srt(caps):
    lines = [f"{i}\n{srt_time(a)} --> {srt_time(b)}\n{text}\n" for i, (a, b, text) in enumerate(caps, 1)]
    path = OUT / "captions.srt"
    path.write_text("\n".join(lines), encoding="utf8")
    return path


def compose(video, wav, dv, da, parts, srt, out):
    """Cut and join the parts, put the phone screen on a dark canvas, add the splash and the captions, and the sound of the
    parts that keep it (the other parts get silence)."""
    n = len(parts)
    vparts = "".join(f"[0:v]trim=start={a + dv:.3f}:end={b + dv:.3f},setpts=PTS-STARTPTS[v{i}];" for i, (a, b, _) in enumerate(parts))
    vin = "".join(f"[v{i}]" for i in range(n))
    style = "FontName=DejaVu Sans,FontSize=7,Bold=1,PrimaryColour=&H00FFFFFF,BorderStyle=1,Outline=0,Shadow=0,Alignment=2,MarginV=12,MarginL=8,MarginR=8"
    fc = (
        vparts + f"{vin}concat=n={n}:v=1:a=0[vv];"
        "[vv]scale=-2:1500,format=yuv420p[app];color=c=0x2b2320:s=1080x1920:r=30[bg];"
        "[bg][app]overlay=(W-w)/2:70:shortest=1[film];"
        f"color=c={SPLASH_BG}:s=1080x1920:r=30:d={LEAD},format=yuv420p,"
        f"drawtext=fontfile={SPLASH_FONT}:text='{APP_NAME}':fontcolor=white:fontsize=170:x=(w-text_w)/2:y=(h-text_h)/2,"
        f"fade=t=out:st={LEAD - 0.2:.2f}:d=0.2[splash];"
        "[splash][film]concat=n=2:v=1:a=0[v];"
        f"[v]subtitles='{srt.as_posix()}':original_size=1080x1920:force_style='{style}'[out]"
    )
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-i", str(video)]
    if wav is not None:
        pieces = []
        for i, (a, b, with_sound) in enumerate(parts):
            if with_sound:
                pieces.append(f"[1:a]atrim=start={a + da:.3f}:end={b + da:.3f},asetpts=PTS-STARTPTS,afade=t=in:d=0.03,afade=t=out:st={max(0, b - a - 0.08):.3f}:d=0.08[a{i}];")
            else:
                pieces.append(f"anullsrc=r=48000:cl=stereo,atrim=duration={b - a:.3f}[a{i}];")
        ain = "".join(f"[a{i}]" for i in range(n))
        fc = ("".join(pieces) + f"{ain}concat=n={n}:v=0:a=1[speech];"
              f"anullsrc=r=48000:cl=stereo,atrim=duration={LEAD}[quiet];[quiet][speech]concat=n=2:v=0:a=1[aa];" + fc)
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
    video, wav, marks, dv, da = record(args.url, args.channel, args.headed, args.silent)
    parts = plan(marks)
    caps, total = captions(parts, marks)
    srt = write_srt(caps)
    out = OUT / ("field-aide-demo-silent-test.mp4" if args.silent else "field-aide-demo.mp4")
    compose(video, wav, dv, da, parts, srt, out)
    print("marks", {k: round(v, 1) for k, v in marks.items()})
    print("video lags the page clock by", round(dv, 2), "s; sound by", round(da, 2), "s")
    print("parts", [(round(a, 1), round(b, 1), s) for a, b, s in parts])
    print("length", round(total + LEAD, 1), "s with the splash ->", out)
    if total + LEAD > MAX_SECONDS:
        print("WARNING: longer than", MAX_SECONDS, "s; the video was cut at that length. Shorten the holds in the steps.")


if __name__ == "__main__":
    sys.exit(main())
