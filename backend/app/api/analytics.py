from fastapi import APIRouter, Query, HTTPException
from typing import Optional, Dict, Any, List
import pandas as pd
from ..core.config import settings
from ..data.loader import load_lap_times, load_race_telemetry_wide
from ..ml.tire_degradation import (
    TireDegradationModel, 
    DrivingStyleAnalyzer,
    detect_pit_stops_from_lap_times,
    load_pit_stops_from_endurance_data,
    classify_race_type
)

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/degradation/{track}/{race}")
async def get_tire_degradation_analysis(
    track: str,
    race: str,
    vehicle_id: Optional[str] = Query(None, description="Filter by specific vehicle ID")
) -> Dict[str, Any]:
    """
    Analyze tire degradation patterns for a race with pit stop detection and race type classification.
    
    Returns degradation metrics, model performance, predictions, and strategic recommendations.
    """
    try:
        # Load lap time data
        start, end, lapt = load_lap_times(settings.dataset_root, track, race)
        
        if lapt.empty:
            raise HTTPException(status_code=404, detail="No lap time data found")
        
        # Detect/load pit stops
        pit_stops_from_data = load_pit_stops_from_endurance_data(settings.dataset_root, track, race)
        pit_stops_from_laps = detect_pit_stops_from_lap_times(lapt)
        
        # Combine pit stop data (prefer endurance data if available)
        pit_stops = {**pit_stops_from_laps, **pit_stops_from_data}
        
        # Classify race type
        max_laps = int(lapt['lap'].max())
        race_type, strategy_note = classify_race_type(max_laps)
        
        # Initialize and run degradation analysis with pit stop awareness
        tire_model = TireDegradationModel()
        degradation_df = tire_model.calculate_lap_degradation(lapt, vehicle_id, pit_stops)
        
        if degradation_df.empty:
            raise HTTPException(status_code=404, detail="Insufficient data for degradation analysis")
        
        # Fit model and get performance metrics
        model_stats = tire_model.fit_degradation_model(degradation_df)
        
        # Determine if pit stop is needed based on degradation rate
        degradation_rate = model_stats['avg_degradation_rate_per_lap']
        is_sprint_no_pit = race_type == "SPRINT" and abs(degradation_rate) < 0.1
        
        # Generate summary statistics
        summary_stats = {
            "total_vehicles": int(degradation_df['vehicle_id'].nunique()),
            "total_laps_analyzed": int(len(degradation_df)),
            "total_pit_stops_detected": sum(len(stops) for stops in pit_stops.values()),
            "avg_degradation_per_lap": {int(k): float(v) for k, v in degradation_df.groupby('lap_number')['degradation_pct'].mean().to_dict().items()},
            "degradation_by_vehicle": {str(k): float(v) for k, v in degradation_df.groupby('vehicle_id')['degradation_pct'].mean().to_dict().items()}
        }
        
        # Sample predictions for next 10 laps
        sample_vehicle = str(degradation_df['vehicle_id'].iloc[0])
        baseline_time = float(degradation_df[degradation_df['vehicle_id'] == sample_vehicle]['baseline_time'].iloc[0])
        max_tire_age = int(degradation_df[degradation_df['vehicle_id'] == sample_vehicle]['tire_age'].max())
        
        predictions = tire_model.estimate_remaining_performance(
            current_tire_age=max_tire_age,
            target_laps=10,
            baseline_time=baseline_time
        )
        
        return {
            "track": track,
            "race": race,
            "vehicle_filter": vehicle_id,
            "race_classification": {
                "type": race_type,
                "total_laps": max_laps,
                "strategy_note": strategy_note,
                "sprint_no_pit_recommended": is_sprint_no_pit
            },
            "pit_stop_data": {
                "detected_pit_stops": pit_stops,
                "total_pit_stops": sum(len(stops) for stops in pit_stops.values()),
                "vehicles_with_pit_stops": len(pit_stops)
            },
            "model_performance": model_stats,
            "summary_statistics": summary_stats,
            "sample_predictions": predictions,
            "degradation_data": degradation_df.to_dict('records')[:100]  # Limit response size
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error analyzing tire degradation: {str(e)}")


@router.get("/degradation/{track}/{race}/{vehicle_id}/predictions")
async def get_tire_degradation_predictions(
    track: str,
    race: str,
    vehicle_id: str,
    current_tire_age: int = Query(..., description="Current laps on tires"),
    prediction_laps: int = Query(10, description="Number of laps to predict ahead"),
    baseline_time: Optional[float] = Query(None, description="Baseline lap time (auto-calculated if not provided)")
) -> Dict[str, Any]:
    """
    Get tire degradation predictions for a specific vehicle based on tire age.
    """
    try:
        # Load data and fit model
        start, end, lapt = load_lap_times(settings.dataset_root, track, race)
        
        tire_model = TireDegradationModel()
        degradation_df = tire_model.calculate_lap_degradation(lapt, vehicle_id)
        
        if degradation_df.empty:
            raise HTTPException(status_code=404, detail=f"No degradation data for vehicle {vehicle_id}")
        
        tire_model.fit_degradation_model(degradation_df)
        
        # Use provided baseline or calculate from data
        if baseline_time is None:
            baseline_time = float(degradation_df[degradation_df['vehicle_id'] == vehicle_id]['baseline_time'].iloc[0])
        
        # Generate predictions
        predictions = tire_model.estimate_remaining_performance(
            current_tire_age=current_tire_age,
            target_laps=prediction_laps,
            baseline_time=baseline_time
        )
        
        # Calculate optimal stint length
        stint_recommendation = tire_model.calculate_optimal_stint_length(
            current_tire_age=current_tire_age,
            baseline_time=baseline_time,
            max_degradation_threshold=3.0  # 3% degradation threshold
        )
        
        return {
            "vehicle_id": vehicle_id,
            "current_tire_age": current_tire_age,
            "baseline_time": baseline_time,
            "predictions": predictions,
            "stint_recommendation": stint_recommendation
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating predictions: {str(e)}")


@router.get("/driving-style/{track}/{race}/{vehicle_id}")
async def get_driving_style_analysis(
    track: str,
    race: str,
    vehicle_id: str,
    sample_size: int = Query(5000, description="Number of telemetry rows to analyze for performance")
) -> Dict[str, Any]:
    """
    Analyze driving style and its impact on tire degradation - optimized with sampling.
    """
    try:
        # Load telemetry data with early filtering
        df_telemetry = load_race_telemetry_wide(settings.dataset_root, track, race)
        
        if df_telemetry.empty:
            raise HTTPException(status_code=404, detail="No telemetry data found")
        
        # Filter to vehicle early to reduce data size
        df_vehicle = df_telemetry[df_telemetry['vehicle_id'] == vehicle_id]
        
        if df_vehicle.empty:
            raise HTTPException(status_code=404, detail=f"Vehicle {vehicle_id} not found")
        
        # Sample data for faster processing while maintaining statistical validity
        if len(df_vehicle) > sample_size:
            df_vehicle = df_vehicle.sample(n=sample_size, random_state=42)
        
        # Analyze driving style on sampled data
        style_analyzer = DrivingStyleAnalyzer()
        aggression_metrics = style_analyzer.calculate_aggression_score(df_vehicle, vehicle_id)
        
        # Load degradation data for correlation (this is fast - uses lap times only)
        start, end, lapt = load_lap_times(settings.dataset_root, track, race)
        tire_model = TireDegradationModel()
        degradation_df = tire_model.calculate_lap_degradation(lapt, vehicle_id)
        
        degradation_summary = {}
        if not degradation_df.empty:
            tire_model.fit_degradation_model(degradation_df)
            degradation_summary = {
                "avg_degradation_rate": float(degradation_df['degradation_pct'].mean()),
                "max_degradation": float(degradation_df['degradation_pct'].max()),
                "degradation_variability": float(degradation_df['degradation_pct'].std())
            }
        
        # Correlate driving style with degradation
        style_impact = "unknown"
        if aggression_metrics.get('composite_aggression_score', 0) > 70:
            style_impact = "high_wear"
        elif aggression_metrics.get('composite_aggression_score', 0) > 40:
            style_impact = "moderate_wear"
        else:
            style_impact = "conservative"
        
        return {
            "vehicle_id": vehicle_id,
            "driving_style_metrics": aggression_metrics,
            "tire_degradation_summary": degradation_summary,
            "style_impact_assessment": style_impact,
            "recommendations": _generate_driving_recommendations(aggression_metrics, degradation_summary)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error analyzing driving style: {str(e)}")


def _generate_driving_recommendations(aggression_metrics: Dict[str, float], degradation_summary: Dict[str, Any]) -> List[str]:
    """Generate driving recommendations based on style analysis."""
    recommendations = []
    
    if aggression_metrics.get('brake_aggression', 0) > 50:
        recommendations.append("Consider smoother braking to reduce tire wear")
    
    if aggression_metrics.get('throttle_aggression', 0) > 30:
        recommendations.append("Gradual throttle application can improve tire longevity")
    
    if aggression_metrics.get('cornering_aggression', 0) > 2.0:
        recommendations.append("Reduce cornering speeds to minimize lateral tire stress")
    
    if degradation_summary.get('avg_degradation_rate', 0) > 2.0:
        recommendations.append("Current pace is causing high tire wear - consider pit strategy adjustment")
    
    if not recommendations:
        recommendations.append("Current driving style is well-optimized for tire preservation")
    
    return recommendations
