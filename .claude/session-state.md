# Session State — dataviz-dash-plotly-poc
## Last updated: 2026-03-15T23:15:00-03:00

---

## Goal

Build a Dash + Plotly POC data visualization app — 6 fully interactive dashboards backed by
DuckDB + Parquet/CSV, served via Docker Compose, with dark mode, sidebar navigation, and CI.
The project is **complete and production-quality** as of this session.

---

## Instructions

- SSH not configured — use HTTPS for all git operations.
- Pre-commit hook blocks direct commits to `main`; always use a feature branch. Exception: session-state and chore-only files may use `--no-verify`.
- `gh pr merge --squash --delete-branch` may leave local main diverged — use `git fetch --prune && git reset --hard origin/main` after every merge.
- No Evidence-POC references in any user-facing file (README, home page). Internal session state may reference it.
- URLs the user is meant to open must be clickable Markdown links `[label](url)`, never backtick-wrapped.
- Dark mode is the **default**. Light mode is the toggle-to state.
- ag-grid components use `ag-theme-alpine-dark` as the initial class (dark default).

---

## Discoveries

- `python:3.12-slim` ships **neither curl nor wget**. The `data-init` service installs curl at runtime via `apt-get`. This is intentional and correct — no alternative without changing the base image.
- `px.scatter_map` (not `px.scatter_mapbox`) is correct in Plotly >= 5.18. Pinned at 5.24.1.
- NYC taxi zone shapefiles are EPSG:2263 (NY State Plane feet) — must reproject via pyproj to WGS84 before use as lat/lon.
- `dash-ag-grid==31.3.1` requires `dash>=2`. Use `domLayout: "autoHeight"` — never `style={"height": None}`.
- Two clientside callbacks cannot share the same `Output`. Dark mode uses three separate callbacks: (1) Bootstrap CSS swap → `theme-store`, (2) Plotly relayout → `plotly-theme-store`, (3) ag-grid class swap → `ag-grid-theme-store`.
- ag-grid dark mode: swap `ag-theme-alpine` ↔ `ag-theme-alpine-dark` via `classList.remove/add` in a clientside callback. Initial class must match the default theme to avoid a flash on load.
- `int(os.environ.get("DUCKDB_THREADS") or "2")` — use `or "2"` not default arg to guard against empty string env var.
- Plotly stackgroup traces: `fillcolor=` is ignored; use `line=dict(color=color, width=0)` for fill colour.
- `lru_cache` caches per worker process. With `--workers 2`, each worker loads data independently (~2× memory). Data frozen until container restart — intentional for static POC datasets.
- `app/data/nyc_taxi_zone_centroids.csv` (263 zones, WGS84, 15 KB) is committed to git under `app/` — NOT part of the Docker data volume. Referenced via `_APP_DIR = Path(__file__).parent`.
- `DATA_DIR` env var controls all data paths (default `/data`). Local dev: `DATA_DIR=./data python app/app.py`.
- Page `order=` in `dash.register_page()` must be unique or sidebar ordering is non-deterministic.
- Dash callback `Output` IDs must match mounted component IDs. Never wire a component to a callback if its data doesn't change on the filter event.
- No-speculation rule applies to **audit output** as much as to factual claims — every finding in a gap analysis must be grounded in a file read or running check, never memory.

---

## Accomplished (all PRs merged to main)

- **PR #1** — Full scaffold: Dash app, 3 dashboards (NYC Taxi, World Energy, Brazil Economy), DuckDB queries, Docker Compose, smoke tests, README.
- **PR #2** — P2/P3 backlog: remove stale import, GitHub Actions CI, local dev README section, callbacks on all 3 original dashboards (payment filter + year sliders), NYC Zone Map page (scatter_map + ag-grid + borough filter).
- **PR #3** — Next phase: World Energy ag-grid country table, NYC Flows page (dropoff map + top-30 O/D pairs), dark mode toggle (Bootstrap + Plotly), DuckDB memory/thread caps.
- **PR #4** — Fix data-init: install curl in `python:3.12-slim` entrypoint, add `mkdir -p` before Brazil economy CSV writes.
- **PR #5** — Dark mode default + NYC collapsible sidebar group: `dbc.Switch value=True`, initial stylesheet DARKLY, NYC pages grouped under collapsible "NYC" parent with chevron.
- **PR #6** — Remove internal Evidence-POC reference from home page subtitle.
- **PR #7** — README full cleanup: remove Comparison section, fix "Three"→"Six", add NYC Flows to table and breakdown, add `nyc_flows.py` to project structure, fix localhost URLs to clickable links.
- **PR #8** — ag-grid dark mode: third clientside callback swaps `ag-theme-alpine` ↔ `ag-theme-alpine-dark`; initial class set to `ag-theme-alpine-dark`.
- **PR #9** — README fix: note ag-grid used in both NYC Zone Map and World Energy.

---

## Current state

`main` is at commit `f635dcc` (PR #9). Clean working tree. Stack healthy at [http://localhost:8050](http://localhost:8050).

### Pages (6 total, all working)

| Order | Path | Description |
|---|---|---|
| 0 | `/` | Home — 5 dashboard cards |
| 1 | `/nyc-taxi` | NYC Yellow Taxi — 7 charts + payment-type checklist callback |
| 2 | `/nyc-zone-map` | NYC Zone Map — scatter_map + ag-grid + borough filter |
| 3 | `/nyc-flows` | NYC Flows — dropoff map + top-30 O/D pairs + borough filter |
| 4 | `/world-energy` | World Energy — 4 charts + year slider + ag-grid country table |
| 5 | `/brazil-economy` | Brazil Economy — 5 charts + year slider |

### Known constraints (not bugs, not fixable without changing base image)

- `data-init` installs curl at runtime via `apt-get` (~10 sec overhead on first container start). `python:3.12-slim` ships neither curl nor wget — this is the only working approach.

---

## In Progress / Pending

**Nothing pending. Project is complete.**

No open branches, no failing tests, no open PRs.

---

## Relevant files / directories

| Path | Purpose |
|---|---|
| `app/app.py` | Dash entrypoint — sidebar with NYC collapse group, 3 dark mode clientside callbacks, dark default |
| `app/queries.py` | DuckDB query layer — all SQL, `lru_cache`, `DATA_DIR`, `DUCKDB_MEMORY_LIMIT`, `DUCKDB_THREADS` |
| `app/data/nyc_taxi_zone_centroids.csv` | 263 zone centroids WGS84 — committed to git, path-independent |
| `app/pages/home.py` | Landing page — 5 dashboard cards |
| `app/pages/nyc_taxi.py` | NYC Taxi — 7 charts + payment-type checklist callback |
| `app/pages/nyc_zone_map.py` | Pickup scatter_map + ag-grid-dark + borough filter |
| `app/pages/nyc_flows.py` | Dropoff scatter_map + top-30 O/D pairs + borough filter |
| `app/pages/world_energy.py` | 4 charts + year slider + ag-grid-dark country table |
| `app/pages/brazil_economy.py` | 5 charts + year slider callback |
| `tests/test_smoke.py` | 4 smoke tests — import, server type, ≥6 pages, 6 paths |
| `.github/workflows/ci.yml` | GitHub Actions CI — pytest on every push/PR |
| `compose.yaml` | Two-service stack — `data-init` (curl install + download) → `dash` (gunicorn, port 8050) |
| `scripts/init_data.sh` | Downloads Parquet + OWID CSV + 7 World Bank CSVs (idempotent) |
| `Makefile` | `up`, `down`, `logs`, `build`, `shell`, `test`, `clean` |
| `~/projects/ports.yml` | Port 8050 registered here |
| `~/.claude/rules/universal-engineering.md` | Global rules — updated this session with no-speculation audit rule and clickable URL rule |
| `~/projects/CLAUDE.md` | Project-wide rules — same two rules added |
