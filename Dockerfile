# =============================================================================
# Dockerfile — Dash + Plotly POC
# =============================================================================
# Multi-stage is not needed here: the image is a pure Python runtime.
# Base: python:3.12-slim (small footprint, no GPU, no build tools needed).
# =============================================================================

FROM python:3.12-slim

LABEL maintainer="rafaelsmoreno"
LABEL description="Dash + Plotly POC — DuckDB-powered multi-dataset dashboard"

# System deps: curl is needed by the init script; no build tools required
# because duckdb ships a pre-built wheel.
RUN apt-get update \
    && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies first (layer-cached until requirements.txt changes)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source
COPY app/ ./app/

# Data directory is mounted at runtime (compose volume); create the mount point
RUN mkdir -p /data/nyc_taxi/raw /data/world_energy /data/brazil_economy

# Expose Dash default port
EXPOSE 8050

# Run with gunicorn in production mode.
# WORKDIR is /app; app.py lives in /app/app/; server object is app:server.
WORKDIR /app/app
CMD ["gunicorn", "--bind", "0.0.0.0:8050", "--workers", "2", "--timeout", "120", "app:server"]
