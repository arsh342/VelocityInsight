#!/usr/bin/env python3
"""
Test Data Processing Pipeline
Tests TelemetryLoader, LapSegmenter, SectorMapper, and FeatureEngine
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from app.data.telemetry_loader import get_telemetry_loader
from app.data.lap_segmenter import get_lap_segmenter
from app.data.sector_mapper import get_sector_mapper
from app.data.feature_engine import get_feature_engine


def test_telemetry_loader():
    """Test loading and pivoting telemetry data."""
    print("\n" + "="*80)
    print("🔄 TELEMETRY LOADER TEST")
    print("="*80)
    
    loader = get_telemetry_loader("../dataset")
    
    # Test 1: Get summary
    print("\n1. Getting telemetry summary...")
    summary = loader.get_telemetry_summary("barber", "R1")
    print(f"   Total records: {summary['total_records']:,}")
    print(f"   Vehicles: {summary['vehicles']}")
    print(f"   Duration: {summary['time_range']['duration_minutes']:.1f} minutes")
    print(f"   Parameters tracked: {len(summary['telemetry_params'])}")
    
    # Test 2: Load and pivot for one vehicle
    print("\n2. Loading and pivoting telemetry for GR86-002-000...")
    vehicle_id = summary['vehicle_list'][0]
    print(f"   Selected vehicle: {vehicle_id}")
    
    df_wide = loader.load_and_pivot("barber", "R1", vehicle_id)
    print(f"   ✅ Pivoted to {len(df_wide)} records")
    print(f"   Columns: {list(df_wide.columns)[:10]}...")
    
    # Test 3: Calculate derived features
    print("\n3. Calculating derived features...")
    df_featured = loader.calculate_derived_features(df_wide)
    print(f"   ✅ Added features: {[c for c in df_featured.columns if c not in df_wide.columns]}")
    
    return df_featured, vehicle_id


def test_lap_segmenter(vehicle_id):
    """Test lap segmentation."""
    print("\n" + "="*80)
    print("🔢 LAP SEGMENTER TEST")
    print("="*80)
    
    segmenter = get_lap_segmenter("../dataset")
    
    # Test 1: Load lap boundaries
    print(f"\n1. Loading lap boundaries for {vehicle_id}...")
    df_laps = segmenter.load_lap_boundaries("barber", "R1", vehicle_id)
    print(f"   ✅ Found {len(df_laps)} laps")
    print(f"   Lap times (first 5):")
    for _, lap in df_laps.head().iterrows():
        print(f"      Lap {lap['lap_number']}: {lap.get('lap_time_seconds', 0):.2f}s")
    
    # Test 2: Segment telemetry by lap
    print(f"\n2. Segmenting telemetry into laps...")
    lap_data = segmenter.segment_by_lap("barber", "R1", vehicle_id)
    print(f"   ✅ Segmented into {len(lap_data)} laps")
    
    # Test 3: Calculate lap summary features
    print(f"\n3. Calculating lap summary features...")
    lap_3_features = segmenter.get_lap_summary_features(lap_data[3])
    print(f"   Lap 3 features:")
    for key, value in list(lap_3_features.items())[:5]:
        print(f"      {key}: {value:.2f}")
    
    return df_laps, lap_data


def test_sector_mapper():
    """Test sector timing integration."""
    print("\n" + "="*80)
    print("🎯 SECTOR MAPPER TEST")
    print("="*80)
    
    mapper = get_sector_mapper("../dataset")
    
    try:
        # Test 1: Load sector data
        print("\n1. Loading sector timing data...")
        df_sectors = mapper.load_sector_data("barber", "R1")
        print(f"   ✅ Loaded {len(df_sectors)} laps with sector times")
        
        if 's1_time' in df_sectors.columns:
            print(f"   Sector 1 times (first 5):")
            for _, row in df_sectors.head().iterrows():
                s1 = row.get('s1_time', 0)
                s2 = row.get('s2_time', 0)
                s3 = row.get('s3_time', 0)
                print(f"      Lap {row['lap_number']}: S1={s1:.2f}s S2={s2:.2f}s S3={s3:.2f}s")
        
        # Test 2: Calculate sector deltas
        print("\n2. Calculating sector deltas...")
        df_sectors_delta = mapper.calculate_sector_deltas(df_sectors)
        print(f"   ✅ Added delta columns")
        
        # Test 3: Get consistency metrics
        print("\n3. Analyzing sector consistency...")
        vehicle_nums = df_sectors['vehicle_number'].unique()
        if len(vehicle_nums) > 0:
            # Create a vehicle_id for testing
            test_vehicle = f"GR86-002-{vehicle_nums[0]:03d}"
            df_sectors['vehicle_id'] = df_sectors['vehicle_number'].apply(
                lambda x: f"GR86-002-{x:03d}"
            )
            
            consistency = mapper.get_sector_consistency(df_sectors, test_vehicle)
            print(f"   Consistency for vehicle {test_vehicle}:")
            for sector, stats in list(consistency.items())[:2]:
                print(f"      {sector}: mean={stats['mean']:.2f}s std={stats['std']:.3f}s")
        
        return df_sectors
    
    except FileNotFoundError as e:
        print(f"   ⚠️  Sector data not found: {e}")
        print(f"   Skipping sector tests...")
        return None


def test_feature_engine(lap_data):
    """Test feature calculation."""
    print("\n" + "="*80)
    print("⚙️  FEATURE ENGINE TEST")
    print("="*80)
    
    engine = get_feature_engine()
    
    # Test 1: Calculate features for single lap
    print("\n1. Calculating features for Lap 3...")
    features = engine.calculate_lap_features(lap_data[3])
    print(f"   ✅ Extracted {len(features)} features")
    print(f"   Sample features:")
    for key, value in list(features.items())[:8]:
        print(f"      {key}: {value:.3f}")
    
    # Test 2: Build feature matrix
    print("\n2. Building feature matrix for all laps...")
    all_features = []
    for lap_num in sorted(lap_data.keys())[:10]:  # First 10 laps
        lap_features = engine.calculate_lap_features(lap_data[lap_num])
        lap_features['lap_number'] = lap_num
        all_features.append(lap_features)
    
    print(f"   ✅ Built feature matrix with {len(all_features)} laps")
    
    return all_features


def test_full_pipeline():
    """Test complete data processing pipeline."""
    print("\n" + "="*80)
    print("🏁 FULL PIPELINE INTEGRATION TEST")
    print("="*80)
    
    # Step 1: Load telemetry
    df_telemetry, vehicle_id = test_telemetry_loader()
    
    # Step 2: Segment by laps
    df_laps, lap_data = test_lap_segmenter(vehicle_id)
    
    # Step 3: Load sector data
    df_sectors = test_sector_mapper()
    
    # Step 4: Calculate features
    all_features = test_feature_engine(lap_data)
    
    print("\n" + "="*80)
    print("✅ FULL PIPELINE TEST COMPLETE")
    print("="*80)
    print("\n📊 Pipeline Summary:")
    print(f"   ✅ TelemetryLoader: {len(df_telemetry)} telemetry records")
    print(f"   ✅ LapSegmenter: {len(lap_data)} laps segmented")
    print(f"   ✅ SectorMapper: {'Available' if df_sectors is not None else 'Not available'}")
    print(f"   ✅ FeatureEngine: {len(all_features)} lap feature sets")
    print(f"\n   Ready for ML model training! 🎉")


def main():
    """Run all tests."""
    print("\n" + "="*80)
    print("🚀 DATA PROCESSING PIPELINE TEST SUITE")
    print("="*80)
    
    try:
        test_full_pipeline()
        return 0
    except Exception as e:
        print(f"\n❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
