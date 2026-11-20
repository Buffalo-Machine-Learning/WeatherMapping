# transforms/weather.py

import pandas as pd

VARIABLES = [
    "temperature_2m",
    "dew_point_2m",
    "relative_humidity_2m",
    "precipitation",
    "pressure_msl",
    "wind_speed_10m",
    "wind_direction_10m",
    "cloud_cover",
]

def transform_forecasts(
    responses,
    coordinates,
    retrieved_at
):
    if len(responses) != len(coordinates):
        raise ValueError("Response location count mismatch")

    frames = []

    for response, (lat, lon) in zip(
        responses, coordinates
    ):
        hourly = response["hourly"]

        df = pd.DataFrame(hourly)

        df["valid_time"] = pd.to_datetime(
            df.pop("time"),
            utc=True
        )

        df["latitude"] = lat
        df["longitude"] = lon
        df["retrieved_at"] = retrieved_at

        frames.append(df)

    result = pd.concat(
        frames,
        ignore_index=True
    )

    for variable in VARIABLES:
        if variable not in result.columns:
            result[variable] = float("nan")

        result[variable] = pd.to_numeric(
            result[variable],
            errors="coerce"
        )

    result = result.dropna(
        subset=["valid_time"]
    )

    result = result.drop_duplicates(
        subset=["latitude", "longitude", "valid_time"],
        keep="last"
    )

    return result[
        ["latitude", "longitude", "valid_time",
         *VARIABLES, "retrieved_at"]
    ]
