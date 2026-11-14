# Working agreement (Kartik + Amrita, two Claude instances, one repo)

Two people, same house, working together on everything. No fixed role split. Each runs their own Claude Code instance on their own clone of this repo. Decisions are made together.

## Sync rules (every Claude instance must follow)

1. **Before any change:** `git pull --rebase`. If something came in, read what changed (`git log -p ORIG_HEAD..HEAD` or `git diff`) and build on it.
2. **After each logical change:** commit with a clear message and `git push` right away so the other instance can pull. Small, frequent commits.
3. Never force-push. On a conflict, stop, show both sides, and ask the human.
4. Before starting a new task, tell the human what you are about to touch so the pair does not edit the same file at once.
5. Keep secrets out of the repo (`.env`, Earthdata/CDS/Sarvam/LLM keys). Share them out of band.
6. Default branch is `master`.

Full detail and conflict-avoidance rules: [docs/GIT_WORKFLOW.md](docs/GIT_WORKFLOW.md).

## Project rules

See `START.md` for scope, build order and checklists. Key rules: LLM narrates only from engine output, every number checked; no strategy shown without gaps and risks; the "supports, does not replace, local expertise" banner is always visible; product code only inside the 14–15 Nov window.

Review: with two people, whoever did not drive a module reads it before it counts as done.

## Commit attribution

Do not add `Co-Authored-By: Claude ...` trailers to commits, or a "Generated with Claude Code" line to PRs. Contributors are Kartik and Amrita only. Write plain commit messages.
