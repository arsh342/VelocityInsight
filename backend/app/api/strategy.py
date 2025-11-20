from fastapi import APIRouter, Query, HTTPException
from typing import Optional, Dict, Any, List
import pandas as pd
from ..core.config import settings
from ..data.loader import load_lap_times, load_race_telemetry_wide
from ..ml.tire_degradation import TireDegradationModel
from ..ml.pit_strategy import PitStrategyOptimizer

router = APIRouter(prefix="/strategy", tags=["strategy"])


@router.get("/pit/{track}/{race}/{vehicle_id}")
async def get_pit_strategy(
    track: str,
    race: str,
    vehicle_id: str,
    current_lap: int = Query(..., description="Current lap number"),
    total_race_laps: int = Query(30, description="Total laps in race"),
    current_tire_age: int = Query(..., description="Laps on current tires"),
    track_position: Optional[int] = Query(None, description="Current race position"),
    gap_to_leader: Optional[float] = Query(None, description="Gap to leader in seconds"),
    gap_to_next: Optional[float] = Query(None, description="Gap to car ahead in seconds")
) -> Dict[str, Any]:
    """
    Calculate optimal pit stop strategy for a vehicle.
    
    Returns pit window recommendations, time loss/gain projections, and strategic advice.
    """
    try:
        # Load data and build degradation model
        start, end, lapt = load_lap_times(settings.dataset_root, track, race)
        
        tire_model = TireDegradationModel()
        degradation_df = tire_model.calculate_lap_degradation(lapt, vehicle_id)
        
        if degradation_df.empty:
            raise HTTPException(status_code=404, detail=f"No data for vehicle {vehicle_id}")
        
        model_stats = tire_model.fit_degradation_model(degradation_df)
        
        # Get baseline laptime and degradation rate
        baseline_time = float(degradation_df[degradation_df['vehicle_id'] == vehicle_id]['baseline_time'].iloc[0])
        degradation_rate = model_stats['avg_degradation_rate_per_lap']
        
        # Initialize pit strategy optimizer
        pit_optimizer = PitStrategyOptimizer()
        
        # Calculate optimal pit window
        strategy = pit_optimizer.calculate_pit_window(
            current_lap=current_lap,
            total_race_laps=total_race_laps,
            current_tire_age=current_tire_age,
            degradation_rate=abs(degradation_rate) if degradation_rate < 0 else degradation_rate,
            baseline_laptime=baseline_time,
            track_position=track_position,
            gap_to_leader=gap_to_leader,
            gap_to_next=gap_to_next
        )
        
        return {
            "vehicle_id": vehicle_id,
            "track": track,
            "race": race,
            "current_lap": current_lap,
            "current_tire_age": current_tire_age,
            "baseline_laptime": baseline_time,
            "degradation_rate_per_lap": abs(degradation_rate),
            "pit_strategy": strategy
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error calculating pit strategy: {str(e)}")


@router.get("/pit/{track}/{race}/{vehicle_id}/undercut")
async def analyze_undercut_opportunity(
    track: str,
    race: str,
    vehicle_id: str,
    current_lap: int = Query(..., description="Current lap number"),
    own_tire_age: int = Query(..., description="Laps on own tires"),
    competitor_tire_age: int = Query(..., description="Laps on competitor's tires"),
    gap_to_competitor: float = Query(..., description="Gap in seconds (positive if ahead)")
) -> Dict[str, Any]:
    """
    Analyze undercut opportunity against a competitor.
    
    Determines if pitting before the competitor would result in a position gain.
    """
    try:
        # Load data and build model
        start, end, lapt = load_lap_times(settings.dataset_root, track, race)
        
        tire_model = TireDegradationModel()
        degradation_df = tire_model.calculate_lap_degradation(lapt, vehicle_id)
        
        if degradation_df.empty:
            raise HTTPException(status_code=404, detail=f"No data for vehicle {vehicle_id}")
        
        model_stats = tire_model.fit_degradation_model(degradation_df)
        
        baseline_time = float(degradation_df[degradation_df['vehicle_id'] == vehicle_id]['baseline_time'].iloc[0])
        degradation_rate = abs(model_stats['avg_degradation_rate_per_lap'])
        
        # Calculate undercut opportunity
        pit_optimizer = PitStrategyOptimizer()
        undercut_analysis = pit_optimizer.calculate_undercut_opportunity(
            current_lap=current_lap,
            own_tire_age=own_tire_age,
            competitor_tire_age=competitor_tire_age,
            gap_to_competitor=gap_to_competitor,
            degradation_rate=degradation_rate,
            baseline_laptime=baseline_time
        )
        
        return {
            "vehicle_id": vehicle_id,
            "current_lap": current_lap,
            "undercut_analysis": {
                "undercut_viable": bool(undercut_analysis['undercut_viable']),
                "time_gain_potential": float(undercut_analysis['time_gain_potential']),
                "gap_required": float(undercut_analysis['gap_required']),
                "advantage_margin": float(undercut_analysis['advantage_margin']),
                "recommendation": str(undercut_analysis['recommendation'])
            },
            "tactical_recommendation": _generate_undercut_advice(undercut_analysis, gap_to_competitor)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error analyzing undercut: {str(e)}")


@router.post("/pit/{track}/{race}/{vehicle_id}/simulate")
async def simulate_race_strategy(
    track: str,
    race: str,
    vehicle_id: str,
    current_lap: int = Query(..., description="Current lap number"),
    total_race_laps: int = Query(30, description="Total laps in race"),
    current_tire_age: int = Query(..., description="Laps on current tires"),
    pit_laps: List[int] = Query(..., description="Laps to execute pit stops")
) -> Dict[str, Any]:
    """
    Simulate a race with a given pit stop strategy.
    
    Returns projected finish time and lap-by-lap analysis.
    """
    try:
        # Load data and build model
        start, end, lapt = load_lap_times(settings.dataset_root, track, race)
        
        tire_model = TireDegradationModel()
        degradation_df = tire_model.calculate_lap_degradation(lapt, vehicle_id)
        
        if degradation_df.empty:
            raise HTTPException(status_code=404, detail=f"No data for vehicle {vehicle_id}")
        
        model_stats = tire_model.fit_degradation_model(degradation_df)
        
        baseline_time = float(degradation_df[degradation_df['vehicle_id'] == vehicle_id]['baseline_time'].iloc[0])
        degradation_rate = abs(model_stats['avg_degradation_rate_per_lap'])
        
        # Run simulation
        pit_optimizer = PitStrategyOptimizer()
        simulation = pit_optimizer.simulate_race_to_finish(
            current_lap=current_lap,
            total_race_laps=total_race_laps,
            current_tire_age=current_tire_age,
            pit_laps=pit_laps,
            degradation_rate=degradation_rate,
            baseline_laptime=baseline_time
        )
        
        return {
            "vehicle_id": vehicle_id,
            "strategy": {
                "pit_laps": pit_laps,
                "total_pit_stops": len(pit_laps)
            },
            "simulation_results": simulation,
            "performance_summary": _generate_simulation_summary(simulation, baseline_time)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error simulating strategy: {str(e)}")


@router.get("/compare/{track}/{race}")
async def compare_strategies(
    track: str,
    race: str,
    vehicle_id: str = Query(..., description="Vehicle to analyze"),
    current_lap: int = Query(..., description="Current lap"),
    total_race_laps: int = Query(30, description="Total race laps"),
    current_tire_age: int = Query(..., description="Current tire age")
) -> Dict[str, Any]:
    """
    Compare multiple pit stop strategies side-by-side.
    
    Evaluates 1-stop, 2-stop, and no-stop strategies.
    """
    try:
        # Load data
        start, end, lapt = load_lap_times(settings.dataset_root, track, race)
        
        tire_model = TireDegradationModel()
        degradation_df = tire_model.calculate_lap_degradation(lapt, vehicle_id)
        
        if degradation_df.empty:
            raise HTTPException(status_code=404, detail=f"No data for vehicle {vehicle_id}")
        
        model_stats = tire_model.fit_degradation_model(degradation_df)
        
        baseline_time = float(degradation_df[degradation_df['vehicle_id'] == vehicle_id]['baseline_time'].iloc[0])
        degradation_rate = abs(model_stats['avg_degradation_rate_per_lap'])
        
        pit_optimizer = PitStrategyOptimizer()
        
        # Define strategies to compare
        remaining = total_race_laps - current_lap
        mid_point = current_lap + (remaining // 2)
        
        strategies = {
            "no_stop": [],
            "one_stop_early": [current_lap + 5],
            "one_stop_mid": [mid_point],
            "one_stop_late": [total_race_laps - 5] if total_race_laps - 5 > current_lap else [total_race_laps - 3],
            "two_stop": [current_lap + remaining // 3, current_lap + 2 * remaining // 3]
        }
        
        # Simulate each strategy
        comparisons = []
        for strategy_name, pit_laps in strategies.items():
            simulation = pit_optimizer.simulate_race_to_finish(
                current_lap=current_lap,
                total_race_laps=total_race_laps,
                current_tire_age=current_tire_age,
                pit_laps=pit_laps,
                degradation_rate=degradation_rate,
                baseline_laptime=baseline_time
            )
            
            comparisons.append({
                "strategy": strategy_name,
                "pit_laps": pit_laps,
                "total_time": simulation['total_race_time'],
                "average_laptime": simulation['average_lap_time'],
                "total_pit_stops": len(pit_laps)
            })
        
        # Sort by total time (fastest first)
        comparisons.sort(key=lambda x: x['total_time'])
        
        return {
            "vehicle_id": vehicle_id,
            "analysis_point": {
                "current_lap": current_lap,
                "total_race_laps": total_race_laps,
                "current_tire_age": current_tire_age
            },
            "strategy_comparison": comparisons,
            "recommended_strategy": comparisons[0]['strategy']
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error comparing strategies: {str(e)}")


def _generate_undercut_advice(undercut_analysis: Dict[str, Any], gap: float) -> str:
    """Generate tactical advice for undercut scenario."""
    if undercut_analysis['undercut_viable']:
        if undercut_analysis['advantage_margin'] > 3:
            return "Strong undercut opportunity - pit this lap to gain position"
        else:
            return "Marginal undercut opportunity - consider pitting if tire performance is declining"
    else:
        if abs(gap) < 2:
            return "Gap too small for undercut - maintain position or wait for competitor to pit"
        else:
            return "Undercut not viable with current gap - focus on tire management"


def _generate_simulation_summary(simulation: Dict[str, Any], baseline: float) -> Dict[str, Any]:
    """Generate summary insights from race simulation."""
    avg_degradation = ((simulation['average_lap_time'] - baseline) / baseline) * 100
    
    return {
        "projected_finish_position_change": 0,  # Would need competitor data
        "average_performance_loss": f"{avg_degradation:.2f}%",
        "tire_management_rating": "excellent" if avg_degradation < 2 else "good" if avg_degradation < 4 else "poor",
        "strategy_viability": "optimal" if simulation['total_pit_stops'] <= 2 else "suboptimal"
    }
