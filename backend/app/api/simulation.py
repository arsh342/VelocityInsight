from fastapi import APIRouter, Query, HTTPException
from typing import Optional, Dict, Any, List
import pandas as pd
from ..core.config import settings
from ..data.loader import load_lap_times
from ..ml.race_simulator import (
    RaceSimulator,
    RaceStrategy,
    PitStop,
    TireCompound
)
from ..ml.tire_degradation import TireDegradationModel

router = APIRouter(prefix="/simulation", tags=["simulation"])


@router.get("/race/{track}/{race}")
async def simulate_full_race(
    track: str,
    race: str,
    strategies: Optional[str] = Query(
        "all",
        description="Comma-separated strategy names or 'all' for default strategies"
    )
) -> Dict[str, Any]:
    """
    Simulate a full race distance with multiple strategies.
    
    Returns lap-by-lap simulation data showing how different strategies perform.
    """
    try:
        # Load race data to get baseline lap time and race length
        start, end, lapt = load_lap_times(settings.dataset_root, track, race)
        
        if lapt.empty:
            raise HTTPException(status_code=404, detail="No lap time data found")
        
        # Calculate baseline lap time from actual data
        tire_model = TireDegradationModel()
        degradation_df = tire_model.calculate_lap_degradation(lapt)
        
        if degradation_df.empty:
            raise HTTPException(status_code=404, detail="Insufficient data for simulation")
        
        baseline_lap_time = float(degradation_df['baseline_time'].mean())
        total_laps = int(lapt['lap'].max())
        
        # Initialize simulator
        simulator = RaceSimulator(
            baseline_lap_time=baseline_lap_time,
            total_race_laps=total_laps,
            track_name=track
        )
        
        # Generate or parse strategies
        if strategies == "all":
            strategy_list = simulator.generate_default_strategies()
        else:
            # Parse custom strategies (simplified for now)
            strategy_list = simulator.generate_default_strategies()
        
        # Run simulations
        results = simulator.simulate_multiple_strategies(strategy_list)
        
        # Format response
        return {
            "track": track,
            "race": race,
            "simulation_config": {
                "baseline_lap_time": baseline_lap_time,
                "total_race_laps": total_laps,
                "strategies_simulated": len(results)
            },
            "results": [
                {
                    "position": result.final_position,
                    "strategy_name": result.strategy.name,
                    "total_time": result.total_time,
                    "total_time_formatted": f"{int(result.total_time // 60)}:{result.total_time % 60:.3f}",
                    "gap_to_leader": result.lap_results[-1].gap_to_leader if result.final_position > 1 else 0.0,
                    "total_pit_stops": result.total_pit_stops,
                    "average_lap_time": result.average_lap_time,
                    "fastest_lap": result.fastest_lap,
                    "starting_compound": result.strategy.starting_compound.value,
                    "tire_usage": {
                        compound.value: laps 
                        for compound, laps in result.tire_usage_summary.items()
                        if laps > 0
                    },
                    "lap_by_lap": [
                        {
                            "lap": lap.lap_number,
                            "lap_time": round(lap.lap_time, 3),
                            "cumulative_time": round(lap.cumulative_time, 2),
                            "tire_compound": lap.tire_compound.value,
                            "tire_age": lap.tire_age,
                            "tire_degradation": round(lap.tire_degradation, 2),
                            "gap_to_leader": round(lap.gap_to_leader, 2),
                            "is_pit_lap": lap.is_pit_lap,
                            "notes": lap.notes
                        }
                        for lap in result.lap_results
                    ]
                }
                for result in results
            ]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error simulating race: {str(e)}")


@router.post("/race/custom")
async def simulate_custom_strategy(
    track: str,
    race: str,
    strategy_name: str,
    starting_compound: str = "medium",
    pit_stops: List[Dict[str, Any]] = []
) -> Dict[str, Any]:
    """
    Simulate a single custom race strategy.
    
    Args:
        track: Track name
        race: Race identifier
        strategy_name: Name for this strategy
        starting_compound: Starting tire compound (soft/medium/hard)
        pit_stops: List of pit stops with lap and new_compound
    """
    try:
        # Load race data
        start, end, lapt = load_lap_times(settings.dataset_root, track, race)
        
        if lapt.empty:
            raise HTTPException(status_code=404, detail="No lap time data found")
        
        # Calculate baseline
        tire_model = TireDegradationModel()
        degradation_df = tire_model.calculate_lap_degradation(lapt)
        baseline_lap_time = float(degradation_df['baseline_time'].mean())
        total_laps = int(lapt['lap'].max())
        
        # Parse strategy
        try:
            compound_map = {
                "soft": TireCompound.SOFT,
                "medium": TireCompound.MEDIUM,
                "hard": TireCompound.HARD
            }
            
            start_compound = compound_map.get(starting_compound.lower(), TireCompound.MEDIUM)
            
            parsed_pit_stops = [
                PitStop(
                    lap=ps['lap'],
                    new_compound=compound_map.get(ps['new_compound'].lower(), TireCompound.MEDIUM)
                )
                for ps in pit_stops
            ]
            
            custom_strategy = RaceStrategy(
                name=strategy_name,
                starting_compound=start_compound,
                pit_stops=parsed_pit_stops
            )
            
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Invalid strategy configuration: {str(e)}")
        
        # Run simulation
        simulator = RaceSimulator(
            baseline_lap_time=baseline_lap_time,
            total_race_laps=total_laps,
            track_name=track
        )
        
        result = simulator.simulate_race(custom_strategy)
        
        return {
            "strategy_name": result.strategy.name,
            "total_time": result.total_time,
            "total_time_formatted": f"{int(result.total_time // 60)}:{result.total_time % 60:.3f}",
            "total_pit_stops": result.total_pit_stops,
            "average_lap_time": result.average_lap_time,
            "fastest_lap": result.fastest_lap,
            "slowest_lap": result.slowest_lap,
            "tire_usage": {
                compound.value: laps 
                for compound, laps in result.tire_usage_summary.items()
                if laps > 0
            },
            "lap_by_lap": [
                {
                    "lap": lap.lap_number,
                    "lap_time": round(lap.lap_time, 3),
                    "cumulative_time": round(lap.cumulative_time, 2),
                    "tire_compound": lap.tire_compound.value,
                    "tire_age": lap.tire_age,
                    "tire_degradation": round(lap.tire_degradation, 2),
                    "fuel_load": lap.fuel_load,
                    "is_pit_lap": lap.is_pit_lap,
                    "notes": lap.notes
                }
                for lap in result.lap_results
            ]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error simulating custom strategy: {str(e)}")


@router.get("/compare/{track}/{race}")
async def compare_strategies(
    track: str,
    race: str,
    strategy1: str = Query("one_stop_early", description="First strategy to compare"),
    strategy2: str = Query("one_stop_late", description="Second strategy to compare")
) -> Dict[str, Any]:
    """
    Compare two specific strategies side-by-side.
    
    Returns lap-by-lap comparison showing time gaps and position changes.
    """
    try:
        # Load data
        start, end, lapt = load_lap_times(settings.dataset_root, track, race)
        tire_model = TireDegradationModel()
        degradation_df = tire_model.calculate_lap_degradation(lapt)
        baseline_lap_time = float(degradation_df['baseline_time'].mean())
        total_laps = int(lapt['lap'].max())
        
        # Initialize simulator
        simulator = RaceSimulator(
            baseline_lap_time=baseline_lap_time,
            total_race_laps=total_laps,
            track_name=track
        )
        
        # Get all strategies
        all_strategies = simulator.generate_default_strategies()
        strategy_dict = {s.name: s for s in all_strategies}
        
        if strategy1 not in strategy_dict:
            raise HTTPException(status_code=404, detail=f"Strategy '{strategy1}' not found")
        if strategy2 not in strategy_dict:
            raise HTTPException(status_code=404, detail=f"Strategy '{strategy2}' not found")
        
        # Simulate both
        result1 = simulator.simulate_race(strategy_dict[strategy1], random_seed=42)
        result2 = simulator.simulate_race(strategy_dict[strategy2], random_seed=42)
        
        # Build comparison
        comparison = []
        for i in range(total_laps):
            lap1 = result1.lap_results[i]
            lap2 = result2.lap_results[i]
            
            comparison.append({
                "lap": lap1.lap_number,
                strategy1: {
                    "lap_time": round(lap1.lap_time, 3),
                    "cumulative_time": round(lap1.cumulative_time, 2),
                    "tire_compound": lap1.tire_compound.value,
                    "tire_age": lap1.tire_age,
                    "is_pit_lap": lap1.is_pit_lap
                },
                strategy2: {
                    "lap_time": round(lap2.lap_time, 3),
                    "cumulative_time": round(lap2.cumulative_time, 2),
                    "tire_compound": lap2.tire_compound.value,
                    "tire_age": lap2.tire_age,
                    "is_pit_lap": lap2.is_pit_lap
                },
                "gap": round(lap2.cumulative_time - lap1.cumulative_time, 2),
                "leader": strategy1 if lap1.cumulative_time < lap2.cumulative_time else strategy2
            })
        
        return {
            "track": track,
            "race": race,
            "strategy1": strategy1,
            "strategy2": strategy2,
            "winner": strategy1 if result1.total_time < result2.total_time else strategy2,
            "time_difference": abs(result1.total_time - result2.total_time),
            "summary": {
                strategy1: {
                    "total_time": result1.total_time,
                    "pit_stops": result1.total_pit_stops,
                    "avg_lap": result1.average_lap_time,
                    "fastest_lap": result1.fastest_lap
                },
                strategy2: {
                    "total_time": result2.total_time,
                    "pit_stops": result2.total_pit_stops,
                    "avg_lap": result2.average_lap_time,
                    "fastest_lap": result2.fastest_lap
                }
            },
            "lap_by_lap_comparison": comparison
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error comparing strategies: {str(e)}")
