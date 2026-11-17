import pyodbc

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from database import get_db
from routers.forecast import router as forecast_router


app = FastAPI(
    title="WeatherMapping API",
    description="API for forecast, observation, and ML weather data.",
    version="0.1.0",
)


# ============================================================
# CORS
# ============================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# ROUTERS
# ============================================================

app.include_router(forecast_router)


# ============================================================
# HEALTH
# ============================================================

@app.get("/health")
def health(
    connection: pyodbc.Connection = Depends(get_db),
):
    cursor = connection.cursor()

    cursor.execute("SELECT 1")

    cursor.fetchone()

    return {
        "status": "healthy",
        "database": "connected",
    }