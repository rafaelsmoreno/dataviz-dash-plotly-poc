# Next Session Kickstart — dataviz-dash-plotly-poc

## Resuming from

The initial scaffold is **complete and merged to `main`**. The Dash + Plotly POC is a
fully containerized Python app with 3 dashboards (NYC Taxi, World Energy, Brazil Economy)
backed by DuckDB + Parquet/CSV — mirroring `dataviz-evidence-poc`. No active branch; all
work is on `main`.

## Read first

`.claude/session-state.md` in this repo has full context.

## Immediate actions

1. Confirm clean state:
   ```bash
   git status && git log --oneline
   ```
   Expected: clean working tree, 2 commits on `main`.

2. If running the stack for the first time:
   ```bash
   make up && make logs
   # open http://localhost:8050
   ```

3. To run smoke tests (no data required):
   ```bash
   make test
   ```

## Pending work (prioritised)

- **P2** — Remove unused `dcc` import in `app/app.py:22` (`from dash import Dash, dcc, html` → remove `dcc`)
- **P2** — Add GitHub Actions CI workflow: run `pytest` on push/PR (no data needed, smoke tests only)
- **P2** — Add local dev setup instructions to README (`venv`, `pip install -r requirements.txt`, `DATA_DIR=./data python app/app.py`)
- **P3** — Add Dash callbacks for interactive filtering (currently all charts are static; no `Input`/`Output` callbacks exist)
- **P3** — NYC Taxi zone map page (`scatter_mapbox` with taxi zone centroids — mirrors the Evidence-POC PointMap page)
- **P3** — Evaluate `dash-ag-grid` for tabular data views

## Key technical facts

1. **Port 8050** — registered in `~/projects/ports.yml`. Do not rebind or change without updating that file.
2. **Pre-commit hook blocks direct commits to `main`** — always create a feature branch first (`git checkout -b feat/<name>`).
3. **DATA_DIR env var** — `app/queries.py` resolves all data paths from `DATA_DIR` (default `/data`). For local dev outside Docker: `DATA_DIR=./data python app/app.py`.
4. **Plotly stackgroup fill color** — `fillcolor=` is ignored on `stackgroup` traces; use `line=dict(color=color, width=0)` instead. Already fixed in `world_energy.py`.
5. **lru_cache behaviour** — all query functions are `@lru_cache(maxsize=1)`; data is frozen per worker process until the container restarts. With `--workers 2` in gunicorn, each worker caches independently (2× memory). This is intentional for static POC datasets.
