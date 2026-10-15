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
    WEATHER_MODEL ||--o{ FORECAST_RUN : produces
    FORECAST_RUN ||--o{ FORECAST : contains
    GRID_POINT ||--o{ FORECAST : has
    GRID_POINT ||--o{ OBSERVATION : records
    GRID_POINT ||--o{ ML_PREDICTION : receives

    WEATHER_MODEL {
        int id
        string name
        string source
        float resolution_km
    }

    FORECAST_RUN {
        bigint id
        int model_id
        datetime initialized_at
        datetime ingested_at
    }

    GRID_POINT {
        bigint id
        float latitude
        float longitude
        geometry location
        float elevation_m
    }

    FORECAST {
        bigint run_id
        bigint grid_point_id
        datetime valid_at
        int lead_hours
        float temperature_c
        float precipitation_mm
        float pressure_hpa
        float wind_speed_ms
        float cloud_cover
    }

    OBSERVATION {
        bigint grid_point_id
        datetime observed_at
        float temperature_c
        float precipitation_mm
        float pressure_hpa
        float wind_speed_ms
    }

    ML_PREDICTION {
        string model_version
        bigint grid_point_id
        datetime issued_at
        datetime valid_at
        float predicted_temperature_c
        float predicted_precipitation_mm
    }
```