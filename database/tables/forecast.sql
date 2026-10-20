-- ============================================================
-- FORECAST
-- Raw forecast values produced by a weather model.
--
-- One row =
-- one forecast run
-- + one grid point
-- + one valid forecast time
-- ============================================================

CREATE TABLE forecast (
    id BIGSERIAL PRIMARY KEY,

    forecast_run_id BIGINT NOT NULL,
    grid_point_id BIGINT NOT NULL,

    valid_at TIMESTAMPTZ NOT NULL,
    lead_hours INTEGER NOT NULL,

    temperature_c REAL,
    dew_point_c REAL,
    relative_humidity REAL,

    precipitation_mm REAL,

    pressure_hpa REAL,

    wind_speed_ms REAL,
    wind_direction_deg REAL,

    cloud_cover REAL,

    datein TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    datemodified TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT uq_forecast
        UNIQUE (
            forecast_run_id,
            grid_point_id,
            valid_at
        )
);

CREATE INDEX idx_forecast_grid_point
ON forecast (grid_point_id);

CREATE INDEX idx_forecast_valid_at
ON forecast (valid_at);

CREATE INDEX idx_forecast_run_id
ON forecast (forecast_run_id);