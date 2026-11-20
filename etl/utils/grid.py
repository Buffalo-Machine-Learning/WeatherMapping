# utils/grid.py

import numpy as np
import pandas as pd

def generate_grid(config: dict) -> pd.DataFrame:
    grid = config["grid"]

    resolution = grid["resolution"]

    latitudes = np.arange(
        grid["min_latitude"],
        grid["max_latitude"] + resolution / 2,
        resolution
    )

    longitudes = np.arange(
        grid["min_longitude"],
        grid["max_longitude"] + resolution / 2,
        resolution
    )

    lat, lon = np.meshgrid(
        latitudes,
        longitudes,
        indexing="ij"
    )

    return pd.DataFrame({
        "latitude": lat.ravel(),
        "longitude": lon.ravel()
    })
