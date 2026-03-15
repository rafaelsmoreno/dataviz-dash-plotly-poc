# Session State — dataviz-dash-plotly-poc
## Last updated: 2026-03-15T19:30:00-03:00

---

## Goal

Bootstrap a Dash + Plotly POC that mirrors `dataviz-evidence-poc` — same three datasets
(NYC Yellow Taxi, World Energy, Brazil Economy), same DuckDB + Parquet/CSV in-memory query
approach — but as a fully self-contained Python + Docker stack, independent of Evidence.dev/Node.

---

## Instructions

- Fully containerized (Docker Compose, independent)
- Same datasets as `dataviz-evidence-poc`
- Same DuckDB + Parquet/CSV approach (in-memory, no persistent .db)
- Push to GitHub as a **private** repo: `rafaelsmoreno/dataviz-dash-plotly-poc`
- Port 8050 (registered in `~/projects/ports.yml`)
- README must mirror the structure of `dataviz-evidence-poc/README.md` with stack-appropriate changes

---

## Discoveries

- `dataviz-evidence-poc` uses three data sources: `sources/nyc_taxi/`, `sources/world_energy/`, `sources/brazil_economy/` — all read via DuckDB `read_parquet()` / `read_csv()`, no persistent .db file.
- NYC Taxi: `yellow_tripdata_2024-01.parquet` (~500 MB) from the TLC CDN. All queries filter to `2024-01-01..2024-02-01`.
- World Energy: `owid-energy-data.csv` from OWID GitHub raw.
- Brazil Economy: 7 CSVs fetched from the World Bank API (`NY.GDP.MKTP.CD`, `NY.GDP.PCAP.CD`, `FP.CPI.TOTL.ZG`, `SL.UEM.TOTL.ZS`, `PA.NUS.FCRF`, `NE.EXP.GNFS.CD`, `NE.IMP.GNFS.CD`).
- Pre-commit hook on this machine blocks direct commits to `main` — always need a feature branch.
- `gh pr merge --squash --delete-branch` deletes the local branch automatically; no manual `git branch -d` needed.
- Initial repo bootstrap had a branch topology issue (scaffold commit was parent of main's init commit) — resolved by orphan-resetting main and cherry-picking. Lesson: for new repos, push an empty-root commit to main *before* pushing any feature branch.
- Plotly stackgroup traces: `fillcolor=` is ignored; use `line=dict(color=color, width=0)` to control fill colour.
- `lru_cache` on module-level DuckDB query functions: caches per worker process. With `--workers 2` in gunicorn, each worker loads data independently (2× memory). Data is frozen until container restart — intentional for static POC datasets.
- `DATA_DIR` env var controls all data paths in `queries.py` (default `/data`). For local dev outside Docker: `DATA_DIR=./data python app/app.py`.
- `px.scatter_map` (not `px.scatter_mapbox`) is the correct API in Plotly >= 5.18. Our pin is `plotly==5.24.1`.
- NYC taxi zone shapefiles are in EPSG:2263 (NY State Plane feet) — must reproject to WGS84 (EPSG:4326) via pyproj before using as lat/lon.
- `dash-ag-grid` requires `dash>=2`; version `31.3.1` is compatible with `dash==2.18.2`. Use `domLayout: "autoHeight"` for variable-height grids — do not set `style={"height": None}`.
- Dash callback `Output` IDs must match component IDs in the layout. If a component doesn't respond to a filter (e.g. vendor chart not broken down by payment type), remove it from the callback outputs rather than returning unchanged data (avoids no-op round-trips).
- Page `order=` values in `dash.register_page()` must be unique; duplicates cause non-deterministic sidebar ordering.
- `app/data/nyc_taxi_zone_centroids.csv` (263 zones, WGS84, 15 KB) is committed to git under `app/data/` — NOT part of the Docker data volume. Referenced in `queries.py` via `_APP_DIR = Path(__file__).parent` so it's path-independent.

---

## Accomplished

- [x] PR #1 — Full scaffold: Dash app, 3 dashboards, DuckDB queries, Docker, tests, README
- [x] PR #2 — All P2/P3 pending work items:
  - [x] Remove unused `dcc` import in `app/app.py`
  - [x] GitHub Actions CI workflow (`.github/workflows/ci.yml`) — pytest on every push + PR to main
  - [x] Local dev setup section in README (venv, `DATA_DIR`, `init_data.sh`)
  - [x] Interactive Dash callbacks on all 3 dashboards:
    - NYC Taxi: payment-type checklist → filters payment donut, distance histogram, fare scatter
    - World Energy: year-range slider → filters stacked area + TWh line charts
    - Brazil Economy: year-range slider → filters all 4 charts
  - [x] NYC Zone Map page (`/nyc-zone-map`): `px.scatter_map` on OpenStreetMap, 263-zone pickup bubble map with borough filter + auto-zoom
  - [x] `dash-ag-grid==31.3.1` — sortable/filterable/paginated zone summary table on zone map page
  - [x] Zone centroid CSV derived from official TLC shapefiles (pyshp + pyproj), committed to git

---

## In Progress / Pending

No active work items. All P2/P3 items are complete and merged to `main`.

**Potential next-phase work (not yet requested):**

- P3 — Add a second ag-grid page for World Energy (195-country latest-year table)
- P3 — Add more NYC Taxi queries: dropoff zone map, top O/D pairs
- P3 — Evaluate adding dark mode (dbc `color_mode_switch`)
- P4 — Performance: consider `dask` or chunked DuckDB reads for the Parquet on lower-memory hosts

---

## Relevant files / directories

| Path | Purpose |
|---|---|
| `app/app.py` | Dash entrypoint — sidebar (5 links), multi-page router, gunicorn `server` |
| `app/queries.py` | All DuckDB SQL + `lru_cache`; `DATA_DIR` env var controls paths; `_APP_DIR` for static lookups |
| `app/data/nyc_taxi_zone_centroids.csv` | 263 zone centroids WGS84 — committed to git, path-independent |
| `app/pages/nyc_taxi.py` | NYC Taxi dashboard — 7 charts + payment-type checklist callback |
| `app/pages/nyc_zone_map.py` | Zone Map — scatter_map + ag-grid table + borough checklist callback |
| `app/pages/world_energy.py` | World Energy — 4 charts + year-range slider callback |
| `app/pages/brazil_economy.py` | Brazil Economy — 5 charts + year-range slider callback |
| `app/pages/home.py` | Landing page — 4 dashboard cards |
| `scripts/init_data.sh` | Data downloader (idempotent) |
| `tests/test_smoke.py` | 4 smoke tests — import, server type, ≥4 pages, 5 paths |
| `.github/workflows/ci.yml` | GitHub Actions CI — pytest on push/PR |
| `Dockerfile` | python:3.12-slim + gunicorn + HEALTHCHECK |
| `compose.yaml` | Two-service stack |
| `Makefile` | Developer shortcuts |
| `README.md` | Full documentation |
| `~/projects/ports.yml` | Port 8050 registered here |
