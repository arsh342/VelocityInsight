"""
Weather service using Open-Meteo API for real-time weather data.
No API key required - completely free and open source.
"""

import httpx
from typing import Optional, Dict
from datetime import datetime


class WeatherService:
    """Service for fetching real-time weather data from Open-Meteo API."""
    
    BASE_URL = "https://api.open-meteo.com/v1/forecast"
    
    # Weather code mapping from Open-Meteo to user-friendly descriptions
    WEATHER_CODE_MAP = {
        0: "sunny",
        1: "cloudy",
        2: "cloudy",
        3: "cloudy",
        45: "cloudy",
        48: "cloudy",
        51: "rainy",
        53: "rainy",
        55: "rainy",
        56: "rainy",
        57: "rainy",
        61: "rainy",
        63: "rainy",
        65: "rainy",
        66: "rainy",
        67: "rainy",
        71: "rainy",
        73: "rainy",
        75: "rainy",
        77: "rainy",
        80: "rainy",
        81: "rainy",
        82: "rainy",
        85: "rainy",
        86: "rainy",
        95: "rainy",
        96: "rainy",
        99: "rainy",
    }
    
    @classmethod
    async def get_weather(cls, latitude: float, longitude: float) -> Dict:
        """
        Fetch current weather for given coordinates.
        
        Args:
            latitude: Latitude coordinate
            longitude: Longitude coordinate
            
        Returns:
            Dictionary with weather data including temperature, conditions, etc.
            
        Raises:
            Exception: If API request fails
        """
        params = {
            "latitude": latitude,
            "longitude": longitude,
            "current": "temperature_2m,weather_code,relative_humidity_2m,wind_speed_10m",
            "temperature_unit": "celsius",
            "wind_speed_unit": "kmh",
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(cls.BASE_URL, params=params, timeout=10.0)
                response.raise_for_status()
                data = response.json()
                
                current = data.get("current", {})
                weather_code = current.get("weather_code", 0)
                
                return {
                    "temperature": round(current.get("temperature_2m", 20.0), 1),
                    "weather_code": weather_code,
                    "weather": cls._get_weather_description(weather_code),
                    "humidity": current.get("relative_humidity_2m"),
                    "wind_speed": round(current.get("wind_speed_10m", 0.0), 1),
                    "timestamp": current.get("time", datetime.utcnow().isoformat())
                }
        except httpx.HTTPError as e:
            raise Exception(f"Failed to fetch weather data: {str(e)}")
        except Exception as e:
            raise Exception(f"Weather service error: {str(e)}")
    
    @classmethod
    def _get_weather_description(cls, weather_code: int) -> str:
        """Convert weather code to user-friendly description."""
        return cls.WEATHER_CODE_MAP.get(weather_code, "sunny")
