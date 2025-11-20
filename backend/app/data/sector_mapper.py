"""
SectorMapper - Integrate sector timing data (S1, S2, S3, IM splits)
Parse and merge sector data from endurance analysis files
"""
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)


class SectorMapper:
    """Map sector timing data to laps."""
    
    def __init__(self, data_dir: str = "../dataset"):
        self.data_dir = Path(data_dir)
    
    def load_sector_data(
        self, 
        track: str, 
        race: str
    ) -> pd.DataFrame:
        """
        Load sector timing data from AnalysisEnduranceWithSections files.
        
        Columns include:
        - S1, S2, S3: Main sector times (formatted as MM:SS.mmm)
        - S1_SECONDS, S2_SECONDS, S3_SECONDS: Sector times in seconds
        - IM1a, IM1, IM2a, IM2, IM3a: Intermediate split times
        """
        # Try to find sector data file
        sector_files = list(self.data_dir.glob(f"{track}/*Endurance*{race.replace('R', 'Race ')}*.CSV"))
        
        if not sector_files:
            sector_files = list(self.data_dir.glob(f"{track}/*Endurance*Race*.CSV"))
        
        if not sector_files:
            raise FileNotFoundError(f"No sector data file found for {track}/{race}")
        
        sector_file = sector_files[0]
        logger.info(f"Loading sector data from {sector_file}")
        
        # Load with semicolon delimiter (common in these files)
        try:
            df = pd.read_csv(sector_file, sep=';')
        except:
            df = pd.read_csv(sector_file)
        
        # Clean column names
        df.columns = df.columns.str.strip()
        
        # Rename to standard format
        column_mapping = {
            'NUMBER': 'vehicle_number',
            'DRIVER_NUMBER': 'driver_number',
            'LAP_NUMBER': 'lap_number',
            'LAP_TIME': 'lap_time',
            'S1_SECONDS': 's1_time',
            'S2_SECONDS': 's2_time',
            'S3_SECONDS': 's3_time',
            'IM1a_time': 'im1a_time',
            'IM1_time': 'im1_time',
            'IM2a_time': 'im2a_time',
            'IM2_time': 'im2_time',
            'IM3a_time': 'im3a_time',
            'TOP_SPEED': 'top_speed',
            'KPH': 'avg_speed',
        }
        
        df = df.rename(columns=column_mapping)
        
        # Convert sector times to numeric
        for col in ['s1_time', 's2_time', 's3_time']:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        # Convert intermediate splits
        for col in ['im1a_time', 'im1_time', 'im2a_time', 'im2_time', 'im3a_time']:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        logger.info(f"Loaded sector data for {len(df)} laps")
        
        return df
    
    def merge_with_laps(
        self,
        df_laps: pd.DataFrame,
        df_sectors: pd.DataFrame
    ) -> pd.DataFrame:
        """
        Merge sector timing with lap data.
        
        Args:
            df_laps: Lap boundaries from LapSegmenter
            df_sectors: Sector timing from load_sector_data
        
        Returns:
            Merged DataFrame with lap and sector info
        """
        # Merge on lap_number and vehicle
        # Note: vehicle_number in sectors vs vehicle_id in laps
        
        # Extract vehicle number from vehicle_id (e.g., GR86-002-000 -> 0)
        if 'vehicle_id' in df_laps.columns:
            df_laps['vehicle_number'] = df_laps['vehicle_id'].str.extract(r'-(\d+)$').astype(int)
        
        # Merge
        df_merged = pd.merge(
            df_laps,
            df_sectors,
            on=['lap_number', 'vehicle_number'],
            how='left'
        )
        
        logger.info(f"Merged sector data: {len(df_merged)} laps with sector info")
        
        return df_merged
    
    def calculate_sector_deltas(
        self,
        df: pd.DataFrame
    ) -> pd.DataFrame:
        """
        Calculate sector time deltas vs best and average.
        
        Adds columns:
        - s1_delta_to_best: How much slower than best S1
        - s2_delta_to_best: How much slower than best S2
        - s3_delta_to_best: How much slower than best S3
        - s1_delta_to_avg: How much different from average S1
        """
        df = df.copy()
        
        for sector in ['s1_time', 's2_time', 's3_time']:
            if sector in df.columns:
                # Best sector time
                best = df[sector].min()
                df[f'{sector}_delta_to_best'] = df[sector] - best
                
                # Average sector time
                avg = df[sector].mean()
                df[f'{sector}_delta_to_avg'] = df[sector] - avg
        
        return df
    
    def get_sector_consistency(
        self,
        df: pd.DataFrame,
        vehicle_id: Optional[str] = None
    ) -> Dict:
        """
        Calculate sector consistency metrics for a driver.
        
        Returns:
            Dictionary with consistency stats per sector
        """
        if vehicle_id:
            df = df[df['vehicle_id'] == vehicle_id]
        
        stats = {}
        
        for sector in ['s1_time', 's2_time', 's3_time']:
            if sector not in df.columns:
                continue
            
            sector_times = df[sector].dropna()
            
            if len(sector_times) == 0:
                continue
            
            stats[sector] = {
                'mean': float(sector_times.mean()),
                'std': float(sector_times.std()),
                'min': float(sector_times.min()),
                'max': float(sector_times.max()),
                'range': float(sector_times.max() - sector_times.min()),
                'cv': float(sector_times.std() / sector_times.mean()),  # Coefficient of variation
            }
        
        return stats
    
    def identify_sector_strengths(
        self,
        df: pd.DataFrame,
        vehicle_id: str
    ) -> Dict:
        """
        Identify which sectors a driver is strongest/weakest in.
        Compares to field average.
        """
        vehicle_df = df[df['vehicle_id'] == vehicle_id]
        
        strengths = {}
        
        for sector in ['s1_time', 's2_time', 's3_time']:
            if sector not in df.columns:
                continue
            
            # Driver's average
            driver_avg = vehicle_df[sector].mean()
            
            # Field average
            field_avg = df[sector].mean()
            
            # Delta (negative = faster than field)
            delta = driver_avg - field_avg
            
            strengths[sector] = {
                'driver_avg': float(driver_avg),
                'field_avg': float(field_avg),
                'delta': float(delta),
                'percentile': float((df[sector] > driver_avg).mean() * 100),
                'strength': 'strong' if delta < 0 else 'weak'
            }
        
        return strengths


# Singleton instance
_mapper = None

def get_sector_mapper(data_dir: str = "../dataset") -> SectorMapper:
    """Get singleton sector mapper instance."""
    global _mapper
    if _mapper is None:
        _mapper = SectorMapper(data_dir)
    return _mapper
