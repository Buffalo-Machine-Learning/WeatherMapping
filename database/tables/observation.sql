-- ============================================================
-- OBSERVATION
-- Actual observed weather.
--
-- This is your ground truth used for training/evaluation.
-- ============================================================

CREATE TABLE observation (
    id BIGSERIAL PRIMARY KEY,

    grid_point_id BIGINT NOT NULL,

    observed_at TIMESTAMPTZ NOT NULL,

    temperature_c REAL,
    dew_point_c REAL,
    relative_humidity REAL,

    precipitation_mm REAL,

    pressure_hpa REAL,

    wind_speed_ms REAL,
    wind_direction_deg REAL,

    cloud_cover REAL,

    source VARCHAR(100),

    datein TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    datemodified TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT uq_observation
        UNIQUE (
            grid_point_id,
            observed_at
        )
);

CREATE INDEX idx_observation_grid_point
ON observation (grid_point_id);

CREATE INDEX idx_observation_observed_at
ON observation (observed_at);