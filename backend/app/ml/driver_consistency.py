"""
Driver Consistency Score Model
Analyzes driver performance consistency across laps and sectors
"""
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional
import logging

from ..data.lap_segmenter import get_lap_segmenter
from ..data.sector_mapper import get_sector_mapper
from ..data.feature_engine import get_feature_engine

logger = logging.getLogger(__name__)


class DriverConsistencyModel:
    """Analyze driver consistency and identify strengths/weaknesses."""
    
    def __init__(self, data_dir: str = "../dataset"):
        self.data_dir = data_dir
    
    def calculate_consistency_score(
        self,
        track: str,
        race: str,
        vehicle_id: str
    ) -> Dict:
        """
        Calculate comprehensive consistency score for a driver.
        
        Metrics:
        - Lap time variance (lower = more consistent)
        - Sector time variance per sector
        - Throttle/brake consistency
        - Peak performance maintenance
        
        Returns:
            Dictionary with consistency metrics and score (0-100)
        """
        segmenter = get_lap_segmenter(self.data_dir)
        mapper = get_sector_mapper(self.data_dir)
        engine = get_feature_engine()
        
        # Load lap boundaries
        df_laps = segmenter.load_lap_boundaries(track, race, vehicle_id)
        
        if len(df_laps) < 5:
            raise ValueError(f"Need at least 5 laps for consistency analysis, found {len(df_laps)}")
        
        # Calculate lap time statistics
        lap_times = df_laps['lap_time_seconds'].dropna()
        lap_times = lap_times[(lap_times > 90) & (lap_times < 150)]  # Filter outliers
        
        lap_time_stats = {
            'mean': float(lap_times.mean()),
            'std': float(lap_times.std()),
            'cv': float(lap_times.std() / lap_times.mean()),  # Coefficient of variation
            'min': float(lap_times.min()),
            'max': float(lap_times.max()),
            'range': float(lap_times.max() - lap_times.min()),
        }
        
        # Load sector data if available
        sector_consistency = {}
        try:
            df_sectors = mapper.load_sector_data(track, race)
            sector_stats = mapper.get_sector_consistency(df_sectors, vehicle_id)
            sector_consistency = sector_stats
        except:
            logger.warning("Sector data not available")
        
        # Load telemetry for behavioral consistency
        lap_data = segmenter.segment_by_lap(track, race, vehicle_id)
        
        throttle_variance = []
        brake_variance = []
        g_force_variance = []
        
        for lap_num in lap_data.keys():
            features = engine.calculate_lap_features(lap_data[lap_num])
            
            if 'throttle_smoothness' in features:
                throttle_variance.append(features['throttle_smoothness'])
            if 'avg_brake_pressure' in features:
                brake_variance.append(features.get('avg_brake_pressure', 0))
            if 'max_g_force' in features:
                g_force_variance.append(features['max_g_force'])
        
        behavioral_consistency = {
            'throttle_smoothness_avg': float(np.mean(throttle_variance)) if throttle_variance else 0,
            'throttle_smoothness_std': float(np.std(throttle_variance)) if throttle_variance else 0,
            'brake_consistency': float(np.std(brake_variance)) if brake_variance else 0,
            'g_force_consistency': float(np.std(g_force_variance)) if g_force_variance else 0,
        }
        
        # Calculate overall consistency score (0-100)
        # Lower variance = higher score
        score = 100
        
        # Penalize lap time variance (10 points per 0.1 CV)
        score -= min(lap_time_stats['cv'] * 1000, 30)
        
        # Penalize sector variance if available
        if sector_consistency:
            for sector, stats in sector_consistency.items():
                score -= min(stats['cv'] * 50, 10)
        
        # Penalize behavioral inconsistency
        score -= min(behavioral_consistency['throttle_smoothness_std'] * 0.5, 10)
        
        # Ensure score is 0-100
        score = max(0, min(100, score))
        
        return {
            'vehicle_id': vehicle_id,
            'track': track,
            'race': race,
            'consistency_score': round(score, 1),
            'total_laps': len(df_laps),
            'lap_time_stats': lap_time_stats,
            'sector_consistency': sector_consistency,
            'behavioral_consistency': behavioral_consistency,
            'rating': self._get_rating(score)
        }
    
    def _get_rating(self, score: float) -> str:
        """Convert score to rating."""
        if score >= 90:
            return "Excellent"
        elif score >= 80:
            return "Very Good"
        elif score >= 70:
            return "Good"
        elif score >= 60:
            return "Fair"
        else:
            return "Needs Improvement"
    
    def identify_strengths_weaknesses(
        self,
        track: str,
        race: str,
        vehicle_id: str
    ) -> Dict:
        """
        Identify driver's strongest and weakest sectors/areas.
        
        Returns:
            Dictionary with strengths and weaknesses
        """
        mapper = get_sector_mapper(self.data_dir)
        
        try:
            df_sectors = mapper.load_sector_data(track, race)
            strengths = mapper.identify_sector_strengths(df_sectors, vehicle_id)
            
            # Find strongest and weakest sectors
            sectors_sorted = sorted(
                strengths.items(),
                key=lambda x: x[1]['delta']  # Negative delta = faster = stronger
            )
            
            strongest = sectors_sorted[0] if sectors_sorted else None
            weakest = sectors_sorted[-1] if sectors_sorted else None
            
            return {
                'vehicle_id': vehicle_id,
                'strongest_sector': {
                    'sector': strongest[0] if strongest else None,
                    'delta_vs_field': round(strongest[1]['delta'], 3) if strongest else None,
                    'percentile': round(strongest[1]['percentile'], 1) if strongest else None
                },
                'weakest_sector': {
                    'sector': weakest[0] if weakest else None,
                    'delta_vs_field': round(weakest[1]['delta'], 3) if weakest else None,
                    'percentile': round(weakest[1]['percentile'], 1) if weakest else None
                },
                'all_sectors': {
                    sector: {
                        'delta': round(stats['delta'], 3),
                        'percentile': round(stats['percentile'], 1),
                        'strength': stats['strength']
                    }
                    for sector, stats in strengths.items()
                }
            }
            
        except Exception as e:
            logger.error(f"Error analyzing strengths/weaknesses: {e}")
            return {}
    
    def compare_drivers(
        self,
        track: str,
        race: str,
        vehicle_ids: List[str]
    ) -> Dict:
        """
        Compare consistency scores across multiple drivers.
        
        Returns:
            Ranked list of drivers by consistency
        """
        results = []
        
        for vehicle_id in vehicle_ids:
            try:
                score = self.calculate_consistency_score(track, race, vehicle_id)
                results.append(score)
            except Exception as e:
                logger.warning(f"Failed to analyze {vehicle_id}: {e}")
                continue
        
        # Sort by consistency score
        results.sort(key=lambda x: x['consistency_score'], reverse=True)
        
        # Add rankings
        for i, result in enumerate(results):
            result['rank'] = i + 1
        
        return {
            'track': track,
            'race': race,
            'drivers_analyzed': len(results),
            'rankings': results
        }


# Singleton instance
_model = None

def get_consistency_model(data_dir: str = "../dataset") -> DriverConsistencyModel:
    """Get singleton consistency model."""
    global _model
    if _model is None:
        _model = DriverConsistencyModel(data_dir)
    return _model
