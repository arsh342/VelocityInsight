"""
LapSegmenter - Match telemetry records to laps using lap_start/end timestamps
Handles lap number errors (32768 issue) by using timestamps instead
"""
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import logging

logger = logging.getLogger(__name__)


class LapSegmenter:
    """Segment telemetry data into laps using timestamp-based matching."""
    
    def __init__(self, data_dir: str = "../dataset"):
        self.data_dir = Path(data_dir)
    
    def load_lap_boundaries(
        self, 
        track: str, 
        race: str,
        vehicle_id: Optional[str] = None
    ) -> pd.DataFrame:
        """
        Load lap start/end times.
        Handles lap number 32768 corruption by ignoring lap field.
        """
        t = track.lower()
        base = self.data_dir / track
        if t == "barber":
            lap_start_file = base / f"{race}_barber_lap_start.csv"
            lap_end_file = base / f"{race}_barber_lap_end.csv"
        elif t == "indianapolis":
            lap_start_file = base / f"{race}_indianapolis_motor_speedway_lap_start.csv"
            lap_end_file = base / f"{race}_indianapolis_motor_speedway_lap_end.csv"
        elif t == "cota":
            sub = base / ("Race 1" if race.upper() == "R1" else "Race 2")
            lap_start_file = sub / f"COTA_lap_start_time_{race}.csv"
            lap_end_file = sub / f"COTA_lap_end_time_{race}.csv"
        elif t == "vir":
            sub = base / ("Race 1" if race.upper() == "R1" else "Race 2")
            lap_start_file = sub / f"vir_lap_start_{race}.csv"
            lap_end_file = sub / f"vir_lap_end_{race}.csv"
        elif t == "road america":
            sub = base / ("Race 1" if race.upper() == "R1" else "Race 2")
            lap_start_file = sub / f"road_america_lap_start_{race}.csv"
            lap_end_file = sub / f"road_america_lap_end_{race}.csv"
        elif t == "sebring":
            sub = base / ("Race 1" if race.upper() == "R1" else "Race 2")
            lap_start_file = sub / f"sebring_lap_start_time_{race}.csv"
            lap_end_file = sub / f"sebring_lap_end_time_{race}.csv"
        elif t == "sonoma":
            sub = base / ("Race 1" if race.upper() == "R1" else "Race 2")
            lap_start_file = sub / f"sonoma_lap_start_time_{race}.csv"
            lap_end_file = sub / f"sonoma_lap_end_time_{race}.csv"
        else:
            lap_start_file = base / f"{race}_{track}_lap_start.csv"
            lap_end_file = base / f"{race}_{track}_lap_end.csv"
        
        # Load lap starts
        if lap_start_file.exists():
            df_start = pd.read_csv(lap_start_file)
            df_start['timestamp'] = pd.to_datetime(df_start['timestamp'])
            if vehicle_id:
                df_start = df_start[df_start['vehicle_id'] == vehicle_id]
            df_start = df_start.sort_values('timestamp').reset_index(drop=True)
        else:
            raise FileNotFoundError(f"Lap start file not found: {lap_start_file}")
        
        # Load lap ends
        if lap_end_file.exists():
            df_end = pd.read_csv(lap_end_file)
            df_end['timestamp'] = pd.to_datetime(df_end['timestamp'])
            if vehicle_id:
                df_end = df_end[df_end['vehicle_id'] == vehicle_id]
            df_end = df_end.sort_values('timestamp').reset_index(drop=True)
        else:
            df_end = None
        
        # Create lap boundaries by matching starts with ends
        laps = []
        for idx, start_row in df_start.iterrows():
            lap_info = {
                'lap_number': idx + 1,  # Ignore corrupted lap field, use sequential numbering
                'vehicle_id': start_row['vehicle_id'],
                'lap_start_time': start_row['timestamp'],
            }
            
            # Find corresponding lap end (next timestamp after start)
            if df_end is not None:
                end_candidates = df_end[
                    (df_end['timestamp'] > start_row['timestamp']) &
                    (df_end['vehicle_id'] == start_row['vehicle_id'])
                ]
                if len(end_candidates) > 0:
                    lap_info['lap_end_time'] = end_candidates.iloc[0]['timestamp']
                else:
                    lap_info['lap_end_time'] = None
            else:
                # Use next lap start as proxy for end
                if idx + 1 < len(df_start):
                    lap_info['lap_end_time'] = df_start.iloc[idx + 1]['timestamp']
                else:
                    lap_info['lap_end_time'] = None
            
            laps.append(lap_info)
        
        df_laps = pd.DataFrame(laps)
        
        # Calculate lap times
        if 'lap_end_time' in df_laps.columns:
            df_laps['lap_time_seconds'] = (
                df_laps['lap_end_time'] - df_laps['lap_start_time']
            ).dt.total_seconds()
        
        logger.info(f"Loaded {len(df_laps)} laps for {vehicle_id or 'all vehicles'}")
        
        return df_laps
    
    def assign_laps_to_telemetry(
        self,
        df_telemetry: pd.DataFrame,
        df_laps: pd.DataFrame
    ) -> pd.DataFrame:
        """
        Assign lap numbers to telemetry records based on timestamps.
        Handles timestamp offset issues by aligning first lap.
        
        Args:
            df_telemetry: Telemetry data with 'timestamp' column
            df_laps: Lap boundaries with 'lap_start_time' and 'lap_end_time'
        
        Returns:
            Telemetry DataFrame with corrected 'lap_number' column
        """
        df = df_telemetry.copy()
        
        # Initialize lap_number column (overwrite existing corrupted lap field)
        if 'lap_number' in df.columns:
            df = df.drop(columns=['lap_number'])
        if 'lap' in df.columns:
            df = df.drop(columns=['lap'])
        
        df['lap_number'] = 0
        
        # Calculate timestamp offset between telemetry and lap boundaries
        # Align first telemetry timestamp with first lap start
        telemetry_start = df['timestamp'].min()
        lap_start = df_laps['lap_start_time'].min()
        offset = lap_start - telemetry_start
        
        logger.info(f"Timestamp offset: {offset.total_seconds():.1f} seconds")
        
        # Adjust telemetry timestamps to match lap boundaries
        df['timestamp_adjusted'] = df['timestamp'] + offset
        
        # For each lap, assign records within time range
        for _, lap in df_laps.iterrows():
            vehicle_match = True
            if 'vehicle_id' in df.columns and 'vehicle_id' in lap:
                vehicle_match = (df['vehicle_id'] == lap['vehicle_id'])
            
            if pd.isna(lap['lap_end_time']):
                # Last lap - everything after start
                mask = (df['timestamp_adjusted'] >= lap['lap_start_time']) & vehicle_match
            else:
                # Normal lap - between start and end
                mask = (
                    (df['timestamp_adjusted'] >= lap['lap_start_time']) &
                    (df['timestamp_adjusted'] < lap['lap_end_time']) &
                    vehicle_match
                )
            
            df.loc[mask, 'lap_number'] = int(lap['lap_number'])
        
        # Remove records not assigned to any lap (before first lap or after last)
        df_assigned = df[df['lap_number'] > 0].copy()
        
        # Drop adjusted timestamp column
        if 'timestamp_adjusted' in df_assigned.columns:
            df_assigned = df_assigned.drop(columns=['timestamp_adjusted'])
        
        logger.info(f"Assigned lap numbers to {len(df_assigned)} telemetry records across {df_assigned['lap_number'].nunique()} laps")
        
        return df_assigned
    
    def segment_by_lap(
        self,
        track: str,
        race: str,
        vehicle_id: str
    ) -> Dict[int, pd.DataFrame]:
        """
        Load telemetry and segment into separate DataFrames per lap.
        
        Returns:
            Dictionary mapping lap_number -> telemetry DataFrame for that lap
        """
        from .telemetry_loader import get_telemetry_loader
        
        # Load telemetry
        loader = get_telemetry_loader(str(self.data_dir))
        df_telemetry = loader.load_and_pivot(track, race, vehicle_id)
        
        # Load lap boundaries
        df_laps = self.load_lap_boundaries(track, race, vehicle_id)
        
        # Assign lap numbers
        df_telemetry = self.assign_laps_to_telemetry(df_telemetry, df_laps)
        
        # Split into dictionary by lap
        lap_data = {}
        for lap_num in sorted(df_telemetry['lap_number'].unique()):
            lap_data[lap_num] = df_telemetry[
                df_telemetry['lap_number'] == lap_num
            ].copy()
        
        logger.info(f"Segmented telemetry into {len(lap_data)} laps")
        
        return lap_data
    
    def get_lap_summary_features(
        self,
        df_lap: pd.DataFrame
    ) -> Dict:
        """
        Calculate summary features for a single lap's telemetry.
        
        Features:
        - avg_throttle: Mean throttle position
        - max_speed: Estimated max speed
        - total_brake_time: Seconds braking
        - avg_lateral_g: Mean absolute lateral G
        - max_g_force: Peak G-force
        """
        features = {}
        
        if 'aps' in df_lap.columns:
            features['avg_throttle'] = df_lap['aps'].mean()
            features['max_throttle'] = df_lap['aps'].max()
            features['throttle_time_pct'] = (df_lap['aps'] > 10).mean() * 100
        
        if 'total_brake' in df_lap.columns:
            brake_on = df_lap['total_brake'] > 5
            features['brake_time_pct'] = brake_on.mean() * 100
            features['avg_brake_pressure'] = df_lap.loc[brake_on, 'total_brake'].mean()
        
        if 'accy_can' in df_lap.columns:
            features['avg_lateral_g'] = df_lap['accy_can'].abs().mean()
            features['max_lateral_g'] = df_lap['accy_can'].abs().max()
        
        if 'accx_can' in df_lap.columns:
            features['avg_long_g'] = df_lap['accx_can'].abs().mean()
            features['max_long_g'] = df_lap['accx_can'].abs().max()
        
        if 'g_force_total' in df_lap.columns:
            features['max_g_force'] = df_lap['g_force_total'].max()
        
        if 'gear' in df_lap.columns:
            features['avg_gear'] = df_lap['gear'].mean()
            features['max_gear'] = df_lap['gear'].max()
            features['gear_shifts'] = (df_lap['gear'].diff() != 0).sum()
        
        if 'nmot' in df_lap.columns:
            features['avg_rpm'] = df_lap['nmot'].mean()
            features['max_rpm'] = df_lap['nmot'].max()
        
        # Time-based features
        if 'time_delta' in df_lap.columns:
            features['lap_duration'] = df_lap['time_delta'].sum()
        
        return features


# Singleton instance
_segmenter = None

def get_lap_segmenter(data_dir: str = "../dataset") -> LapSegmenter:
    """Get singleton lap segmenter instance."""
    global _segmenter
    if _segmenter is None:
        _segmenter = LapSegmenter(data_dir)
    return _segmenter
