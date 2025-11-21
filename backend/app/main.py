from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .api.telemetry import router as telemetry_router
from .api.laps import router as laps_router
from .api.tracks import router as tracks_router
from .api.analytics import router as analytics_router
from .api.strategy import router as strategy_router
from .api.simulation import router as simulation_router
from .api.predictions import router as predictions_router
from .api.consistency import router as consistency_router
from .api.insights import router as insights_router
from .api.results import router as results_router
from .api.weather import router as weather_router
from .websocket.live import router as ws_router

app = FastAPI(title="GR-Insight Backend", description="Real-time race strategy & analytics for Toyota GR Cup")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",  # Frontend local dev
        "http://localhost:3000",  # Alternative local dev
        "https://velocityinsight-backend.onrender.com",  # Production backend
        "https://velocityinsight.onrender.com",  # Production frontend (if applicable)
        "*"  # Allow all for now to debug
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(telemetry_router)
app.include_router(laps_router)
app.include_router(tracks_router)
app.include_router(analytics_router)
app.include_router(strategy_router)
app.include_router(simulation_router)
app.include_router(predictions_router)
app.include_router(consistency_router)
app.include_router(insights_router)
app.include_router(results_router)
app.include_router(weather_router)
app.include_router(ws_router)



@app.get("/")
async def root():
    return {
        "status": "ok", 
        "service": "gr-insight",
        "version": "1.0.0",
        "description": "Real-time race strategy & analytics for Toyota GR Cup"
    }
