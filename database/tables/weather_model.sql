-- ============================================================
-- WEATHER MODEL
-- Defines the source/model that produced a forecast.
--
-- Examples:
--   HRRR
--   GFS
--   Open-Meteo
--   WeatherML-v1
-- ============================================================

CREATE TABLE weather_model (
    id BIGSERIAL PRIMARY KEY,

    name VARCHAR(100) NOT NULL,
    source VARCHAR(255) NOT NULL,
    resolution_km REAL,

    description TEXT,

    datein TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    datemodified TIMESTAMPTZ NOT NULL DEFAULT NOW()
);