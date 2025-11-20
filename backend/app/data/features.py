from __future__ import annotations
import pandas as pd
import numpy as np
from typing import Dict, List, Optional


def calculate_lap_features(df_segmented: pd.DataFrame) -> pd.DataFrame:
    """Calculate lap-level features from segmented telemetry data."""
    features = []
    
    for (vehicle_id, lap_id), group in df_segmented.groupby(["vehicle_id", "lap_id"]):
        if group.empty:
            continue
            
        lap_features = {
            "vehicle_id": vehicle_id,
            "lap_id": lap_id,
            "lap_duration_s": (group["timestamp"].max() - group["timestamp"].min()).total_seconds(),
            "telemetry_points": len(group),
        }
        
        # Speed features
        if "Speed" in group.columns:
            speed_data = group["Speed"].dropna()
            if not speed_data.empty:
                lap_features.update({
                    "avg_speed_kmh": speed_data.mean(),
                    "max_speed_kmh": speed_data.max(),
                    "min_speed_kmh": speed_data.min(),
                    "speed_std": speed_data.std(),
                })
        
        # Throttle features
        if "aps" in group.columns:
            throttle_data = group["aps"].dropna()
            if not throttle_data.empty:
                lap_features.update({
                    "avg_throttle_pct": throttle_data.mean(),
                    "max_throttle_pct": throttle_data.max(),
                    "throttle_usage_pct": (throttle_data > 0).mean() * 100,
                })
        
        # Brake features
        brake_cols = ["pbrake_f", "pbrake_r"]
        for col in brake_cols:
            if col in group.columns:
                brake_data = group[col].dropna()
                if not brake_data.empty:
                    lap_features[f"avg_{col}_bar"] = brake_data.mean()
                    lap_features[f"max_{col}_bar"] = brake_data.max()
                    lap_features[f"{col}_usage_pct"] = (brake_data > 0).mean() * 100
        
        # G-force features
        if "accx_can" in group.columns:
            accx_data = group["accx_can"].dropna()
            if not accx_data.empty:
                lap_features.update({
                    "avg_longitudinal_g": accx_data.mean(),
                    "max_acceleration_g": accx_data.max(),
                    "max_braking_g": abs(accx_data.min()),
                })
        
        if "accy_can" in group.columns:
            accy_data = group["accy_can"].dropna()
            if not accy_data.empty:
                lap_features.update({
                    "avg_lateral_g": accy_data.mean(),
                    "max_lateral_g": accy_data.max(),
                    "lateral_g_std": accy_data.std(),
                })
        
        # Steering features
        if "Steering_Angle" in group.columns:
            steering_data = group["Steering_Angle"].dropna()
            if not steering_data.empty:
                lap_features.update({
                    "avg_steering_angle": steering_data.mean(),
                    "max_steering_angle": steering_data.max(),
                    "steering_activity": steering_data.diff().abs().sum(),
                })
        
        # Engine features
        if "nmot" in group.columns:
            rpm_data = group["nmot"].dropna()
            if not rpm_data.empty:
                lap_features.update({
                    "avg_rpm": rpm_data.mean(),
                    "max_rpm": rpm_data.max(),
                    "min_rpm": rpm_data.min(),
                })
        
        # Gear features
        if "Gear" in group.columns:
            gear_data = group["Gear"].dropna()
            if not gear_data.empty:
                lap_features.update({
                    "avg_gear": gear_data.mean(),
                    "gear_changes": (gear_data.diff() != 0).sum(),
                })
        
        features.append(lap_features)
    
    return pd.DataFrame(features)


def calculate_tire_degradation_features(df_laps: pd.DataFrame) -> pd.DataFrame:
    """Calculate tire degradation features based on lap progression."""
    df = df_laps.copy()
    df = df.sort_values(["vehicle_id", "lap_id"])
    
    # Rolling averages for smoothing
    for col in ["avg_speed_kmh", "avg_throttle_pct", "avg_longitudinal_g", "avg_lateral_g"]:
        if col in df.columns:
            df[f"{col}_rolling3"] = df.groupby("vehicle_id")[col].rolling(3, min_periods=1).mean().reset_index(0, drop=True)
    
    # Lap progression features
    df["lap_progression"] = df.groupby("vehicle_id")["lap_id"].rank()
    df["total_laps"] = df.groupby("vehicle_id")["lap_id"].transform("max")
    df["race_progress_pct"] = (df["lap_progression"] / df["total_laps"]) * 100
    
    # Performance delta features (vs previous lap)
    for col in ["avg_speed_kmh", "lap_duration_s"]:
        if col in df.columns:
            df[f"{col}_delta"] = df.groupby("vehicle_id")[col].diff()
            df[f"{col}_delta_pct"] = df.groupby("vehicle_id")[col].pct_change() * 100
    
    return df


def create_ml_features(df_laps: pd.DataFrame, target_col: str = "lap_duration_s") -> pd.DataFrame:
    """Create features suitable for ML model training."""
    df = df_laps.copy()
    
    # Select numeric features for ML
    feature_cols = [
        "lap_progression", "race_progress_pct", "total_laps",
        "avg_speed_kmh", "max_speed_kmh", "speed_std",
        "avg_throttle_pct", "max_throttle_pct", "throttle_usage_pct",
        "avg_pbrake_f_bar", "max_pbrake_f_bar", "pbrake_f_usage_pct",
        "avg_pbrake_r_bar", "max_pbrake_r_bar", "pbrake_r_usage_pct",
        "avg_longitudinal_g", "max_acceleration_g", "max_braking_g",
        "avg_lateral_g", "max_lateral_g", "lateral_g_std",
        "avg_steering_angle", "max_steering_angle", "steering_activity",
        "avg_rpm", "max_rpm", "min_rpm",
        "avg_gear", "gear_changes",
        "avg_speed_kmh_rolling3", "avg_throttle_pct_rolling3",
        "avg_longitudinal_g_rolling3", "avg_lateral_g_rolling3",
        "avg_speed_kmh_delta", "lap_duration_s_delta",
        "avg_speed_kmh_delta_pct", "lap_duration_s_delta_pct",
    ]
    
    # Only include columns that exist
    available_features = [col for col in feature_cols if col in df.columns]
    
    # Create feature matrix
    feature_df = df[["vehicle_id", "lap_id"] + available_features + [target_col]].copy()
    
    # Fill missing values
    feature_df[available_features] = feature_df[available_features].fillna(0)
    
    return feature_df
