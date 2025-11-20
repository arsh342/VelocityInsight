from __future__ import annotations
from typing import Optional, List, Dict, Any, Tuple
import pandas as pd
import numpy as np
from dataclasses import dataclass


@dataclass
class PitStopScenario:
    """Represents a potential pit stop strategy scenario."""
    pit_lap: int
    time_in_pit: float  # seconds
    tire_age_at_pit: int  # laps on current tires
    projected_finish_time: float
    total_time_loss: float
    total_time_gain: float
    net_advantage: float
    recommendation_score: float


class PitStrategyOptimizer:
    """
    Optimizes pit stop strategy based on tire degradation, track position,
    and race conditions to maximize competitive advantage.
    """
    
    def __init__(self):
        self.typical_pit_time = 45.0  # seconds (typical GR Cup pit stop)
        self.track_position_weight = 0.3
        self.tire_performance_weight = 0.5
        self.race_position_weight = 0.2
        
    def calculate_pit_window(
        self,
        current_lap: int,
        total_race_laps: int,
        current_tire_age: int,
        degradation_rate: float,
        baseline_laptime: float,
        track_position: Optional[int] = None,
        gap_to_leader: Optional[float] = None,
        gap_to_next: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Calculate optimal pit stop window considering multiple factors.
        
        Args:
            current_lap: Current lap number
            total_race_laps: Total laps in the race
            current_tire_age: Laps completed on current tires
            degradation_rate: Degradation percentage per lap
            baseline_laptime: Best lap time achieved
            track_position: Current position in race (1st, 2nd, etc.)
            gap_to_leader: Time gap to race leader in seconds
            gap_to_next: Time gap to car ahead in seconds
            
        Returns:
            Dict with optimal pit strategy recommendations
        """
        remaining_laps = total_race_laps - current_lap
        
        # Calculate scenarios for different pit lap options
        scenarios = []
        
        # Evaluate pit stops from current lap to 15 laps ahead (or race end)
        max_lookahead = min(15, remaining_laps)
        
        for future_pit_lap in range(current_lap + 1, current_lap + max_lookahead + 1):
            scenario = self._evaluate_pit_scenario(
                current_lap=current_lap,
                pit_lap=future_pit_lap,
                total_race_laps=total_race_laps,
                current_tire_age=current_tire_age,
                degradation_rate=degradation_rate,
                baseline_laptime=baseline_laptime
            )
            scenarios.append(scenario)
        
        # Only evaluate no-pit scenario if remaining laps < 8 and current tires are relatively fresh
        # No-pit is rarely optimal in professional racing except very short sprints
        if remaining_laps <= 8 and current_tire_age < 12:
            no_pit_scenario = self._evaluate_no_pit_scenario(
                current_lap=current_lap,
                total_race_laps=total_race_laps,
                current_tire_age=current_tire_age,
                degradation_rate=degradation_rate,
                baseline_laptime=baseline_laptime
            )
            scenarios.append(no_pit_scenario)
        
        # Rank scenarios by net advantage
        scenarios.sort(key=lambda x: x.net_advantage, reverse=True)
        optimal_scenario = scenarios[0]
        
        # Generate strategic recommendation
        recommendation = self._generate_recommendation(
            optimal_scenario=optimal_scenario,
            current_lap=current_lap,
            track_position=track_position,
            gap_to_leader=gap_to_leader,
            gap_to_next=gap_to_next
        )
        
        return {
            "optimal_pit_lap": optimal_scenario.pit_lap,
            "laps_until_pit": optimal_scenario.pit_lap - current_lap if optimal_scenario.pit_lap > 0 else 0,
            "projected_time_loss": optimal_scenario.total_time_loss,
            "projected_time_gain": optimal_scenario.total_time_gain,
            "net_advantage": optimal_scenario.net_advantage,
            "recommendation": recommendation,
            "confidence_score": optimal_scenario.recommendation_score,
            "alternative_scenarios": [
                {
                    "pit_lap": s.pit_lap,
                    "net_advantage": s.net_advantage,
                    "score": s.recommendation_score
                }
                for s in scenarios[:3]  # Top 3 alternatives
            ]
        }
    
    def _evaluate_pit_scenario(
        self,
        current_lap: int,
        pit_lap: int,
        total_race_laps: int,
        current_tire_age: int,
        degradation_rate: float,
        baseline_laptime: float
    ) -> PitStopScenario:
        """Evaluate a specific pit stop scenario."""
        
        # Calculate tire age at pit
        tire_age_at_pit = current_tire_age + (pit_lap - current_lap)
        
        # Laps remaining after pit
        laps_after_pit = total_race_laps - pit_lap
        
        # Time loss from pit stop itself
        time_in_pit = self.typical_pit_time
        
        # Calculate cumulative time loss on old tires before pit
        time_loss_before_pit = 0
        for lap in range(current_lap + 1, pit_lap + 1):
            lap_tire_age = current_tire_age + (lap - current_lap)
            degradation = degradation_rate * lap_tire_age
            time_loss_before_pit += baseline_laptime * (degradation / 100)
        
        # Calculate time gain on fresh tires after pit vs continuing on old tires
        time_gain_after_pit = 0
        for lap in range(pit_lap + 1, total_race_laps + 1):
            # Time on fresh tires
            fresh_tire_age = lap - pit_lap
            fresh_degradation = degradation_rate * fresh_tire_age
            fresh_time = baseline_laptime * (1 + fresh_degradation / 100)
            
            # Time on old tires (if no pit)
            old_tire_age = current_tire_age + (lap - current_lap)
            old_degradation = degradation_rate * old_tire_age
            old_time = baseline_laptime * (1 + old_degradation / 100)
            
            # Gain is the difference
            time_gain_after_pit += (old_time - fresh_time)
        
        # Total time calculations
        total_time_loss = time_in_pit + time_loss_before_pit
        total_time_gain = time_gain_after_pit
        net_advantage = total_time_gain - total_time_loss
        
        # Calculate recommendation score (0-100)
        # Higher score = better strategy
        score = 50 + (net_advantage / 5)  # Normalize around 50
        score = max(0, min(100, score))  # Clamp to 0-100
        
        return PitStopScenario(
            pit_lap=pit_lap,
            time_in_pit=time_in_pit,
            tire_age_at_pit=tire_age_at_pit,
            projected_finish_time=0,  # Can be calculated with more data
            total_time_loss=total_time_loss,
            total_time_gain=total_time_gain,
            net_advantage=net_advantage,
            recommendation_score=score
        )
    
    def _evaluate_no_pit_scenario(
        self,
        current_lap: int,
        total_race_laps: int,
        current_tire_age: int,
        degradation_rate: float,
        baseline_laptime: float
    ) -> PitStopScenario:
        """Evaluate scenario where no pit stop is taken."""
        
        remaining_laps = total_race_laps - current_lap
        
        # Calculate cumulative time loss on degrading tires
        # CRITICAL: Tire degradation accelerates with age (quadratic effect)
        time_loss = 0
        for lap in range(current_lap + 1, total_race_laps + 1):
            tire_age = current_tire_age + (lap - current_lap)
            
            # Apply realistic degradation: linear + quadratic penalty for old tires
            # degradation_rate is %/lap, but it accelerates
            base_degradation = degradation_rate * tire_age
            
            # Add quadratic penalty for worn tires (gets worse exponentially)
            if tire_age > 15:  # Tires get significantly worse after 15 laps
                age_penalty = ((tire_age - 15) ** 1.5) * 0.2  # Exponential penalty
                base_degradation += age_penalty
            
            time_loss += baseline_laptime * (base_degradation / 100)
        
        # No pit time saved, but severe degradation cost
        # The net advantage should be VERY negative for long stints
        net_advantage = -time_loss  # Negative because we're losing time
        
        # Score heavily penalized for no-pit strategies in typical races
        # Only viable if remaining laps < 8 AND degradation is low
        if remaining_laps <= 5 and abs(degradation_rate) < 0.5:
            score = 60 - (time_loss / 2)  # Might be viable for short sprint
        else:
            score = 20 - (time_loss / 3)  # Heavily penalized
        
        score = max(0, min(100, score))
        
        return PitStopScenario(
            pit_lap=0,  # 0 indicates no pit
            time_in_pit=0,
            tire_age_at_pit=current_tire_age + remaining_laps,
            projected_finish_time=0,
            total_time_loss=time_loss,
            total_time_gain=0,
            net_advantage=net_advantage,
            recommendation_score=score
        )
    
    def _generate_recommendation(
        self,
        optimal_scenario: PitStopScenario,
        current_lap: int,
        track_position: Optional[int],
        gap_to_leader: Optional[float],
        gap_to_next: Optional[float]
    ) -> str:
        """Generate human-readable pit strategy recommendation."""
        
        if optimal_scenario.pit_lap == 0:
            return "NO_PIT_RECOMMENDED"
        
        laps_until_pit = optimal_scenario.pit_lap - current_lap
        
        if laps_until_pit <= 1:
            return "PIT_NOW"
        elif laps_until_pit <= 3:
            return f"PIT_IN_{laps_until_pit}_LAPS"
        elif laps_until_pit <= 5:
            return "PIT_SOON"
        else:
            return f"PIT_WINDOW_LAP_{optimal_scenario.pit_lap}"
    
    def calculate_undercut_opportunity(
        self,
        current_lap: int,
        own_tire_age: int,
        competitor_tire_age: int,
        gap_to_competitor: float,
        degradation_rate: float,
        baseline_laptime: float
    ) -> Dict[str, Any]:
        """
        Calculate if an undercut strategy (pitting before competitor) would be advantageous.
        
        Args:
            current_lap: Current lap number
            own_tire_age: Laps on own current tires
            competitor_tire_age: Laps on competitor's tires
            gap_to_competitor: Time gap in seconds (positive if ahead)
            degradation_rate: Degradation percentage per lap
            baseline_laptime: Best lap time
            
        Returns:
            Dict with undercut opportunity analysis
        """
        
        # Calculate out-lap performance (first lap out of pits on fresh tires)
        out_lap_time = baseline_laptime + (self.typical_pit_time / 2)  # Slower due to pit exit
        
        # Calculate competitor's in-lap (last lap before their pit)
        competitor_degradation = degradation_rate * (competitor_tire_age + 1)
        competitor_in_lap_time = baseline_laptime * (1 + competitor_degradation / 100)
        
        # Time delta on the lap
        undercut_gain = competitor_in_lap_time - out_lap_time
        
        # Fresh tire advantage for next few laps
        fresh_tire_advantage = 0
        for lap_offset in range(1, 4):  # Next 3 laps
            fresh_deg = degradation_rate * lap_offset
            old_deg = degradation_rate * (competitor_tire_age + lap_offset)
            
            fresh_time = baseline_laptime * (1 + fresh_deg / 100)
            old_time = baseline_laptime * (1 + old_deg / 100)
            
            fresh_tire_advantage += (old_time - fresh_time)
        
        total_undercut_potential = undercut_gain + fresh_tire_advantage
        
        # Determine if undercut is viable
        viable = total_undercut_potential > abs(gap_to_competitor)
        
        return {
            "undercut_viable": viable,
            "time_gain_potential": total_undercut_potential,
            "gap_required": abs(gap_to_competitor),
            "advantage_margin": total_undercut_potential - abs(gap_to_competitor),
            "recommendation": "UNDERCUT_NOW" if viable and total_undercut_potential > gap_to_competitor + 2 else "MONITOR"
        }
    
    def simulate_race_to_finish(
        self,
        current_lap: int,
        total_race_laps: int,
        current_tire_age: int,
        pit_laps: List[int],
        degradation_rate: float,
        baseline_laptime: float
    ) -> Dict[str, Any]:
        """
        Simulate race to finish with given pit stop strategy.
        
        Args:
            current_lap: Current lap number
            total_race_laps: Total laps in race
            current_tire_age: Current tire age in laps
            pit_laps: List of laps on which to pit
            degradation_rate: Degradation rate per lap
            baseline_laptime: Best lap time
            
        Returns:
            Dict with simulation results
        """
        
        tire_age = current_tire_age
        total_time = 0
        lap_times = []
        tire_ages = []
        
        for lap in range(current_lap + 1, total_race_laps + 1):
            # Check if this is a pit lap
            if lap in pit_laps:
                total_time += self.typical_pit_time
                tire_age = 0  # Fresh tires
            
            # Calculate lap time with degradation
            degradation = degradation_rate * tire_age
            lap_time = baseline_laptime * (1 + degradation / 100)
            
            total_time += lap_time
            lap_times.append(lap_time)
            tire_ages.append(tire_age)
            
            tire_age += 1
        
        return {
            "total_race_time": total_time,
            "average_lap_time": np.mean(lap_times),
            "slowest_lap_time": np.max(lap_times),
            "fastest_lap_time": np.min(lap_times),
            "total_pit_stops": len(pit_laps),
            "final_tire_age": tire_age,
            "lap_times": lap_times
        }
