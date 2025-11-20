"""
Full Race Distance Simulator
Simulates complete races with multiple strategies, pit stops, and tire management.
"""

from __future__ import annotations
from typing import Optional, List, Dict, Any, Tuple
from dataclasses import dataclass, field
import pandas as pd
import numpy as np
from enum import Enum


class TireCompound(Enum):
    """Tire compound types with different characteristics."""
    SOFT = "soft"
    MEDIUM = "medium"
    HARD = "hard"


@dataclass
class TireCharacteristics:
    """Characteristics of different tire compounds."""
    compound: TireCompound
    base_grip_advantage: float  # Lap time advantage when fresh (seconds)
    degradation_rate: float  # Degradation % per lap
    cliff_lap: int  # Lap where performance drops significantly
    optimal_stint_length: int  # Optimal laps before change
    
    @classmethod
    def get_compound_characteristics(cls, compound: TireCompound) -> 'TireCharacteristics':
        """Get predefined characteristics for tire compounds."""
        characteristics = {
            TireCompound.SOFT: cls(
                compound=TireCompound.SOFT,
                base_grip_advantage=-0.5,  # 0.5s faster per lap
                degradation_rate=0.3,  # 0.3% degradation per lap
                cliff_lap=12,
                optimal_stint_length=10
            ),
            TireCompound.MEDIUM: cls(
                compound=TireCompound.MEDIUM,
                base_grip_advantage=0.0,  # Baseline
                degradation_rate=0.15,  # 0.15% degradation per lap
                cliff_lap=18,
                optimal_stint_length=15
            ),
            TireCompound.HARD: cls(
                compound=TireCompound.HARD,
                base_grip_advantage=0.3,  # 0.3s slower per lap
                degradation_rate=0.08,  # 0.08% degradation per lap
                cliff_lap=25,
                optimal_stint_length=20
            ),
        }
        return characteristics[compound]


@dataclass
class PitStop:
    """Pit stop configuration."""
    lap: int
    new_compound: TireCompound
    pit_loss_time: float = 45.0  # Time lost in pit (seconds)
    
    
@dataclass
class RaceStrategy:
    """Complete race strategy definition."""
    name: str
    starting_compound: TireCompound
    pit_stops: List[PitStop]
    fuel_saving_mode: bool = False
    push_laps: List[int] = field(default_factory=list)  # Laps to push hard
    
    
@dataclass
class LapResult:
    """Result of a single lap simulation."""
    lap_number: int
    lap_time: float
    cumulative_time: float
    tire_compound: TireCompound
    tire_age: int
    tire_degradation: float
    position_estimate: int
    gap_to_leader: float
    is_pit_lap: bool
    fuel_load: float
    notes: str = ""


@dataclass
class RaceSimulationResult:
    """Complete race simulation result."""
    strategy: RaceStrategy
    lap_results: List[LapResult]
    total_time: float
    final_position: int
    total_pit_stops: int
    average_lap_time: float
    fastest_lap: float
    slowest_lap: float
    tire_usage_summary: Dict[TireCompound, int]
    
    
class RaceSimulator:
    """
    Simulates full race distance with multiple strategies and realistic tire/fuel dynamics.
    """
    
    def __init__(
        self,
        baseline_lap_time: float,
        total_race_laps: int,
        track_name: str = "Unknown",
        fuel_effect_per_lap: float = 0.03,  # 0.03s per lap of fuel
        traffic_variance: float = 0.2  # Random traffic impact
    ):
        """
        Initialize race simulator.
        
        Args:
            baseline_lap_time: Baseline fastest lap time (seconds)
            total_race_laps: Total number of laps in race
            track_name: Name of the track
            fuel_effect_per_lap: Lap time penalty per lap of fuel (seconds)
            traffic_variance: Random variation from traffic (seconds)
        """
        self.baseline_lap_time = baseline_lap_time
        self.total_race_laps = total_race_laps
        self.track_name = track_name
        self.fuel_effect_per_lap = fuel_effect_per_lap
        self.traffic_variance = traffic_variance
        
    def simulate_race(
        self,
        strategy: RaceStrategy,
        random_seed: Optional[int] = None
    ) -> RaceSimulationResult:
        """
        Simulate a complete race with the given strategy.
        
        Args:
            strategy: Race strategy to simulate
            random_seed: Random seed for reproducibility
            
        Returns:
            RaceSimulationResult with complete lap-by-lap data
        """
        if random_seed is not None:
            np.random.seed(random_seed)
        
        lap_results = []
        cumulative_time = 0.0
        current_compound = strategy.starting_compound
        tire_age = 0
        fuel_load = self.total_race_laps
        
        # Track tire usage
        tire_usage = {compound: 0 for compound in TireCompound}
        pit_stop_count = 0
        
        for lap in range(1, self.total_race_laps + 1):
            # Check for pit stop
            is_pit_lap = any(ps.lap == lap for ps in strategy.pit_stops)
            
            if is_pit_lap:
                # Find pit stop configuration
                pit_stop = next(ps for ps in strategy.pit_stops if ps.lap == lap)
                
                # Change tires
                current_compound = pit_stop.new_compound
                tire_age = 0
                pit_stop_count += 1
                
                # Add pit time
                pit_loss = pit_stop.pit_loss_time
                cumulative_time += pit_loss
            else:
                tire_age += 1
            
            # Calculate lap time
            lap_time = self._calculate_lap_time(
                lap_number=lap,
                tire_compound=current_compound,
                tire_age=tire_age,
                fuel_load=fuel_load,
                is_push_lap=lap in strategy.push_laps,
                fuel_saving=strategy.fuel_saving_mode
            )
            
            # Add to cumulative time
            cumulative_time += lap_time
            
            # Calculate tire degradation
            tire_chars = TireCharacteristics.get_compound_characteristics(current_compound)
            tire_degradation = self._calculate_tire_degradation(tire_age, tire_chars)
            
            # Track tire usage
            tire_usage[current_compound] += 1
            
            # Reduce fuel
            fuel_load -= 1
            
            # Store lap result
            lap_result = LapResult(
                lap_number=lap,
                lap_time=lap_time,
                cumulative_time=cumulative_time,
                tire_compound=current_compound,
                tire_age=tire_age,
                tire_degradation=tire_degradation,
                position_estimate=1,  # Will be calculated in comparison
                gap_to_leader=0.0,
                is_pit_lap=is_pit_lap,
                fuel_load=fuel_load,
                notes=self._generate_lap_notes(lap, tire_age, tire_chars, is_pit_lap)
            )
            lap_results.append(lap_result)
        
        # Calculate statistics
        lap_times = [lr.lap_time for lr in lap_results if not lr.is_pit_lap]
        avg_lap_time = np.mean(lap_times)
        fastest_lap = np.min(lap_times)
        slowest_lap = np.max(lap_times)
        
        return RaceSimulationResult(
            strategy=strategy,
            lap_results=lap_results,
            total_time=cumulative_time,
            final_position=1,  # Will be calculated in comparison
            total_pit_stops=pit_stop_count,
            average_lap_time=avg_lap_time,
            fastest_lap=fastest_lap,
            slowest_lap=slowest_lap,
            tire_usage_summary=tire_usage
        )
    
    def simulate_multiple_strategies(
        self,
        strategies: List[RaceStrategy],
        random_seed: Optional[int] = 42
    ) -> List[RaceSimulationResult]:
        """
        Simulate multiple strategies and rank them.
        
        Args:
            strategies: List of strategies to simulate
            random_seed: Random seed for reproducibility
            
        Returns:
            List of RaceSimulationResults sorted by total time
        """
        results = []
        
        for strategy in strategies:
            result = self.simulate_race(strategy, random_seed)
            results.append(result)
        
        # Sort by total time (fastest first)
        results.sort(key=lambda r: r.total_time)
        
        # Update positions and gaps
        for i, result in enumerate(results):
            result.final_position = i + 1
            
            # Update lap-by-lap gaps to leader
            leader_result = results[0]
            for lap_idx, lap_result in enumerate(result.lap_results):
                lap_result.position_estimate = i + 1
                lap_result.gap_to_leader = (
                    lap_result.cumulative_time - 
                    leader_result.lap_results[lap_idx].cumulative_time
                )
        
        return results
    
    def _calculate_lap_time(
        self,
        lap_number: int,
        tire_compound: TireCompound,
        tire_age: int,
        fuel_load: float,
        is_push_lap: bool,
        fuel_saving: bool
    ) -> float:
        """Calculate lap time based on all factors."""
        # Start with baseline
        lap_time = self.baseline_lap_time
        
        # Tire compound effect
        tire_chars = TireCharacteristics.get_compound_characteristics(tire_compound)
        lap_time += tire_chars.base_grip_advantage
        
        # Tire degradation effect
        degradation = self._calculate_tire_degradation(tire_age, tire_chars)
        lap_time += self.baseline_lap_time * (degradation / 100)
        
        # Fuel load effect
        fuel_penalty = fuel_load * self.fuel_effect_per_lap
        lap_time += fuel_penalty
        
        # Push lap (go faster, but adds risk)
        if is_push_lap:
            lap_time -= 0.3  # 0.3s faster when pushing
        
        # Fuel saving mode
        if fuel_saving:
            lap_time += 0.2  # 0.2s slower when saving fuel
        
        # Traffic variance (random)
        traffic = np.random.uniform(-self.traffic_variance, self.traffic_variance)
        lap_time += traffic
        
        return max(lap_time, self.baseline_lap_time * 0.95)  # Can't be too fast
    
    def _calculate_tire_degradation(
        self,
        tire_age: int,
        tire_chars: TireCharacteristics
    ) -> float:
        """
        Calculate tire degradation percentage.
        
        Applies linear degradation until cliff, then exponential.
        """
        if tire_age == 0:
            return 0.0
        
        # Linear degradation
        base_deg = tire_age * tire_chars.degradation_rate
        
        # Cliff effect (exponential after cliff lap)
        if tire_age > tire_chars.cliff_lap:
            laps_past_cliff = tire_age - tire_chars.cliff_lap
            cliff_penalty = (laps_past_cliff ** 1.5) * 0.2
            base_deg += cliff_penalty
        
        return base_deg
    
    def _generate_lap_notes(
        self,
        lap: int,
        tire_age: int,
        tire_chars: TireCharacteristics,
        is_pit_lap: bool
    ) -> str:
        """Generate descriptive notes for the lap."""
        if is_pit_lap:
            return f"PIT STOP - Fresh {tire_chars.compound.value} tires"
        
        if tire_age == 1:
            return f"Fresh {tire_chars.compound.value} tires"
        
        if tire_age > tire_chars.cliff_lap:
            laps_past = tire_age - tire_chars.cliff_lap
            return f"CRITICAL: {laps_past} laps past cliff!"
        
        if tire_age >= tire_chars.optimal_stint_length:
            return f"Tires worn - consider pit stop"
        
        if tire_age < 5:
            return f"Good tire performance"
        
        return f"Managing tire wear"
    
    def generate_default_strategies(self) -> List[RaceStrategy]:
        """
        Generate a set of common racing strategies for the race distance.
        
        Returns:
            List of pre-configured strategies
        """
        strategies = []
        
        # Strategy 1: No Stop (if race is short enough)
        if self.total_race_laps <= 25:
            strategies.append(RaceStrategy(
                name="no_stop",
                starting_compound=TireCompound.MEDIUM,
                pit_stops=[]
            ))
        
        # Strategy 2: One Stop - Early (Lap 10-12)
        early_stop_lap = min(12, self.total_race_laps // 2)
        strategies.append(RaceStrategy(
            name="one_stop_early",
            starting_compound=TireCompound.SOFT,
            pit_stops=[PitStop(lap=early_stop_lap, new_compound=TireCompound.MEDIUM)]
        ))
        
        # Strategy 3: One Stop - Late (Lap 18-20)
        late_stop_lap = min(18, int(self.total_race_laps * 0.65))
        strategies.append(RaceStrategy(
            name="one_stop_late",
            starting_compound=TireCompound.MEDIUM,
            pit_stops=[PitStop(lap=late_stop_lap, new_compound=TireCompound.SOFT)]
        ))
        
        # Strategy 4: Two Stop (aggressive)
        if self.total_race_laps > 30:
            first_stop = self.total_race_laps // 3
            second_stop = int(self.total_race_laps * 0.67)
            strategies.append(RaceStrategy(
                name="two_stop_aggressive",
                starting_compound=TireCompound.SOFT,
                pit_stops=[
                    PitStop(lap=first_stop, new_compound=TireCompound.SOFT),
                    PitStop(lap=second_stop, new_compound=TireCompound.SOFT)
                ]
            ))
        
        # Strategy 5: Conservative (Medium-Hard)
        mid_stop = self.total_race_laps // 2
        strategies.append(RaceStrategy(
            name="conservative",
            starting_compound=TireCompound.MEDIUM,
            pit_stops=[PitStop(lap=mid_stop, new_compound=TireCompound.HARD)]
        ))
        
        return strategies
