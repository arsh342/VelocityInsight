"""
Weather API endpoints for fetching real-time weather data for race tracks.
"""

from fastapi import APIRouter, HTTPException
from app.services.weather import WeatherService
from app.api.tracks import get_available_tracks

router = APIRouter(prefix="/weather", tags=["weather"])


@router.get("/{track}")
async def get_track_weather(track: str):
    """
    Get real-time weather data for a specific track.
    
    Args:
        track: Track name (e.g., 'barber', 'indianapolis', 'COTA')
        
    Returns:
        Current weather data including temperature, conditions, humidity, and wind speed
        
    Raises:
        HTTPException: If track not found or weather API fails
    """
    # Get track data including coordinates
    tracks_data = get_available_tracks()
    tracks = tracks_data.get("tracks", [])
    
    # Find the track
    track_info = next(
        (t for t in tracks if t["name"].lower() == track.lower()),
        None
    )
    
    if not track_info:
        raise HTTPException(
            status_code=404,
            detail=f"Track '{track}' not found. Available tracks: {[t['name'] for t in tracks]}"
        )
    
    location = track_info.get("location")
    if not location:
        raise HTTPException(
            status_code=500,
            detail=f"Track '{track}' does not have location coordinates configured"
        )
    
    try:
        # Fetch weather data
        weather_data = await WeatherService.get_weather(
            latitude=location["lat"],
            longitude=location["lon"]
        )
        
        return {
            "track": track,
            "location": location,
            **weather_data
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch weather data: {str(e)}"
        )
