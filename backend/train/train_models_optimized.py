#!/usr/bin/env python3
"""
Optimized ML Model Training Script with Hyperparameter Tuning
- Uses Optuna for hyperparameter optimization
- Implements k-fold cross-validation
- Parallel training across tracks
- Enhanced feature engineering
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
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import xgboost as xgb
import lightgbm as lgb
import optuna
from joblib import Parallel, delayed
import warnings

warnings.filterwarnings('ignore')

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Suppress Optuna logging
optuna.logging.set_verbosity(optuna.logging.WARNING)

# API base URL
API_BASE = "http://localhost:8000"


class OptimizedLapTimePredictor:
    """Optimized lap time predictor with hyperparameter tuning"""
    
    def __init__(self, use_optuna=True, n_trials=20):
        self.model = None
        self.feature_columns = None
        self.is_trained = False
        self.use_optuna = use_optuna
        self.n_trials = n_trials
        self.best_params = None
        
    def create_enhanced_features(self, lap_data: pd.DataFrame) -> pd.DataFrame:
        """Create enhanced features with domain knowledge"""
        features = []
        
        for vehicle_id in lap_data['vehicle_id'].unique():
            vehicle_laps = lap_data[lap_data['vehicle_id'] == vehicle_id].sort_values('timestamp')
            
            for i, (_, lap) in enumerate(vehicle_laps.iterrows()):
                if pd.isna(lap['lap_time']) or lap['lap_time'] <= 0 or lap['lap_time'] > 200:
                    continue
                    
                feature_row = {
                    'lap_time': lap['lap_time'],
                    'lap_number': lap.get('lap', i + 1),
                    'tire_age': i + 1,
                    'vehicle_encoded': hash(str(vehicle_id)) % 100,
                }
                
                # Previous lap features
                if i > 0:
                    prev_lap = vehicle_laps.iloc[i-1]
                    feature_row['prev_lap_time'] = prev_lap.get('lap_time', lap['lap_time'])
                    feature_row['lap_time_delta'] = lap['lap_time'] - prev_lap.get('lap_time', lap['lap_time'])
                else:
                    feature_row['prev_lap_time'] = lap['lap_time']
                    feature_row['lap_time_delta'] = 0
                
                # Rolling statistics (3-lap window)
                if i >= 2:
                    recent_laps = vehicle_laps.iloc[max(0, i-2):i]['lap_time'].dropna()
                    if len(recent_laps) > 0:
                        feature_row['avg_recent_laptime'] = recent_laps.mean()
                        feature_row['std_recent_laptime'] = recent_laps.std() if len(recent_laps) > 1 else 0
                        feature_row['min_recent_laptime'] = recent_laps.min()
                        feature_row['max_recent_laptime'] = recent_laps.max()
                    else:
                        feature_row['avg_recent_laptime'] = lap['lap_time']
                        feature_row['std_recent_laptime'] = 0
                        feature_row['min_recent_laptime'] = lap['lap_time']
                        feature_row['max_recent_laptime'] = lap['lap_time']
                else:
                    feature_row['avg_recent_laptime'] = lap['lap_time']
                    feature_row['std_recent_laptime'] = 0
                    feature_row['min_recent_laptime'] = lap['lap_time']
                    feature_row['max_recent_laptime'] = lap['lap_time']
                
                # Tire degradation proxy
                if i > 0:
                    initial_pace = vehicle_laps.iloc[0].get('lap_time', lap['lap_time'])
                    feature_row['pace_degradation'] = lap['lap_time'] - initial_pace
                else:
                    feature_row['pace_degradation'] = 0
                
                # Lap position indicators (early/mid/late race)
                total_laps = len(vehicle_laps)
                feature_row['race_progress'] = (i + 1) / total_laps if total_laps > 0 else 0
                feature_row['is_early_race'] = 1 if (i + 1) <= total_laps * 0.2 else 0
                feature_row['is_mid_race'] = 1 if 0.2 < (i + 1) / total_laps <= 0.8 else 0
                feature_row['is_late_race'] = 1 if (i + 1) > total_laps * 0.8 else 0
                
                # Consistency metrics
                if i >= 4:
                    last_5_laps = vehicle_laps.iloc[max(0, i-4):i]['lap_time'].dropna()
                    if len(last_5_laps) > 1:
                        feature_row['consistency_score'] = last_5_laps.std()
                    else:
                        feature_row['consistency_score'] = 0
                else:
                    feature_row['consistency_score'] = 0
                
                features.append(feature_row)
        
        return pd.DataFrame(features)
    
    def optimize_hyperparameters(self, X, y):
        """Use Optuna to find optimal hyperparameters"""
        
        def objective(trial):
            params = {
                'n_estimators': trial.suggest_int('n_estimators', 100, 500),
                'max_depth': trial.suggest_int('max_depth', 3, 10),
                'learning_rate': trial.suggest_float('learning_rate', 0.01, 0.3, log=True),
                'subsample': trial.suggest_float('subsample', 0.6, 1.0),
                'colsample_bytree': trial.suggest_float('colsample_bytree', 0.6, 1.0),
                'min_child_weight': trial.suggest_int('min_child_weight', 1, 7),
                'gamma': trial.suggest_float('gamma', 0, 0.5),
                'reg_alpha': trial.suggest_float('reg_alpha', 0, 2),
                'reg_lambda': trial.suggest_float('reg_lambda', 0, 2),
                'random_state': 42,
                'n_jobs': -1
            }
            
            model = xgb.XGBRegressor(**params)
            
            # 5-fold cross-validation
            scores = cross_val_score(
                model, X, y, cv=5, 
                scoring='neg_mean_absolute_error',
                n_jobs=-1
            )
            
            return -scores.mean()  # Return positive MAE
        
        study = optuna.create_study(direction='minimize')
        study.optimize(objective, n_trials=self.n_trials, show_progress_bar=False)
        
        self.best_params = study.best_params
        logger.info(f"Best hyperparameters: {self.best_params}")
        logger.info(f"Best CV MAE: {study.best_value:.3f}s")
        
        return self.best_params

    def train(self, X: pd.DataFrame, y: pd.Series) -> dict:
        """Train the XGBoost model with optional hyperparameter tuning"""
        try:
            # Store feature columns
            self.feature_columns = X.columns.tolist()
            
            # Hyperparameter optimization
            if self.use_optuna:
                logger.info("Optimizing hyperparameters...")
                params = self.optimize_hyperparameters(X, y)
                params['random_state'] = 42
                params['n_jobs'] = -1
            else:
                # Default improved parameters
                params = {
                    'n_estimators': 300,
                    'max_depth': 6,
                    'learning_rate': 0.05,
                    'subsample': 0.9,
                    'colsample_bytree': 0.9,
                    'min_child_weight': 3,
                    'gamma': 0.1,
                    'reg_alpha': 0.5,
                    'reg_lambda': 1.0,
                    'random_state': 42,
                    'n_jobs': -1
                }
            
            # Split data
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.2, random_state=42, shuffle=False
            )
            
            # Train model
            self.model = xgb.XGBRegressor(**params)
            
            logger.info(f"Training model with {len(X_train)} samples, {len(X.columns)} features")
            self.model.fit(X_train, y_train)
            
            # Evaluate
            y_pred_train = self.model.predict(X_train)
            y_pred_test = self.model.predict(X_test)
            
            metrics = {
                'train_mae': mean_absolute_error(y_train, y_pred_train),
                'test_mae': mean_absolute_error(y_test, y_pred_test),
                'train_rmse': np.sqrt(mean_squared_error(y_train, y_pred_train)),
                'test_rmse': np.sqrt(mean_squared_error(y_test, y_pred_test)),
                'train_r2': r2_score(y_train, y_pred_train),
                'test_r2': r2_score(y_test, y_pred_test),
                'train_samples': len(X_train),
                'test_samples': len(X_test),
                'features': len(X.columns),
                'hyperparameters': params
            }
            
            self.is_trained = True
            
            logger.info(f"Training completed:")
            logger.info(f"  Train MAE: {metrics['train_mae']:.3f}s | Test MAE: {metrics['test_mae']:.3f}s")
            logger.info(f"  Train RMSE: {metrics['train_rmse']:.3f}s | Test RMSE: {metrics['test_rmse']:.3f}s")
            logger.info(f"  Train R²: {metrics['train_r2']:.3f} | Test R²: {metrics['test_r2']:.3f}")
            
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
            'is_trained': self.is_trained,
            'best_params': self.best_params
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
        self.best_params = model_data.get('best_params')
        
        logger.info(f"Model loaded from {filepath}")


def load_lap_times_from_api(track: str, race: str) -> pd.DataFrame:
    """Load lap times from the API endpoint, with fallback to direct dataset loading"""
    try:
        response = requests.get(f"{API_BASE}/laps", params={"track": track, "race": race})
        response.raise_for_status()
        
        vehicles_data = response.json()
        vehicles = list(vehicles_data.get("laps_by_vehicle", {}).keys())
        
        if not vehicles:
            logger.warning(f"No vehicles found via API for {track} {race}")
            return pd.DataFrame()
        
        all_lap_times = []
        
        for vehicle_id in vehicles[:10]:  # Increased from 5 to 10 for more training data
            try:
                response = requests.get(f"{API_BASE}/laps/times", params={
                    "track": track, 
                    "race": race, 
                    "vehicle_id": vehicle_id
                })
                response.raise_for_status()
                
                data = response.json()
                lap_times = data.get("lap_times", [])
                
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
            return pd.DataFrame()
            
    except Exception as e:
        logger.error(f"Error loading lap times from API: {e}")
        return pd.DataFrame()


def train_single_track(track: str, use_optuna: bool = True, n_trials: int = 20) -> tuple:
    """Train model for a single track"""
    logger.info(f"Training model for {track}")
    
    try:
        races = ["R1", "R2"]
        all_features = []
        predictor = OptimizedLapTimePredictor(use_optuna=use_optuna, n_trials=n_trials)
        
        for race in races:
            try:
                logger.info(f"Loading {track} {race} data...")
                lapt = load_lap_times_from_api(track, race)
                
                if lapt.empty:
                    logger.warning(f"No lap data for {track} {race}")
                    continue
                
                # Create enhanced features
                features = predictor.create_enhanced_features(lapt)
                
                if not features.empty:
                    all_features.append(features)
                    logger.info(f"Added {len(features)} samples from {track} {race}")
                
            except Exception as e:
                logger.error(f"Error processing {track} {race}: {e}")
                continue
        
        if not all_features:
            logger.warning(f"No training data available for {track}")
            return (track, None, None)
        
        # Combine all features
        combined_features = pd.concat(all_features, ignore_index=True)
        logger.info(f"Total training samples for {track}: {len(combined_features)}")
        
        # Prepare training data
        X = combined_features.drop(['lap_time'], axis=1)
        y = combined_features['lap_time']
        
        # Train model
        metrics = predictor.train(X, y)
        
        return (track, predictor, metrics)
        
    except Exception as e:
        logger.error(f"Failed to train model for {track}: {e}")
        return (track, None, None)


def train_models_parallel(use_optuna: bool = True, n_trials: int = 20, n_jobs: int = 2):
    """Train lap time prediction models for all tracks in parallel"""
    
    # Create models directory
    models_dir = Path("models")
    models_dir.mkdir(exist_ok=True)
    
    tracks = ["barber", "indianapolis", "COTA", "road america", "sonoma", "VIR"]
    
    logger.info(f"Training models for {len(tracks)} tracks in parallel ({n_jobs} jobs)")
    logger.info(f"Hyperparameter optimization: {'ON' if use_optuna else 'OFF'}")
    
    # Train models in parallel
    results = Parallel(n_jobs=n_jobs)(
        delayed(train_single_track)(track, use_optuna, n_trials) 
        for track in tracks
    )
    
    # Save models and display results
    for track, predictor, metrics in results:
        if predictor is not None and metrics is not None:
            # Save model
            model_path = models_dir / f"lap_time_predictor_{track}.pkl"
            predictor.save(str(model_path))
            
            logger.info(f"✅ {track} model training completed!")
            logger.info(f"   Test MAE: {metrics['test_mae']:.3f}s")
            logger.info(f"   Test RMSE: {metrics['test_rmse']:.3f}s")
            logger.info(f"   Test R²: {metrics['test_r2']:.3f}")
            logger.info(f"   Features: {metrics['features']}")
        else:
            logger.info(f"❌ {track} model training failed")
    
    logger.info("🎉 Model training process completed!")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Train optimized ML models")
    parser.add_argument('--no-optuna', action='store_true', help='Disable hyperparameter optimization')
    parser.add_argument('--trials', type=int, default=20, help='Number of Optuna trials')
    parser.add_argument('--jobs', type=int, default=2, help='Number of parallel jobs')
    
    args = parser.parse_args()
    
    logger.info("Starting optimized ML model training...")
    train_models_parallel(
        use_optuna=not args.no_optuna,
        n_trials=args.trials,
        n_jobs=args.jobs
    )
