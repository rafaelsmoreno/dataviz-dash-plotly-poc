# Dash + Plotly POC

A proof-of-concept data visualization project built with [Dash](https://dash.plotly.com) and [Plotly](https://plotly.com/python/),
evaluating Dash as a candidate for a Python-native, version-controlled analytics platform.

Three fully interactive dashboards, built entirely in Python. No drag-and-drop. No GUI.
Everything is code, everything is in git.

---

## Dashboards

| Dataset | Charts | Source |
|---|---|---|
| **NYC Yellow Taxi** | KPIs, daily trend, heatmap, payment, vendor, distribution, scatter | TLC Jan 2024 Parquet (2.7M rows) |
| **World Energy Mix** | Global mix share, TWh by source, top renewable countries, country mix | Our World in Data CSV |
| **Brazil Economy** | GDP, inflation, FX, trade balance (2000–2025) | World Bank Open Data API |

### NYC Yellow Taxi
- KPI overview: total trips, revenue, avg fare, avg distance, avg duration, avg tip %
- Daily trip volume + revenue trend for January 2024
- Hourly heatmap (trips by hour × day of week)
- Payment type donut chart
- Vendor comparison (grouped bar)
- Trip distance distribution (histogram)
- Fare vs. distance scatter plot (5 000-row sample, coloured by payment type)

### World Energy Mix
- Global electricity mix share over time — stacked area (1990–present)
- Absolute generation by source in TWh — line chart
- Top 20 countries by renewable share (latest year)
- Energy mix breakdown for top-10 countries by total generation

### Brazil Economy
- GDP (total and per capita), inflation, unemployment, USD/BRL rate
- Exports, imports, trade balance — all from World Bank API
- Full time-series from 2000 to 2025

---

## Stack

```
Dash + Plotly  →  Python multi-page app served by gunicorn
DuckDB         →  In-memory query engine (no persistent .db file)
Docker Compose →  Two-service stack: data-init + dash app server
```

All raw data is downloaded at container start by `scripts/init_data.sh`. Nothing is committed to git.

---

## How to Run

```bash
docker compose up --build
```

Open **http://localhost:8050**.

The `data-init` service downloads all raw data files on first run (skips if already present).
The `dash` service waits for it to finish, then starts gunicorn.

**First run** takes ~3–5 min (downloads ~500 MB of raw data — mainly the Parquet file).
**Subsequent runs** start in ~10 sec (data already present in the named Docker volume).

### Makefile targets

```bash
make up       # build + start in detached mode
make logs     # tail container logs
make down     # stop containers
make build    # rebuild the dash image without cache
make shell    # open a shell inside the running dash container
make test     # run smoke tests inside the dash container (no data required)
make clean    # full reset — removes containers AND the data volume (re-downloads on next up)
```

---

## Project Structure

```
app/
  app.py                        # Dash entrypoint — sidebar nav, multi-page router
  queries.py                    # DuckDB query layer — all SQL, lru_cache, path helpers
  pages/
    home.py                     # Landing page — links to all 3 dashboards
    nyc_taxi.py                 # 7 charts: KPIs, daily, heatmap, payment, vendor, dist, scatter
    world_energy.py             # 4 charts: stacked area, TWh lines, top-20 bar, country mix
    brazil_economy.py           # 5 charts: KPIs, GDP, inflation/unemp, FX, trade balance

scripts/
  init_data.sh                  # Downloads all raw data files (idempotent — skips if present)

tests/
  test_smoke.py                 # Import smoke tests — server object, page registry

Dockerfile                      # python:3.12-slim + gunicorn + HEALTHCHECK
compose.yaml                    # data-init (runs once) → dash (always, port 8050)
requirements.txt                # pinned Python dependencies
pytest.ini                      # pytest config
Makefile                        # Developer shortcuts
```

---

## Architecture Notes

**In-memory DuckDB** — `queries.py` opens a fresh `:memory:` connection per query call and reads
raw files directly via `read_parquet()` or `read_csv()`. No persistent `.db` file, no schema
migration, no cross-container path issues.

**`lru_cache` query caching** — every query function is decorated with `@lru_cache(maxsize=1)`.
Results are cached in-process after the first request. This means:
- First page load is slow (DuckDB scans the full Parquet/CSV).
- Subsequent loads are instant (served from memory).
- Data does not refresh until the container is restarted. For a POC with static datasets, this is intentional.
- With `--workers 2` in gunicorn, each worker caches independently (~2× memory usage).

**DATA_DIR env var** — all data paths are resolved from `DATA_DIR` (default: `/data`).
Override this for local development outside Docker:

```bash
DATA_DIR=./data python app/app.py
```

**Smoke tests** — `tests/test_smoke.py` verifies the Dash app imports cleanly, the gunicorn
`server` object is a Flask app, and all 4 page paths are registered — without requiring any
data files. Run with `make test`.

---

## Comparison with Evidence-POC

This repo and [`dataviz-evidence-poc`](https://github.com/rafaelsmoreno/dataviz-evidence-poc) use
identical datasets and the same DuckDB + Parquet/CSV in-memory query approach. The difference is
the rendering layer:

| Dimension | Evidence.dev | Dash + Plotly |
|---|---|---|
| Language | SQL + Markdown | Python |
| Interactivity | Client-side DuckDB-WASM | Server-side Python callbacks |
| Output | Static site (pre-aggregated) | Dynamic WSGI app |
| Deployment | Static hosting (CDN/S3) | Container (gunicorn) |
| Customisation | Limited to Evidence components | Full Plotly + HTML/CSS |
| Learning curve | Low (SQL-first) | Medium (Python + Dash API) |
