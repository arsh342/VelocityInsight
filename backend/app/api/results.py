from fastapi import APIRouter, HTTPException
from typing import Dict, Any, List
import pandas as pd
import os
from ..core.config import settings

router = APIRouter(prefix="/results", tags=["results"])


@router.get("/{track}/{race}")
async def get_race_results(track: str, race: str) -> Dict[str, Any]:
    """
    Get race results from the CSV files.
    """
    try:
        # Try different file naming patterns for different tracks
        possible_files = []
        
        if track.lower() in ["cota", "sebring", "road america", "sonoma", "vir"]:
            # These tracks have subdirectories
            race_dir = f"Race {race.replace('R', '')}"
            possible_files = [
                os.path.join(settings.dataset_root, track, race_dir, f"03_Provisional Results_{race.replace('R', 'Race ')}_Anonymized.CSV"),
                os.path.join(settings.dataset_root, track, race_dir, f"03_Provisional Results_ {race.replace('R', 'Race ')}_Anonymized.CSV"),  # COTA pattern with space
                os.path.join(settings.dataset_root, track, race_dir, f"00_Results GR Cup {race.replace('R', 'Race ')} Official_Anonymized.CSV"),
                os.path.join(settings.dataset_root, track, race_dir, f"03_Results_Anonymized.CSV"),  # Sonoma pattern
            ]
        elif track.lower() == "indianapolis":
            # Indianapolis has different naming without _Anonymized
            possible_files = [
                os.path.join(settings.dataset_root, track, f"03_Provisional Results_{race.replace('R', 'Race ')}.CSV"),
                os.path.join(settings.dataset_root, track, f"03_GR Cup {race.replace('R', 'Race ')} Official Results.CSV"),
            ]
        else:
            # Default pattern for barber and other tracks
            possible_files = [
                os.path.join(settings.dataset_root, track, f"03_Provisional Results_{race.replace('R', 'Race ')}_Anonymized.CSV"),
                os.path.join(settings.dataset_root, track, f"03_Results GR Cup {race.replace('R', 'Race ')} Official_Anonymized.CSV"),
            ]
        
        results_file = None
        for file_path in possible_files:
            if os.path.exists(file_path):
                results_file = file_path
                break
        
        if not results_file:
            raise HTTPException(status_code=404, detail=f"Race results not found for {track} {race}")
        
        # Read the CSV file - try both semicolon and comma separators
        try:
            df = pd.read_csv(results_file, sep=';')
        except:
            df = pd.read_csv(results_file, sep=',')
        
        # Clean and format the data
        results = []
        for _, row in df.iterrows():
            try:
                result = {
                    "position": int(float(row['POSITION'])) if pd.notna(row['POSITION']) and row['POSITION'] != '' else None,
                    "number": str(row['NUMBER']) if pd.notna(row['NUMBER']) and row['NUMBER'] != '' else None,
                    "driver": f"Driver #{row['NUMBER']}" if pd.notna(row['NUMBER']) and row['NUMBER'] != '' else "Unknown",
                    "team": "Toyota GR Cup",
                    "vehicle": str(row['VEHICLE']) if pd.notna(row['VEHICLE']) and row['VEHICLE'] != '' else "Toyota GR86",
                    "status": str(row['STATUS']) if pd.notna(row['STATUS']) and row['STATUS'] != '' else "Unknown",
                    "laps": int(float(row['LAPS'])) if pd.notna(row['LAPS']) and row['LAPS'] != '' else None,
                    "total_time": str(row['TOTAL_TIME']) if pd.notna(row['TOTAL_TIME']) else None,
                    "gap_first": str(row['GAP_FIRST']) if pd.notna(row['GAP_FIRST']) else None,
                    "gap_previous": str(row['GAP_PREVIOUS']) if pd.notna(row['GAP_PREVIOUS']) else None,
                    "fastest_lap_time": str(row['FL_TIME']) if pd.notna(row['FL_TIME']) else None,
                    "fastest_lap_number": int(float(row['FL_LAPNUM'])) if pd.notna(row['FL_LAPNUM']) and row['FL_LAPNUM'] != '' else None,
                    "fastest_lap_speed": float(row['FL_KPH']) if pd.notna(row['FL_KPH']) and row['FL_KPH'] != '' else None,
                    "class": str(row['CLASS']) if pd.notna(row['CLASS']) else None,
                    "points": 25 if pd.notna(row['POSITION']) and int(float(row['POSITION'])) == 1 else (18 if pd.notna(row['POSITION']) and int(float(row['POSITION'])) == 2 else (15 if pd.notna(row['POSITION']) and int(float(row['POSITION'])) == 3 else max(0, 13 - int(float(row['POSITION']))) if pd.notna(row['POSITION']) else 0))
                }
                results.append(result)
            except Exception as e:
                # Skip rows with invalid data
                continue
        
        # Get winner information
        winner = results[0] if results else None
        
        return {
            "track": track,
            "race": race,
            "results": results,
            "winner": winner,
            "total_entries": len(results),
            "race_distance": results[0]["laps"] if results and results[0]["laps"] else None
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading race results: {str(e)}")


@router.get("/weather/{track}/{race}")
async def get_weather_data(track: str, race: str):
    """Get weather data for a specific track and race"""
    try:
        dataset_path = settings.dataset_root
        race_num = race.replace('R', '')
        
        # Try different patterns for finding weather file
        if track.lower() in ["cota", "sebring", "road america", "sonoma", "vir"]:
            # These tracks have subdirectories
            race_dir = f"Race {race_num}"
            possible_files = [
                os.path.join(dataset_path, track, race_dir, f"26_Weather_{race.replace('R', 'Race ')}_Anonymized.CSV"),
                os.path.join(dataset_path, track, race_dir, f"26_Weather_ {race.replace('R', 'Race ')}_Anonymized.CSV"),  # COTA pattern with space
                os.path.join(dataset_path, track, race_dir, f"26_Weather_Race {race_num}_Anonymized.CSV"),
            ]
        elif track.lower() == "indianapolis":
            # Indianapolis has different naming without _Anonymized
            possible_files = [
                os.path.join(dataset_path, track, f"26_Weather_{race.replace('R', 'Race ')}.CSV"),
                os.path.join(dataset_path, track, f"26_Weather_Race {race_num}.CSV"),
            ]
        else:
            # Default pattern for barber and other tracks
            possible_files = [
                os.path.join(dataset_path, track, f"26_Weather_{race.replace('R', 'Race ')}_Anonymized.CSV"),
                os.path.join(dataset_path, track, f"26_Weather_Race {race_num}_Anonymized.CSV"),
            ]
        
        weather_file = None
        for file_path in possible_files:
            if os.path.exists(file_path):
                weather_file = file_path
                break
        
        if not weather_file:
            raise HTTPException(status_code=404, detail=f"Weather data not found for {track} {race}")
        
        # Read the CSV file
        try:
            df = pd.read_csv(weather_file, sep=';')
        except:
            df = pd.read_csv(weather_file, sep=',')
        
        # Get the first row of weather data (assuming it's consistent throughout race)
        if df.empty:
            raise HTTPException(status_code=404, detail=f"No weather data found for {track} {race}")
        
        weather_row = df.iloc[0]
        weather_data = {
            "track": track,
            "race": race,
            "air_temperature": float(weather_row['AIR_TEMP']) if pd.notna(weather_row.get('AIR_TEMP')) else None,
            "track_temperature": float(weather_row['TRACK_TEMP']) if pd.notna(weather_row.get('TRACK_TEMP')) else None,
            "humidity": float(weather_row['HUMIDITY']) if pd.notna(weather_row.get('HUMIDITY')) else None,
            "wind_speed": float(weather_row['WIND_SPEED']) if pd.notna(weather_row.get('WIND_SPEED')) else None,
            "wind_direction": float(weather_row['WIND_DIRECTION']) if pd.notna(weather_row.get('WIND_DIRECTION')) else None,
            "barometric_pressure": float(weather_row['PRESSURE']) if pd.notna(weather_row.get('PRESSURE')) else None,
            "rain": float(weather_row['RAIN']) if pd.notna(weather_row.get('RAIN')) else None,
        }
        
        return weather_data
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading weather data: {str(e)}")


@router.get("/{track}/{race}/weather")
async def get_weather_data(track: str, race: str) -> Dict[str, Any]:
    """
    Get weather data for a race.
    """
    try:
        # Try different file naming patterns for different tracks
        possible_files = []
        
        if track.lower() in ["cota", "sebring", "road america", "sonoma", "vir"]:
            # These tracks have subdirectories
            race_dir = f"Race {race.replace('R', '')}"
            possible_files = [
                os.path.join(settings.dataset_root, track, race_dir, f"26_Weather_{race.replace('R', 'Race ')}_Anonymized.CSV"),
            ]
        elif track.lower() == "indianapolis":
            # Indianapolis has different naming without _Anonymized
            possible_files = [
                os.path.join(settings.dataset_root, track, f"26_Weather_{race.replace('R', 'Race ')}.CSV"),
            ]
        else:
            # Default pattern for barber and other tracks
            possible_files = [
                os.path.join(settings.dataset_root, track, f"26_Weather_{race.replace('R', 'Race ')}_Anonymized.CSV"),
            ]
        
        weather_file = None
        for file_path in possible_files:
            if os.path.exists(file_path):
                weather_file = file_path
                break
        
        if not weather_file:
            raise HTTPException(status_code=404, detail=f"Weather data not found for {track} {race}")
        
        # Read the CSV file - try different separators
        try:
            df = pd.read_csv(weather_file, sep=';')
        except:
            df = pd.read_csv(weather_file, sep=',')
        
        # Get latest weather reading
        latest_weather = df.iloc[-1] if len(df) > 0 else None
        
        if latest_weather is not None:
            weather_data = {
                "air_temperature": float(latest_weather['AIR_TEMP']) if pd.notna(latest_weather['AIR_TEMP']) else None,
                "track_temperature": float(latest_weather['TRACK_TEMP']) if pd.notna(latest_weather['TRACK_TEMP']) else None,
                "humidity": float(latest_weather['HUMIDITY']) if pd.notna(latest_weather['HUMIDITY']) else None,
                "pressure": float(latest_weather['PRESSURE']) if pd.notna(latest_weather['PRESSURE']) else None,
                "wind_speed": float(latest_weather['WIND_SPEED']) if pd.notna(latest_weather['WIND_SPEED']) else None,
                "wind_direction": float(latest_weather['WIND_DIRECTION']) if pd.notna(latest_weather['WIND_DIRECTION']) else None,
                "rain": bool(latest_weather['RAIN']) if pd.notna(latest_weather['RAIN']) else False,
                "timestamp": str(latest_weather['TIME_UTC_STR']) if pd.notna(latest_weather['TIME_UTC_STR']) else None
            }
        else:
            weather_data = None
        
        return {
            "track": track,
            "race": race,
            "current_weather": weather_data,
            "total_readings": len(df)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading weather data: {str(e)}")


@router.get("/{track}/{race}/vehicles")
async def get_race_vehicles(track: str, race: str) -> Dict[str, Any]:
    """
    Get list of vehicles that participated in the race.
    """
    try:
        # Load lap times to get vehicle list
        from ..data.loader import load_lap_times
        start, end, lapt = load_lap_times(settings.dataset_root, track=track, race=race)
        
        vehicles = []
        if "vehicle_id" in lapt.columns:
            unique_vehicles = lapt["vehicle_id"].unique()
            for vehicle_id in unique_vehicles:
                vehicle_laps = lapt[lapt["vehicle_id"] == vehicle_id]
                vehicles.append({
                    "vehicle_id": str(vehicle_id),
                    "total_laps": len(vehicle_laps),
                    "first_lap": int(vehicle_laps["lap"].min()) if "lap" in vehicle_laps.columns else None,
                    "last_lap": int(vehicle_laps["lap"].max()) if "lap" in vehicle_laps.columns else None
                })
        
        return {
            "track": track,
            "race": race,
            "vehicles": vehicles,
            "total_vehicles": len(vehicles)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting vehicle list: {str(e)}")
