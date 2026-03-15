# Next Session Kickstart — dataviz-dash-plotly-poc

## Resuming from

The project is **complete**. All 9 PRs are merged to `main` at `f635dcc`.
6 dashboards, dark mode default, NYC sidebar group, ag-grid dark mode, CI, clean README.
No open branches, no failing tests, no pending work.

## Read first

`.claude/session-state.md` in this repo has full context.

## Immediate actions

1. Confirm clean state:
   ```bash
   git status && git log --oneline -5
   ```
   Expected: clean working tree, `f635dcc` at HEAD.

2. If the stack is not running:
   ```bash
   make up && make logs
   ```
   Open [http://localhost:8050](http://localhost:8050). First load is slow (~20s) — DuckDB cold scan.

3. Run smoke tests to confirm nothing drifted:
   ```bash
   make test
   ```
   Expected: 4 passed.

## Pending work (prioritised)

**Nothing pending.** The POC is complete and production-quality.

If new work is requested, start by reading `session-state.md` for full technical context,
then create a feature branch (`git checkout -b feat/<name>`) before any change.

## Key technical facts

1. **Dark mode is the default.** Bootstrap loads `DARKLY`, switch starts `value=True`, ag-grid starts `ag-theme-alpine-dark`. Three separate clientside callbacks handle Bootstrap / Plotly / ag-grid independently — they cannot share an `Output`.
2. **`python:3.12-slim` has no curl or wget.** `data-init` installs curl via `apt-get` at container start. This is verified and intentional — do not attempt to replace with wget (not present).
3. **Port 8050** — registered in `~/projects/ports.yml`. Do not rebind.
4. **Pre-commit hook blocks direct commits to `main`** — always create a feature branch first.
5. **No user-facing Evidence-POC references** — README and home page are clean; keep them clean.
