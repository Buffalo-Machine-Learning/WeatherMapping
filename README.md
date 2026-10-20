# WeatherMapping
This repository is going to be a weather mapping project, ultimately this will be used to provide insights that can be used to predict other things (betting on outdoor sports, stock prediction, shipping effects, etc.)

## Future State

```mermaid
flowchart LR
    %% =========================
    %% Data Sources
    %% =========================
    subgraph Sources[Weather Data Sources]
        S1[Open-Meteo API]
        S2[NOAA / NWS API]
        S3[Historical Forecast Data]
        S4[Observed Weather Data]
    end

    %% =========================
    %% Ingestion + Processing
    %% =========================
    subgraph Ingestion[Python Data Ingestion Layer]
        I1[Scheduled Fetch Jobs]
        I2[Normalization / Validation]
        I3[Feature Engineering]
    end

    %% =========================
    %% Storage
    %% =========================
    subgraph Storage[Data Storage]
        D1[(PostgreSQL + PostGIS)]
        D2[(Optional Raw File Store\nGRIB / NetCDF / Zarr)]
    end

    %% =========================
    %% ML
    %% =========================
    subgraph ML[Prediction Pipeline]
        M1[Training Dataset Builder]
        M2[Forecast Bias Correction Model]
        M3[Model Predictions]
        M4[Model Metrics / Evaluation]
    end

    %% =========================
    %% Backend
    %% =========================
    subgraph Backend[Backend API]
        B1[FastAPI Service]
        B2[Forecast Endpoints]
        B3[GeoJSON / Coordinate Endpoints]
        B4[Model Metrics Endpoint]
    end

    %% =========================
    %% Frontend
    %% =========================
    subgraph Frontend[Frontend]
        F1[React App]
        F2[MapLibre Map]
        F3[Weather Layers / Markers]
        F4[Forecast Controls\nTime / Variable / Model Toggle]
    end

    %% Flow
    S1 --> I1
    S2 --> I1
    S3 --> I1
    S4 --> I1

    I1 --> I2
    I2 --> D1
    I2 --> D2
    D1 --> I3

    D1 --> M1
    D2 --> M1
    M1 --> M2
    M2 --> M3
    M3 --> D1
    M2 --> M4
    M4 --> D1

    D1 --> B1
    B1 --> B2
    B1 --> B3
    B1 --> B4

    B2 --> F1
    B3 --> F1
    B4 --> F1

    F1 --> F2
    F2 --> F3
    F1 --> F4
```

## DB Model Plan:

```mermaid
erDiagram
    WEATHER_MODEL {
        bigint id
        varchar name
        varchar source
        real resolution_km
        text description
        timestamptz datein
        timestamptz datemodified
    }

    GRID_POINT {
        bigint id
        double latitude
        double longitude
        real elevation_m
        geometry location
        timestamptz datein
        timestamptz datemodified
    }

    FORECAST_RUN {
        bigint id
        bigint weather_model_id
        timestamptz initialized_at
        timestamptz ingested_at
        timestamptz datein
        timestamptz datemodified
    }

    FORECAST {
        bigint id
        bigint forecast_run_id
        bigint grid_point_id
        timestamptz valid_at
        int lead_hours
        real temperature_c
        real dew_point_c
        real relative_humidity
        real precipitation_mm
        real pressure_hpa
        real wind_speed_ms
        real wind_direction_deg
        real cloud_cover
        timestamptz datein
        timestamptz datemodified
    }

    OBSERVATION {
        bigint id
        bigint grid_point_id
        timestamptz observed_at
        real temperature_c
        real dew_point_c
        real relative_humidity
        real precipitation_mm
        real pressure_hpa
        real wind_speed_ms
        real wind_direction_deg
        real cloud_cover
        varchar source
        timestamptz datein
        timestamptz datemodified
    }

    ML_MODEL {
        bigint id
        varchar name
        varchar version
        varchar model_type
        varchar target_variable
        timestamptz training_start_date
        timestamptz training_end_date
        real mae
        real rmse
        real r_squared
        text model_path
        text description
        timestamptz datein
        timestamptz datemodified
    }

    ML_PREDICTION {
        bigint id
        bigint ml_model_id
        bigint grid_point_id
        bigint source_forecast_id
        timestamptz issued_at
        timestamptz valid_at
        real predicted_temperature_c
        real predicted_precipitation_mm
        real predicted_error_temperature_c
        timestamptz datein
        timestamptz datemodified
    }

    WEATHER_MODEL ||--o{ FORECAST_RUN : weather_model_id
    FORECAST_RUN ||--o{ FORECAST : forecast_run_id
    GRID_POINT ||--o{ FORECAST : grid_point_id
    GRID_POINT ||--o{ OBSERVATION : grid_point_id
    GRID_POINT ||--o{ ML_PREDICTION : grid_point_id
    ML_MODEL ||--o{ ML_PREDICTION : ml_model_id
    FORECAST ||--o{ ML_PREDICTION : source_forecast_id
```