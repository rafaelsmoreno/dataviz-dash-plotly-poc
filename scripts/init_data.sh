#!/bin/sh
# =============================================================================
# init_data.sh — Download all raw data files for Dash+Plotly POC
# Mirrors the Evidence-POC init_db.sh logic; no DuckDB binary needed here —
# files are downloaded as-is and DuckDB reads them at query time in Python.
# =============================================================================

set -e

download() {
    DEST="$1"; URL="$2"; LABEL="$3"
    mkdir -p "$(dirname "$DEST")"
    if [ -f "$DEST" ]; then
        echo "[init] $LABEL already exists ($(du -h "$DEST" | cut -f1)) — skipping."
    else
        echo "[init] Downloading $LABEL ..."
        curl -L --progress-bar -o "$DEST" "$URL"
        echo "[init] Done: $DEST ($(du -h "$DEST" | cut -f1))"
    fi
}

# ── NYC Yellow Taxi Jan 2024 ──────────────────────────────────────────────────
download \
    "/data/nyc_taxi/raw/yellow_tripdata_2024-01.parquet" \
    "https://d37ci6vzurychx.cloudfront.net/trip-data/yellow_tripdata_2024-01.parquet" \
    "NYC Yellow Taxi Jan 2024"

# ── Our World in Data — Energy ────────────────────────────────────────────────
download \
    "/data/world_energy/owid-energy-data.csv" \
    "https://raw.githubusercontent.com/owid/energy-data/master/owid-energy-data.csv" \
    "OWID Energy CSV"

# ── Brazil Economy — World Bank ───────────────────────────────────────────────
BASE_URL="https://api.worldbank.org/v2/country/BR/indicator"

fetch_wb() {
    INDICATOR="$1"; DEST="$2"; LABEL="$3"
    if [ -f "$DEST" ]; then
        echo "[init] $LABEL already exists — skipping."
        return
    fi
    echo "[init] Fetching $LABEL from World Bank..."
    curl -s "${BASE_URL}/${INDICATOR}?format=json&per_page=100&mrv=40" \
        | python3 -c "
import json, sys, csv
data = json.load(sys.stdin)
rows = data[1] if len(data) > 1 and data[1] else []
writer = csv.writer(sys.stdout)
writer.writerow(['year','value'])
for r in rows:
    if r.get('value') is not None:
        writer.writerow([r['date'], r['value']])
" > "$DEST"
    echo "[init] Saved $DEST"
}

fetch_wb "NY.GDP.MKTP.CD"      "/data/brazil_economy/gdp_usd.csv"        "Brazil GDP (USD)"
fetch_wb "NY.GDP.PCAP.CD"      "/data/brazil_economy/gdp_per_capita.csv" "Brazil GDP per capita"
fetch_wb "FP.CPI.TOTL.ZG"      "/data/brazil_economy/inflation.csv"      "Brazil Inflation"
fetch_wb "SL.UEM.TOTL.ZS"      "/data/brazil_economy/unemployment.csv"   "Brazil Unemployment"
fetch_wb "PA.NUS.FCRF"         "/data/brazil_economy/usd_brl.csv"        "USD/BRL rate"
fetch_wb "NE.EXP.GNFS.CD"      "/data/brazil_economy/exports.csv"        "Brazil Exports"
fetch_wb "NE.IMP.GNFS.CD"      "/data/brazil_economy/imports.csv"        "Brazil Imports"

echo "[init] All data files ready."
