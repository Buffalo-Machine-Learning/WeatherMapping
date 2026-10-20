-- ============================================================
-- FORECAST RUN
-- Represents one run of a weather model.
--
-- Example:
-- HRRR initialized at:
-- 2026-10-19 12:00 UTC
-- ============================================================

CREATE TABLE forecast_run (
    id BIGSERIAL PRIMARY KEY,

    weather_model_id BIGINT NOT NULL,

    initialized_at TIMESTAMPTZ NOT NULL,
    ingested_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    datein TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    datemodified TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT uq_forecast_run
        UNIQUE (weather_model_id, initialized_at)
);


CREATE INDEX idx_forecast_run_initialized_at
ON forecast_run (initialized_at);