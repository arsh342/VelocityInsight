"""
API endpoints for driver consistency analysis
"""
from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
import logging

from ..ml.driver_consistency import get_consistency_model

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/consistency", tags=["consistency"])


@router.get("/{track}/{race}/{vehicle_id}")
async def get_driver_consistency(
    track: str,
    race: str,
    vehicle_id: str
):
    """
    Get comprehensive consistency analysis for a driver.
    
    Returns:
        - Consistency score (0-100)
        - Lap time statistics
        - Sector consistency (if available)
        - Behavioral consistency (throttle, brake, G-forces)
    """
    try:
        model = get_consistency_model()
        analysis = model.calculate_consistency_score(track, race, vehicle_id)
        
        return analysis
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error analyzing consistency: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{track}/{race}/{vehicle_id}/strengths")
async def get_driver_strengths(
    track: str,
    race: str,
    vehicle_id: str
):
    """
    Identify driver's strongest and weakest sectors.
    
    Returns:
        - Strongest sector with percentile ranking
        - Weakest sector with improvement needed
        - All sector analysis
    """
    try:
        model = get_consistency_model()
        analysis = model.identify_strengths_weaknesses(track, race, vehicle_id)
        
        if not analysis:
            raise HTTPException(status_code=404, detail="Sector data not available")
        
        return analysis
        
    except Exception as e:
        logger.error(f"Error analyzing strengths: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{track}/{race}/compare")
async def compare_driver_consistency(
    track: str,
    race: str,
    vehicle_ids: List[str] = Query(None)
):
    """
    Compare consistency across multiple drivers.
    
    Args:
        vehicle_ids: List of vehicle IDs to compare (query param, can repeat)
    
    Returns:
        Ranked list of drivers by consistency score
    """
    try:
        if not vehicle_ids:
            # If no vehicles specified, get all from first few laps
            from ..data.telemetry_loader import get_telemetry_loader
            loader = get_telemetry_loader()
            summary = loader.get_telemetry_summary(track, race)
            vehicle_ids = summary['vehicle_list'][:10]  # Limit to 10
        
        model = get_consistency_model()
        comparison = model.compare_drivers(track, race, vehicle_ids)
        
        return comparison
        
    except Exception as e:
        logger.error(f"Error comparing drivers: {e}")
        raise HTTPException(status_code=500, detail=str(e))
