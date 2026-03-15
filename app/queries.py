"""
queries.py — DuckDB query layer for Dash+Plotly POC.

All queries mirror the Evidence-POC SQL sources but run via duckdb.connect()
in Python. Data files are read with read_parquet() / read_csv() directly —
same approach as Evidence: no persistent .db file, fully in-memory.

Path convention: DATA_DIR is set from the DATA_DIR env var (default: /data).
Inside Docker the init container downloads files to /data; locally the path
is ./data (relative to repo root, passed via env).

Memory management:
  DUCKDB_MEMORY_LIMIT env var caps the DuckDB working-set per query connection
  (default: 1GB). This prevents OOM on low-memory hosts during cold scan of the
  ~500 MB Parquet file. After lru_cache warms up, _q() is no longer called —
  the limit only applies to the initial per-worker cold scan.

  DUCKDB_THREADS env var limits parallel threads per connection (default: 2).
  With gunicorn --workers 2, this caps total CPU usage at 4 threads.

  Tune both via environment variables in compose.yaml or the Docker run command.
"""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

import duckdb
import pandas as pd

# ---------------------------------------------------------------------------
# Path helpers
# ---------------------------------------------------------------------------

DATA_DIR = Path(os.environ.get("DATA_DIR", "/data"))

# Static lookup file shipped with the app code — not part of the data volume.
_APP_DIR = Path(__file__).parent
NYC_ZONE_CENTROIDS_CSV = _APP_DIR / "data" / "nyc_taxi_zone_centroids.csv"

NYC_PARQUET = DATA_DIR / "nyc_taxi" / "raw" / "yellow_tripdata_2024-01.parquet"
ENERGY_CSV = DATA_DIR / "world_energy" / "owid-energy-data.csv"
BR_GDP = DATA_DIR / "brazil_economy" / "gdp_usd.csv"
BR_GDPPC = DATA_DIR / "brazil_economy" / "gdp_per_capita.csv"
BR_INF = DATA_DIR / "brazil_economy" / "inflation.csv"
BR_UNEMP = DATA_DIR / "brazil_economy" / "unemployment.csv"
BR_FX = DATA_DIR / "brazil_economy" / "usd_brl.csv"
BR_EXP = DATA_DIR / "brazil_economy" / "exports.csv"
BR_IMP = DATA_DIR / "brazil_economy" / "imports.csv"

# DuckDB resource limits — tunable via environment variables
_DUCKDB_MEMORY_LIMIT = os.environ.get("DUCKDB_MEMORY_LIMIT", "1GB")
_DUCKDB_THREADS = int(os.environ.get("DUCKDB_THREADS") or "2")


def _q(sql: str) -> pd.DataFrame:
    """
    Execute a DuckDB SQL query (in-memory) and return a DataFrame.

    Each call opens a fresh :memory: connection with resource limits applied.
    In practice, _q() is only called once per query function per worker process
    (lru_cache handles subsequent calls); the limits guard the initial cold scan.
    """
    con = duckdb.connect(database=":memory:")
    con.execute(f"SET memory_limit='{_DUCKDB_MEMORY_LIMIT}'")
    con.execute(f"SET threads={_DUCKDB_THREADS}")
    return con.execute(sql).df()


def _p(path: Path) -> str:
    """Return a quoted POSIX path string safe to embed in SQL."""
    return f"'{path.as_posix()}'"


# ===========================================================================
# NYC Taxi
# ===========================================================================


@lru_cache(maxsize=1)
def nyc_overview_kpis() -> pd.DataFrame:
    return _q(f"""
        SELECT
            COUNT(*)                                                        AS total_trips,
            ROUND(SUM(total_amount), 2)                                    AS total_revenue,
            ROUND(AVG(total_amount), 2)                                    AS avg_fare,
            ROUND(AVG(trip_distance), 2)                                   AS avg_distance_miles,
            ROUND(AVG(DATEDIFF('minute',
                tpep_pickup_datetime, tpep_dropoff_datetime)), 1)          AS avg_duration_min,
            ROUND(AVG(tip_amount / NULLIF(fare_amount,0)) * 100, 1)       AS avg_tip_pct,
            ROUND(SUM(tip_amount), 2)                                      AS total_tips,
            COUNT(DISTINCT DATE_TRUNC('day', tpep_pickup_datetime))        AS days_in_dataset
        FROM read_parquet({_p(NYC_PARQUET)})
        WHERE tpep_pickup_datetime  >= '2024-01-01'
          AND tpep_pickup_datetime  <  '2024-02-01'
          AND tpep_dropoff_datetime >  tpep_pickup_datetime
          AND trip_distance > 0 AND fare_amount > 0 AND passenger_count > 0
    """)


@lru_cache(maxsize=1)
def nyc_daily_trips() -> pd.DataFrame:
    return _q(f"""
        SELECT
            DATE_TRUNC('day', tpep_pickup_datetime)::DATE                  AS date,
            COUNT(*)                                                        AS trips,
            ROUND(SUM(total_amount), 2)                                    AS revenue,
            ROUND(AVG(total_amount), 2)                                    AS avg_fare,
            ROUND(AVG(trip_distance), 2)                                   AS avg_distance,
            ROUND(AVG(DATEDIFF('minute',
                tpep_pickup_datetime, tpep_dropoff_datetime)), 1)          AS avg_duration_min,
            ROUND(AVG(tip_amount / NULLIF(fare_amount,0)) * 100, 1)       AS avg_tip_pct
        FROM read_parquet({_p(NYC_PARQUET)})
        WHERE tpep_pickup_datetime  >= '2024-01-01'
          AND tpep_pickup_datetime  <  '2024-02-01'
          AND tpep_dropoff_datetime >  tpep_pickup_datetime
          AND trip_distance > 0 AND fare_amount > 0 AND passenger_count > 0
        GROUP BY DATE_TRUNC('day', tpep_pickup_datetime)
        ORDER BY 1
    """)


@lru_cache(maxsize=1)
def nyc_hourly_patterns() -> pd.DataFrame:
    return _q(f"""
        SELECT
            DAYOFWEEK(tpep_pickup_datetime)                                AS day_of_week,
            DAYNAME(tpep_pickup_datetime)                                  AS day_name,
            HOUR(tpep_pickup_datetime)                                     AS hour_of_day,
            COUNT(*)                                                       AS trips,
            ROUND(AVG(total_amount), 2)                                   AS avg_fare,
            ROUND(AVG(DATEDIFF('minute',
                tpep_pickup_datetime, tpep_dropoff_datetime)), 1)         AS avg_duration_min
        FROM read_parquet({_p(NYC_PARQUET)})
        WHERE tpep_pickup_datetime  >= '2024-01-01'
          AND tpep_pickup_datetime  <  '2024-02-01'
          AND tpep_dropoff_datetime >  tpep_pickup_datetime
          AND trip_distance > 0 AND fare_amount > 0 AND passenger_count > 0
        GROUP BY 1, 2, 3
        ORDER BY 1, 3
    """)


@lru_cache(maxsize=1)
def nyc_payment_breakdown() -> pd.DataFrame:
    return _q(f"""
        SELECT
            CASE payment_type
                WHEN 1 THEN 'Credit Card' WHEN 2 THEN 'Cash'
                WHEN 3 THEN 'No Charge'  WHEN 4 THEN 'Dispute'
                WHEN 5 THEN 'Unknown'    WHEN 6 THEN 'Voided Trip'
                ELSE 'Other'
            END                                                            AS payment_type_name,
            COUNT(*)                                                       AS trips,
            ROUND(SUM(total_amount), 2)                                   AS total_revenue,
            ROUND(AVG(total_amount), 2)                                   AS avg_fare,
            ROUND(AVG(tip_amount), 2)                                     AS avg_tip,
            ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 1)           AS pct_of_trips
        FROM read_parquet({_p(NYC_PARQUET)})
        WHERE tpep_pickup_datetime  >= '2024-01-01'
          AND tpep_pickup_datetime  <  '2024-02-01'
          AND tpep_dropoff_datetime >  tpep_pickup_datetime
          AND trip_distance > 0 AND fare_amount > 0 AND passenger_count > 0
        GROUP BY payment_type
        ORDER BY trips DESC
    """)


@lru_cache(maxsize=1)
def nyc_vendor_comparison() -> pd.DataFrame:
    return _q(f"""
        SELECT
            CASE VendorID
                WHEN 1 THEN 'Creative Mobile Technologies'
                WHEN 2 THEN 'VeriFone Inc.'
                ELSE 'Unknown'
            END                                                            AS vendor_name,
            COUNT(*)                                                       AS trips,
            ROUND(AVG(total_amount), 2)                                   AS avg_fare,
            ROUND(AVG(trip_distance), 2)                                  AS avg_distance,
            ROUND(AVG(DATEDIFF('minute',
                tpep_pickup_datetime, tpep_dropoff_datetime)), 1)         AS avg_duration_min,
            ROUND(AVG(tip_amount / NULLIF(fare_amount,0)) * 100, 1)      AS avg_tip_pct,
            ROUND(SUM(total_amount), 2)                                   AS total_revenue
        FROM read_parquet({_p(NYC_PARQUET)})
        WHERE tpep_pickup_datetime  >= '2024-01-01'
          AND tpep_pickup_datetime  <  '2024-02-01'
          AND tpep_dropoff_datetime >  tpep_pickup_datetime
          AND trip_distance > 0 AND fare_amount > 0 AND passenger_count > 0
        GROUP BY VendorID
        ORDER BY trips DESC
    """)


@lru_cache(maxsize=1)
def nyc_distance_distribution() -> pd.DataFrame:
    return _q(f"""
        SELECT
            ROUND(FLOOR(trip_distance / 0.5) * 0.5, 1) AS distance_bucket_miles,
            COUNT(*)                                     AS trips,
            ROUND(AVG(total_amount), 2)                 AS avg_fare,
            ROUND(AVG(tip_amount), 2)                   AS avg_tip
        FROM read_parquet({_p(NYC_PARQUET)})
        WHERE tpep_pickup_datetime  >= '2024-01-01'
          AND tpep_pickup_datetime  <  '2024-02-01'
          AND tpep_dropoff_datetime >  tpep_pickup_datetime
          AND trip_distance > 0 AND trip_distance <= 20
          AND fare_amount > 0 AND passenger_count > 0
        GROUP BY distance_bucket_miles
        ORDER BY distance_bucket_miles
    """)


@lru_cache(maxsize=1)
def nyc_fare_vs_distance() -> pd.DataFrame:
    return _q(f"""
        SELECT
            ROUND(trip_distance, 1)                                        AS trip_distance,
            ROUND(fare_amount, 2)                                          AS fare_amount,
            ROUND(tip_amount, 2)                                           AS tip_amount,
            ROUND(total_amount, 2)                                         AS total_amount,
            CASE payment_type
                WHEN 1 THEN 'Credit Card' WHEN 2 THEN 'Cash'
                ELSE 'Other'
            END                                                            AS payment_type_name,
            DATEDIFF('minute',
                tpep_pickup_datetime, tpep_dropoff_datetime)               AS trip_duration_min,
            HOUR(tpep_pickup_datetime)                                     AS hour_of_day
        FROM read_parquet({_p(NYC_PARQUET)})
        WHERE tpep_pickup_datetime  >= '2024-01-01'
          AND tpep_pickup_datetime  <  '2024-02-01'
          AND tpep_dropoff_datetime >  tpep_pickup_datetime
          AND trip_distance BETWEEN 0.1 AND 30
          AND fare_amount   BETWEEN 1   AND 150
          AND passenger_count > 0
        USING SAMPLE 5000 ROWS
    """)


# ===========================================================================
# World Energy
# ===========================================================================


@lru_cache(maxsize=1)
def energy_global_trends() -> pd.DataFrame:
    return _q(f"""
        SELECT
            year,
            COALESCE(coal_share_elec, 0)       AS coal_pct,
            COALESCE(gas_share_elec, 0)        AS gas_pct,
            COALESCE(nuclear_share_elec, 0)    AS nuclear_pct,
            COALESCE(hydro_share_elec, 0)      AS hydro_pct,
            COALESCE(solar_share_elec, 0)      AS solar_pct,
            COALESCE(wind_share_elec, 0)       AS wind_pct,
            COALESCE(renewables_share_elec, 0) AS renewables_pct,
            COALESCE(fossil_share_elec, 0)     AS fossil_pct,
            COALESCE(low_carbon_share_elec, 0) AS low_carbon_pct,
            COALESCE(electricity_generation, 0) AS electricity_twh,
            COALESCE(solar_electricity, 0)     AS solar_twh,
            COALESCE(wind_electricity, 0)      AS wind_twh,
            COALESCE(hydro_electricity, 0)     AS hydro_twh,
            COALESCE(nuclear_electricity, 0)   AS nuclear_twh,
            COALESCE(coal_electricity, 0)      AS coal_twh
        FROM read_csv({_p(ENERGY_CSV)}, auto_detect=true, nullstr='')
        WHERE country = 'World'
          AND year >= 1990
        ORDER BY year
    """)


@lru_cache(maxsize=1)
def energy_top_renewable_countries() -> pd.DataFrame:
    return _q(f"""
        SELECT
            country,
            year,
            ROUND(renewables_share_elec, 1)  AS renewables_pct,
            ROUND(solar_share_elec, 1)       AS solar_pct,
            ROUND(wind_share_elec, 1)        AS wind_pct,
            ROUND(hydro_share_elec, 1)       AS hydro_pct,
            ROUND(electricity_generation, 0) AS electricity_twh
        FROM read_csv({_p(ENERGY_CSV)}, auto_detect=true, nullstr='')
        WHERE iso_code IS NOT NULL
          AND iso_code NOT LIKE 'OWID_%'
          AND length(iso_code) = 3
          AND year = (
              SELECT MAX(year)
              FROM read_csv({_p(ENERGY_CSV)}, auto_detect=true, nullstr='')
              WHERE iso_code IS NOT NULL AND iso_code NOT LIKE 'OWID_%'
                AND renewables_share_elec IS NOT NULL
          )
          AND electricity_generation >= 10
          AND renewables_share_elec IS NOT NULL
        ORDER BY renewables_pct DESC
        LIMIT 20
    """)


@lru_cache(maxsize=1)
def energy_country_mix() -> pd.DataFrame:
    return _q(f"""
        SELECT
            country,
            year,
            COALESCE(coal_share_elec, 0)             AS coal_pct,
            COALESCE(gas_share_elec, 0)              AS gas_pct,
            COALESCE(oil_share_elec, 0)              AS oil_pct,
            COALESCE(nuclear_share_elec, 0)          AS nuclear_pct,
            COALESCE(hydro_share_elec, 0)            AS hydro_pct,
            COALESCE(solar_share_elec, 0)            AS solar_pct,
            COALESCE(wind_share_elec, 0)             AS wind_pct,
            COALESCE(other_renewables_share_elec, 0) AS other_renewables_pct,
            COALESCE(renewables_share_elec, 0)       AS total_renewables_pct,
            COALESCE(fossil_share_elec, 0)           AS total_fossil_pct,
            COALESCE(low_carbon_share_elec, 0)       AS low_carbon_pct,
            COALESCE(electricity_generation, 0)      AS electricity_twh,
            COALESCE(population, 0)                  AS population
        FROM read_csv({_p(ENERGY_CSV)}, auto_detect=true, nullstr='')
        WHERE iso_code IS NOT NULL
          AND iso_code NOT LIKE 'OWID_%'
          AND length(iso_code) = 3
          AND year = (
              SELECT MAX(year)
              FROM read_csv({_p(ENERGY_CSV)}, auto_detect=true, nullstr='')
              WHERE iso_code IS NOT NULL AND iso_code NOT LIKE 'OWID_%'
                AND electricity_generation IS NOT NULL
          )
          AND electricity_generation > 0
        ORDER BY electricity_twh DESC
    """)


# ===========================================================================
# Brazil Economy
# ===========================================================================


@lru_cache(maxsize=1)
def brazil_macro() -> pd.DataFrame:
    return _q(f"""
        SELECT
            g.year::INT                                  AS year,
            ROUND(g.value / 1e9, 1)                     AS gdp_billion_usd,
            ROUND(gp.value, 0)                          AS gdp_per_capita_usd,
            ROUND(i.value, 2)                           AS inflation_pct,
            ROUND(u.value, 2)                           AS unemployment_pct,
            ROUND(f.value, 4)                           AS usd_brl_rate,
            ROUND(ex.value / 1e9, 1)                    AS exports_billion_usd,
            ROUND(im.value / 1e9, 1)                    AS imports_billion_usd,
            ROUND((ex.value - im.value) / 1e9, 1)       AS trade_balance_billion_usd
        FROM read_csv({_p(BR_GDP)}, auto_detect=true)         g
        LEFT JOIN read_csv({_p(BR_GDPPC)}, auto_detect=true)  gp ON g.year = gp.year
        LEFT JOIN read_csv({_p(BR_INF)},   auto_detect=true)  i  ON g.year = i.year
        LEFT JOIN read_csv({_p(BR_UNEMP)}, auto_detect=true)  u  ON g.year = u.year
        LEFT JOIN read_csv({_p(BR_FX)},    auto_detect=true)  f  ON g.year = f.year
        LEFT JOIN read_csv({_p(BR_EXP)},   auto_detect=true)  ex ON g.year = ex.year
        LEFT JOIN read_csv({_p(BR_IMP)},   auto_detect=true)  im ON g.year = im.year
        ORDER BY year
    """)


@lru_cache(maxsize=1)
def nyc_zone_pickup_map() -> pd.DataFrame:
    """
    Pickup trip count + avg fare per taxi zone, joined with centroid coordinates.

    Returns columns: location_id, zone, borough, lat, lon, trips, avg_fare, avg_tip_pct.
    The centroid CSV is bundled with the app (app/data/nyc_taxi_zone_centroids.csv);
    the Parquet is in DATA_DIR.
    """
    return _q(f"""
        WITH pickups AS (
            SELECT
                PULocationID                                                AS location_id,
                COUNT(*)                                                    AS trips,
                ROUND(AVG(total_amount), 2)                                AS avg_fare,
                ROUND(AVG(tip_amount / NULLIF(fare_amount, 0)) * 100, 1)  AS avg_tip_pct
            FROM read_parquet({_p(NYC_PARQUET)})
            WHERE tpep_pickup_datetime >= '2024-01-01'
              AND tpep_pickup_datetime <  '2024-02-01'
              AND tpep_dropoff_datetime > tpep_pickup_datetime
              AND trip_distance > 0 AND fare_amount > 0 AND passenger_count > 0
            GROUP BY PULocationID
        ),
        zones AS (
            SELECT
                location_id::INT  AS location_id,
                zone,
                borough,
                lat::DOUBLE       AS lat,
                lon::DOUBLE       AS lon
            FROM read_csv({_p(NYC_ZONE_CENTROIDS_CSV)}, auto_detect=true)
        )
        SELECT
            z.location_id,
            z.zone,
            z.borough,
            z.lat,
            z.lon,
            COALESCE(p.trips, 0)        AS trips,
            COALESCE(p.avg_fare, 0)     AS avg_fare,
            COALESCE(p.avg_tip_pct, 0)  AS avg_tip_pct
        FROM zones z
        LEFT JOIN pickups p ON z.location_id = p.location_id
        ORDER BY trips DESC
    """)


@lru_cache(maxsize=1)
def nyc_zone_dropoff_map() -> pd.DataFrame:
    """
    Dropoff trip count + avg fare per taxi zone, joined with centroid coordinates.

    Returns same schema as nyc_zone_pickup_map but keyed on DOLocationID.
    """
    return _q(f"""
        WITH dropoffs AS (
            SELECT
                DOLocationID                                                AS location_id,
                COUNT(*)                                                    AS trips,
                ROUND(AVG(total_amount), 2)                                AS avg_fare,
                ROUND(AVG(tip_amount / NULLIF(fare_amount, 0)) * 100, 1)  AS avg_tip_pct
            FROM read_parquet({_p(NYC_PARQUET)})
            WHERE tpep_pickup_datetime >= '2024-01-01'
              AND tpep_pickup_datetime <  '2024-02-01'
              AND tpep_dropoff_datetime > tpep_pickup_datetime
              AND trip_distance > 0 AND fare_amount > 0 AND passenger_count > 0
            GROUP BY DOLocationID
        ),
        zones AS (
            SELECT
                location_id::INT  AS location_id,
                zone,
                borough,
                lat::DOUBLE       AS lat,
                lon::DOUBLE       AS lon
            FROM read_csv({_p(NYC_ZONE_CENTROIDS_CSV)}, auto_detect=true)
        )
        SELECT
            z.location_id,
            z.zone,
            z.borough,
            z.lat,
            z.lon,
            COALESCE(d.trips, 0)        AS trips,
            COALESCE(d.avg_fare, 0)     AS avg_fare,
            COALESCE(d.avg_tip_pct, 0)  AS avg_tip_pct
        FROM zones z
        LEFT JOIN dropoffs d ON z.location_id = d.location_id
        ORDER BY trips DESC
    """)


@lru_cache(maxsize=1)
def nyc_top_od_pairs() -> pd.DataFrame:
    """
    Top 30 origin–destination zone pairs by trip volume.

    Returns columns: pu_zone, do_zone, pu_borough, do_borough, trips, avg_fare, avg_distance.
    Excludes same-zone (pu == do) trips.
    """
    return _q(f"""
        WITH od AS (
            SELECT
                PULocationID  AS pu_id,
                DOLocationID  AS do_id,
                COUNT(*)                                AS trips,
                ROUND(AVG(total_amount), 2)             AS avg_fare,
                ROUND(AVG(trip_distance), 2)            AS avg_distance
            FROM read_parquet({_p(NYC_PARQUET)})
            WHERE tpep_pickup_datetime >= '2024-01-01'
              AND tpep_pickup_datetime <  '2024-02-01'
              AND tpep_dropoff_datetime > tpep_pickup_datetime
              AND trip_distance > 0 AND fare_amount > 0 AND passenger_count > 0
              AND PULocationID != DOLocationID
            GROUP BY PULocationID, DOLocationID
        ),
        zones AS (
            SELECT location_id::INT AS location_id, zone, borough
            FROM read_csv({_p(NYC_ZONE_CENTROIDS_CSV)}, auto_detect=true)
        )
        SELECT
            pu.zone     AS pu_zone,
            do.zone     AS do_zone,
            pu.borough  AS pu_borough,
            do.borough  AS do_borough,
            od.trips,
            od.avg_fare,
            od.avg_distance
        FROM od
        JOIN zones pu ON od.pu_id = pu.location_id
        JOIN zones do ON od.do_id = do.location_id
        ORDER BY trips DESC
        LIMIT 30
    """)
