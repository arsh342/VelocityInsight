from fastapi import APIRouter, Query
from typing import Optional
import pandas as pd
import numpy as np
from ..core.config import settings
from ..data.loader import load_lap_times, load_race_telemetry_wide, segment_laps_by_time

router = APIRouter(prefix="/laps", tags=["laps"])


@router.get("")
def get_laps(track: str = Query("barber"), race: str = Query("R1"), vehicle_id: Optional[str] = None):
    """Get lap data - optimized for fast response by returning lap times without full telemetry segmentation."""
    try:
        start, end, lapt = load_lap_times(settings.dataset_root, track=track, race=race)
    except (ValueError, FileNotFoundError) as e:
        return {"error": str(e)}

    # Filter by vehicle if specified
    if vehicle_id:
        lapt_filtered = lapt[lapt["vehicle_id"] == vehicle_id] if "vehicle_id" in lapt.columns else lapt
        start_filtered = start[start["vehicle_id"] == vehicle_id] if "vehicle_id" in start.columns else start
        end_filtered = end[end["vehicle_id"] == vehicle_id] if "vehicle_id" in end.columns else end
    else:
        lapt_filtered = lapt
        start_filtered = start
        end_filtered = end
    
    # Aggregate lap statistics by vehicle
    laps_by_vehicle = {}
    if "vehicle_id" in lapt_filtered.columns:
        for vid, group in lapt_filtered.groupby("vehicle_id"):
            laps_by_vehicle[str(vid)] = {
                "total_laps": len(group),
                "lap_numbers": group["lap"].tolist() if "lap" in group.columns else []
            }
    
    # Replace NaN values with None for JSON serialization
    lapt_sample = lapt_filtered.head(100).replace({np.nan: None})

    return {
        "track": track,
        "race": race,
        "total_lap_records": len(lapt_filtered),
        "laps_by_vehicle": laps_by_vehicle,
        "sample_lap_times": lapt_sample.to_dict(orient="records"),
        "note": "Full telemetry segmentation available via /telemetry endpoint"
    }


@router.get("/times")
def get_lap_times(track: str = Query("barber"), race: str = Query("R1"), vehicle_id: Optional[str] = None):
    """Get actual lap times with timing data for visualization."""
    try:
        start, end, lapt = load_lap_times(settings.dataset_root, track=track, race=race)
    except (ValueError, FileNotFoundError) as e:
        return {"error": str(e)}

    # Filter by vehicle if specified FIRST to reduce processing time
    if vehicle_id:
        lapt_filtered = lapt[lapt["vehicle_id"] == vehicle_id] if "vehicle_id" in lapt.columns else lapt
        if len(lapt_filtered) == 0:
            return {"track": track, "race": race, "vehicle_id": vehicle_id, "total_records": 0, "lap_times": []}
    else:
        # Limit to first 100 records for overview if no specific vehicle
        lapt_filtered = lapt.head(100)
    
    # Only calculate lap times if we have a reasonable number of records
    if len(lapt_filtered) > 0 and len(lapt_filtered) < 1000:
        # Calculate lap times from timestamps
        if "timestamp" in lapt_filtered.columns:
            # Convert timestamp to datetime
            lapt_filtered = lapt_filtered.copy()
            lapt_filtered["timestamp"] = pd.to_datetime(lapt_filtered["timestamp"])
            
            # Sort by vehicle and lap number
            lapt_filtered = lapt_filtered.sort_values(["vehicle_id", "lap"]).reset_index(drop=True)
            
            # Calculate lap time as difference between consecutive timestamps
            if vehicle_id:
                # For single vehicle, calculate lap time from consecutive laps
                lapt_filtered["lap_time"] = lapt_filtered["timestamp"].diff().dt.total_seconds()
            else:
                # For multiple vehicles, calculate within each vehicle group
                lapt_filtered["lap_time"] = lapt_filtered.groupby("vehicle_id")["timestamp"].diff().dt.total_seconds()
    
    # Replace NaN values with None for JSON serialization
    lap_times_clean = lapt_filtered.replace({np.nan: None})

    return {
        "track": track,
        "race": race,
        "vehicle_id": vehicle_id,
        "total_records": len(lap_times_clean),
        "lap_times": lap_times_clean.to_dict(orient="records")
    }
