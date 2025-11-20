"""
FeatureEngine - Calculate derived metrics for ML models
Combines telemetry, lap, and sector data into ML-ready features
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)


class FeatureEngine:
    """Calculate ML features from telemetry and lap data."""
    
    @staticmethod
    def calculate_lap_features(
        df_telemetry: pd.DataFrame,
        df_sectors: Optional[pd.DataFrame] = None,
        tire_age: Optional[int] = None
    ) -> Dict:
        """
        Calculate comprehensive features for a lap.
        
        Args:
            df_telemetry: Telemetry data for the lap (wide format)
            df_sectors: Sector timing data (optional)
            tire_age: Laps since last pit stop (optional)
        
        Returns:
            Dictionary of features for ML model
        """
        features = {}
        
        # === Throttle Features ===
        if 'aps' in df_telemetry.columns:
            throttle = df_telemetry['aps'].dropna()
            features['avg_throttle'] = throttle.mean()
            features['max_throttle'] = throttle.max()
            features['throttle_time_pct'] = (throttle > 10).mean() * 100
            features['full_throttle_time_pct'] = (throttle > 90).mean() * 100
            
            # Throttle application smoothness (lower std = smoother)
            features['throttle_smoothness'] = throttle.std()
        
        # === Brake Features ===
        if 'pbrake_f' in df_telemetry.columns and 'pbrake_r' in df_telemetry.columns:
            total_brake = df_telemetry['pbrake_f'] + df_telemetry['pbrake_r']
            brake_on = total_brake > 5
            
            features['brake_time_pct'] = brake_on.mean() * 100
            features['avg_brake_pressure'] = total_brake[brake_on].mean() if brake_on.any() else 0
            features['max_brake_pressure'] = total_brake.max()
            
            # Brake balance
            features['avg_brake_balance'] = (
                df_telemetry.loc[brake_on, 'pbrake_f'] / total_brake[brake_on]
            ).mean() if brake_on.any() else 0.5
            
            # Brake application count (number of braking zones)
            features['brake_applications'] = (brake_on.diff() == True).sum()
        
        # === G-Force Features ===
        if 'accx_can' in df_telemetry.columns:
            features['avg_long_g'] = df_telemetry['accx_can'].mean()
            features['max_long_g'] = df_telemetry['accx_can'].max()
            features['min_long_g'] = df_telemetry['accx_can'].min()  # Peak braking
            features['long_g_variance'] = df_telemetry['accx_can'].var()
        
        if 'accy_can' in df_telemetry.columns:
            features['avg_lateral_g'] = df_telemetry['accy_can'].abs().mean()
            features['max_lateral_g'] = df_telemetry['accy_can'].abs().max()
            features['lateral_g_variance'] = df_telemetry['accy_can'].var()
        
        if 'accx_can' in df_telemetry.columns and 'accy_can' in df_telemetry.columns:
            g_total = np.sqrt(df_telemetry['accx_can']**2 + df_telemetry['accy_can']**2)
            features['max_g_force'] = g_total.max()
            features['avg_g_force'] = g_total.mean()
        
        # === Cornering Features ===
        if 'accy_can' in df_telemetry.columns and 'aps' in df_telemetry.columns:
            # Cornering while on throttle (cornering efficiency)
            cornering = df_telemetry['accy_can'].abs() > 0.3
            throttle_on = df_telemetry['aps'] > 50
            features['corner_throttle_pct'] = (cornering & throttle_on).mean() * 100
        
        # === Gear/RPM Features ===
        if 'gear' in df_telemetry.columns:
            features['avg_gear'] = df_telemetry['gear'].mean()
            features['max_gear'] = df_telemetry['gear'].max()
            features['gear_shifts'] = (df_telemetry['gear'].diff().abs() > 0).sum()
        
        if 'nmot' in df_telemetry.columns:
            features['avg_rpm'] = df_telemetry['nmot'].mean()
            features['max_rpm'] = df_telemetry['nmot'].max()
            features['rpm_variance'] = df_telemetry['nmot'].var()
        
        # === Steering Features ===
        if 'Steering_Angle' in df_telemetry.columns:
            steering = df_telemetry['Steering_Angle'].abs()
            features['avg_steering_angle'] = steering.mean()
            features['max_steering_angle'] = steering.max()
            features['steering_smoothness'] = steering.diff().abs().mean()
        
        # === Sector Times (if available) ===
        if df_sectors is not None and len(df_sectors) > 0:
            for col in ['s1_time', 's2_time', 's3_time']:
                if col in df_sectors.columns:
                    features[col] = df_sectors[col].iloc[0]
            
            # Intermediate splits
            for col in ['im1a_time', 'im1_time', 'im2a_time', 'im2_time', 'im3a_time']:
                if col in df_sectors.columns:
                    features[col] = df_sectors[col].iloc[0]
        
        # === Tire Age ===
        if tire_age is not None:
            features['tire_age'] = tire_age
        
        # === Consistency Metrics ===
        # Calculate variance/std for key metrics (lower = more consistent)
        if 'aps' in df_telemetry.columns:
            features['throttle_variance'] = df_telemetry['aps'].var()
        
        return features
    
    @staticmethod
    def build_feature_matrix(
        lap_features_list: List[Dict],
        target_column: str = 'lap_time'
    ) -> tuple:
        """
        Convert list of lap features to X (features) and y (target) arrays.
        
        Args:
            lap_features_list: List of feature dictionaries (one per lap)
            target_column: Name of target variable
        
        Returns:
            (X, y, feature_names) tuple
        """
        df = pd.DataFrame(lap_features_list)
        
        # Separate target from features
        if target_column in df.columns:
            y = df[target_column].values
            X = df.drop(columns=[target_column])
        else:
            y = None
            X = df
        
        # Fill NaN values with median
        X = X.fillna(X.median())
        
        # Get feature names
        feature_names = X.columns.tolist()
        
        # Convert to numpy array
        X = X.values
        
        return X, y, feature_names
    
    @staticmethod
    def calculate_speed_delta(
        df_telemetry: pd.DataFrame,
        reference_lap: pd.DataFrame,
        distance_col: str = 'Laptrigger_lapdist_dls'
    ) -> pd.DataFrame:
        """
        Calculate speed delta vs reference lap at each track position.
        
        Args:
            df_telemetry: Current lap telemetry
            reference_lap: Reference lap telemetry (e.g., best lap)
            distance_col: Column with distance from start/finish
        
        Returns:
            DataFrame with speed deltas
        """
        # This is complex - requires GPS/distance interpolation
        # Simplified version: just compare average speeds in distance buckets
        
        if distance_col not in df_telemetry.columns:
            logger.warning(f"Distance column {distance_col} not found")
            return pd.DataFrame()
        
        # Create distance buckets (e.g., every 100m)
        df_telemetry['distance_bucket'] = (df_telemetry[distance_col] // 100) * 100
        reference_lap['distance_bucket'] = (reference_lap[distance_col] // 100) * 100
        
        # Calculate average speed per bucket (estimated from GPS or distance changes)
        # TODO: Implement proper speed calculation
        
        return pd.DataFrame()
    
    @staticmethod
    def calculate_brake_point_metrics(
        df_telemetry: pd.DataFrame,
        distance_col: str = 'Laptrigger_lapdist_dls'
    ) -> Dict:
        """
        Analyze brake point consistency and optimization.
        
        Returns:
            Dictionary with brake point analysis
        """
        if 'pbrake_f' not in df_telemetry.columns or distance_col not in df_telemetry.columns:
            return {}
        
        total_brake = df_telemetry['pbrake_f'] + df_telemetry.get('pbrake_r', 0)
        brake_on = total_brake > 10
        
        # Find brake zones (where braking starts/ends)
        brake_starts = df_telemetry.loc[brake_on.diff() == True, distance_col].tolist()
        brake_ends = df_telemetry.loc[brake_on.diff() == False, distance_col].tolist()
        
        return {
            'num_brake_zones': len(brake_starts),
            'brake_zone_distances': brake_starts,
            'total_brake_distance': (brake_ends[0] - brake_starts[0]) if brake_starts and brake_ends else 0
        }
    
    @staticmethod
    def calculate_gear_shift_efficiency(
        df_telemetry: pd.DataFrame
    ) -> Dict:
        """
        Analyze gear shift timing and optimization.
        
        Returns:
            Dictionary with gear shift metrics
        """
        if 'gear' not in df_telemetry.columns or 'nmot' not in df_telemetry.columns:
            return {}
        
        # Find gear shifts
        gear_shifts = df_telemetry['gear'].diff() != 0
        shift_rpms = df_telemetry.loc[gear_shifts, 'nmot'].tolist()
        
        return {
            'total_shifts': gear_shifts.sum(),
            'avg_shift_rpm': np.mean(shift_rpms) if shift_rpms else 0,
            'shift_rpm_variance': np.var(shift_rpms) if shift_rpms else 0
        }


# Singleton instance
_engine = None

def get_feature_engine() -> FeatureEngine:
    """Get singleton feature engine instance."""
    global _engine
    if _engine is None:
        _engine = FeatureEngine()
    return _engine
