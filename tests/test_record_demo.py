"""scripts/record_demo.py makes the 30-second demo video. Its edit plan and captions are logic worth testing, and the
on-screen labels it looks for must still exist in the app, or the next recording fails halfway."""

import importlib.util
import re
import unicodedata
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location("record_demo", ROOT / "scripts/record_demo.py")
R = importlib.util.module_from_spec(spec)
spec.loader.exec_module(R)

# Times (seconds into the recording) of a typical run.
MARKS = {"sync": 3.5, "home": 4.2, "tap_start": 5.2, "q1_visible": 12.6, "waiting": 16.6, "first_answer": 18.1,
         "tap_english": 19.3, "english_shown_end": 22.6, "last_tap": 28.0, "results": 31.0, "tap_option": 34.0,
         "tap_estimate": 35.3, "end": 38.7}
nfc = lambda text: unicodedata.normalize("NFC", text)  # noqa: E731


def test_the_kept_parts_are_in_order_and_do_not_overlap():
    parts = R.plan(MARKS)
    assert all(a < b for a, b, _ in parts)
    assert all(parts[i][1] <= parts[i + 1][0] + 0.5 for i in range(len(parts) - 1))  # at most a small overlap, never a rewind


def test_only_the_hindi_opening_keeps_its_sound():
    assert [with_sound for _, _, with_sound in R.plan(MARKS)] == [True, False, False, False]


def test_the_hindi_opening_lets_the_greeting_the_question_and_the_wait_finish():
    a, b, _ = R.plan(MARKS)[0]
    assert a <= MARKS["tap_start"] and b >= MARKS["first_answer"]  # from the home screen to the farmer's answer, uncut


def test_the_edited_video_is_under_the_30_second_limit_with_the_splash():
    caps, total = R.captions(R.plan(MARKS), MARKS)
    assert total + R.LEAD <= R.MAX_SECONDS < 30


def test_a_longer_greeting_is_made_to_fit_by_shortening_the_tails_not_by_cutting_the_hindi():
    slow = {**MARKS, **{k: v + 2.0 for k, v in MARKS.items() if k in ("q1_visible", "waiting", "first_answer", "tap_english",
            "english_shown_end", "last_tap", "results", "tap_option", "tap_estimate", "end")}}
    parts = R.plan(slow)
    assert sum(b - a for a, b, _ in parts) + R.LEAD <= R.MAX_SECONDS
    assert parts[0][1] >= slow["first_answer"]  # the Hindi opening is intact


def test_captions_cover_the_whole_video_one_after_another():
    caps, total = R.captions(R.plan(MARKS), MARKS)
    assert abs(caps[0][0] - R.LEAD) < 1e-6 and abs(caps[-1][1] - (total + R.LEAD)) < 1e-6  # nothing is captioned during the splash
    for (a1, b1, _), (a2, b2, _) in zip(caps, caps[1:]):
        assert a1 < b1 and abs(b1 - a2) < 1e-6  # no gap and no overlap
    assert all(text.strip() for _, _, text in caps)


def test_the_captions_explain_the_call_in_order_ask_read_wait_take_the_answer_move_on():
    caps, _ = R.captions(R.plan(MARKS), MARKS)
    text = " ".join(t for _, _, t in caps).lower()
    positions = [text.index(w) for w in ("greets", "asks one question", "waits", "takes the answer", "moves on")]
    assert positions == sorted(positions)


def test_the_hindi_speech_is_subtitled_in_english():
    caps, _ = R.captions(R.plan(MARKS), MARKS)
    assert any("in Hindi" in t and "I will ask you a few questions" in t for _, _, t in caps)  # the greeting
    assert any("Which district is your farm in?" in t for _, _, t in caps)                       # the first question


def test_the_first_caption_names_the_team_and_the_challenge_and_the_last_one_says_what_is_next():
    caps, _ = R.captions(R.plan(MARKS), MARKS)
    assert "Team Kartik and Amrita" in caps[0][2] and "Adapting Farms with NASA Data" in caps[0][2]
    assert "Next:" in caps[-1][2]


def test_subtitle_times_are_written_as_hours_minutes_seconds_milliseconds():
    assert R.srt_time(3.5) == "00:00:03,500"
    assert R.srt_time(29.9996) == "00:00:29,999"
    assert R.srt_time(-1) == "00:00:00,000"


def test_a_mark_outside_every_kept_part_is_an_error_not_a_wrong_caption():
    bad = {**MARKS, "first_answer": 26.0}  # between the kept parts, so it is cut out
    with pytest.raises(ValueError):
        R.captions(R.plan(MARKS), bad)


def test_the_on_screen_labels_the_script_looks_for_still_exist_in_the_app():
    """If this fails, the app's wording changed: update LABELS, HINDI_STEP or ENGLISH_STEPS in scripts/record_demo.py (one place)."""
    web = nfc("".join(p.read_text(encoding="utf8") for p in (ROOT / "web/app").glob("*.ts*")))
    wanted = [R.LABELS[k] for k in ("start", "waiting", "english", "results", "estimate")] + [R.HINDI_STEP] + [label for label, _ in R.ENGLISH_STEPS]
    missing = [w for w in wanted if nfc(w) not in web]
    assert missing == [], f"not found in the app's text: {missing}; update scripts/record_demo.py"


def test_the_script_taps_one_tile_for_each_of_the_eight_questions():
    assert 1 + len(R.ENGLISH_STEPS) == 8
    assert 1 <= R.SHOWN_ENGLISH_STEPS <= len(R.ENGLISH_STEPS)


def test_the_splash_shows_the_apps_name_in_white_on_the_apps_own_green():
    css = (ROOT / "web/app/globals.css").read_text(encoding="utf8")
    forest = css.split("--color-forest:")[1].split(";")[0].strip().lstrip("#").lower()
    assert R.SPLASH_BG.lower() == "0x" + forest
    assert 1.0 <= R.LEAD <= 2.0  # long enough to read, short enough for the 30 seconds
    title = (ROOT / "web/app/call-script.ts").read_text(encoding="utf8")
    assert f'title: "{R.APP_NAME}"' in title, "the splash name differs from the app's name"


def test_the_hindi_labels_the_screenshot_script_taps_still_exist_in_the_app():
    """scripts/readme_screenshots.py finds buttons by their Hindi text. If this fails, the Hindi wording changed: update the script."""
    web = nfc("".join(p.read_text(encoding="utf8") for p in (ROOT / "web/app").glob("*.ts*")))
    script = (ROOT / "scripts/readme_screenshots.py").read_text(encoding="utf8")
    labels = set(re.findall(r'"([^"\n]*[ऀ-ॿ][^"\n]*)"', script))
    missing = sorted(label for label in labels if nfc(label) not in web)
    assert missing == [], f"not found in the app's text: {missing}; update scripts/readme_screenshots.py"
