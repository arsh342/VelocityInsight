from __future__ import annotations
from typing import Optional, List, Dict, Any, Tuple
import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import PolynomialFeatures
from sklearn.metrics import mean_absolute_error, r2_score
from pathlib import Path


def detect_pit_stops_from_lap_times(df_laps: pd.DataFrame, pit_time_threshold: float = 130.0) -> Dict[str, List[int]]:
    """
    Detect pit stops from lap time anomalies.
    
    Args:
        df_laps: DataFrame with lap times
        pit_time_threshold: Lap time above this indicates pit stop (seconds)
        
    Returns:
        Dict mapping vehicle_id to list of pit stop lap numbers
    """
    pit_stops = {}
    
    for vehicle, group in df_laps.groupby('vehicle_id'):
        group = group.sort_values('timestamp').reset_index(drop=True)
        
        # Calculate lap times
        lap_times = []
        lap_nums = []
        for i in range(1, len(group)):
            lap_time = (group.loc[i, 'timestamp'] - group.loc[i-1, 'timestamp']).total_seconds()
            lap_times.append(lap_time)
            lap_nums.append(group.loc[i, 'lap'])
        
        if not lap_times:
            continue
        
        # Detect outliers as pit stops
        lap_times = np.array(lap_times)
        lap_nums = np.array(lap_nums)
        median = np.median(lap_times)
        
        # Laps significantly longer than median are likely pit stops
        pit_indices = np.where(lap_times > max(pit_time_threshold, median * 1.5))[0]
        pit_laps = lap_nums[pit_indices].tolist()
        
        if pit_laps:
            pit_stops[str(vehicle)] = pit_laps
    
    return pit_stops


def load_pit_stops_from_endurance_data(dataset_root: Path, track: str, race: str) -> Dict[str, List[int]]:
    """
    Load pit stop data from endurance analysis CSV if available.
    
    Args:
        dataset_root: Path to dataset directory
        track: Track name
        race: Race number
        
    Returns:
        Dict mapping driver number to list of pit stop lap numbers
    """
    # Try to find endurance analysis file
    endurance_file = dataset_root / track / f"23_AnalysisEnduranceWithSections_Race {race}_Anonymized.CSV"
    
    if not endurance_file.exists():
        return {}
    
    try:
        df = pd.read_csv(endurance_file, sep=';')
        df.columns = [c.strip() for c in df.columns]
        
        # Find laps with pit time recorded
        pit_laps = df[df['PIT_TIME'].notna()][['NUMBER', 'LAP_NUMBER']]
        
        # Group by driver
        pit_stops = {}
        for driver, group in pit_laps.groupby('NUMBER'):
            pit_stops[str(driver)] = group['LAP_NUMBER'].tolist()
        
        return pit_stops
    except Exception:
        return {}


def classify_race_type(total_laps: int, race_duration_minutes: Optional[float] = None) -> Tuple[str, str]:
    """
    Classify race type based on distance.
    
    Args:
        total_laps: Total number of laps in race
        race_duration_minutes: Optional race duration
        
    Returns:
        Tuple of (race_type, strategy_recommendation)
    """
    if total_laps <= 20:
        return "SPRINT", "Minimal tire management - Focus on track position"
    elif total_laps <= 35:
        return "SPRINT", "Single pit stop may be optional depending on tire wear"
    elif total_laps <= 60:
        return "ENDURANCE", "One pit stop recommended - Monitor tire degradation"
    else:
        return "ENDURANCE", "Multiple pit stops required - Active tire management"


class TireDegradationModel:
    """
    Model to predict tire performance degradation over race distance.
    Analyzes lap time progression and driving style impact on tire wear.
    """
    
    def __init__(self):
        self.model: Optional[LinearRegression] = None
        self.poly_features: Optional[PolynomialFeatures] = None
        self.degradation_rate: Optional[float] = None
        self.baseline_laptime: Optional[float] = None
        
    def calculate_lap_degradation(self, df_laps: pd.DataFrame, vehicle_id: Optional[str] = None, 
                                 pit_stops: Optional[Dict[str, List[int]]] = None) -> pd.DataFrame:
        """
        Calculate tire degradation metrics from lap time data with pit stop awareness.
        
        Args:
            df_laps: DataFrame with lap times and metadata
            vehicle_id: Optional filter for specific vehicle
            pit_stops: Optional dict mapping vehicle_id to list of pit stop lap numbers
            
        Returns:
            DataFrame with degradation metrics per lap including proper tire age tracking
        """
        if vehicle_id:
            df_laps = df_laps[df_laps['vehicle_id'] == vehicle_id].copy()
        
        # Auto-detect pit stops if not provided
        if pit_stops is None:
            pit_stops = detect_pit_stops_from_lap_times(df_laps)
            
        # Sort by timestamp to get lap progression
        df_laps = df_laps.sort_values(['vehicle_id', 'timestamp']).copy()
        
        degradation_data = []
        
        for vehicle, group in df_laps.groupby('vehicle_id'):
            if len(group) < 5:  # Need minimum 5 laps for reliable analysis
                continue
                
            group = group.reset_index(drop=True)
            
            # Calculate lap times (timestamp difference between consecutive laps)
            lap_times = []
            lap_nums = []
            for i in range(1, len(group)):
                lap_time = (group.loc[i, 'timestamp'] - group.loc[i-1, 'timestamp']).total_seconds()
                lap_times.append(lap_time)
                lap_nums.append(group.loc[i, 'lap'])
            
            if len(lap_times) < 5:
                continue
            
            # IMPROVED OUTLIER REMOVAL: Use percentile-based filtering
            lap_times = np.array(lap_times)
            lap_nums = np.array(lap_nums)
            
            # Calculate median and MAD (Median Absolute Deviation)
            median_time = np.median(lap_times)
            mad = np.median(np.abs(lap_times - median_time))
            
            # Use 3*MAD threshold (more robust than IQR for racing data)
            lower_bound = median_time - 3 * mad
            upper_bound = median_time + 3 * mad
            
            # Also add absolute bounds (typical GR Cup lap times: 90-110s at most tracks)
            # Remove obvious outliers like pit stops (>130s) or invalid data (<80s)
            valid_laps = (lap_times >= max(80, lower_bound)) & (lap_times <= min(130, upper_bound))
            
            clean_lap_times = lap_times[valid_laps]
            clean_lap_nums = lap_nums[valid_laps]
            
            if len(clean_lap_times) < 5:
                continue
            
            # Use the best 3 laps average as baseline (more stable than single best lap)
            sorted_times = np.sort(clean_lap_times)
            baseline_time = np.mean(sorted_times[:3])
            
            # Get pit stops for this vehicle
            vehicle_pit_stops = pit_stops.get(str(vehicle), [])
            
            # Calculate degradation metrics for each lap with proper tire age tracking
            tire_age = 0  # Resets after each pit stop
            stint_number = 1
            
            for i, (lap_num, lap_time) in enumerate(zip(clean_lap_nums, clean_lap_times)):
                # Check if this lap had a pit stop (reset tire age)
                if int(lap_num) in vehicle_pit_stops:
                    tire_age = 1  # Fresh tires after pit
                    stint_number += 1
                else:
                    tire_age += 1
                
                degradation_data.append({
                    'vehicle_id': vehicle,
                    'lap_number': int(lap_num),
                    'stint_number': stint_number,
                    'tire_age': tire_age,
                    'lap_time': lap_time,
                    'baseline_time': baseline_time,
                    'time_delta': lap_time - baseline_time,
                    'degradation_pct': ((lap_time - baseline_time) / baseline_time) * 100,
                    'cumulative_laps': i + 1,
                    'is_pit_lap': int(lap_num) in vehicle_pit_stops
                })
        
        return pd.DataFrame(degradation_data)
    
    def fit_degradation_model(self, degradation_df: pd.DataFrame) -> Dict[str, Any]:
        """
        Fit polynomial regression model to predict tire degradation.
        
        Args:
            degradation_df: DataFrame from calculate_lap_degradation
            
        Returns:
            Dict with model performance metrics
        """
        if degradation_df.empty:
            raise ValueError("No degradation data available for model fitting")
        
        # Use tire_age as the primary predictor (more meaningful than lap_number)
        X = degradation_df[['tire_age']].values
        y = degradation_df['degradation_pct'].values
        
        # Use polynomial features to capture non-linear tire degradation
        # Degree 2 captures quadratic wear pattern (tires degrade faster over time)
        self.poly_features = PolynomialFeatures(degree=2, include_bias=False)
        X_poly = self.poly_features.fit_transform(X)
        
        # Fit linear regression on polynomial features
        self.model = LinearRegression()
        self.model.fit(X_poly, y)
        
        # Calculate model performance
        y_pred = self.model.predict(X_poly)
        mae = mean_absolute_error(y, y_pred)
        r2 = r2_score(y, y_pred)
        
        # Calculate realistic degradation rate based on tire age
        # Group by tire age and calculate mean degradation at each age
        tire_age_degradation = degradation_df.groupby('tire_age')['degradation_pct'].mean()
        
        # Calculate incremental degradation per lap
        if len(tire_age_degradation) > 1:
            # Use linear regression on tire_age vs degradation to get rate
            ages = tire_age_degradation.index.values.reshape(-1, 1)
            degs = tire_age_degradation.values
            lr = LinearRegression()
            lr.fit(ages, degs)
            self.degradation_rate = float(lr.coef_[0])  # % per lap
        else:
            self.degradation_rate = 0.1  # Default 0.1% per lap if insufficient data
        
        self.baseline_laptime = degradation_df['baseline_time'].mean()
        
        return {
            'mae': mae,
            'r2_score': r2,
            'avg_degradation_rate_per_lap': self.degradation_rate,
            'samples': len(degradation_df),
            'baseline_laptime': self.baseline_laptime
        }
    
    def predict_degradation(self, tire_age: int) -> float:
        """
        Predict tire degradation for given tire age.
        
        Args:
            tire_age: Laps completed on current tires
            
        Returns:
            Predicted degradation percentage
        """
        if self.model is None:
            raise ValueError("Model not fitted. Call fit_degradation_model first.")
            
        X = np.array([[tire_age]])
        X_poly = self.poly_features.transform(X)
        
        return float(self.model.predict(X_poly)[0])
    
    def estimate_remaining_performance(self, current_tire_age: int, target_laps: int, baseline_time: float) -> List[Dict[str, Any]]:
        """
        Estimate performance for future laps based on current tire age.
        
        Args:
            current_tire_age: Current laps on tires
            target_laps: Number of additional laps to predict
            baseline_time: Best lap time achieved
            
        Returns:
            List of dicts with performance predictions
        """
        predictions = []
        
        for i in range(1, target_laps + 1):
            future_tire_age = current_tire_age + i
            
            degradation_pct = self.predict_degradation(future_tire_age)
            predicted_time = baseline_time * (1 + degradation_pct / 100)
            
            predictions.append({
                'lap': i,
                'tire_age': future_tire_age,
                'degradation_pct': degradation_pct,
                'predicted_laptime': predicted_time,
                'time_loss': predicted_time - baseline_time
            })
        
        return predictions
    
    def calculate_optimal_stint_length(self, current_tire_age: int, baseline_time: float, 
                                     max_degradation_threshold: float = 3.0) -> Dict[str, Any]:
        """
        Calculate optimal stint length before pit stop based on degradation threshold.
        
        Args:
            current_tire_age: Current laps on tires
            baseline_time: Best lap time achieved
            max_degradation_threshold: Maximum acceptable degradation percentage
            
        Returns:
            Dict with optimal stint recommendations
        """
        if self.model is None:
            raise ValueError("Model not fitted. Call fit_degradation_model first.")
        
        optimal_tire_age = current_tire_age
        cumulative_time_loss = 0
        recommended_pit_age = current_tire_age + 15  # Default to 15 more laps
        
        # Find the tire age where degradation exceeds threshold
        for additional_laps in range(1, 50):  # Check up to 50 more laps
            future_tire_age = current_tire_age + additional_laps
            degradation_pct = self.predict_degradation(future_tire_age)
            
            if degradation_pct > max_degradation_threshold:
                recommended_pit_age = future_tire_age - 1  # Pit before this age
                break
                
            time_loss = baseline_time * (degradation_pct / 100)
            cumulative_time_loss += time_loss
        
        remaining_laps_available = recommended_pit_age - current_tire_age
        
        return {
            'optimal_tire_age_for_pit': recommended_pit_age,
            'remaining_laps_on_tires': remaining_laps_available,
            'projected_degradation_at_pit': self.predict_degradation(recommended_pit_age),
            'cumulative_time_loss': cumulative_time_loss,
            'recommendation': 'CONTINUE' if remaining_laps_available > 3 else 'CONSIDER_PIT' if remaining_laps_available > 1 else 'PIT_NOW'
        }


class DrivingStyleAnalyzer:
    """
    Analyzes driving style impact on tire degradation.
    """
    
    @staticmethod
    def calculate_aggression_score(telemetry_df: pd.DataFrame, vehicle_id: str) -> Dict[str, float]:
        """
        Calculate driving aggression score based on telemetry data.
        
        Args:
            telemetry_df: DataFrame with telemetry data
            vehicle_id: Vehicle to analyze
            
        Returns:
            Dict with aggression metrics
        """
        vehicle_data = telemetry_df[telemetry_df['vehicle_id'] == vehicle_id].copy()
        
        if vehicle_data.empty:
            return {}
        
        metrics = {}
        
        # Brake aggression (sudden hard braking)
        if 'pbrake_f' in vehicle_data.columns:
            brake_data = vehicle_data['pbrake_f'].dropna()
            if not brake_data.empty:
                brake_changes = brake_data.diff().abs()
                metrics['brake_aggression'] = brake_changes.mean()
                metrics['max_brake_pressure'] = brake_data.max()
        
        # Throttle aggression (rapid acceleration changes)
        if 'aps' in vehicle_data.columns:
            throttle_data = vehicle_data['aps'].dropna()
            if not throttle_data.empty:
                throttle_changes = throttle_data.diff().abs()
                metrics['throttle_aggression'] = throttle_changes.mean()
                metrics['avg_throttle'] = throttle_data.mean()
        
        # G-force indicators (cornering aggression)
        if 'accy_can' in vehicle_data.columns:
            lateral_g = vehicle_data['accy_can'].dropna()
            if not lateral_g.empty:
                metrics['cornering_aggression'] = lateral_g.abs().mean()
                metrics['max_lateral_g'] = lateral_g.abs().max()
        
        # Calculate composite aggression score (0-100)
        if metrics:
            # Normalize and combine metrics (simplified approach)
            aggression_components = [
                metrics.get('brake_aggression', 0) * 10,
                metrics.get('throttle_aggression', 0) * 5,
                metrics.get('cornering_aggression', 0) * 20
            ]
            metrics['composite_aggression_score'] = min(100, sum(aggression_components))
        
        return metrics
