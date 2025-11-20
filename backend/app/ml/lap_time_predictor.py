"""
Lap Time Predictor using XGBoost
Predicts next lap time based on telemetry features, sector times, and tire age
"""
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import pickle
import logging
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import xgboost as xgb

from ..data.telemetry_loader import get_telemetry_loader
from ..data.lap_segmenter import get_lap_segmenter
from ..data.sector_mapper import get_sector_mapper
from ..data.feature_engine import get_feature_engine

logger = logging.getLogger(__name__)


class LapTimePredictor:
    """
    XGBoost model to predict lap times.
    
    Features:
    - Sector times (S1, S2, S3)
    - Avg throttle, brake, G-forces
    - Tire age
    - Weather conditions (if available)
    """
    
    def __init__(self, model_path: Optional[str] = None):
        self.model = None
        self.feature_names = None
        self.model_path = model_path
        
        if model_path and Path(model_path).exists():
            self.load_model(model_path)
    
    def prepare_training_data(
        self,
        track: str,
        race: str,
        vehicle_ids: Optional[List[str]] = None,
        data_dir: str = "../dataset"
    ) -> Tuple[np.ndarray, np.ndarray, List[str]]:
        """
        Load and prepare training data for the model.
        
        Returns:
            (X, y, feature_names) where:
            - X: Feature matrix
            - y: Target lap times
            - feature_names: List of feature column names
        """
        logger.info(f"Preparing training data for {track}/{race}")
        
        loader = get_telemetry_loader(data_dir)
        segmenter = get_lap_segmenter(data_dir)
        engine = get_feature_engine()
        
        # Get all vehicles if not specified
        if vehicle_ids is None:
            summary = loader.get_telemetry_summary(track, race)
            vehicle_ids = summary['vehicle_list'][:5]  # Limit to 5 vehicles for speed
        
        all_features = []
        
        # Process each vehicle
        for vehicle_id in vehicle_ids:
            try:
                logger.info(f"  Processing vehicle {vehicle_id}...")
                
                # Segment telemetry by lap
                lap_data = segmenter.segment_by_lap(track, race, vehicle_id)
                
                # Load lap boundaries to get lap times
                df_laps = segmenter.load_lap_boundaries(track, race, vehicle_id)
                
                # Calculate features for each lap
                for lap_num in sorted(lap_data.keys()):
                    if lap_num >= len(df_laps):
                        continue
                    
                    # Get lap time (target)
                    lap_time = df_laps.iloc[lap_num - 1]['lap_time_seconds']
                    
                    # Skip invalid lap times
                    if pd.isna(lap_time) or lap_time < 80 or lap_time > 200:
                        continue
                    
                    # Calculate features
                    lap_features = engine.calculate_lap_features(
                        lap_data[lap_num],
                        tire_age=lap_num  # Simplified: assume no pit stops
                    )
                    
                    lap_features['lap_time'] = lap_time
                    lap_features['lap_number'] = lap_num
                    lap_features['vehicle_id'] = vehicle_id
                    
                    all_features.append(lap_features)
                
            except Exception as e:
                logger.warning(f"  Failed to process {vehicle_id}: {e}")
                continue
        
        logger.info(f"Collected {len(all_features)} laps for training")
        
        # Convert to DataFrame
        df = pd.DataFrame(all_features)
        
        # Remove non-feature columns
        target = df['lap_time'].values
        features_to_drop = ['lap_time', 'vehicle_id']
        X = df.drop(columns=[col for col in features_to_drop if col in df.columns])
        
        # Fill NaN with median
        X = X.fillna(X.median())
        
        feature_names = X.columns.tolist()
        X = X.values
        
        return X, target, feature_names
    
    def train(
        self,
        X: np.ndarray,
        y: np.ndarray,
        feature_names: List[str],
        test_size: float = 0.3,
        random_state: int = 42
    ) -> Dict:
        """
        Train XGBoost model.
        
        Args:
            X: Feature matrix
            y: Target lap times
            feature_names: List of feature names
            test_size: Fraction of data for testing
            random_state: Random seed
        
        Returns:
            Dictionary with training metrics
        """
        logger.info(f"Training XGBoost model on {len(X)} samples")
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=random_state, shuffle=True
        )
        
        # Create XGBoost model
        self.model = xgb.XGBRegressor(
            n_estimators=100,
            max_depth=6,
            learning_rate=0.1,
            subsample=0.8,
            colsample_bytree=0.8,
            random_state=random_state,
            objective='reg:squarederror'
        )
        
        # Train
        self.model.fit(
            X_train, y_train,
            eval_set=[(X_test, y_test)],
            verbose=False
        )
        
        self.feature_names = feature_names
        
        # Evaluate
        y_pred_train = self.model.predict(X_train)
        y_pred_test = self.model.predict(X_test)
        
        metrics = {
            'train_mae': float(mean_absolute_error(y_train, y_pred_train)),
            'test_mae': float(mean_absolute_error(y_test, y_pred_test)),
            'train_rmse': float(np.sqrt(mean_squared_error(y_train, y_pred_train))),
            'test_rmse': float(np.sqrt(mean_squared_error(y_test, y_pred_test))),
            'train_r2': float(r2_score(y_train, y_pred_train)),
            'test_r2': float(r2_score(y_test, y_pred_test)),
            'n_samples': len(X),
            'n_features': X.shape[1],
            'n_train': len(X_train),
            'n_test': len(X_test)
        }
        
        logger.info(f"Training complete:")
        logger.info(f"  Train MAE: {metrics['train_mae']:.3f}s")
        logger.info(f"  Test MAE: {metrics['test_mae']:.3f}s")
        logger.info(f"  Test R²: {metrics['test_r2']:.3f}")
        
        return metrics
    
    def predict(self, features: Dict) -> float:
        """
        Predict lap time for given features.
        
        Args:
            features: Dictionary of feature values
        
        Returns:
            Predicted lap time in seconds
        """
        if self.model is None:
            raise ValueError("Model not trained. Call train() first.")
        
        # Convert to DataFrame to ensure correct feature order
        df = pd.DataFrame([features])
        
        # Ensure all expected features are present
        for feat in self.feature_names:
            if feat not in df.columns:
                df[feat] = 0  # Default missing features to 0
        
        # Select only model features in correct order
        df = df[self.feature_names]
        
        # Fill NaN
        df = df.fillna(0)
        
        # Predict
        prediction = self.model.predict(df.values)[0]
        
        return float(prediction)
    
    def get_feature_importance(self, top_n: int = 10) -> Dict[str, float]:
        """Get top N most important features."""
        if self.model is None:
            raise ValueError("Model not trained")
        
        importance = self.model.feature_importances_
        
        # Sort by importance
        indices = np.argsort(importance)[::-1][:top_n]
        
        top_features = {
            self.feature_names[i]: float(importance[i])
            for i in indices
        }
        
        return top_features
    
    def save_model(self, path: str):
        """Save model to disk."""
        if self.model is None:
            raise ValueError("No model to save")
        
        model_data = {
            'model': self.model,
            'feature_names': self.feature_names
        }
        
        with open(path, 'wb') as f:
            pickle.dump(model_data, f)
        
        logger.info(f"Model saved to {path}")
    
    def load_model(self, path: str):
        """Load model from disk."""
        with open(path, 'rb') as f:
            model_data = pickle.load(f)
        
        self.model = model_data['model']
        # Handle both 'feature_names' and 'feature_columns' keys for compatibility
        self.feature_names = model_data.get('feature_names') or model_data.get('feature_columns', [])
        
        logger.info(f"Model loaded from {path}")


# Global cache for predictors by track
_predictor_cache = {}

def get_lap_time_predictor(model_path: Optional[str] = None) -> LapTimePredictor:
    """Get lap time predictor, using cache by model path."""
    if model_path is None:
        # Return a new instance if no path specified
        return LapTimePredictor(model_path)
    
    # Check cache for this model path
    if model_path not in _predictor_cache:
        _predictor_cache[model_path] = LapTimePredictor(model_path)
    
    return _predictor_cache[model_path]
