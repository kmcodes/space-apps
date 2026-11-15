"""scripts/record_demo.py makes the 30-second demo video. Its edit plan and captions are logic worth testing, and the
on-screen labels it looks for must still exist in the app, or the next recording fails halfway."""

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location("record_demo", ROOT / "scripts/record_demo.py")
R = importlib.util.module_from_spec(spec)
spec.loader.exec_module(R)

# Times (seconds into the recording) from a real run.
MARKS = {"sync": 3.6, "home": 4.3, "tap_start": 5.6, "q1_visible": 11.9, "first_answer": 12.8, "last_tap": 22.6, "results": 29.0,
         "tap_option": 33.4, "tap_estimate": 35.2, "tap_hindi": 38.7, "end": 42.2}


def test_the_kept_parts_are_in_order_and_do_not_overlap():
    parts = R.plan(MARKS)
    assert all(a < b for a, b in parts)
    assert all(parts[i][1] <= parts[i + 1][0] + 0.5 for i in range(len(parts) - 1))  # at most a small overlap, never a rewind


def test_the_edited_video_is_under_the_30_second_limit():
    caps, total = R.captions(R.plan(MARKS), MARKS)
    assert total + R.LEAD <= R.MAX_SECONDS < 30  # the splash counts too


def test_captions_cover_the_whole_video_one_after_another():
    caps, total = R.captions(R.plan(MARKS), MARKS)
    assert abs(caps[0][0] - R.LEAD) < 1e-6 and abs(caps[-1][1] - (total + R.LEAD)) < 1e-6  # nothing is captioned during the splash
    for (a1, b1, _), (a2, b2, _) in zip(caps, caps[1:]):
        assert a1 < b1 and abs(b1 - a2) < 1e-6  # no gap and no overlap
    assert all(text.strip() for _, _, text in caps)


def test_the_first_caption_names_the_team_and_the_challenge_and_the_last_one_says_what_is_next():
    caps, _ = R.captions(R.plan(MARKS), MARKS)
    assert "Team Kartik and Amrita" in caps[0][2] and "Adapting Farms with NASA Data" in caps[0][2]
    assert "Next:" in caps[-1][2]


def test_subtitle_times_are_written_as_hours_minutes_seconds_milliseconds():
    assert R.srt_time(3.5) == "00:00:03,500"
    assert R.srt_time(29.9996) == "00:00:29,999"
    assert R.srt_time(-1) == "00:00:00,000"


def test_a_mark_outside_every_kept_part_is_an_error_not_a_wrong_caption():
    import pytest

    bad = {**MARKS, "first_answer": 26.0}  # between the kept parts, so it is cut out
    with pytest.raises(ValueError):
        R.captions(R.plan(MARKS), bad)


def test_the_on_screen_labels_the_script_looks_for_still_exist_in_the_app():
    """If this fails, the app's wording changed: update LABELS or STEPS in scripts/record_demo.py (one place)."""
    web = "".join((ROOT / "web/app" / f).read_text(encoding="utf8") for f in ("call-script.ts", "results-script.ts", "lang.tsx"))
    wanted = [R.LABELS["start"], R.LABELS["results"], R.LABELS["estimate"], R.LABELS["hindi"]] + [label for label, _ in R.STEPS]
    missing = [w for w in wanted if w not in web]
    assert missing == [], f"not found in the app's text: {missing}; update LABELS or STEPS in scripts/record_demo.py"


def test_the_script_taps_one_tile_for_each_of_the_eight_questions():
    assert len(R.STEPS) == 8


def test_the_hindi_labels_the_screenshot_script_taps_still_exist_in_the_app():
    """scripts/readme_screenshots.py finds buttons by their Hindi text. If this fails, the Hindi wording changed: update the script."""
    import re
    import unicodedata

    nfc = lambda text: unicodedata.normalize("NFC", text)  # noqa: E731
    web = nfc("".join(p.read_text(encoding="utf8") for p in (ROOT / "web/app").glob("*.ts*")))
    script = (ROOT / "scripts/readme_screenshots.py").read_text(encoding="utf8")
    labels = set(re.findall(r'"([^"\n]*[\u0900-\u097F][^"\n]*)"', script))
    missing = sorted(label for label in labels if nfc(label) not in web)
    assert missing == [], f"not found in the app's text: {missing}; update scripts/readme_screenshots.py"


def test_the_splash_shows_the_apps_name_in_white_on_the_apps_own_green():
    css = (ROOT / "web/app/globals.css").read_text(encoding="utf8")
    forest = css.split("--color-forest:")[1].split(";")[0].strip().lstrip("#").lower()
    assert R.SPLASH_BG.lower() == "0x" + forest
    assert 1.0 <= R.LEAD <= 2.0  # long enough to read, short enough for the 30 seconds
    title = (ROOT / "web/app/call-script.ts").read_text(encoding="utf8")
    assert f'title: "{R.APP_NAME}"' in title, "the splash name differs from the app's name"
