# sources/open_meteo.py

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

def make_session():
    session = requests.Session()

    retry = Retry(
        total=4,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
        respect_retry_after_header=True
    )

    session.mount(
        "https://",
        HTTPAdapter(max_retries=retry)
    )

    return session


def get_forecasts(
    coordinates,
    config,
    session
):
    settings = config["open_meteo"]

    params = {
        "latitude": ",".join(
            str(lat) for lat, lon in coordinates
        ),
        "longitude": ",".join(
            str(lon) for lat, lon in coordinates
        ),
        "hourly": ",".join(settings["hourly"]),
        "forecast_days": settings["forecast_days"],
        "timezone": "UTC",
        "models": "auto",
        "cell_selection": "nearest"
    }

    response = session.get(
        settings["url"],
        params=params,
        timeout=120
    )

    response.raise_for_status()
    data = response.json()

    return data if isinstance(data, list) else [data]
