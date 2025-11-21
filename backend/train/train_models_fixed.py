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
        
        if self.feature_columns:
            X = X[self.feature_columns]
        
        return self.model.predict(X)

    def save_model(self, filepath: str):
        """Save the trained model"""
        if not self.is_trained:
            raise ValueError("No trained model to save")
        
        model_data = {
            'model': self.model,
            'feature_columns': self.feature_columns,
            'is_trained': self.is_trained
        }
        
        with open(filepath, 'wb') as f:
            pickle.dump(model_data, f)
        
        logger.info(f"Model saved to {filepath}")

    def load_model(self, filepath: str):
        """Load a trained model"""
        with open(filepath, 'rb') as f:
            model_data = pickle.load(f)
        
        self.model = model_data['model']
        self.feature_columns = model_data['feature_columns']
        self.is_trained = model_data['is_trained']
        
        logger.info(f"Model loaded from {filepath}")


def load_lap_times_from_api(track: str, race: str) -> pd.DataFrame:
    """Load lap times from the API endpoint"""
    try:
        # Get list of vehicles first
        response = requests.get(f"{API_BASE}/laps", params={"track": track, "race": race})
        response.raise_for_status()
        
        vehicles_data = response.json()
        vehicles = list(vehicles_data.get("laps_by_vehicle", {}).keys())
        
        if not vehicles:
            logger.warning(f"No vehicles found for {track} {race}")
            return pd.DataFrame()
        
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
            logger.info(f"Loaded {len(combined_df)} lap records for {track} {race}")
            return combined_df
        else:
            return pd.DataFrame()
            
    except Exception as e:
        logger.error(f"Error loading lap times from API: {e}")
        return pd.DataFrame()


def train_models_for_tracks():
    """Train models for each track using API data"""
    try:
        # Available tracks and races
        tracks_races = [
            ("barber", "R1"),
            ("barber", "R2"), 
            ("indianapolis", "R1"),
            ("indianapolis", "R2"),
            ("COTA", "R1"),
            ("COTA", "R2")
        ]
        
        # Create models directory
        os.makedirs("models", exist_ok=True)
        
        all_data = []
        
        # Collect training data from all tracks
        for track, race in tracks_races:
            logger.info(f"Loading data for {track} {race}...")
            
            lap_data = load_lap_times_from_api(track, race)
            if not lap_data.empty:
                lap_data['track'] = track
                lap_data['race'] = race
                all_data.append(lap_data)
                logger.info(f"Added {len(lap_data)} samples from {track} {race}")
            else:
                logger.warning(f"No data loaded for {track} {race}")
        
        if not all_data:
            logger.error("No training data available")
            return
        
        # Combine all data
        combined_data = pd.concat(all_data, ignore_index=True)
        logger.info(f"Total training data: {len(combined_data)} samples")
        
        # Create predictor and prepare features
        predictor = SimpleLapTimePredictor()
        
        # Create features
        feature_data = predictor.create_features(combined_data)
        
        if feature_data.empty:
            logger.error("No valid features created")
            return
        
        # Separate features and target
        y = feature_data['lap_time']
        X = feature_data.drop('lap_time', axis=1)
        
        logger.info(f"Training with {len(X)} samples and {len(X.columns)} features")
        logger.info(f"Features: {list(X.columns)}")
        
        # Train the model
        metrics = predictor.train(X, y)
        
        # Save the model
        model_path = "models/lap_time_predictor.pkl"
        predictor.save_model(model_path)
        
        # Save training summary
        summary = {
            'training_metrics': metrics,
            'tracks_used': [f"{track}_{race}" for track, race in tracks_races if any(
                (d['track'] == track and d['race'] == race) for d in all_data)],
            'total_samples': len(combined_data),
            'feature_samples': len(X),
            'features': list(X.columns)
        }
        
        with open("models/training_summary.json", "w") as f:
            json.dump(summary, f, indent=2)
        
        logger.info("Training completed successfully!")
        logger.info(f"Model saved to: {model_path}")
        logger.info(f"Summary saved to: models/training_summary.json")
        
        return predictor, metrics
        
    except Exception as e:
        logger.error(f"Error in training pipeline: {e}")
        raise


if __name__ == "__main__":
    logger.info("Starting ML model training...")
    try:
        predictor, metrics = train_models_for_tracks()
        logger.info("Training pipeline completed successfully!")
    except Exception as e:
        logger.error(f"Training failed: {e}")
        sys.exit(1)
