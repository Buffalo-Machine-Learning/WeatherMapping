-- ============================================================
-- ML MODEL
-- Stores information about your own trained models.
--
-- Example:
-- xgboost-temp-v1
-- ============================================================

CREATE TABLE ml_model (
    id BIGSERIAL PRIMARY KEY,

    name VARCHAR(100) NOT NULL,
    version VARCHAR(50) NOT NULL,

    model_type VARCHAR(100),

    target_variable VARCHAR(100),

    training_start_date TIMESTAMPTZ,
    training_end_date TIMESTAMPTZ,

    mae REAL,
    rmse REAL,
    r_squared REAL,

    model_path TEXT,

    description TEXT,

    datein TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    datemodified TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT uq_ml_model_version
        UNIQUE (name, version)
);
