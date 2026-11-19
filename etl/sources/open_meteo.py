from datetime import datetime, timezone
from pathlib import Path

import pyodbc
import requests
import yaml


OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"

MODEL_NAME = "Open-Meteo Best Match"
MODEL_SOURCE = "Open-Meteo"

PROJECT_ROOT = Path(__file__).resolve().parents[0]
CONFIG_PATH = PROJECT_ROOT / "config.yaml"


# ============================================================
# DATABASE
# ============================================================

def load_config() -> dict:
    with open(CONFIG_PATH, "r") as file:
        return yaml.safe_load(file)


def get_connection():
    config = load_config()
    db = config["database"]

    connection_string = (
        f"DRIVER={{{db['driver']}}};"
        f"SERVER={db['host']};"
        f"PORT={db['port']};"
        f"DATABASE={db['database']};"
        f"UID={db['user']};"
        f"PWD={db['password']};"
    )

    return pyodbc.connect(connection_string)


# ============================================================
# OPEN-METEO
# ============================================================

def get_forecast(latitude: float, longitude: float) -> dict:
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "hourly": [
            "temperature_2m",
            "dew_point_2m",
            "relative_humidity_2m",
            "precipitation",
            "pressure_msl",
            "wind_speed_10m",
            "wind_direction_10m",
            "cloud_cover",
        ],
        "wind_speed_unit": "ms",
        "timezone": "UTC",
        "forecast_days": 2,
    }

    response = requests.get(
        OPEN_METEO_URL,
        params=params,
        timeout=30,
    )

    response.raise_for_status()

    return response.json()


def parse_forecast(data: dict) -> list[dict]:
    hourly = data["hourly"]

    records = []

    for i, valid_at in enumerate(hourly["time"]):
        record = {
            "valid_at": valid_at,
            "temperature_c": hourly["temperature_2m"][i],
            "dew_point_c": hourly["dew_point_2m"][i],
            "relative_humidity": hourly["relative_humidity_2m"][i],
            "precipitation_mm": hourly["precipitation"][i],
            "pressure_hpa": hourly["pressure_msl"][i],
            "wind_speed_ms": hourly["wind_speed_10m"][i],
            "wind_direction_deg": hourly["wind_direction_10m"][i],
            "cloud_cover": hourly["cloud_cover"][i],
        }

        records.append(record)

    return records


# ============================================================
# WEATHER MODEL
# ============================================================

def get_or_create_weather_model(cursor) -> int:
    cursor.execute(
        """
        SELECT id
        FROM weather_model
        WHERE name = ?
          AND source = ?
        LIMIT 1
        """,
        MODEL_NAME,
        MODEL_SOURCE,
    )

    row = cursor.fetchone()

    if row:
        return row[0]

    cursor.execute(
        """
        INSERT INTO weather_model (
            name,
            source,
            description
        )
        VALUES (?, ?, ?)
        RETURNING id
        """,
        MODEL_NAME,
        MODEL_SOURCE,
        "Open-Meteo automatically selected best-match forecast model",
    )

    return cursor.fetchone()[0]


# ============================================================
# GRID POINT
# ============================================================

def get_or_create_grid_point(
    cursor,
    latitude: float,
    longitude: float,
    elevation_m: float | None,
) -> int:

    cursor.execute(
        """
        SELECT id
        FROM grid_point
        WHERE latitude = ?
          AND longitude = ?
        LIMIT 1
        """,
        latitude,
        longitude,
    )

    row = cursor.fetchone()

    if row:
        return row[0]

    cursor.execute(
        """
        INSERT INTO grid_point (
            latitude,
            longitude,
            elevation_m,
            location
        )
        VALUES (
            ?,
            ?,
            ?,
            ST_SetSRID(ST_MakePoint(?, ?), 4326)
        )
        RETURNING id
        """,
        latitude,
        longitude,
        elevation_m,

        # PostGIS uses longitude first
        longitude,
        latitude,
    )

    return cursor.fetchone()[0]


# ============================================================
# FORECAST RUN
# ============================================================

def create_forecast_run(
    cursor,
    weather_model_id: int,
    initialized_at: datetime,
) -> int:

    cursor.execute(
        """
        INSERT INTO forecast_run (
            weather_model_id,
            initialized_at
        )
        VALUES (?, ?)
        RETURNING id
        """,
        weather_model_id,
        initialized_at,
    )

    return cursor.fetchone()[0]


# ============================================================
# FORECAST DATA
# ============================================================

def insert_forecasts(
    cursor,
    forecast_run_id: int,
    grid_point_id: int,
    forecasts: list[dict],
    initialized_at: datetime,
) -> None:

    for forecast in forecasts:

        valid_at = datetime.fromisoformat(
            forecast["valid_at"]
        ).replace(tzinfo=timezone.utc)

        lead_hours = max(
            0,
            round(
                (valid_at - initialized_at).total_seconds()
                / 3600
            ),
        )

        cursor.execute(
            """
            INSERT INTO forecast (
                forecast_run_id,
                grid_point_id,
                valid_at,
                lead_hours,
                temperature_c,
                dew_point_c,
                relative_humidity,
                precipitation_mm,
                pressure_hpa,
                wind_speed_ms,
                wind_direction_deg,
                cloud_cover
            )
            VALUES (
                ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
            )
            """,
            forecast_run_id,
            grid_point_id,
            valid_at,
            lead_hours,
            forecast["temperature_c"],
            forecast["dew_point_c"],
            forecast["relative_humidity"],
            forecast["precipitation_mm"],
            forecast["pressure_hpa"],
            forecast["wind_speed_ms"],
            forecast["wind_direction_deg"],
            forecast["cloud_cover"],
        )


# ============================================================
# LOAD FORECAST
# ============================================================

def load_forecast(
    latitude: float,
    longitude: float,
) -> None:

    print(f"Fetching forecast for {latitude}, {longitude}...")

    data = get_forecast(
        latitude,
        longitude,
    )

    forecasts = parse_forecast(data)

    # Open-Meteo's simple best-match endpoint does not expose a clean
    # model initialization timestamp, so for now this represents when
    # we pulled this forecast run.
    initialized_at = datetime.now(timezone.utc).replace(
        minute=0,
        second=0,
        microsecond=0,
    )

    connection = get_connection()

    try:
        cursor = connection.cursor()

        weather_model_id = get_or_create_weather_model(
            cursor
        )

        # Open-Meteo may return a slightly adjusted coordinate
        # corresponding to the actual forecast grid point.
        grid_point_id = get_or_create_grid_point(
            cursor,
            latitude=data["latitude"],
            longitude=data["longitude"],
            elevation_m=data.get("elevation"),
        )

        forecast_run_id = create_forecast_run(
            cursor,
            weather_model_id,
            initialized_at,
        )

        insert_forecasts(
            cursor,
            forecast_run_id,
            grid_point_id,
            forecasts,
            initialized_at,
        )

        connection.commit()

        print(
            f"Inserted {len(forecasts)} forecast rows."
        )

        print(
            f"Weather Model ID: {weather_model_id}"
        )

        print(
            f"Grid Point ID: {grid_point_id}"
        )

        print(
            f"Forecast Run ID: {forecast_run_id}"
        )

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":

    # Buffalo test point
    latitude = 42.8864
    longitude = -78.8784

    load_forecast(
        latitude=latitude,
        longitude=longitude,
    )