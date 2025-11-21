"""
API endpoints for Driver Training & Insights, Pre-Event Prediction, and Post-Event Analysis
"""
from fastapi import APIRouter, HTTPException, Query, UploadFile, File
from typing import Optional, Dict, Any, List
import pandas as pd
import json
import logging
from pathlib import Path
import os
from datetime import datetime

from ..core.config import settings
from ..data.loader import load_lap_times, load_race_telemetry_wide
from ..data.sector_mapper import get_sector_mapper
from ..ml.tire_degradation import TireDegradationModel
from ..ml.pit_strategy import PitStrategyOptimizer
from ..ml.lap_time_predictor import get_lap_time_predictor
import pandas as pd

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/insights", tags=["insights"])

# Gemini API integration
# GEMINI_API_KEY is now loaded from settings

try:
    from google.generativeai import configure, GenerativeModel
    configure(api_key=settings.gemini_api_key)
    gemini_model = GenerativeModel('gemini-2.5-flash')
except ImportError:
    logger.warning("Google Generative AI not installed. Some features may not work.")
    gemini_model = None
except Exception as e:
    logger.warning(f"Failed to initialize Gemini: {e}")
    gemini_model = None


async def generate_ai_insights(prompt: str) -> str:
    """Generate AI insights using Gemini"""
    if not gemini_model:
        return "AI insights unavailable. Please install google-generativeai package."
    
    try:
        response = gemini_model.generate_content(prompt)
        return response.text
    except Exception as e:
        logger.error(f"Error generating AI insights: {e}")
        return f"Error generating insights: {str(e)}"


@router.get("/driver-training/{track}/{race}/{vehicle_id}")
async def get_driver_training_insights(
    track: str,
    race: str,
    vehicle_id: str
) -> Dict[str, Any]:
    """
    Driver Training & Insights: Identify areas for improvement, optimize racing line, 
    understand performance patterns.
    """
    try:
        # Load performance data
        start, end, lapt = load_lap_times(settings.dataset_root, track, race)
        df_telemetry = load_race_telemetry_wide(settings.dataset_root, track, race)
        
        # Filter to vehicle
        vehicle_laps = lapt[lapt['vehicle_id'] == vehicle_id].copy()
        vehicle_telemetry = df_telemetry[df_telemetry['vehicle_id'] == vehicle_id]
        
        if vehicle_laps.empty:
            raise HTTPException(status_code=404, detail=f"No data for vehicle {vehicle_id}")
        
        # Sort by lap number and calculate lap times
        vehicle_laps = vehicle_laps.sort_values("lap").reset_index(drop=True)
        vehicle_laps['lap_time'] = vehicle_laps['timestamp'].diff().dt.total_seconds()
        
        # Calculate key metrics
        lap_times = vehicle_laps['lap_time'].dropna()
        avg_lap_time = float(lap_times.mean())
        best_lap_time = float(lap_times.min())
        worst_lap_time = float(lap_times.max())
        consistency = float(lap_times.std())
        
        
        # Sector analysis - use SectorMapper to load actual sector data
        sectors = {}
        try:
            mapper = get_sector_mapper(settings.dataset_root)
            df_sectors = mapper.load_sector_data(track, race)
            
            # Filter to vehicle
            vehicle_sectors = df_sectors[df_sectors['vehicle_id'] == vehicle_id]
            
            if not vehicle_sectors.empty:
                # Get sector consistency stats
                sector_stats = mapper.get_sector_consistency(df_sectors, vehicle_id)
                
                # Format for frontend
                for sector_name, stats in sector_stats.items():
                    sectors[sector_name] = {
                        'avg': stats['mean'],
                        'best': stats['min'],
                        'consistency': stats['std']
                    }
        except Exception as e:
            logger.warning(f"Could not load sector data for {track}/{race}/{vehicle_id}: {e}")
            # sectors will remain empty dict
        
        
        # Telemetry analysis
        telemetry_insights = {}
        if not vehicle_telemetry.empty:
            telemetry_insights = {
                'avg_speed': float(vehicle_telemetry['speed'].mean()),
                'max_speed': float(vehicle_telemetry['speed'].max()),
                'avg_throttle': float(vehicle_telemetry.get('aps', vehicle_telemetry.get('throttle', pd.Series([0]))).mean()),
                'avg_brake': float(vehicle_telemetry.get('pbrake_f', pd.Series([0])).mean()),
                'avg_g_force': float(vehicle_telemetry.get('accx_can', pd.Series([0])).abs().mean())
            }
        
        # Generate AI insights
        prompt = f"""
You are an expert racing coach analyzing telemetry data for driver improvement.

TRACK: {track}
RACE: {race}
VEHICLE: {vehicle_id}

PERFORMANCE METRICS:
- Average Lap Time: {avg_lap_time:.2f}s
- Best Lap Time: {best_lap_time:.2f}s
- Worst Lap Time: {worst_lap_time:.2f}s
- Consistency (std dev): {consistency:.2f}s
- Sectors: {json.dumps(sectors, indent=2)}
- Telemetry: {json.dumps(telemetry_insights, indent=2)}

Provide:
1. Areas for improvement (specific sectors or techniques)
2. Racing line optimization suggestions
3. Performance patterns and insights
4. Actionable training recommendations

Format as JSON with keys: areasForImprovement, racingLineTips, performanceInsights, trainingRecommendations
"""
        
        ai_analysis = await generate_ai_insights(prompt)
        
        # Try to parse JSON from AI response
        try:
            ai_data = json.loads(ai_analysis)
        except:
            # Fallback if not JSON
            ai_data = {
                "analysis": ai_analysis,
                "areasForImprovement": ["Review AI analysis for specific recommendations"],
                "racingLineTips": ["Analyze telemetry data for optimal racing line"],
                "performanceInsights": ["Performance data analyzed"],
                "trainingRecommendations": ["Focus on consistency improvement"]
            }
        
        return {
            "vehicle_id": vehicle_id,
            "track": track,
            "race": race,
            "performance_summary": {
                "avg_lap_time": avg_lap_time,
                "best_lap_time": best_lap_time,
                "worst_lap_time": worst_lap_time,
                "consistency": consistency,
                "total_laps": len(lap_times)
            },
            "sector_analysis": sectors,
            "telemetry_insights": telemetry_insights,
            "ai_analysis": ai_data
        }
        
    except Exception as e:
        logger.error(f"Error generating driver training insights: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/pre-event-prediction/{track}")
async def get_pre_event_prediction(
    track: str,
    race: Optional[str] = Query(None, description="Race identifier (optional)"),
    weather: Optional[str] = Query(None, description="Weather conditions"),
    track_temp: Optional[float] = Query(None, description="Track temperature (°C)")
) -> Dict[str, Any]:
    """
    Pre-Event Prediction: Forecast qualifying results, race pace, tire degradation 
    before the green flag drops.
    """
    try:
        # Load historical data for this track
        races = ["R1", "R2"] if not race else [race]
        
        all_predictions = {}
        for r in races:
            try:
                start, end, lapt = load_lap_times(settings.dataset_root, track, r)
                
                if lapt.empty:
                    continue
                
                # Calculate lap_time from timestamps if not present
                if 'lap_time' not in lapt.columns and 'timestamp' in lapt.columns:
                    lapt = lapt.copy()
                    lapt['timestamp'] = pd.to_datetime(lapt['timestamp'], errors='coerce')
                    lapt = lapt.sort_values(['vehicle_id', 'lap']).reset_index(drop=True)
                    lapt['lap_time'] = lapt.groupby('vehicle_id')['timestamp'].diff().dt.total_seconds()
                
                # Filter out invalid lap times (NaN, negative, or unreasonably large)
                lapt_valid = lapt[lapt['lap_time'].notna() & (lapt['lap_time'] > 5) & (lapt['lap_time'] < 600)].copy()
                
                if lapt_valid.empty:
                    logger.warning(f"No valid lap times found for {track}/{r}")
                    continue
                
                # Ensure required columns exist for degradation calculation
                if 'vehicle_id' not in lapt_valid.columns:
                    logger.warning(f"No vehicle_id column for {track}/{r}")
                    continue
                
                # Calculate baseline predictions from historical data
                avg_lap_time = float(lapt_valid['lap_time'].mean())
                
                # For qualifying pace, use realistic lap times only (filter out likely sector times)
                # Realistic lap times for racing are typically 30s - 5min (300s)
                realistic_laps = lapt_valid[(lapt_valid['lap_time'] >= 30) & (lapt_valid['lap_time'] <= 300)]
                
                if not realistic_laps.empty:
                    # Use the 5th percentile instead of absolute minimum to avoid outliers
                    best_lap_time = float(realistic_laps['lap_time'].quantile(0.05))
                else:
                    # Fallback to average if no realistic laps found
                    best_lap_time = avg_lap_time
                
                # Tire degradation prediction - use full lapt dataframe, not filtered
                tire_model = TireDegradationModel()
                try:
                    degradation_df = tire_model.calculate_lap_degradation(lapt_valid)
                    degradation_rate = 0.0
                    if not degradation_df.empty:
                        model_stats = tire_model.fit_degradation_model(degradation_df)
                        degradation_rate = abs(model_stats.get('avg_degradation_rate_per_lap', 0))
                except Exception as e:
                    logger.warning(f"Could not calculate degradation for {track}/{r}: {e}")
                    degradation_rate = 0.0
                
                # Predict qualifying pace (best lap + 1-2% for qualifying simulation)
                predicted_qualifying_pace = best_lap_time * 1.01
                
                # Predict race pace (average lap time)
                predicted_race_pace = avg_lap_time
                
                # Predict tire degradation over 30 laps
                predicted_degradation_30_laps = degradation_rate * 30
                
                all_predictions[r] = {
                    "predicted_qualifying_pace": predicted_qualifying_pace,
                    "predicted_race_pace": predicted_race_pace,
                    "predicted_tire_degradation_per_lap": degradation_rate,
                    "predicted_degradation_30_laps": predicted_degradation_30_laps,
                    "baseline_lap_time": avg_lap_time,
                    "best_historical_lap": best_lap_time,
                    "weather_factor": weather or "unknown",
                    "track_temp": track_temp
                }
            except Exception as e:
                logger.error(f"Error loading data for {track}/{r}: {e}", exc_info=True)
                continue
        
        if not all_predictions:
            raise HTTPException(status_code=404, detail=f"No historical data for track {track}")
        
        # Generate AI predictions with structured output
        prompt = f"""
You are a GR Cup race strategist. Provide predictions for {track} in valid JSON format.

HISTORICAL DATA: {json.dumps(all_predictions, indent=2)}
CONDITIONS: Weather={weather or 'Unknown'}, Track Temp={track_temp or 'Unknown'}°C

Return ONLY a valid JSON object with these exact keys:

{{
  "qualifyingPredictions": [
    "Predicted qualifying pace: X:XX.XXXs based on historical best",
    "Expect 2-3 flying laps with peak grip on lap 2",
    "Cold track will require careful tire warm-up"
  ],
  "racePaceForecast": [
    "Target race pace: X:XX.XXXs average",
    "Degradation estimate: X.XXs per lap over 30 laps",
    "Consistent pace management critical in cold conditions"
  ],
  "tireDegradationForecast": [
    "Expected degradation: X.XXs total over race distance",
    "Monitor for graining in cold temperatures"
  ],
  "keyPerformanceIndicators": [
    "Lap time consistency",
    "Tire temperature management",
    "Fuel efficiency"
  ],
  "strategicRecommendations": [
    "Primary strategy: One-stop at lap XX-XX",
    "Focus on tire warm-up in out-laps",
    "Monitor weather changes for strategy adjustments"
  ]
}}

IMPORTANT: Return ONLY the JSON object, no markdown formatting, no explanations.
Use actual numbers from the historical data provided.
"""
        
        ai_predictions = await generate_ai_insights(prompt)
        
        try:
            # Clean any markdown formatting
            cleaned = ai_predictions.strip()
            if cleaned.startswith("```"):
                # Remove markdown code blocks
                lines = cleaned.split("\n")
                cleaned = "\n".join([l for l in lines if not l.startswith("```")])
            
            ai_data = json.loads(cleaned)
            
            # Validate required fields
            required_fields = ["qualifyingPredictions", "racePaceForecast", "strategicRecommendations"]
            if not all(field in ai_data for field in required_fields):
                raise ValueError("Missing required fields in AI response")
                
        except Exception as e:
            logger.warning(f"Failed to parse AI predictions as JSON: {e}")
            # Fallback with more detailed predictions
            ai_data = {
                "qualifyingPredictions": [
                    f"Expected qualifying pace: {list(all_predictions.values())[0].get('predicted_qualifying_pace', 0):.3f}s",
                    "Optimal tire performance on lap 2-3 of qualifying",
                    "Cold track requires gradual tire warm-up"
                ],
                "racePaceForecast": [
                    f"Target race pace: {list(all_predictions.values())[0].get('predicted_race_pace', 0):.3f}s average",
                    f"Tire degradation: {list(all_predictions.values())[0].get('predicted_tire_degradation_per_lap', 0):.3f}s per lap",
                    "Consistency key for race distance management"
                ],
                "tireDegradationForecast": [
                    f"30-lap degradation: {list(all_predictions.values())[0].get('predicted_degradation_30_laps', 0):.2f}s total",
                    "Monitor for graining in cold conditions"
                ],
                "keyPerformanceIndicators": [
                    "Lap time consistency",
                    "Tire management",
                    "Fuel efficiency"
                ],
                "strategicRecommendations": [
                    "Primary strategy: Monitor degradation for pit decision",
                    "Focus on smooth inputs for tire preservation",
                    "Adapt to changing track conditions"
                ]
            }
        
        return {
            "track": track,
            "predictions": all_predictions,
            "ai_analysis": ai_data,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error generating pre-event predictions: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/post-event-analysis")
async def analyze_post_event_data(
    file: UploadFile = File(...),
    track: Optional[str] = Query(None),
    race: Optional[str] = Query(None)
) -> Dict[str, Any]:
    """
    Post-Event Analysis: Upload post-race data and get comprehensive analysis 
    revealing key moments and strategic decisions.
    """
    try:
        # Create uploads directory
        upload_dir = Path("uploads")
        upload_dir.mkdir(exist_ok=True)
        
        # Save uploaded file
        file_path = upload_dir / f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{file.filename}"
        content = await file.read()
        with open(file_path, "wb") as f:
            f.write(content)
        
        # Load and parse CSV
        try:
            df = pd.read_csv(file_path)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Could not parse CSV: {str(e)}")
        
        # Analyze data
        analysis = {
            "file_name": file.filename,
            "rows_analyzed": len(df),
            "columns": list(df.columns),
            "timestamp": datetime.now().isoformat()
        }
        
        # Key moments detection
        key_moments = []
        
        # Detect fastest lap
        if 'lap_time' in df.columns:
            fastest_lap_idx = df['lap_time'].idxmin()
            key_moments.append({
                "type": "fastest_lap",
                "lap": int(df.loc[fastest_lap_idx, 'lap']) if 'lap' in df.columns else "unknown",
                "time": float(df.loc[fastest_lap_idx, 'lap_time']),
                "description": "Fastest lap of the race"
            })
        
        # Detect pit stops (large time gaps)
        if 'lap_time' in df.columns:
            df_sorted = df.sort_values('lap' if 'lap' in df.columns else df.index)
            time_diffs = df_sorted['lap_time'].diff()
            pit_stops = df_sorted[time_diffs > df_sorted['lap_time'].quantile(0.9)]
            for idx, row in pit_stops.iterrows():
                key_moments.append({
                    "type": "pit_stop",
                    "lap": int(row['lap']) if 'lap' in row else "unknown",
                    "description": f"Potential pit stop detected"
                })
        
        # Generate AI race story
        prompt = f"""
You are a motorsports journalist analyzing a race and telling its story.

TRACK: {track or 'Unknown'}
RACE: {race or 'Unknown'}
DATA ANALYSIS: {json.dumps(analysis, indent=2)}
KEY MOMENTS: {json.dumps(key_moments, indent=2)}
SAMPLE DATA: {df.head(10).to_dict('records')}

Tell the story of this race:
1. Race narrative (beginning, middle, end)
2. Key strategic decisions
3. Critical moments that defined the outcome
4. Performance highlights
5. Lessons learned

Format as JSON with keys: raceNarrative, strategicDecisions, criticalMoments, performanceHighlights, lessonsLearned
"""
        
        ai_story = await generate_ai_insights(prompt)
        
        try:
            ai_data = json.loads(ai_story)
        except:
            ai_data = {
                "story": ai_story,
                "raceNarrative": ["Race data analyzed and story generated"],
                "strategicDecisions": ["Review key moments for strategic insights"],
                "criticalMoments": key_moments,
                "performanceHighlights": ["Check fastest lap and key moments"],
                "lessonsLearned": ["Analyze data patterns for improvements"]
            }
        
        return {
            "file_name": file.filename,
            "track": track,
            "race": race,
            "data_analysis": analysis,
            "key_moments": key_moments,
            "ai_story": ai_data
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error analyzing post-event data: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/post-event-analysis/{track}/{race}")
async def get_post_event_analysis(
    track: str,
    race: str
) -> Dict[str, Any]:
    """
    Post-Event Analysis: Analyze existing race data and generate comprehensive report.
    """
    try:
        # Load race data
        start, end, lapt = load_lap_times(settings.dataset_root, track, race)
        df_telemetry = load_race_telemetry_wide(settings.dataset_root, track, race)
        
        if lapt.empty:
            raise HTTPException(status_code=404, detail=f"No data for {track} {race}")
        
        # Sort by vehicle and lap
        lapt = lapt.sort_values(["vehicle_id", "lap"]).reset_index(drop=True)
        
        # Calculate lap_time from timestamps only if not present
        if 'lap_time' not in lapt.columns and 'timestamp' in lapt.columns:
            lapt['lap_time'] = lapt.groupby("vehicle_id")["timestamp"].diff().dt.total_seconds()
            
        # Filter out invalid lap times (negative or zero)
        if 'lap_time' in lapt.columns:
            lapt = lapt[lapt['lap_time'] > 0]
        
        # Race summary
        if lapt.empty:
             raise HTTPException(status_code=404, detail=f"No valid lap data for {track} {race}")

        total_laps = int(lapt['lap'].max())
        total_vehicles = lapt['vehicle_id'].nunique()
        
        # Key moments
        key_moments = []
        
        # Fastest lap (excluding NaN values from lap_time calculation)
        valid_laps = lapt[lapt['lap_time'].notna()]
        if not valid_laps.empty:
            fastest_lap = valid_laps.loc[valid_laps['lap_time'].idxmin()]
            key_moments.append({
                "type": "fastest_lap",
                "vehicle": str(fastest_lap['vehicle_id']),
                "lap": int(fastest_lap['lap']),
                "time": float(fastest_lap['lap_time']),
                "description": f"Fastest lap by {fastest_lap['vehicle_id']}"
            })
        
        # Generate AI race story
        prompt = f"""
You are a motorsports journalist analyzing a race.
TRACK: {track}
RACE: {race}
TOTAL LAPS: {total_laps}
VEHICLES: {total_vehicles}
KEY MOMENTS: {json.dumps(key_moments, indent=2)}
SAMPLE LAP DATA: {lapt.head(20).to_dict('records')}

Analyze the race and provide a JSON response with the following structure:
{{
    "raceNarrative": "A string containing the race story...",
    "strategicDecisions": ["List of key strategic decisions..."],
    "criticalMoments": ["List of critical moments..."],
    "performanceHighlights": ["List of performance highlights..."],
    "lessonsLearned": ["List of lessons learned..."]
}}
Ensure the response is valid JSON. Do not include markdown formatting like ```json.
"""
        
        ai_story = await generate_ai_insights(prompt)
        
        try:
            ai_data = json.loads(ai_story)
        except:
            ai_data = {
                "story": ai_story,
                "raceNarrative": ["Race data analyzed"],
                "strategicDecisions": ["Review race data for strategic insights"],
                "criticalMoments": key_moments,
                "performanceHighlights": ["Check fastest lap and key moments"],
                "lessonsLearned": ["Analyze data patterns for improvements"]
            }
        
        return {
            "track": track,
            "race": race,
            "race_summary": {
                "total_laps": total_laps,
                "total_vehicles": total_vehicles,
                "fastest_lap_time": float(lapt['lap_time'].min())
            },
            "key_moments": key_moments,
            "ai_story": ai_data
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error analyzing post-event: {e}")
        raise HTTPException(status_code=500, detail=str(e))
