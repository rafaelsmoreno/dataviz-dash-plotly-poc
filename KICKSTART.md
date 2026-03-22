# Kickstart Prompt — dataviz-dash-plotly-poc

Last updated: 2026-03-22
Maintained by `scripts/update_kickstart.py` — do not edit manually.

---

## Paste this at the start of the next session:

```
Repo: dataviz-dash-plotly-poc — continuing from previous session.

## Last completed (2026-03-22)
POC is COMPLETE — all 9 PRs merged to main at f635dcc. 6 dashboards, dark mode default, NYC sidebar group, ag-grid dark mode, CI, clean README.

## Repo: dataviz-dash-plotly-poc
## Date: 2026-03-22

## Current branch
main

## Open PRs
  (none)

## Last 3 commits
  7a80c60 chore(claude): create .claude/CLAUDE.md (M4 consolidation) (#10)
  f635dcc fix: README — note ag-grid is used in both NYC Zone Map and World Energy (#9)
  e447a8c fix: ag-grid dark mode — swap ag-theme-alpine ↔ ag-theme-alpine-dark on toggle (#8)

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
