@.claude/NEXT_SESSION.md

# dataviz-dash-plotly-poc — Agent Instructions

## Start Here

Read `.claude/session-state.md` for current state.
If `KICKSTART.md` exists at repo root, read it first.

Universal engineering rules live in `~/projects/CLAUDE.md` — not repeated here.

---

## What This Repo Is

Proof-of-concept data visualization app — Dash + Plotly + DuckDB + Parquet/CSV,
served via Docker Compose. Six fully interactive dashboards. **Project is complete.**

## Stack

- **Python:** Dash, Plotly ≥5.18 (`px.scatter_map`, not `px.scatter_mapbox`), DuckDB
- **Data:** NYC Yellow Taxi (TLC Jan 2024 Parquet, 2.7M rows), World Energy (OWID CSV), Brazil Economy (World Bank API)
- **UI:** ag-grid (`ag-theme-alpine-dark` — dark mode is default; light mode is toggle-to state)
- **Infra:** Docker Compose (`compose.yaml`), `data-init` service installs curl at runtime (not in base image)
- **Tests:** pytest (`pytest.ini` at root)

## Key Technical Facts

- `python:3.12-slim` has no curl/wget — `data-init` installs curl at runtime via `apt-get`
- NYC taxi zone shapefiles are EPSG:2263 (NY State Plane feet) — reproject to WGS84 via pyproj before use
- Port registered in `~/projects/ports.yml`; run `make validate-ports` before changing

## Dev workflow

```bash
docker compose up        # start all services
make test                # run tests
```

## Git Notes

- SSH not configured — use HTTPS for all git operations
- Pre-commit hook blocks direct commits to `main`; always use a feature branch
- After `gh pr merge --squash`: run `git fetch --prune && git reset --hard origin/main`
- No Evidence-POC references in any user-facing file (README, home page)
