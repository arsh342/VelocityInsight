from fastapi import APIRouter

router = APIRouter(prefix="/tracks", tags=["tracks"])


@router.get("")
def get_available_tracks():
    """Get list of available tracks and races - fast hardcoded version."""
    # Hardcoded list with GPS coordinates for weather API
    tracks = [
        {
            "name": "barber",
            "location": {"lat": 33.5370, "lon": -86.0697},  # Barber Motorsports Park, Alabama
            "races": ["R1", "R2"],
            "has_maps": False
        },
        {
            "name": "indianapolis",
            "location": {"lat": 39.7950, "lon": -86.2344},  # Indianapolis Motor Speedway, Indiana
            "races": ["R1", "R2"],
            "has_maps": False
        }, 
        {
            "name": "COTA",
            "location": {"lat": 30.1328, "lon": -97.6411},  # Circuit of The Americas, Texas
            "races": ["R1", "R2"],
            "has_maps": False
        },
        {
            "name": "Road America",
            "location": {"lat": 43.7985, "lon": -87.9897},  # Road America, Wisconsin
            "races": ["R1", "R2"],
            "has_maps": False
        },
        {
            "name": "Sebring",
            "location": {"lat": 27.4506, "lon": -81.3481},  # Sebring International Raceway, Florida
            "races": ["R1", "R2"],
            "has_maps": False
        },
        {
            "name": "Sonoma",
            "location": {"lat": 38.1617, "lon": -122.4544},  # Sonoma Raceway, California
            "races": ["R1", "R2"],
            "has_maps": False
        },
        {
            "name": "VIR",
            "location": {"lat": 36.5876, "lon": -79.2027},  # Virginia International Raceway, Virginia
            "races": ["R1", "R2"],
            "has_maps": False
        }
    ]
    
    return {
        "tracks": tracks,
        "total_tracks": len(tracks)
    }


@router.get("/{track}/races")
def get_track_races(track: str):
    """Get available races for a specific track."""
    # Hardcoded race list
    return {
        "track": track,
        "races": ["R1", "R2"]
    }
