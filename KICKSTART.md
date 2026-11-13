# Kickstart Prompt — dataviz-dash-plotly-poc

Last updated: 2026-11-13
Base commit: f138bd6067168aacdaa1d280f1fd268432358429
Maintained by `scripts/update_kickstart.py` — do not edit manually.

---

## Session bootstrap — /kickstart reads and executes this automatically:

```
Repo: dataviz-dash-plotly-poc — continuing from previous session.

## Last completed (2026-11-13)
POC is COMPLETE — all 9 PRs merged to main at f635dcc. 6 dashboards, dark mode default, NYC sidebar group, ag-grid dark mode, CI, clean README.

REFRESHED 2026-11-13 (handoff bookkeeping only; no session worked this repo): the handoff had gone stale against main. Commits that landed since it was last written, taken from the commit log rather than from any session record, so no narrative beyond the subjects is available: f138bd6 chore(ci): bump actions to node24 — checkout v6.0.2, setup-python v6.2.0 (#12);

## Current branch
main

## Open PRs
  (none)

## Start here: POC is complete — no pending work. If new work requested, create feature branch first.

- Confirm clean state: git status && git log --oneline -5
- If stack not running: make up && make logs, open http://localhost:8050
- Run smoke tests: make test (expect 4 passed)

## Persistent context
- Dark mode is the default — Bootstrap DARKLY, switch starts True, ag-grid alpine-dark
- Port 8050 — registered in ~/projects/ports.yml. Do not rebind.
- python:3.12-slim has no curl/wget — data-init installs curl via apt-get at container start
- Pre-commit hook blocks direct commits to main — always create feature branch first

## Blockers / Watch out
none
Do not ask about optional parameters. Start working.
```
