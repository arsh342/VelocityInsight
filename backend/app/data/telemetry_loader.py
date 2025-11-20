"""
TelemetryLoader - Transform long-format telemetry to wide format for ML
Handles the pivot from one-parameter-per-row to one-row-per-timestamp
"""
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)


class TelemetryLoader:
    """Load and pivot telemetry data from long to wide format."""
    
    # Key telemetry parameters we care about
    TELEMETRY_PARAMS = [
        'accx_can',      # Longitudinal acceleration
        'accy_can',      # Lateral acceleration
        'aps',           # Throttle position (%)
        'pbrake_f',      # Front brake pressure
        'pbrake_r',      # Rear brake pressure
        'gear',          # Current gear
        'nmot',          # Engine RPM
        'Steering_Angle',
        'VBOX_Long_Minutes',  # GPS longitude
        'VBOX_Lat_Min',       # GPS latitude
        'Laptrigger_lapdist_dls',  # Distance from start/finish
    ]
    
    def __init__(self, data_dir: str = "../dataset"):
        self.data_dir = Path(data_dir)
    
    def load_telemetry_long(
        self, 
        track: str, 
        race: str, 
        vehicle_id: Optional[str] = None
    ) -> pd.DataFrame:
        """Load raw telemetry in long format with per-track filename mapping."""
        t = track.lower()
        base = self.data_dir / track
        if t == "barber":
            telemetry_file = base / f"{race}_barber_telemetry_data.csv"
        elif t == "indianapolis":
            telemetry_file = base / f"{race}_indianapolis_motor_speedway_telemetry.csv"
        elif t == "cota":
            sub = base / ("Race 1" if race.upper() == "R1" else "Race 2")
            telemetry_file = sub / f"{race}_cota_telemetry_data.csv"
        elif t == "road america":
            sub = base / ("Race 1" if race.upper() == "R1" else "Race 2")
            telemetry_file = sub / f"{race}_road_america_telemetry_data.csv"
        elif t == "sebring":
            sub = base / ("Race 1" if race.upper() == "R1" else "Race 2")
            telemetry_file = sub / f"sebring_telemetry_{race}.csv"
        elif t == "sonoma":
            sub = base / ("Race 1" if race.upper() == "R1" else "Race 2")
            telemetry_file = sub / f"sonoma_telemetry_{race}.csv"
        elif t == "vir":
            sub = base / ("Race 1" if race.upper() == "R1" else "Race 2")
            telemetry_file = sub / f"{race}_vir_telemetry_data.csv"
        else:
            telemetry_file = base / f"{race}_{track}_telemetry_data.csv"
            if not telemetry_file.exists():
                telemetry_file = base / f"{race}_{track}_telemetry.csv"
        
        if not telemetry_file.exists():
            raise FileNotFoundError(f"Telemetry file not found: {telemetry_file}")
        
        logger.info(f"Loading telemetry from {telemetry_file}")
        
        # Load with low_memory=False to avoid dtype warnings on large files
        df = pd.read_csv(telemetry_file, low_memory=False)
        
        # Filter by vehicle if specified
        if vehicle_id:
            df = df[df['vehicle_id'] == vehicle_id].copy()
        
        # Convert timestamps
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df['meta_time'] = pd.to_datetime(df['meta_time'])
        
        logger.info(f"Loaded {len(df)} telemetry records")
        return df
    
    def pivot_to_wide(
        self, 
        df_long: pd.DataFrame,
        vehicle_id: Optional[str] = None
    ) -> pd.DataFrame:
        """
        Pivot telemetry from long format (one param per row) to wide format.
        
        Long format:
            timestamp, telemetry_name, telemetry_value
            2025-09-05 00:28:20.593, accx_can, 0.346
            2025-09-05 00:28:20.593, accy_can, -0.074
            2025-09-05 00:28:20.593, aps, 100
        
        Wide format:
            timestamp, accx_can, accy_can, aps, ...
            2025-09-05 00:28:20.593, 0.346, -0.074, 100, ...
        """
        if vehicle_id:
            df_long = df_long[df_long['vehicle_id'] == vehicle_id].copy()
        
        logger.info("Pivoting telemetry to wide format...")
        
        # Convert telemetry_value to numeric
        df_long['telemetry_value'] = pd.to_numeric(df_long['telemetry_value'], errors='coerce')
        
        # Filter to only params we care about
        df_filtered = df_long[df_long['telemetry_name'].isin(self.TELEMETRY_PARAMS)].copy()
        
        # Pivot: index=timestamp, columns=telemetry_name, values=telemetry_value
        df_wide = df_filtered.pivot_table(
            index=['timestamp', 'vehicle_id', 'lap'],
            columns='telemetry_name',
            values='telemetry_value',
            aggfunc='first'  # Take first value if duplicates
        ).reset_index()
        
        # Flatten column names
        df_wide.columns.name = None
        
        # Sort by timestamp
        df_wide = df_wide.sort_values('timestamp').reset_index(drop=True)
        
        logger.info(f"Pivoted to {len(df_wide)} wide-format records with {len(df_wide.columns)} columns")
        
        return df_wide
    
    def load_and_pivot(
        self,
        track: str,
        race: str,
        vehicle_id: Optional[str] = None,
        time_start: Optional[str] = None,
        time_end: Optional[str] = None
    ) -> pd.DataFrame:
        """
        Load telemetry and pivot to wide format in one call.
        
        Args:
            track: Track name (e.g., 'barber')
            race: Race name (e.g., 'R1')
            vehicle_id: Filter to specific vehicle
            time_start: Start timestamp filter
            time_end: End timestamp filter
        
        Returns:
            Wide-format telemetry DataFrame
        """
        # Load long format
        df_long = self.load_telemetry_long(track, race, vehicle_id)
        
        # Apply time filters if provided
        if time_start:
            df_long = df_long[df_long['timestamp'] >= pd.to_datetime(time_start)]
        if time_end:
            df_long = df_long[df_long['timestamp'] <= pd.to_datetime(time_end)]
        
        # Pivot to wide
        df_wide = self.pivot_to_wide(df_long, vehicle_id)
        
        return df_wide
    
    def get_telemetry_summary(self, track: str, race: str) -> Dict:
        """Get summary statistics about telemetry data."""
        df = self.load_telemetry_long(track, race)
        
        summary = {
            'total_records': len(df),
            'vehicles': df['vehicle_id'].nunique(),
            'vehicle_list': sorted(df['vehicle_id'].unique().tolist()),
            'telemetry_params': sorted(df['telemetry_name'].unique().tolist()),
            'time_range': {
                'start': df['timestamp'].min().isoformat(),
                'end': df['timestamp'].max().isoformat(),
                'duration_minutes': (df['timestamp'].max() - df['timestamp'].min()).total_seconds() / 60
            },
            'laps': {
                'min': int(df['lap'].min()) if 'lap' in df.columns else None,
                'max': int(df['lap'].max()) if 'lap' in df.columns else None,
            }
        }
        
        return summary
    
    def calculate_derived_features(self, df_wide: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate derived features from telemetry.
        
        Features:
        - total_brake: pbrake_f + pbrake_r
        - brake_balance: pbrake_f / total_brake
        - speed_estimated: from GPS or distance changes
        - throttle_efficiency: aps vs acceleration
        """
        df = df_wide.copy()
        
        # Total brake pressure
        if 'pbrake_f' in df.columns and 'pbrake_r' in df.columns:
            df['total_brake'] = df['pbrake_f'] + df['pbrake_r']
            df['brake_balance'] = np.where(
                df['total_brake'] > 0,
                df['pbrake_f'] / df['total_brake'],
                0.5  # Default 50/50 when not braking
            )
        
        # Throttle binary (on/off threshold at 10%)
        if 'aps' in df.columns:
            df['throttle_on'] = (df['aps'] > 10).astype(int)
        
        # Brake binary
        if 'total_brake' in df.columns:
            df['brake_on'] = (df['total_brake'] > 5).astype(int)
        
        # G-force magnitude
        if 'accx_can' in df.columns and 'accy_can' in df.columns:
            df['g_force_total'] = np.sqrt(df['accx_can']**2 + df['accy_can']**2)
        
        # Time delta for rate calculations
        df['time_delta'] = df['timestamp'].diff().dt.total_seconds()
        
        return df


# Singleton instance
_loader = None

def get_telemetry_loader(data_dir: str = "../dataset") -> TelemetryLoader:
    """Get singleton telemetry loader instance."""
    global _loader
    if _loader is None:
        _loader = TelemetryLoader(data_dir)
    return _loader
