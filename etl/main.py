# main.py (core execution flow)

from datetime import datetime, timezone

from sources.open_meteo import (
    make_session, get_forecasts
)
from transforms.weather import transform_forecasts
from loaders.postgres import load_weather

def run_forecast_etl(conn, config, locations):
    batch_size = config["open_meteo"]["batch_size"]
    total_loaded = 0

    with make_session() as session:
        for start in range(0, len(locations), batch_size):
            batch = locations[
                start:start + batch_size
            ]

            coordinates = list(
                batch[["latitude", "longitude"]]
                .itertuples(index=False, name=None)
            )

            responses = get_forecasts(
                coordinates,
                config,
                session
            )

            df = transform_forecasts(
                responses,
                coordinates,
                datetime.now(timezone.utc)
            )

            total_loaded += load_weather(conn, df)

    return total_loaded
