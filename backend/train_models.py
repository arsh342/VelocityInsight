#!/usr/bin/env python3
"""
Standalone script to train ML models for lap time prediction.
This script can be run independently to train models on available race data.
"""

import sys
import os
from pathlib import Path
import pandas as pd
import numpy as np
import logging
import pickle
import requests
import json
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import xgboost as xgb

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# API base URL
API_BASE = "http://localhost:8000"


class SimpleLapTimePredictor:
    """Simple lap time predictor using XGBoost"""
    
    def __init__(self):
        self.model = None
        self.feature_columns = None
        self.is_trained = False
        
    def create_features(self, lap_data: pd.DataFrame) -> pd.DataFrame:
        """Create simple features from lap time data"""
        features = []
        
        for vehicle_id in lap_data['vehicle_id'].unique():
            vehicle_laps = lap_data[lap_data['vehicle_id'] == vehicle_id].sort_values('timestamp')
            
            for i, (_, lap) in enumerate(vehicle_laps.iterrows()):
                if pd.isna(lap['lap_time']) or lap['lap_time'] <= 0 or lap['lap_time'] > 200:
                    continue
                    
                feature_row = {
                    'lap_time': lap['lap_time'],
                    'lap_number': lap.get('lap', i + 1),
                    'tire_age': i + 1,  # Simple tire age approximation
                    'vehicle_encoded': hash(str(vehicle_id)) % 100,  # Simple vehicle encoding
                }
                
                # Add previous lap time if available
                if i > 0:
                    prev_lap = vehicle_laps.iloc[i-1]
                    feature_row['prev_lap_time'] = prev_lap.get('lap_time', lap['lap_time'])
                    feature_row['lap_time_delta'] = lap['lap_time'] - prev_lap.get('lap_time', lap['lap_time'])
                else:
                    feature_row['prev_lap_time'] = lap['lap_time']
                    feature_row['lap_time_delta'] = 0
                
                # Add rolling averages if we have enough data
                if i >= 2:
                    recent_laps = vehicle_laps.iloc[max(0, i-2):i]['lap_time'].dropna()
                    if len(recent_laps) > 0:
                        feature_row['avg_recent_laptime'] = recent_laps.mean()
                        feature_row['std_recent_laptime'] = recent_laps.std() if len(recent_laps) > 1 else 0
                    else:
                        feature_row['avg_recent_laptime'] = lap['lap_time']
                        feature_row['std_recent_laptime'] = 0
                else:
                    feature_row['avg_recent_laptime'] = lap['lap_time']
                    feature_row['std_recent_laptime'] = 0
                
                features.append(feature_row)
        
        return pd.DataFrame(features)


def load_lap_times_from_api(track: str, race: str) -> pd.DataFrame:
    """Load lap times from the API endpoint, with fallback to direct dataset loading"""
    try:
        # Get list of vehicles first
        response = requests.get(f"{API_BASE}/laps", params={"track": track, "race": race})
        response.raise_for_status()
        
        vehicles_data = response.json()
        vehicles = list(vehicles_data.get("laps_by_vehicle", {}).keys())
        
        if not vehicles:
            logger.warning(f"No vehicles found via API for {track} {race}, trying direct file load")
            return load_lap_times_from_files(track, race)
        
        # Get lap times for all vehicles
        all_lap_times = []
        
        for vehicle_id in vehicles[:5]:  # Limit to first 5 vehicles for faster training
            try:
                response = requests.get(f"{API_BASE}/laps/times", params={
                    "track": track, 
                    "race": race, 
                    "vehicle_id": vehicle_id
                })
                response.raise_for_status()
                
                data = response.json()
                lap_times = data.get("lap_times", [])
                
                # Convert to DataFrame
                df = pd.DataFrame(lap_times)
                if not df.empty and 'lap_time' in df.columns:
                    df['vehicle_id'] = vehicle_id
                    all_lap_times.append(df)
                    
            except Exception as e:
                logger.warning(f"Error loading data for vehicle {vehicle_id}: {e}")
                continue
        
        if all_lap_times:
            combined_df = pd.concat(all_lap_times, ignore_index=True)
            logger.info(f"Loaded {len(combined_df)} lap records for {track} {race} from API")
            return combined_df
        else:
            logger.warning(f"No lap times retrieved from API for {track} {race}, trying direct file load")
            return load_lap_times_from_files(track, race)
            
    except Exception as e:
        logger.error(f"Error loading lap times from API: {e}, trying direct file load")
        return load_lap_times_from_files(track, race)


def load_lap_times_from_files(track: str, race: str) -> pd.DataFrame:
    """Load lap times directly from dataset files"""
    try:
        dataset_root = Path("../dataset")
        track_dir = dataset_root / track
        
        # Handle different naming conventions across tracks
        if track.lower() == "barber":
            lapt = pd.read_csv(track_dir / f"{race}_barber_lap_time.csv")
        elif track.lower() == "indianapolis":
            prefix = "indianapolis_motor_speedway"
            lapt = pd.read_csv(track_dir / f"{race}_{prefix}_lap_time.csv")
        elif track.lower() == "cota":
            race_folder = "Race 1" if race.upper() == "R1" else "Race 2"
            sub = track_dir / race_folder
            lapt = pd.read_csv(sub / f"COTA_lap_time_{race}.csv")
        elif track.lower() == "vir":
            race_folder = "Race 1" if race.upper() == "R1" else "Race 2"
            sub = track_dir / race_folder
            lapt = pd.read_csv(sub / f"vir_lap_time_{race}.csv")
        elif track.lower() == "road america":
            race_folder = "Race 1" if race.upper() == "R1" else "Race 2"
            sub = track_dir / race_folder
            lapt = pd.read_csv(sub / f"road_america_lap_time_{race}.csv")
        elif track.lower() == "sebring":
            race_folder = "Race 1" if race.upper() == "R1" else "Race 2"
            sub = track_dir / race_folder
            lapt = pd.read_csv(sub / f"Sebring_lap_time_{race}.csv")
        elif track.lower() == "sonoma":
            race_folder = "Race 1" if race.upper() == "R1" else "Race 2"
            sub = track_dir / race_folder
            lapt = pd.read_csv(sub / f"sonoma_lap_time_{race}.csv")
        else:
            raise ValueError(f"Unsupported track: {track}")
        
        # Normalize columns
        lapt.columns = [c.strip() for c in lapt.columns]
        
        if "timestamp" in lapt.columns:
            lapt["timestamp"] = pd.to_datetime(lapt["timestamp"], errors="coerce", utc=True)
        
        # Calculate lap_time from consecutive timestamps (same as API does)
        lapt = lapt.sort_values(["vehicle_id", "lap"]).reset_index(drop=True)
        lapt["lap_time"] = lapt.groupby("vehicle_id")["timestamp"].diff().dt.total_seconds()
        
        logger.info(f"Loaded {len(lapt)} lap records for {track} {race} from files")
        return lapt
        
    except Exception as e:
        logger.error(f"Error loading lap times from files for {track} {race}: {e}")
        return pd.DataFrame()



class SimpleLapTimePredictor:
    """Simple lap time predictor using XGBoost"""
    
    def __init__(self):
        self.model = None
        self.feature_columns = None
        self.is_trained = False
        
    def create_features(self, lap_data: pd.DataFrame) -> pd.DataFrame:
        """Create simple features from lap time data"""
        features = []
        
        for vehicle_id in lap_data['vehicle_id'].unique():
            vehicle_laps = lap_data[lap_data['vehicle_id'] == vehicle_id].sort_values('timestamp')
            
            for i, (_, lap) in enumerate(vehicle_laps.iterrows()):
                if pd.isna(lap['lap_time']) or lap['lap_time'] <= 0 or lap['lap_time'] > 200:
                    continue
                    
                feature_row = {
                    'lap_time': lap['lap_time'],
                    'lap_number': lap.get('lap', i + 1),
                    'tire_age': i + 1,  # Simple tire age approximation
                    'vehicle_encoded': hash(str(vehicle_id)) % 100,  # Simple vehicle encoding
                }
                
                # Add previous lap time if available
                if i > 0:
                    prev_lap = vehicle_laps.iloc[i-1]
                    feature_row['prev_lap_time'] = prev_lap.get('lap_time', lap['lap_time'])
                    feature_row['lap_time_delta'] = lap['lap_time'] - prev_lap.get('lap_time', lap['lap_time'])
                else:
                    feature_row['prev_lap_time'] = lap['lap_time']
                    feature_row['lap_time_delta'] = 0
                
                # Add rolling averages if we have enough data
                if i >= 2:
                    recent_laps = vehicle_laps.iloc[max(0, i-2):i]['lap_time'].dropna()
                    if len(recent_laps) > 0:
                        feature_row['avg_recent_laptime'] = recent_laps.mean()
                        feature_row['std_recent_laptime'] = recent_laps.std() if len(recent_laps) > 1 else 0
                    else:
                        feature_row['avg_recent_laptime'] = lap['lap_time']
                        feature_row['std_recent_laptime'] = 0
                else:
                    feature_row['avg_recent_laptime'] = lap['lap_time']
                    feature_row['std_recent_laptime'] = 0
                
                features.append(feature_row)
        
        return pd.DataFrame(features)

    def train(self, X: pd.DataFrame, y: pd.Series) -> dict:
        """Train the XGBoost model"""
        try:
            # Store feature columns
            self.feature_columns = X.columns.tolist()
            
            # Split data
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.2, random_state=42
            )
            
            # Train XGBoost model
            self.model = xgb.XGBRegressor(
                n_estimators=100,
                max_depth=6,
                learning_rate=0.1,
                random_state=42,
                n_jobs=-1
            )
            
            logger.info(f"Training model with {len(X_train)} samples, {len(X.columns)} features")
            self.model.fit(X_train, y_train)
            
            # Evaluate
            y_pred = self.model.predict(X_test)
            
            metrics = {
                'mae': mean_absolute_error(y_test, y_pred),
                'rmse': np.sqrt(mean_squared_error(y_test, y_pred)),
                'r2': r2_score(y_test, y_pred),
                'train_samples': len(X_train),
                'test_samples': len(X_test),
                'features': len(X.columns)
            }
            
            self.is_trained = True
            
            logger.info(f"Training completed. MAE: {metrics['mae']:.3f}, RMSE: {metrics['rmse']:.3f}, R²: {metrics['r2']:.3f}")
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error training model: {e}")
            raise
    
    def predict(self, X: pd.DataFrame) -> np.ndarray:
        """Make predictions"""
        if not self.is_trained or self.model is None:
            raise ValueError("Model not trained")
        
        # Ensure feature columns match
        if list(X.columns) != self.feature_columns:
            logger.warning("Feature columns don't match training data")
            X = X[self.feature_columns]
        
        return self.model.predict(X)
    
    def save(self, filepath: str):
        """Save the trained model"""
        if not self.is_trained:
            raise ValueError("Model not trained")
        
        model_data = {
            'model': self.model,
            'feature_columns': self.feature_columns,
            'is_trained': self.is_trained
        }
        
        with open(filepath, 'wb') as f:
            pickle.dump(model_data, f)
        
        logger.info(f"Model saved to {filepath}")
    
    def load(self, filepath: str):
        """Load a trained model"""
        with open(filepath, 'rb') as f:
            model_data = pickle.load(f)
        
        self.model = model_data['model']
        self.feature_columns = model_data['feature_columns']
        self.is_trained = model_data['is_trained']
        
        logger.info(f"Model loaded from {filepath}")


def train_models_for_tracks():
    """Train lap time prediction models for all available tracks"""
    
    # Create models directory
    models_dir = Path("models")
    models_dir.mkdir(exist_ok=True)
    
    # Available tracks to train on (expanded with Road America, Sonoma, VIR)
    tracks = ["barber", "indianapolis", "COTA", "road america", "sonoma", "VIR"]
    races = ["R1", "R2"]
    
    for track in tracks:
        logger.info(f"Training model for {track}")
        
        try:
            # Collect training data from all races for this track
            all_features = []
            predictor = SimpleLapTimePredictor()  # Create predictor once
            
            for race in races:
                try:
                    logger.info(f"Loading {track} {race} data...")
                    lapt = load_lap_times_from_api(track, race)
                    
                    if lapt.empty:
                        logger.warning(f"No lap data for {track} {race}")
                        continue
                    
                    # Create features
                    features = predictor.create_features(lapt)
                    
                    if not features.empty:
                        all_features.append(features)
                        logger.info(f"Added {len(features)} samples from {track} {race}")
                    
                except Exception as e:
                    logger.error(f"Error processing {track} {race}: {e}")
                    continue
            
            if not all_features:
                logger.warning(f"No training data available for {track}")
                continue
            
            # Combine all features
            combined_features = pd.concat(all_features, ignore_index=True)
            logger.info(f"Total training samples for {track}: {len(combined_features)}")
            
            # Prepare training data
            X = combined_features.drop(['lap_time'], axis=1)
            y = combined_features['lap_time']
            
            # Train model (use the same predictor object)
            metrics = predictor.train(X, y)
            
            # Save model
            model_path = models_dir / f"lap_time_predictor_{track}.pkl"
            predictor.save(str(model_path))
            
            logger.info(f"✅ {track} model training completed!")
            logger.info(f"   MAE: {metrics['mae']:.3f}s")
            logger.info(f"   RMSE: {metrics['rmse']:.3f}s")
            logger.info(f"   R²: {metrics['r2']:.3f}")
            logger.info(f"   Training samples: {metrics['train_samples']}")
            
        except Exception as e:
            logger.error(f"❌ Failed to train model for {track}: {e}")
            continue
    
    logger.info("🎉 Model training process completed!")


if __name__ == "__main__":
    logger.info("Starting ML model training...")
    train_models_for_tracks()
