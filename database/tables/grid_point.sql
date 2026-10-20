-- ============================================================
-- GRID POINT
-- Geographic locations where forecasts/predictions exist.
-- ============================================================

CREATE TABLE grid_point (
    id BIGSERIAL PRIMARY KEY,

    latitude DOUBLE PRECISION NOT NULL,
    longitude DOUBLE PRECISION NOT NULL,
    elevation_m REAL,

    location GEOMETRY(Point, 4326) NOT NULL,

    datein TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    datemodified TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT uq_grid_point_lat_lon
        UNIQUE (latitude, longitude)
);


CREATE INDEX idx_grid_point_location
ON grid_point
USING GIST (location);