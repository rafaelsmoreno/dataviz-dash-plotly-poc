# Session State — dataviz-dash-plotly-poc
## Last updated: 2026-03-15T21:30:00-03:00

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
- `dcc` is imported but unused in `app/app.py` (minor P2 leftover).

---

## Accomplished

- [x] Initialized git repo on `main`, created private GitHub repo `rafaelsmoreno/dataviz-dash-plotly-poc`
- [x] Registered port 8050 in `~/projects/ports.yml`
- [x] Scaffolded full project structure: `app/`, `data/`, `scripts/`, `tests/`
- [x] `scripts/init_data.sh` — idempotent downloader for Parquet + 7 CSVs
- [x] `app/queries.py` — full DuckDB query layer: 9 NYC Taxi queries, 3 World Energy queries, 1 Brazil macro query; all `lru_cache`-decorated
- [x] `app/pages/nyc_taxi.py` — 7 charts: KPI cards, daily trips+revenue, hourly heatmap, payment donut, vendor grouped bar, distance distribution, fare vs. distance scatter
- [x] `app/pages/world_energy.py` — 4 charts: stacked area mix share, TWh lines, top-20 renewable countries bar, country mix stacked bar (fixed fill color bug)
- [x] `app/pages/brazil_economy.py` — 5 charts: KPI cards, GDP dual-axis, inflation+unemployment, USD/BRL area, trade balance
- [x] `app/pages/home.py` — landing page with 3 dashboard card links
- [x] `app/app.py` — Dash multi-page entrypoint, fixed sidebar nav, gunicorn `server` object
- [x] `Dockerfile` — `python:3.12-slim`, gunicorn, HEALTHCHECK (90s start-period), copies `tests/` and `pytest.ini`
- [x] `compose.yaml` — `data-init` (runs once, `service_completed_successfully`) → `dash` (always, port 8050), named volume `data`
- [x] `Makefile` — `up / down / build / logs / shell / test / clean`
- [x] `requirements.txt` — pinned: dash 2.18.2, dbc 1.6.0, plotly 5.24.1, duckdb 1.2.0, pandas 2.2.3, gunicorn 23.0.0, pytest 8.3.5
- [x] `pytest.ini` + `tests/test_smoke.py` — 4 smoke tests (module import, Flask server type, pages count, all 4 paths registered)
- [x] `README.md` — mirrors `dataviz-evidence-poc/README.md` structure: Dashboards, Stack, How to Run, Makefile targets, Project Structure, Architecture Notes, Comparison table
- [x] PR #1 opened, PR review run (3 findings: HEALTHCHECK, tests, fill-color — all fixed), PR merged via squash, branch deleted, post-merge cleanup done

---

## In Progress / Pending

No active work items. The POC scaffold is complete and merged to `main`.

**Potential next-phase work (not yet requested):**

- P2 — Remove unused `dcc` import in `app/app.py:22`
- P2 — Add a GitHub Actions CI workflow (`pytest` on push/PR)
- P2 — Local dev setup: `pip install -e .` / `venv` instructions in README
- P3 — Add Dash callbacks for interactive filtering (currently all charts are static renders)
- P3 — Add a zone map page for NYC Taxi (the Evidence-POC has a PointMap — equivalent would be a Plotly `scatter_mapbox`)
- P3 — Evaluate adding `dash-ag-grid` for tabular data views

---

## Relevant files / directories

| Path | Purpose |
|---|---|
| `app/app.py` | Dash entrypoint — sidebar, multi-page router, gunicorn `server` |
| `app/queries.py` | All DuckDB SQL + `lru_cache`; `DATA_DIR` env var controls paths |
| `app/pages/nyc_taxi.py` | NYC Taxi dashboard — 7 charts |
| `app/pages/world_energy.py` | World Energy dashboard — 4 charts (fill-color fixed) |
| `app/pages/brazil_economy.py` | Brazil Economy dashboard — 5 charts |
| `app/pages/home.py` | Landing page |
| `scripts/init_data.sh` | Data downloader (idempotent) |
| `tests/test_smoke.py` | 4 smoke tests — no data required |
| `Dockerfile` | Build + HEALTHCHECK |
| `compose.yaml` | Two-service stack |
| `Makefile` | Developer shortcuts |
| `README.md` | Full documentation |
| `~/projects/ports.yml` | Port 8050 registered here |
