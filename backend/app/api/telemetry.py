from fastapi import APIRouter, Query, HTTPException
from typing import Optional
from pathlib import Path
import pandas as pd
import numpy as np
import logging
from ..core.config import settings
from ..data.loader import load_race_telemetry_wide

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/telemetry", tags=["telemetry"])


@router.get("")
def get_telemetry(track: str = Query("barber"), race: str = Query("R1"), vehicle_id: Optional[str] = None,
                  lap_number: Optional[int] = None, limit: int = 1000):
    """Get telemetry data for any supported track/race combination. Optimized for fast response."""
    try:
        # Validate inputs
        if limit <= 0 or limit > 10000:
            raise HTTPException(status_code=400, detail="Limit must be between 1 and 10000")
            
        # Load data with comprehensive error handling
        try:
            df = load_race_telemetry_wide(settings.dataset_root, track=track, race=race)
        except (ValueError, FileNotFoundError) as e:
            logger.error(f"Failed to load telemetry data for {track}/{race}: {e}")
            raise HTTPException(status_code=404, detail=f"No telemetry data found for {track} {race}")
        except Exception as e:
            logger.error(f"Unexpected error loading telemetry: {e}")
            raise HTTPException(status_code=500, detail="Internal server error loading telemetry data")

        # Validate data exists
        if df.empty:
            raise HTTPException(status_code=404, detail=f"No telemetry data available for {track} {race}")

        # Apply filters with validation
        original_count = len(df)
        
        if vehicle_id:
            if vehicle_id not in df["vehicle_id"].values:
                available_vehicles = df["vehicle_id"].unique().tolist()
                raise HTTPException(
                    status_code=404, 
                    detail=f"Vehicle {vehicle_id} not found. Available vehicles: {available_vehicles[:5]}"
                )
            df = df[df["vehicle_id"] == vehicle_id]
        
        if lap_number:
            if lap_number <= 0:
                raise HTTPException(status_code=400, detail="Lap number must be positive")
            if "lap" in df.columns and lap_number not in df["lap"].values:
                available_laps = sorted(df["lap"].unique().tolist()) if "lap" in df.columns else []
                raise HTTPException(
                    status_code=404,
                    detail=f"Lap {lap_number} not found. Available laps: {available_laps[:10]}"
                )
            df = df[df["lap"] == lap_number]
    
        # Limit to first N rows for fast response (can be increased per request)
        df = df.head(limit)
        
        # Replace NaN values with None for JSON serialization
        df = df.replace({np.nan: None})
        
        # Return enhanced data with metadata
        return {
            "track": track,
            "race": race,
            "vehicle_id": vehicle_id,
            "lap_number": lap_number,
            "count": len(df),
            "original_count": original_count,
            "limit_applied": limit,
            "total_available": "Use limit parameter to control response size",
            "columns": list(df.columns),
            "rows": df.to_dict(orient="records"),
            "status": "success"
        }
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        # Log unexpected errors and return generic error
        logger.error(f"Unexpected error in get_telemetry: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
