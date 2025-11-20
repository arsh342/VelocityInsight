from __future__ import annotations
from pathlib import Path
from typing import Optional, Tuple
import pandas as pd

from .schemas import TelemetryRow


def load_long_telemetry_csv(csv_path: Path) -> pd.DataFrame:
    df = pd.read_csv(csv_path)
    # Normalize column names
    df.columns = [c.strip() for c in df.columns]
    
    # Handle empty first column (expire_at)
    if df.columns[0] == 'expire_at' and df.iloc[:, 0].isna().all():
        df = df.drop(columns=[df.columns[0]])
    
    # Ensure types
    if "telemetry_value" in df.columns:
        df["telemetry_value"] = pd.to_numeric(df["telemetry_value"], errors="coerce")
    if "lap" in df.columns:
        df["lap"] = pd.to_numeric(df["lap"], errors="coerce")
    # Parse timestamps
    for col in ("timestamp", "meta_time"):
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce", utc=True)
    return df


def pivot_telemetry_wide(df_long: pd.DataFrame) -> pd.DataFrame:
    # Handle erroneous lap values (e.g., 32768) by nulling and backfilling via timestamp segmentation later
    if "lap" in df_long.columns:
        df_long.loc[df_long["lap"] == 32768, "lap"] = pd.NA
    pivot = (
        df_long
        .sort_values(["vehicle_id", "timestamp"])  # use ECU timestamp order
        .pivot_table(index=["vehicle_id", "timestamp", "lap"],
                     columns="telemetry_name",
                     values="telemetry_value",
                     aggfunc="last")
        .reset_index()
        .sort_values(["vehicle_id", "timestamp"])  # ensure final order
    )
    pivot.columns.name = None
    return pivot


def get_track_directory(dataset_root: Path, track: str) -> Path:
    """Find the correct track directory handling different naming conventions."""
    track_lower = track.lower()
    
    # Map normalized track names to actual directory names
    track_map = {
        "barber": "barber",
        "indianapolis": "indianapolis",
        "cota": "COTA",
        "vir": "VIR",
        "road america": "Road America",
        "sebring": "Sebring",
        "sonoma": "Sonoma",
    }
    
    if track_lower not in track_map:
        raise ValueError(f"Unsupported track: {track}")
    
    actual_dir_name = track_map[track_lower]
    track_dir = dataset_root / actual_dir_name
    
    if not track_dir.exists():
        raise FileNotFoundError(f"Track directory not found: {track_dir}")
    
    return track_dir


def load_race_telemetry_wide(dataset_root: Path, track: str, race: str) -> pd.DataFrame:
    """Load and pivot telemetry data for any track/race combination."""
    track_dir = get_track_directory(dataset_root, track)
    
    # Handle different naming conventions across tracks
    if track.lower() == "barber":
        telemetry_file = track_dir / f"{race}_barber_telemetry_data.csv"
    elif track.lower() == "indianapolis":
        telemetry_file = track_dir / f"{race}_indianapolis_motor_speedway_telemetry.csv"
    elif track.lower() == "cota":
        race_folder = "Race 1" if race.upper() == "R1" else "Race 2"
        telemetry_file = track_dir / race_folder / f"{race}_cota_telemetry_data.csv"
    elif track.lower() == "vir":
        race_folder = "Race 1" if race.upper() == "R1" else "Race 2"
        telemetry_file = track_dir / race_folder / f"{race}_vir_telemetry_data.csv"
    elif track.lower() == "road america":
        race_folder = "Race 1" if race.upper() == "R1" else "Race 2"
        telemetry_file = track_dir / race_folder / f"{race}_road_america_telemetry_data.csv"
    elif track.lower() == "sebring":
        race_folder = "Race 1" if race.upper() == "R1" else "Race 2"
        telemetry_file = track_dir / race_folder / f"sebring_telemetry_{race}.csv"
    elif track.lower() == "sonoma":
        # Sonoma files use a different convention: sonoma_telemetry_R1.csv
        race_folder = "Race 1" if race.upper() == "R1" else "Race 2"
        telemetry_file = track_dir / race_folder / f"sonoma_telemetry_{race}.csv"
    else:
        raise ValueError(f"Unsupported track: {track}")
    
    if not telemetry_file.exists():
        raise FileNotFoundError(f"Telemetry file not found: {telemetry_file}")
    
    df_long = load_long_telemetry_csv(telemetry_file)
    return pivot_telemetry_wide(df_long)


def load_barber_race_wide(dataset_root: Path, race: str = "R1") -> pd.DataFrame:
    """Legacy function for backward compatibility."""
    return load_race_telemetry_wide(dataset_root, "barber", race)


def load_lap_times(dataset_root: Path, track: str, race: str) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Load lap start, end, and time files for any track/race combination."""
    track_dir = get_track_directory(dataset_root, track)
    
    # Handle different naming conventions across tracks
    if track.lower() == "barber":
        start = pd.read_csv(track_dir / f"{race}_barber_lap_start.csv")
        end = pd.read_csv(track_dir / f"{race}_barber_lap_end.csv")
        lapt = pd.read_csv(track_dir / f"{race}_barber_lap_time.csv")
    elif track.lower() == "indianapolis":
        prefix = "indianapolis_motor_speedway"
        start = pd.read_csv(track_dir / f"{race}_{prefix}_lap_start.csv")
        end = pd.read_csv(track_dir / f"{race}_{prefix}_lap_end.csv")
        lapt = pd.read_csv(track_dir / f"{race}_{prefix}_lap_time.csv")
    elif track.lower() == "cota":
        race_folder = "Race 1" if race.upper() == "R1" else "Race 2"
        sub = track_dir / race_folder
        start = pd.read_csv(sub / f"COTA_lap_start_time_{race}.csv")
        end = pd.read_csv(sub / f"COTA_lap_end_time_{race}.csv")
        lapt = pd.read_csv(sub / f"COTA_lap_time_{race}.csv")
    elif track.lower() == "vir":
        race_folder = "Race 1" if race.upper() == "R1" else "Race 2"
        sub = track_dir / race_folder
        # Actual files are lowercase and without "_time_" in name
        start = pd.read_csv(sub / f"vir_lap_start_{race}.csv")
        end = pd.read_csv(sub / f"vir_lap_end_{race}.csv")
        lapt = pd.read_csv(sub / f"vir_lap_time_{race}.csv")
    elif track.lower() == "road america":
        race_folder = "Race 1" if race.upper() == "R1" else "Race 2"
        sub = track_dir / race_folder
        # Actual files are lowercase, with race suffix at end
        start = pd.read_csv(sub / f"road_america_lap_start_{race}.csv")
        end = pd.read_csv(sub / f"road_america_lap_end_{race}.csv")
        lapt = pd.read_csv(sub / f"road_america_lap_time_{race}.csv")
    elif track.lower() == "sebring":
        race_folder = "Race 1" if race.upper() == "R1" else "Race 2"
        sub = track_dir / race_folder
        start = pd.read_csv(sub / f"Sebring_lap_start_time_{race}.csv")
        end = pd.read_csv(sub / f"Sebring_lap_end_time_{race}.csv")
        lapt = pd.read_csv(sub / f"Sebring_lap_time_{race}.csv")
    elif track.lower() == "sonoma":
        race_folder = "Race 1" if race.upper() == "R1" else "Race 2"
        sub = track_dir / race_folder
        start = pd.read_csv(sub / f"sonoma_lap_start_time_{race}.csv")
        end = pd.read_csv(sub / f"sonoma_lap_end_time_{race}.csv")
        lapt = pd.read_csv(sub / f"sonoma_lap_time_{race}.csv")
    else:
        raise ValueError(f"Unsupported track: {track}")

    # Normalize column names and parse timestamps
    for d in (start, end, lapt):
        cols = [c.strip() for c in d.columns]
        d.columns = cols
        if "timestamp" in d.columns:
            d["timestamp"] = pd.to_datetime(d["timestamp"], errors="coerce", utc=True)
    return start, end, lapt


def segment_laps_by_time(df_wide: pd.DataFrame, lap_starts: pd.DataFrame, lap_ends: pd.DataFrame) -> pd.DataFrame:
    # Creates lap_id per vehicle by aligning timestamps between start/end windows
    # Assumes df_wide has columns: vehicle_id, timestamp
    df = df_wide.copy()
    df["lap_id"] = pd.NA

    for vehicle_id, group in df.groupby("vehicle_id"):
        starts = lap_starts[lap_starts["vehicle_id"] == vehicle_id].sort_values("timestamp")
        ends = lap_ends[lap_ends["vehicle_id"] == vehicle_id].sort_values("timestamp")
        if starts.empty or ends.empty:
            continue
        # Pairwise windows by index
        for idx in range(min(len(starts), len(ends))):
            t0 = starts.iloc[idx]["timestamp"]
            t1 = ends.iloc[idx]["timestamp"]
            mask = (df["vehicle_id"] == vehicle_id) & (df["timestamp"] >= t0) & (df["timestamp"] <= t1)
            df.loc[mask, "lap_id"] = idx + 1

    return df
