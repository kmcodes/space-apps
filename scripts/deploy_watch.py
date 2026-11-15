"""Redeploy the live app when someone pushes to GitHub. Runs on one PC, only while that PC is on.

Why: the repo is on Kartik's GitHub account, so Render and Vercel cannot be told about pushes directly.
This script polls GitHub instead and redeploys what changed:

- web/ changed            -> Vercel production deploy (Vercel CLI, logged in on this PC; Vercel builds it)
- api/, engine/, data/,
  requirements.txt changed -> Render deploy hook (Render builds from GitHub itself)

It deploys from its own clean clone in .deploy/ (gitignored), so it never touches your working copy.

Needs, in the repo-root .env (gitignored):
    RENDER_DEPLOY_HOOK=https://api.render.com/deploy/srv-...?key=...
and `npx vercel login` done once on this PC.

Run from the repo root:   .venv\\Scripts\\python scripts\\deploy_watch.py
Stop with Ctrl-C.          Add --once to check and deploy once, then exit.
"""
import json
import shutil
import subprocess
import sys
import time
import urllib.request
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CLONE = ROOT / ".deploy" / "space-apps"
STATE = ROOT / ".deploy" / "state.json"
REPO_URL = "https://github.com/kmcodes/space-apps.git"
BRANCH = "master"
API_URL = "https://space-apps-dzma.onrender.com"
INTERVAL_S = 120
WEB_PATHS = ("web/",)
API_PATHS = ("api/", "engine/", "data/", "requirements.txt")
NPX = shutil.which("npx") or r"C:\Program Files\nodejs\npx.cmd"


def log(msg):
    print(f"[{datetime.now():%H:%M:%S}] {msg}", flush=True)


def git(*args, cwd=CLONE):
    return subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True, text=True, encoding="utf-8", errors="replace").stdout.strip()


def render_hook():
    env = ROOT / ".env"
    for line in env.read_text().splitlines() if env.exists() else []:
        if line.startswith("RENDER_DEPLOY_HOOK="):
            value = line.split("=", 1)[1].strip()
            if value.startswith("https://") and "PASTE" not in value:
                return value
    return None


def load_state():
    try:
        return json.loads(STATE.read_text())
    except (OSError, ValueError):
        return {}


def save_state(state):
    STATE.write_text(json.dumps(state, indent=2))


def ensure_clone():
    if not (CLONE / ".git").exists():
        log("making a clean clone for deploys in .deploy/ ...")
        CLONE.parent.mkdir(parents=True, exist_ok=True)
        git("clone", "--quiet", "--branch", BRANCH, REPO_URL, str(CLONE), cwd=ROOT)
    link = ROOT / "web" / ".vercel" / "project.json"  # which Vercel project to deploy to
    if link.exists():
        (CLONE / "web" / ".vercel").mkdir(parents=True, exist_ok=True)
        shutil.copy(link, CLONE / "web" / ".vercel" / "project.json")


def changed(old, new):
    if not old:
        return None  # unknown: deploy everything once
    return git("diff", "--name-only", old, new).splitlines()


def touches(files, prefixes):
    return files is None or any(f.startswith(p) for f in files for p in prefixes)


_warned = set()


def deploy_render(hook):
    if not hook:
        if "hook" not in _warned:  # say it once, not every two minutes; it is picked up once added
            log("Render: no RENDER_DEPLOY_HOOK in .env yet, waiting for it")
            _warned.add("hook")
        return False
    with urllib.request.urlopen(urllib.request.Request(hook, method="POST"), timeout=60) as r:
        ok = 200 <= r.status < 300
    log("Render: deploy started (it builds from GitHub; takes a few minutes)" if ok else f"Render: hook answered {r.status}")
    return ok


def deploy_vercel():
    log("Vercel: deploying web/ ...")
    r = subprocess.run([NPX, "--yes", "vercel@latest", "deploy", "--prod", "--yes",
                        "--build-env", f"NEXT_PUBLIC_API_URL={API_URL}"],
                       cwd=CLONE / "web", capture_output=True, text=True, encoding="utf-8", errors="replace")
    if r.returncode == 0:
        log("Vercel: live at https://field-shift-opal.vercel.app")
        return True
    log("Vercel: deploy FAILED:\n" + (r.stderr or r.stdout)[-1500:])
    return False


def check_once():
    ensure_clone()
    git("fetch", "--quiet", "origin", BRANCH)
    new = git("rev-parse", f"origin/{BRANCH}")
    state = load_state()
    if new == state.get("web") and new == state.get("api"):
        return
    git("reset", "--quiet", "--hard", f"origin/{BRANCH}")
    log(f"new commit {new[:7]}: {git('log', '-1', '--format=%an: %s')}")
    hook = render_hook()
    if new != state.get("api"):
        if touches(changed(state.get("api"), new), API_PATHS):
            if deploy_render(hook):
                state["api"] = new
        else:
            state["api"] = new
    if new != state.get("web"):
        if touches(changed(state.get("web"), new), WEB_PATHS):
            if deploy_vercel():
                state["web"] = new
        else:
            state["web"] = new
    save_state(state)


def main():
    # Commit messages can be Hindi; a Windows console may not print them, so never let printing stop a deploy.
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    once = "--once" in sys.argv
    log(f"watching {REPO_URL} ({BRANCH}) every {INTERVAL_S}s. Ctrl-C to stop.")
    if not render_hook():
        log("note: RENDER_DEPLOY_HOOK is not set in .env, so only Vercel will redeploy")
    while True:
        try:
            check_once()
        except Exception as e:  # keep watching after a network blip or a failed deploy
            log(f"error: {e}")
        if once:
            return
        time.sleep(INTERVAL_S)


if __name__ == "__main__":
    main()
