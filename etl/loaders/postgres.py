# loaders/postgres.py

import pandas as pd

COLUMNS = [
    "latitude", "longitude", "valid_time",
    "temperature_2m", "dew_point_2m",
    "relative_humidity_2m", "precipitation",
    "pressure_msl", "wind_speed_10m",
    "wind_direction_10m", "cloud_cover",
    "retrieved_at"
]

def load_weather(conn, df: pd.DataFrame):
    if df.empty:
        return 0

    cursor = conn.cursor()

    try:
        cursor.execute("""
            CREATE TEMP TABLE IF NOT EXISTS
                forecast_stage (
                    latitude DOUBLE PRECISION,
                    longitude DOUBLE PRECISION,
                    valid_time TIMESTAMPTZ,
                    temperature_2m DOUBLE PRECISION,
                    dew_point_2m DOUBLE PRECISION,
                    relative_humidity_2m DOUBLE PRECISION,
                    precipitation DOUBLE PRECISION,
                    pressure_msl DOUBLE PRECISION,
                    wind_speed_10m DOUBLE PRECISION,
                    wind_direction_10m DOUBLE PRECISION,
                    cloud_cover DOUBLE PRECISION,
                    retrieved_at TIMESTAMPTZ
                ) ON COMMIT DELETE ROWS
        """)

        cursor.execute("TRUNCATE forecast_stage")

        values = (
            df[COLUMNS]
            .astype(object)
            .where(pd.notna(df[COLUMNS]), None)
        )

        records = list(
            values.itertuples(index=False, name=None)
        )

        # Benchmark this with your PostgreSQL ODBC driver.
        cursor.fast_executemany = True

        placeholders = ", ".join(["?"] * len(COLUMNS))
        names = ", ".join(COLUMNS)

        cursor.executemany(
            f"INSERT INTO forecast_stage ({names}) "
            f"VALUES ({placeholders})",
            records
        )

        cursor.execute("""
            INSERT INTO weather.forecast_hourly (
                location_id,
                valid_time,
                temperature_2m,
                dew_point_2m,
                relative_humidity_2m,
                precipitation,
                pressure_msl,
                wind_speed_10m,
                wind_direction_10m,
                cloud_cover,
                retrieved_at
            )
            SELECT
                l.id,
                s.valid_time,
                s.temperature_2m,
                s.dew_point_2m,
                s.relative_humidity_2m,
                s.precipitation,
                s.pressure_msl,
                s.wind_speed_10m,
                s.wind_direction_10m,
                s.cloud_cover,
                s.retrieved_at
            FROM forecast_stage s
            JOIN weather.location l
              ON l.latitude = s.latitude
             AND l.longitude = s.longitude
            ON CONFLICT (location_id, valid_time)
            DO UPDATE SET
                temperature_2m =
                    EXCLUDED.temperature_2m,
                dew_point_2m =
                    EXCLUDED.dew_point_2m,
                relative_humidity_2m =
                    EXCLUDED.relative_humidity_2m,
                precipitation =
                    EXCLUDED.precipitation,
                pressure_msl =
                    EXCLUDED.pressure_msl,
                wind_speed_10m =
                    EXCLUDED.wind_speed_10m,
                wind_direction_10m =
                    EXCLUDED.wind_direction_10m,
                cloud_cover =
                    EXCLUDED.cloud_cover,
                retrieved_at =
                    EXCLUDED.retrieved_at,
                datemodified = NOW()
            WHERE weather.forecast_hourly.retrieved_at
                <= EXCLUDED.retrieved_at
        """)

        conn.commit()
        return len(records)

    except Exception:
        conn.rollback()
        raise
    finally:
        cursor.close()
