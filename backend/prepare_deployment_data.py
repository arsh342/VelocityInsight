import os
import shutil
import pandas as pd
from pathlib import Path

def prepare_data():
    # Define paths
    project_root = Path(__file__).parent.parent
    source_dir = project_root / "dataset" / "barber"
    dest_dir = project_root / "backend" / "data" / "barber"
    
    print(f"Source: {source_dir}")
    print(f"Destination: {dest_dir}")
    
    if not source_dir.exists():
        print(f"Error: Source directory {source_dir} does not exist!")
        return

    # Create destination directory
    if dest_dir.exists():
        shutil.rmtree(dest_dir)
    dest_dir.mkdir(parents=True, exist_ok=True)
    
    # Files to copy directly (small files)
    files_to_copy = [
        "R1_barber_lap_end.csv",
        "R1_barber_lap_start.csv",
        "R1_barber_lap_time.csv",
        "R2_barber_lap_end.csv",
        "R2_barber_lap_start.csv",
        "R2_barber_lap_time.csv",
        "03_Provisional Results_Race 1_Anonymized.CSV",
        "03_Provisional Results_Race 2_Anonymized.CSV",
        "26_Weather_Race 1_Anonymized.CSV",
        "26_Weather_Race 2_Anonymized.CSV"
    ]
    
    print("Copying small files...")
    for filename in files_to_copy:
        src_file = source_dir / filename
        dst_file = dest_dir / filename
        if src_file.exists():
            shutil.copy2(src_file, dst_file)
            print(f"  Copied {filename}")
        else:
            print(f"  Warning: {filename} not found")

    # Process Telemetry Files (Downsample)
    telemetry_files = [
        "R1_barber_telemetry_data.csv",
        "R2_barber_telemetry_data.csv"
    ]
    
    print("\nProcessing telemetry files (this may take a moment)...")
    for filename in telemetry_files:
        src_file = source_dir / filename
        dst_file = dest_dir / filename
        
        if not src_file.exists():
            print(f"  Warning: {filename} not found")
            continue
            
        print(f"  Reading {filename}...")
        # Read the CSV
        # Use chunks if memory is an issue, but for 1.5GB on local machine it should be fine
        # We'll read only necessary columns to save memory if needed, but let's try full read first
        try:
            # Downsample: Keep 1 row every 100 rows
            # This reduces 1.5GB -> ~15MB
            df = pd.read_csv(src_file)
            print(f"    Original shape: {df.shape}")
            
            # Simple downsampling
            df_sampled = df.iloc[::100, :]
            print(f"    Sampled shape: {df_sampled.shape}")
            
            df_sampled.to_csv(dst_file, index=False)
            print(f"    Saved sampled file to {dst_file}")
            
        except Exception as e:
            print(f"  Error processing {filename}: {e}")

    print("\nData preparation complete!")

if __name__ == "__main__":
    prepare_data()
