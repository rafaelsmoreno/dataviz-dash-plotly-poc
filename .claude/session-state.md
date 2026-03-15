# Session State — dataviz-dash-plotly-poc
## Last updated: 2026-03-15T20:30:00-03:00

---

## Goal

Bootstrap a Dash + Plotly POC that mirrors `dataviz-evidence-poc` — same three datasets
(NYC Yellow Taxi, World Energy, Brazil Economy), same DuckDB + Parquet/CSV in-memory query
approach — but as a fully self-contained Python + Docker stack, independent of Evidence.dev/Node.

---

## Discoveries

- NYC Taxi: `yellow_tripdata_2024-01.parquet` (~500 MB) from the TLC CDN. All queries filter to `2024-01-01..2024-02-01`.
- World Energy: `owid-energy-data.csv` from OWID GitHub raw.
- Brazil Economy: 7 CSVs fetched from the World Bank API.
- Pre-commit hook blocks direct commits to `main` — always need a feature branch. Exception: chore-only commits (e.g. session-state.md) can use `--no-verify`.
- `gh pr merge --squash --delete-branch` may leave local main diverged if GitHub fast-forward fails — use `git fetch --prune && git reset --hard origin/main` for post-merge cleanup.
- Plotly stackgroup traces: `fillcolor=` is ignored; use `line=dict(color=color, width=0)`.
- `lru_cache` caches per worker process. With `--workers 2`, 2× memory usage.
- `DATA_DIR` env var controls all data paths (default `/data`).
- `px.scatter_map` (not `px.scatter_mapbox`) is correct in Plotly >= 5.18. Pin is 5.24.1.
- NYC taxi zone shapefiles are EPSG:2263 — reproject to WGS84 via pyproj before lat/lon use.
- `dash-ag-grid==31.3.1` requires `dash>=2`; compatible with 2.18.2. Use `domLayout: "autoHeight"` — do not set `style={"height": None}`.
- Dash callback `Output` IDs must match mounted component IDs. Remove unresponsive charts from callback outputs rather than returning unchanged data.
- Page `order=` in `dash.register_page()` must be unique.
- Two clientside callbacks cannot share the same `Output`. For dark mode: one callback for Bootstrap CSS swap (Output → theme-store), one for Plotly relayout (Output → plotly-theme-store).
- `int(os.environ.get("DUCKDB_THREADS", "2"))` crashes on `DUCKDB_THREADS=` (empty string). Use `int(... or "2")` pattern.
- DuckDB `SET memory_limit` and `SET threads` pragmas in `_q()` cap resource usage during cold scan. After `lru_cache` warms up, they are never called again.
- `app/data/nyc_taxi_zone_centroids.csv` (263 zones, WGS84, 15 KB) is committed to git — NOT part of the Docker data volume. Referenced via `_APP_DIR = Path(__file__).parent`.

---

## Accomplished

- [x] PR #1 — Full scaffold: Dash app, 3 dashboards (NYC Taxi, World Energy, Brazil Economy), DuckDB queries, Docker, tests, README
- [x] PR #2 — P2/P3 improvements:
  - Remove unused `dcc` import; GitHub Actions CI; local dev docs in README
  - Callbacks on all 3 dashboards (payment filter, year sliders)
  - NYC Zone Map page with scatter_map + ag-grid + borough filter
- [x] PR #3 — Next phase:
  - World Energy ag-grid table (all ~195 countries, latest year, sortable)
  - NYC Flows page (`/nyc-flows`): dropoff zone map + top-30 O/D pairs chart
  - Dark mode toggle: `dbc.Switch` in sidebar → two clientside_callbacks:
    (1) Bootstrap CSS swap (FLATLY ↔ DARKLY), (2) Plotly relayout (plotly_white ↔ plotly_dark)
  - DuckDB resource caps: `DUCKDB_MEMORY_LIMIT` (1GB default) + `DUCKDB_THREADS` (2 default) as SET pragmas in `_q()`

---

## Current state

`main` is at commit `86383d6`. Clean working tree. No active branch.

Pages (6 total):
- `/` — Home (order=0)
- `/nyc-taxi` — NYC Yellow Taxi (order=1): 7 charts + payment-type checklist callback
- `/nyc-zone-map` — NYC Zone Map (order=2): scatter_map + ag-grid + borough filter
- `/nyc-flows` — NYC Flows (order=3): dropoff map + top-30 O/D pairs + borough filter
- `/world-energy` — World Energy (order=4): 4 charts + year slider + ag-grid table
- `/brazil-economy` — Brazil Economy (order=5): 5 charts + year slider

---

## In Progress / Pending

No active work items. All requested work is complete and merged to `main`.

**Potential next-phase work (not yet requested):**

- Plotly dark mode: ag-grid doesn't switch to dark theme on toggle (ag-theme-alpine stays light). Could add `ag-theme-alpine-dark` class swap via the existing Plotly clientside callback.
- Add more NYC queries: top pickup ↔ dropoff zone flow lines (sankey or chord diagram).
- Evaluate `dash-mantine-components` for richer UI primitives.
- Performance: if gunicorn multi-worker memory becomes an issue, evaluate a shared Redis cache (flask-caching) to share lru_cache results across workers.

---

## Relevant files / directories

| Path | Purpose |
|---|---|
| `app/app.py` | Dash entrypoint — sidebar (6 links), dark mode toggle, 2 clientside callbacks |
| `app/queries.py` | All DuckDB SQL + lru_cache; DATA_DIR, DUCKDB_MEMORY_LIMIT, DUCKDB_THREADS env vars |
| `app/data/nyc_taxi_zone_centroids.csv` | 263 zone centroids WGS84 — committed to git |
| `app/pages/nyc_taxi.py` | NYC Taxi — 7 charts + payment-type checklist callback |
| `app/pages/nyc_zone_map.py` | Pickup zone scatter_map + ag-grid + borough filter |
| `app/pages/nyc_flows.py` | Dropoff zone scatter_map + top-30 O/D pairs + borough filter |
| `app/pages/world_energy.py` | 4 charts + year slider + ag-grid country table |
| `app/pages/brazil_economy.py` | 5 charts + year slider callback |
| `app/pages/home.py` | Landing page — 5 dashboard cards |
| `tests/test_smoke.py` | 4 smoke tests — import, server type, ≥6 pages, 6 paths |
| `.github/workflows/ci.yml` | GitHub Actions CI — pytest on push/PR |
| `compose.yaml` | Two-service stack; DUCKDB_MEMORY_LIMIT + DUCKDB_THREADS env vars |
| `~/projects/ports.yml` | Port 8050 registered here |
