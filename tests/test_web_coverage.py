"""The web app decides early, before the farm map, whether a phone's location is inside the area we cover.
It must make exactly the engine's decision (engine/coverage.py: inside the soil tile and within 50 km of a preset),
so a farmer is never shown a map and asked eight questions only to reach a dead end. This runs the app's TypeScript
(web/app/coverage.ts) and the engine on the same points. Skipped where node or web/node_modules is missing."""

import json
import shutil
import subprocess
from pathlib import Path

import pytest

from engine.coverage import locate, presets

ROOT = Path(__file__).resolve().parent.parent
TS_FILE = ROOT / "web/app/coverage.ts"
TS_LIB = ROOT / "web/node_modules/typescript"
NODE = shutil.which("node")

pytestmark = pytest.mark.skipif(not (NODE and TS_LIB.exists()), reason="needs node and web/node_modules (npm install)")

RUNNER = """
const ts = require(process.argv[1]);
const src = require('fs').readFileSync(process.argv[2], 'utf8');
const js = ts.transpileModule(src, { compilerOptions: { module: 'commonjs', target: 'es2020' } }).outputText;
const m = { exports: {} };
new Function('module', 'exports', js)(m, m.exports);
const points = JSON.parse(require('fs').readFileSync(0, 'utf8'));
console.log(JSON.stringify(points.map(([lat, lon]) => m.exports.isServed(lat, lon))));
"""


def web_served(points):
    out = subprocess.run([NODE, "-e", RUNNER, str(TS_LIB), str(TS_FILE)], input=json.dumps(points), capture_output=True, text=True, check=True)
    return json.loads(out.stdout)


def grid():
    lats = [19.5 + 0.25 * i for i in range(11)]  # 19.5 .. 22.0
    lons = [75.8 + 0.25 * j for j in range(11)]  # 75.8 .. 78.3
    return [(round(a, 3), round(b, 3)) for a in lats for b in lons]


def near_the_limit():
    """Points about 49 km and 52 km from each preset, in four directions: either side of the 50 km rule."""
    pts = []
    for lat, lon in presets().values():
        for km in (49, 52):
            d_lat = km / 110.57
            d_lon = km / (111.32 * 0.9376)  # cos(20.5 degrees)
            pts += [(lat + d_lat, lon), (lat - d_lat, lon), (lat, lon + d_lon), (lat, lon - d_lon)]
    return pts


def test_the_app_and_the_engine_agree_on_a_grid_over_and_around_vidarbha():
    pts = grid()
    assert web_served(pts) == [locate(a, b).served for a, b in pts]


def test_the_app_and_the_engine_agree_just_inside_and_just_outside_the_50_km_limit():
    pts = near_the_limit()
    assert web_served(pts) == [locate(a, b).served for a, b in pts]


def test_known_places():
    # Akola town, Bangalore (where the first tester was), Delhi.
    assert web_served([(20.70, 77.008), (12.972, 77.594), (28.61, 77.20)]) == [True, False, False]
