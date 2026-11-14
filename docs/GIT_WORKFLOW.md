# Git workflow: two people, minimal conflicts

One repo, `master` only. Both push directly. Conflicts are avoided by *not editing the same file at the same time*, plus tiny, frequent syncs.

## Setup (once, each person)

```bash
git clone https://github.com/kmcodes/space-apps.git
cd space-apps
git config pull.rebase true        # pull always rebases, linear history
git config rebase.autoStash true   # auto-stash uncommitted work during pull
git config user.name  "<your name>"
git config user.email "<your email>"
```

## The loop (every change)

```bash
git pull                 # 1. get the other person's work
# ... edit ...
git add <specific files> # 2. never `git add -A` blindly (avoids committing .env / data)
git commit -m "area: what changed"
git pull                 # 3. again, in case they pushed meanwhile
git push                 # 4. push immediately
```

Rules of thumb:
- Commit + push every 15–30 min or after each working step. Small diffs rarely conflict.
- Never leave work unpushed when you stop for a break or the other person starts a related task.
- Never force-push. Never rewrite pushed history.
- If `git push` is rejected: `git pull`, then push again.

## Ownership by folder (the main conflict-avoider)

At each check-in, say who drives which folder. Only the driver edits it; the other reads and suggests. Switch at check-ins, not mid-task.

| Folder / file | Typical content |
|---|---|
| `pipeline/` + `data/` | fetch scripts, feature derivation |
| `engine/` | scorer, crop profiles, weights |
| `api/` | `/compare` endpoint |
| `web/` | dashboard |
| `voice/` | Hindi flow, fallback audio |
| `docs/`, `START.md`, `README.md` | notes, checklists |

Shared files that both touch (`START.md` checklists, `requirements.txt`, `package.json`, lockfiles): only edit in small, separate commits and pull right before.

## Keep files small and separate

- One module per file (e.g. `engine/scoring.py`, `engine/crops.py`) rather than one big file.
- Each person writes notes in their own file (`docs/notes-kartik.md`, `docs/notes-amrita.md`) instead of one shared notes file.
- Generated files, lockfiles, big data: do not hand-edit; regenerate. Raw data stays gitignored (`data/raw/`); share via a message or shared drive.
- Don't reformat or rename files you don't own (no repo-wide formatter runs while the other is working).

## Claude instances

Each Claude follows `CLAUDE.md`: pull first, tell you what it is about to touch, commit + push after each change. Before asking Claude to start a task, tell the other person which files you'll touch.

## If there is a conflict anyway

1. `git status` shows the conflicted files. Do not panic, nothing is lost.
2. Open the file, keep both sides' intent, remove `<<<<<<<`, `=======`, `>>>>>>>` markers.
3. `git add <file>` then `git rebase --continue`.
4. Unsure: `git rebase --abort` returns to before the pull. Then ask the other person.
5. Run the code/tests, then push.

## Secrets

Never commit API keys (Earthdata, CDS, Sarvam, LLM). Use a local `.env` (gitignored) and send keys privately. Keep a committed `.env.example` with names only.
