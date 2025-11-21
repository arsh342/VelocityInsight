#!/usr/bin/env python3
"""
Enhanced Tire Degradation Model Test
Tests pit stop detection, race classification, and multi-track analysis
"""

import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from app.data.loader import load_lap_times
from app.core.config import settings
from app.ml.tire_degradation import (
    TireDegradationModel, 
    detect_pit_stops_from_lap_times,
    load_pit_stops_from_endurance_data,
    classify_race_type
)


def test_track(track_name: str, race_num: str):
    """Test tire degradation analysis for a specific track."""
    print(f"\n{'=' * 80}")
    print(f"🏁 {track_name.upper()} - Race {race_num}")
    print(f"{'=' * 80}")
    
    try:
        # Load data
        start, end, lapt = load_lap_times(settings.dataset_root, track_name, race_num)
        
        if lapt.empty:
            print(f"❌ No lap data found for {track_name}")
            return
        
        # Race classification
        max_laps = int(lapt['lap'].max())
        race_type, strategy_note = classify_race_type(max_laps)
        
        print(f"\n📊 RACE CLASSIFICATION:")
        print(f"  Type: {race_type}")
        print(f"  Total Laps: {max_laps}")
        print(f"  Strategy: {strategy_note}")
        
        # Detect pit stops
        pit_stops_laps = detect_pit_stops_from_lap_times(lapt)
        pit_stops_data = load_pit_stops_from_endurance_data(settings.dataset_root, track_name, race_num)
        pit_stops = {**pit_stops_laps, **pit_stops_data}
        
        total_pit_stops = sum(len(stops) for stops in pit_stops.values())
        print(f"\n⛽ PIT STOP DETECTION:")
        print(f"  Detected from lap times: {len(pit_stops_laps)} vehicles")
        print(f"  Loaded from endurance data: {len(pit_stops_data)} vehicles")
        print(f"  Total pit stops: {total_pit_stops}")
        
        if total_pit_stops > 0:
            print(f"  Vehicles with pit stops:")
            for vehicle, laps in list(pit_stops.items())[:5]:
                print(f"    {vehicle}: Laps {laps}")
        
        # Analyze degradation with pit stop awareness
        model = TireDegradationModel()
        degradation_df = model.calculate_lap_degradation(lapt, pit_stops=pit_stops)
        
        if degradation_df.empty:
            print(f"❌ No degradation data calculated")
            return
        
        print(f"\n📈 DEGRADATION ANALYSIS:")
        print(f"  Samples: {len(degradation_df)}")
        print(f"  Vehicles: {degradation_df['vehicle_id'].nunique()}")
        print(f"  Stints detected: {degradation_df['stint_number'].max()}")
        
        # Fit model
        metrics = model.fit_degradation_model(degradation_df)
        
        print(f"\n🔬 MODEL METRICS:")
        print(f"  R² Score: {metrics['r2_score']:.3f}")
        print(f"  MAE: {metrics['mae']:.3f}%")
        print(f"  Degradation Rate: {metrics['avg_degradation_rate_per_lap']:.4f}% per lap")
        print(f"  Baseline Lap Time: {metrics['baseline_laptime']:.2f}s")
        
        # Predictions
        print(f"\n🔮 TIRE WEAR PREDICTIONS:")
        for tire_age in [5, 10, 15, 20, 25]:
            deg = model.predict_degradation(tire_age)
            time_loss = metrics['baseline_laptime'] * (deg / 100)
            print(f"  {tire_age} laps: +{deg:.2f}% ({time_loss:+.2f}s)")
        
        # Strategic recommendation
        degradation_rate = metrics['avg_degradation_rate_per_lap']
        print(f"\n🎯 STRATEGIC RECOMMENDATION:")
        
        if race_type == "SPRINT" and abs(degradation_rate) < 0.1:
            print(f"  ✅ SPRINT RACE - NO PIT STOP REQUIRED")
            print(f"  Minimal tire degradation ({abs(degradation_rate):.3f}%/lap)")
            print(f"  Focus on track position and qualifying")
        elif race_type == "SPRINT" and abs(degradation_rate) < 0.5:
            print(f"  ⚠️  SPRINT RACE - MONITOR TIRE WEAR")
            print(f"  Moderate degradation ({abs(degradation_rate):.3f}%/lap)")
            print(f"  Single pit stop may be beneficial")
        else:
            print(f"  🔧 ACTIVE TIRE MANAGEMENT REQUIRED")
            print(f"  Significant degradation ({abs(degradation_rate):.3f}%/lap)")
            print(f"  Pit stop strategy critical for success")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run enhanced tire degradation tests."""
    print("\n" + "=" * 80)
    print("🔧 ENHANCED TIRE DEGRADATION MODEL - COMPREHENSIVE TEST")
    print("=" * 80)
    print("\nTesting pit stop detection, race classification, and multi-track analysis")
    
    # Test multiple tracks (use R1, R2 format)
    tracks_to_test = [
        ("barber", "R1"),
        ("indianapolis", "R1"),
    ]
    
    results = []
    for track, race in tracks_to_test:
        success = test_track(track, race)
        results.append((track, race, success))
    
    # Summary
    print("\n" + "=" * 80)
    print("📊 TEST SUMMARY")
    print("=" * 80)
    
    for track, race, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"  {track} Race {race}: {status}")
    
    total = len(results)
    passed = sum(1 for _, _, s in results if s)
    print(f"\nTotal: {passed}/{total} tests passed ({passed/total*100:.0f}%)")
    
    if passed == total:
        print("\n🎉 All tests passed! Enhanced model working correctly!")
    
    print("\n" + "=" * 80)


if __name__ == "__main__":
    main()
