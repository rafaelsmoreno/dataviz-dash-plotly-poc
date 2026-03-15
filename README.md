# Dash + Plotly POC

A proof-of-concept data visualization project built with [Dash](https://dash.plotly.com) and [Plotly](https://plotly.com/python/),
evaluating Dash as a candidate for a Python-native, version-controlled analytics platform.

Six fully interactive dashboards, built entirely in Python. No drag-and-drop. No GUI.
Everything is code, everything is in git.

---

## Dashboards

| Page | Charts | Source | Interactive filter |
|---|---|---|---|
| **NYC Yellow Taxi** | KPIs, daily trend, heatmap, payment, vendor, distribution, scatter | TLC Jan 2024 Parquet (2.7M rows) | Payment type checklist |
| **NYC Zone Map** | Pickup volume scatter map + ag-grid table | TLC Parquet + zone centroids | Borough checklist |
| **NYC Flows** | Dropoff zone scatter map + top-30 O/D pairs chart | TLC Parquet + zone centroids | Borough checklist |
| **World Energy Mix** | Global mix share, TWh by source, top renewable countries, country mix + ag-grid | Our World in Data CSV | Year range slider |
| **Brazil Economy** | GDP, inflation, FX, trade balance (2000–2025) | World Bank Open Data API | Year range slider |

### NYC Yellow Taxi
- KPI overview: total trips, revenue, avg fare, avg distance, avg duration, avg tip %
- Daily trip volume + revenue trend for January 2024
- Hourly heatmap (trips by hour × day of week)
- Payment type donut chart (filtered by payment type checklist)
- Vendor comparison (grouped bar)
- Trip distance distribution (histogram, filtered by payment type)
- Fare vs. distance scatter plot (5 000-row sample, filtered by payment type)

### NYC Zone Map
- OpenStreetMap scatter map — one bubble per taxi zone, sized by pickup volume, coloured by avg fare
- Borough multi-select filter — auto-zooms map and filters the table
- ag-grid table — 263-zone pickup summary with sort, filter, pagination, and column resize

### NYC Flows
- Dropoff zone scatter map — same zone centroid layer, coloured by avg fare (Plasma palette)
- Top-30 origin → destination pairs — horizontal bar chart, coloured by avg fare
- Borough checklist filter — auto-zooms the dropoff map

### World Energy Mix
- Global electricity mix share over time — stacked area (1990–present, year range slider)
- Absolute generation by source in TWh — line chart (year range slider)
- Top 20 countries by renewable share (latest year)
- Energy mix breakdown for top-10 countries by total generation

### Brazil Economy
- GDP (total and per capita), inflation, unemployment, USD/BRL rate
- Exports, imports, trade balance — all from World Bank API
- Full time-series from 2000 to 2025 (year range slider across all four charts)

---

## Stack

```
Dash + Plotly      →  Python multi-page app served by gunicorn
dash-ag-grid       →  Client-side sortable/filterable grid (NYC Zone Map, World Energy)
DuckDB             →  In-memory query engine (no persistent .db file)
Docker Compose     →  Two-service stack: data-init + dash app server
```

All raw data is downloaded at container start by `scripts/init_data.sh`. Large raw data files (Parquet, OWID CSV, World Bank CSVs) are not committed to git. The NYC taxi zone centroid lookup (`app/data/nyc_taxi_zone_centroids.csv`, 15 KB) is committed alongside the app code.

---

## How to Run

```bash
docker compose up --build
```

Open [http://localhost:8050](http://localhost:8050).

The `data-init` service downloads all raw data files on first run (skips if already present).
The `dash` service waits for it to finish, then starts gunicorn.

**First run** takes ~3–5 min (downloads ~500 MB of raw data — mainly the Parquet file).
**Subsequent runs** start in ~10 sec (data already present in the named Docker volume).

### Local development (without Docker)

```bash
# 1. Create and activate a virtual environment
python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Download data (first time only — same script used by Docker)
bash scripts/init_data.sh

# 4. Run the dev server
DATA_DIR=./data python app/app.py
```

Open [http://localhost:8050](http://localhost:8050). The server reloads automatically on file changes (`debug=True`).

> **Note:** `DATA_DIR=./data` tells `queries.py` to look for data files in `./data/` instead
> of the Docker volume path `/data`. The `init_data.sh` script writes files there automatically.

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
  data/
    nyc_taxi_zone_centroids.csv # 263 NYC taxi zone centroids (WGS84) — committed to git
  pages/
    home.py                     # Landing page — links to all dashboards
    nyc_taxi.py                 # 7 charts: KPIs, daily, heatmap, payment, vendor, dist, scatter
    nyc_zone_map.py             # Scatter map + ag-grid table — pickup volume by zone
    nyc_flows.py                # Dropoff scatter map + top-30 O/D pairs
    world_energy.py             # 4 charts + ag-grid: stacked area, TWh lines, top-20, country mix
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

**DuckDB resource limits** — two env vars cap DuckDB's working-set during the initial cold scan:

| Variable | Default | Effect |
|---|---|---|
| `DUCKDB_MEMORY_LIMIT` | `1GB` | Max working memory per connection; prevents OOM on low-memory hosts |
| `DUCKDB_THREADS` | `2` | Parallel threads per connection; with `--workers 2`, total = 4 threads |

Both are set in `compose.yaml` and can be overridden at `docker compose up` or in a `.env` file.
After `lru_cache` warms up (first request per worker), DuckDB is no longer called — the limits
only affect the cold scan.

**Smoke tests** — `tests/test_smoke.py` verifies the Dash app imports cleanly, the gunicorn
`server` object is a Flask app, and all 6 page paths are registered — without requiring any
data files. Run with `make test`.

