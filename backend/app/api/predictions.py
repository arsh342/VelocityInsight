"""
API endpoints for lap time predictions using XGBoost model
"""
from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import Dict, Optional, List
import logging
import os
import pandas as pd
from pathlib import Path

from ..ml.lap_time_predictor import get_lap_time_predictor, LapTimePredictor
from ..data.lap_segmenter import get_lap_segmenter
from ..data.feature_engine import get_feature_engine
from ..data.loader import load_lap_times, load_race_telemetry_wide
from ..core.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/predictions", tags=["predictions"])


@router.get("/laptime/{track}/{race}/{vehicle_id}")
async def predict_lap_time(
    track: str,
    race: str,
    vehicle_id: str,
    lap_number: Optional[int] = None
):
    """
    Predict lap time for a vehicle based on telemetry features.
    Prefers offline trained models for all tracks.
    
    Args:
        track: Track name (e.g., 'barber')
        race: Race identifier (e.g., 'R1')
        vehicle_id: Vehicle identifier
        lap_number: Specific lap to predict (default: latest)
    
    Returns:
        Predicted lap time and confidence metrics
    """
    try:
        # Normalize track name for model file lookup
        # The model files use title case for multi-word tracks
        normalized_track = track.title() if " " in track.lower() else track.lower()
        
        # Try to load offline model - this is now the preferred path
        model_path = Path("models") / f"lap_time_predictor_{normalized_track}.pkl"
        
        if not model_path.exists():
            logger.warning(f"Model not found at {model_path}")
            return {
                "vehicle_id": vehicle_id,
                "track": track,
                "race": race,
                "lap_number": lap_number or "latest",
                "predicted_lap_time": None,
                "confidence": 0.0,
                "status": "model_not_available",
                "message": f"ML model for {track} not found. Run /predictions/laptime/train/{track} to train.",
                "error": f"Missing model file: {model_path}"
            }
        
        # Load the offline model
        predictor = get_lap_time_predictor(str(model_path))
        
        # Load lap data with error handling
        try:
            segmenter = get_lap_segmenter(str(settings.dataset_root))
            engine = get_feature_engine()
            
            lap_data = segmenter.segment_by_lap(track, race, vehicle_id)
            
            if not lap_data:
                raise HTTPException(status_code=404, detail="No lap data found for vehicle")
        except Exception as e:
            logger.error(f"Error loading lap data: {e}")
            raise HTTPException(status_code=500, detail=f"Error processing lap data: {str(e)}")
        
        # Use specified lap or latest
        if lap_number is None:
            lap_number = max(lap_data.keys())
        
        if lap_number not in lap_data:
            raise HTTPException(status_code=404, detail=f"Lap {lap_number} not found")
        
        # Calculate features
        features = engine.calculate_lap_features(
            lap_data[lap_number],
            tire_age=lap_number
        )
        
        # Predict
        predicted_time = predictor.predict(features)
        
        # Get actual time if available
        try:
            df_laps = segmenter.load_lap_boundaries(track, race, vehicle_id)
            actual_time = None
            if lap_number <= len(df_laps):
                actual_time = df_laps.iloc[lap_number - 1]['lap_time_seconds']
        except:
            actual_time = None
        
        return {
            "vehicle_id": vehicle_id,
            "track": track,
            "race": race,
            "lap_number": lap_number,
            "predicted_lap_time": round(predicted_time, 3),
            "actual_lap_time": round(float(actual_time), 3) if actual_time else None,
            "error": round(abs(predicted_time - actual_time), 3) if actual_time else None,
            "model_source": "offline",
            "model_path": str(model_path),
            "status": "success",
            "features": {
                "avg_throttle": round(features.get('avg_throttle', 0), 2),
                "avg_brake_pressure": round(features.get('avg_brake_pressure', 0), 2),
                "max_g_force": round(features.get('max_g_force', 0), 2),
                "tire_age": features.get('tire_age', 0)
            }
        }
        
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error predicting lap time: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/laptime/train/{track}/{race}")
async def train_lap_predictor(
    track: str,
    race: str
):
    """
    Train XGBoost lap time predictor on specified track/race data.
    
    Args:
        track: Track name
        race: Race identifier
    
    Returns:
        Training metrics and model performance
    """
    try:
        predictor = get_lap_time_predictor()
        
        # Prepare training data (use first 5 vehicles)
        X, y, feature_names = predictor.prepare_training_data(
            track=track,
            race=race,
            vehicle_ids=None,
            data_dir="../dataset"
        )
        
        # Train model
        metrics = predictor.train(X, y, feature_names)
        
        # Save model
        model_path = f"models/lap_time_predictor_{track}.pkl"
        predictor.save_model(model_path)
        
        # Get feature importance
        importance = predictor.get_feature_importance(top_n=10)
        
        return {
            "status": "success",
            "track": track,
            "race": race,
            "model_path": model_path,
            "metrics": metrics,
            "top_features": importance
        }
        
    except Exception as e:
        logger.error(f"Error training model: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/laptime/next/{track}/{race}/{vehicle_id}")
async def predict_next_lap(
    track: str,
    race: str,
    vehicle_id: str
):
    """
    Predict the next lap time based on most recent lap telemetry.
    Uses offline trained model for the track.
    
    Returns:
        Prediction for upcoming lap
    """
    try:
        # Normalize track name for model file lookup
        # The model files use title case for multi-word tracks
        normalized_track = track.title() if " " in track.lower() else track.lower()
        
        # Try to load offline model - prefer this
        model_path = Path("models") / f"lap_time_predictor_{normalized_track}.pkl"
        
        if not model_path.exists():
            logger.warning(f"Model not found at {model_path}")
            return {
                "status": "model_not_available",
                "message": f"ML model for {track} not found. Run /predictions/laptime/train/{track} to train.",
                "vehicle_id": vehicle_id,
                "track": track,
                "race": race
            }
        
        predictor = get_lap_time_predictor(str(model_path))
        segmenter = get_lap_segmenter(str(settings.dataset_root))
        engine = get_feature_engine()
        
        # Get latest lap
        lap_data = segmenter.segment_by_lap(track, race, vehicle_id)
        latest_lap = max(lap_data.keys())
        
        # Calculate features from latest lap
        features = engine.calculate_lap_features(
            lap_data[latest_lap],
            tire_age=latest_lap + 1  # Next lap will be +1 tire age
        )
        
        predicted_time = predictor.predict(features)
        
        # Get recent lap times for context
        df_laps = segmenter.load_lap_boundaries(track, race, vehicle_id)
        recent_laps = df_laps.tail(5)['lap_time_seconds'].tolist()
        
        return {
            "vehicle_id": vehicle_id,
            "track": track,
            "race": race,
            "current_lap": latest_lap,
            "next_lap": latest_lap + 1,
            "predicted_next_lap_time": round(predicted_time, 3),
            "model_source": "offline",
            "model_path": str(model_path),
            "recent_lap_times": [round(float(t), 3) for t in recent_laps],
            "avg_recent_laps": round(sum(recent_laps) / len(recent_laps), 3),
            "predicted_delta_vs_avg": round(predicted_time - (sum(recent_laps) / len(recent_laps)), 3),
            "status": "success"
        }
        
    except Exception as e:
        logger.error(f"Error predicting next lap: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/laptime/train/{track}")
async def train_lap_time_model(
    track: str,
    background_tasks: BackgroundTasks,
    races: Optional[str] = "R1,R2"  # Comma-separated list of races
):
    """
    Train a lap time prediction model for a specific track.
    This endpoint triggers background training using available race data.
    """
    try:
        # Create models directory if it doesn't exist
        models_dir = Path("models")
        models_dir.mkdir(exist_ok=True)
        
        race_list = races.split(",") if races else ["R1", "R2"]
        
        # Start training in background
        background_tasks.add_task(
            train_model_background, 
            track, 
            race_list
        )
        
        return {
            "status": "training_started",
            "track": track,
            "races": race_list,
            "message": f"Model training started for {track}. Check /predictions/laptime/train/{track}/status for progress.",
            "model_path": f"models/lap_time_predictor_{track}.pkl"
        }
        
    except Exception as e:
        logger.error(f"Error starting model training: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to start training: {str(e)}")


async def train_model_background(track: str, races: List[str]):
    """Background task to train the lap time model"""
    try:
        logger.info(f"Starting background training for {track} with races {races}")
        
        # Initialize predictor
        predictor = LapTimePredictor()
        
        # Collect training data from all races
        all_features = []
        all_targets = []
        
        for race in races:
            try:
                logger.info(f"Loading data for {track} {race}")
                
                # Load basic lap time data
                start, end, lapt = load_lap_times(settings.dataset_root, track, race)
                
                if lapt.empty:
                    logger.warning(f"No lap data for {track} {race}")
                    continue
                
                # Create simple features from lap times
                features_df = create_simple_features(lapt)
                
                if not features_df.empty:
                    all_features.append(features_df)
                    logger.info(f"Added {len(features_df)} training samples from {track} {race}")
                    
            except Exception as e:
                logger.error(f"Error loading data for {track} {race}: {e}")
                continue
        
        if not all_features:
            logger.error(f"No training data available for {track}")
            return
            
        # Combine all features
        combined_features = pd.concat(all_features, ignore_index=True)
        logger.info(f"Total training samples: {len(combined_features)}")
        
        # Train the model
        X = combined_features.drop(['lap_time'], axis=1)
        y = combined_features['lap_time']
        
        # Train the model with the collected data
        metrics = predictor.train_model(X, y)
        
        # Save the trained model
        model_path = f"models/lap_time_predictor_{track}.pkl"
        predictor.save_model(model_path)
        
        logger.info(f"Model training completed for {track}. MAE: {metrics.get('mae', 'N/A')}")
        
    except Exception as e:
        logger.error(f"Background training failed for {track}: {e}")


def create_simple_features(lapt: pd.DataFrame) -> pd.DataFrame:
    """Create simple features from lap time data for training"""
    try:
        features = []
        
        for vehicle_id in lapt['vehicle_id'].unique():
            vehicle_laps = lapt[lapt['vehicle_id'] == vehicle_id].sort_values('timestamp')
            
            for i, (_, lap) in enumerate(vehicle_laps.iterrows()):
                if pd.isna(lap['lap_time']) or lap['lap_time'] <= 0:
                    continue
                    
                feature_row = {
                    'lap_time': lap['lap_time'],
                    'lap_number': lap.get('lap', i + 1),
                    'tire_age': i + 1,  # Simple tire age approximation
                    'vehicle_id_encoded': hash(vehicle_id) % 1000,  # Simple encoding
                    'sector1': lap.get('sector1', lap['lap_time'] * 0.3),  # Rough sector approximation
                    'sector2': lap.get('sector2', lap['lap_time'] * 0.4),
                    'sector3': lap.get('sector3', lap['lap_time'] * 0.3),
                }
                
                # Add previous lap time as feature if available
                if i > 0:
                    prev_lap = vehicle_laps.iloc[i-1]
                    feature_row['prev_lap_time'] = prev_lap.get('lap_time', lap['lap_time'])
                else:
                    feature_row['prev_lap_time'] = lap['lap_time']
                
                features.append(feature_row)
        
        return pd.DataFrame(features)
        
    except Exception as e:
        logger.error(f"Error creating features: {e}")
        return pd.DataFrame()
