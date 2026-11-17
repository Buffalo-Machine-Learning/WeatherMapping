from datetime import datetime

import pyodbc
from fastapi import APIRouter, Depends, HTTPException, Query

from database import get_db


router = APIRouter(
    prefix="/api/v1/forecast",
    tags=["forecast"],
)


def get_latest_forecast_run(cursor):
    cursor.execute(
        """
        SELECT
            id,
            weather_model_id,
            initialized_at
        FROM forecast_run
        ORDER BY initialized_at DESC
        LIMIT 1
        """
    )

    row = cursor.fetchone()

    if row is None:
        raise HTTPException(
            status_code=404,
            detail="No forecast runs found",
        )

    return row


def resolve_valid_at(
    cursor,
    forecast_run_id: int,
    valid_at: datetime | None,
):
    # If the caller supplied a time, make sure we actually
    # have that timestamp in this forecast run.
    if valid_at is not None:
        cursor.execute(
            """
            SELECT valid_at
            FROM forecast
            WHERE forecast_run_id = ?
              AND valid_at = ?
            LIMIT 1
            """,
            forecast_run_id,
            valid_at,
        )

        row = cursor.fetchone()

        if row is None:
            raise HTTPException(
                status_code=404,
                detail="Requested forecast time not found",
            )

        return row[0]

    # Otherwise use the next available forecast time.
    cursor.execute(
        """
        SELECT MIN(valid_at)
        FROM forecast
        WHERE forecast_run_id = ?
          AND valid_at >= NOW()
        """,
        forecast_run_id,
    )

    row = cursor.fetchone()

    if row and row[0]:
        return row[0]

    # If the entire forecast is now in the past,
    # just return the latest timestamp available.
    cursor.execute(
        """
        SELECT MAX(valid_at)
        FROM forecast
        WHERE forecast_run_id = ?
        """,
        forecast_run_id,
    )

    row = cursor.fetchone()

    if row is None or row[0] is None:
        raise HTTPException(
            status_code=404,
            detail="No forecast data found",
        )

    return row[0]


# ============================================================
# AVAILABLE FORECAST TIMES
# ============================================================

@router.get("/times")
def get_forecast_times(
    connection: pyodbc.Connection = Depends(get_db),
):
    cursor = connection.cursor()

    run = get_latest_forecast_run(cursor)

    forecast_run_id = run[0]

    cursor.execute(
        """
        SELECT DISTINCT valid_at
        FROM forecast
        WHERE forecast_run_id = ?
        ORDER BY valid_at
        """,
        forecast_run_id,
    )

    times = [
        row[0]
        for row in cursor.fetchall()
    ]

    return {
        "forecast_run_id": forecast_run_id,
        "initialized_at": run[2],
        "times": times,
    }


# ============================================================
# FORECAST FOR ONE LOCATION
# ============================================================

@router.get("/point")
def get_point_forecast(
    lat: float = Query(..., ge=-90, le=90),
    lon: float = Query(..., ge=-180, le=180),
    valid_at: datetime | None = None,
    connection: pyodbc.Connection = Depends(get_db),
):
    cursor = connection.cursor()

    run = get_latest_forecast_run(cursor)

    forecast_run_id = run[0]

    forecast_time = resolve_valid_at(
        cursor,
        forecast_run_id,
        valid_at,
    )

    cursor.execute(
        """
        SELECT
            gp.id,
            gp.latitude,
            gp.longitude,
            gp.elevation_m,

            f.id,
            f.valid_at,
            f.lead_hours,
            f.temperature_c,
            f.dew_point_c,
            f.relative_humidity,
            f.precipitation_mm,
            f.pressure_hpa,
            f.wind_speed_ms,
            f.wind_direction_deg,
            f.cloud_cover,

            ST_Distance(
                gp.location::geography,
                ST_SetSRID(
                    ST_MakePoint(?, ?),
                    4326
                )::geography
            ) AS distance_m

        FROM forecast f

        JOIN grid_point gp
            ON gp.id = f.grid_point_id

        WHERE f.forecast_run_id = ?
          AND f.valid_at = ?

        ORDER BY
            gp.location <-> ST_SetSRID(
                ST_MakePoint(?, ?),
                4326
            )

        LIMIT 1
        """,
        lon,
        lat,
        forecast_run_id,
        forecast_time,
        lon,
        lat,
    )

    row = cursor.fetchone()

    if row is None:
        raise HTTPException(
            status_code=404,
            detail="No forecast found",
        )

    return {
        "grid_point": {
            "id": row[0],
            "latitude": row[1],
            "longitude": row[2],
            "elevation_m": row[3],
            "distance_m": row[15],
        },
        "forecast": {
            "id": row[4],
            "valid_at": row[5],
            "lead_hours": row[6],
            "temperature_c": row[7],
            "dew_point_c": row[8],
            "relative_humidity": row[9],
            "precipitation_mm": row[10],
            "pressure_hpa": row[11],
            "wind_speed_ms": row[12],
            "wind_direction_deg": row[13],
            "cloud_cover": row[14],
        },
    }


# ============================================================
# FORECAST DATA FOR THE MAP
# ============================================================

@router.get("/map")
def get_map_forecast(
    min_lat: float = Query(..., ge=-90, le=90),
    max_lat: float = Query(..., ge=-90, le=90),
    min_lon: float = Query(..., ge=-180, le=180),
    max_lon: float = Query(..., ge=-180, le=180),
    valid_at: datetime | None = None,
    limit: int = Query(5000, ge=1, le=10000),
    connection: pyodbc.Connection = Depends(get_db),
):
    if min_lat >= max_lat:
        raise HTTPException(
            status_code=400,
            detail="min_lat must be less than max_lat",
        )

    if min_lon >= max_lon:
        raise HTTPException(
            status_code=400,
            detail="min_lon must be less than max_lon",
        )

    cursor = connection.cursor()

    run = get_latest_forecast_run(cursor)

    forecast_run_id = run[0]

    forecast_time = resolve_valid_at(
        cursor,
        forecast_run_id,
        valid_at,
    )

    cursor.execute(
        """
        SELECT
            gp.id,
            gp.latitude,
            gp.longitude,

            f.id,
            f.valid_at,
            f.lead_hours,

            f.temperature_c,
            f.dew_point_c,
            f.relative_humidity,
            f.precipitation_mm,
            f.pressure_hpa,
            f.wind_speed_ms,
            f.wind_direction_deg,
            f.cloud_cover

        FROM forecast f

        JOIN grid_point gp
            ON gp.id = f.grid_point_id

        WHERE f.forecast_run_id = ?
          AND f.valid_at = ?

          AND gp.location && ST_MakeEnvelope(
              ?,
              ?,
              ?,
              ?,
              4326
          )

        ORDER BY gp.id

        LIMIT ?
        """,
        forecast_run_id,
        forecast_time,
        min_lon,
        min_lat,
        max_lon,
        max_lat,
        limit,
    )

    rows = cursor.fetchall()

    features = []

    for row in rows:
        features.append(
            {
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [
                        row[2],
                        row[1],
                    ],
                },
                "properties": {
                    "grid_point_id": row[0],
                    "forecast_id": row[3],
                    "valid_at": row[4],
                    "lead_hours": row[5],
                    "temperature_c": row[6],
                    "dew_point_c": row[7],
                    "relative_humidity": row[8],
                    "precipitation_mm": row[9],
                    "pressure_hpa": row[10],
                    "wind_speed_ms": row[11],
                    "wind_direction_deg": row[12],
                    "cloud_cover": row[13],
                },
            }
        )

    return {
        "type": "FeatureCollection",
        "forecast_run_id": forecast_run_id,
        "valid_at": forecast_time,
        "features": features,
    }