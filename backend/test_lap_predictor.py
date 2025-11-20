#!/usr/bin/env python3
"""
Test XGBoost Lap Time Predictor
Train and evaluate the model on Barber data
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from app.ml.lap_time_predictor import LapTimePredictor


def test_lap_predictor():
    """Test XGBoost lap time predictor."""
    print("\n" + "="*80)
    print("🤖 XGBOOST LAP TIME PREDICTOR TEST")
    print("="*80)
    
    predictor = LapTimePredictor()
    
    # Step 1: Prepare training data
    print("\n1. Preparing training data from Barber R1...")
    X, y, feature_names = predictor.prepare_training_data(
        track="barber",
        race="R1",
        vehicle_ids=None,  # Use first 5 vehicles
        data_dir="../dataset"
    )
    
    print(f"   ✅ Prepared {len(X)} laps")
    print(f"   Features: {len(feature_names)}")
    print(f"   Target range: {y.min():.1f}s to {y.max():.1f}s")
    
    # Step 2: Train model
    print("\n2. Training XGBoost model...")
    metrics = predictor.train(X, y, feature_names, test_size=0.3)
    
    print(f"   ✅ Training complete")
    print(f"\n   📊 Performance Metrics:")
    print(f"      Train MAE: {metrics['train_mae']:.3f}s")
    print(f"      Test MAE: {metrics['test_mae']:.3f}s")
    print(f"      Train RMSE: {metrics['train_rmse']:.3f}s")
    print(f"      Test RMSE: {metrics['test_rmse']:.3f}s")
    print(f"      Train R²: {metrics['train_r2']:.3f}")
    print(f"      Test R²: {metrics['test_r2']:.3f}")
    
    # Step 3: Feature importance
    print("\n3. Top 10 Most Important Features:")
    importance = predictor.get_feature_importance(top_n=10)
    for i, (feat, imp) in enumerate(importance.items(), 1):
        print(f"      {i}. {feat}: {imp:.4f}")
    
    # Step 4: Save model
    print("\n4. Saving model...")
    model_path = "models/lap_time_predictor_barber.pkl"
    Path("models").mkdir(exist_ok=True)
    predictor.save_model(model_path)
    print(f"   ✅ Model saved to {model_path}")
    
    # Step 5: Test prediction
    print("\n5. Testing prediction...")
    # Use first feature set as example
    from app.data.lap_segmenter import get_lap_segmenter
    from app.data.feature_engine import get_feature_engine
    
    segmenter = get_lap_segmenter("../dataset")
    engine = get_feature_engine()
    
    lap_data = segmenter.segment_by_lap("barber", "R1", "GR86-002-000")
    test_features = engine.calculate_lap_features(lap_data[5], tire_age=5)
    
    predicted_time = predictor.predict(test_features)
    print(f"   Example prediction for Lap 5: {predicted_time:.2f}s")
    
    print("\n" + "="*80)
    print("✅ XGBOOST LAP PREDICTOR TEST COMPLETE!")
    print("="*80)
    
    # Quality assessment
    print("\n🎯 Model Quality Assessment:")
    if metrics['test_mae'] < 2.0:
        print("   ✅ EXCELLENT: MAE < 2s")
    elif metrics['test_mae'] < 5.0:
        print("   ✅ GOOD: MAE < 5s")
    else:
        print("   ⚠️  FAIR: MAE > 5s - consider more training data")
    
    if metrics['test_r2'] > 0.8:
        print("   ✅ EXCELLENT: R² > 0.8")
    elif metrics['test_r2'] > 0.6:
        print("   ✅ GOOD: R² > 0.6")
    else:
        print("   ⚠️  FAIR: R² < 0.6 - model may need tuning")
    
    return metrics


def main():
    """Run test."""
    try:
        metrics = test_lap_predictor()
        return 0
    except Exception as e:
        print(f"\n❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
