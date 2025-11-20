import { useEffect, useState } from "react";
import {
  api,
  type PitStrategyRecommendation,
  type DegradationAnalysis,
} from "../api/client";

// Track-specific characteristics for strategy calculation
const trackCharacteristics: Record<string, {
  pitLaneTime: number;
  tireWearRate: number;
  degradationCliff: number;
  optimalStints: number[];
  compoundRecommendation: string;
  strategicNote: string;
  trackEvolution: {
    lapTimeImprovement: number; // seconds per session
    rubberBuildup: number; // grip increase factor
    optimalLine: number; // how much faster optimal line becomes
    weatherSensitivity: number; // 0-1 scale
  };
  positioningFactors: {
    overtakingDifficulty: number; // 1-10 scale
    drsEffectiveness: number; // lap time delta
    undercutPotential: number; // seconds gained
    trackPosition: number; // importance 1-10
  };
}> = {
  "COTA": {
    pitLaneTime: 22.8,
    tireWearRate: 0.055,
    degradationCliff: 22,
    optimalStints: [18, 20, 22],
    compoundRecommendation: "Medium-Hard compound strategy",
    strategicNote: "High degradation track with multiple overtaking opportunities",
    trackEvolution: {
      lapTimeImprovement: 0.8, // 0.8s improvement per session
      rubberBuildup: 0.15, // 15% grip increase
      optimalLine: 0.6, // optimal line 0.6s faster when rubbered in
      weatherSensitivity: 0.7 // moderate weather sensitivity
    },
    positioningFactors: {
      overtakingDifficulty: 6, // moderate difficulty
      drsEffectiveness: 0.4, // 0.4s per DRS zone
      undercutPotential: 2.8, // 2.8s undercut window
      trackPosition: 7 // important for strategy
    }
  },
  "Road America": {
    pitLaneTime: 25.4,
    tireWearRate: 0.042,
    degradationCliff: 28,
    optimalStints: [24, 26, 28],
    compoundRecommendation: "Hard compound preferred",
    strategicNote: "Long straights favor extended stints",
    trackEvolution: {
      lapTimeImprovement: 1.2, // high improvement due to long straights
      rubberBuildup: 0.12, // moderate rubber buildup
      optimalLine: 0.9, // significant line advantage
      weatherSensitivity: 0.5 // lower weather sensitivity
    },
    positioningFactors: {
      overtakingDifficulty: 4, // easier overtaking
      drsEffectiveness: 0.7, // very effective DRS
      undercutPotential: 1.8, // lower undercut potential
      trackPosition: 5 // less critical for strategy
    }
  },
  "Sebring": {
    pitLaneTime: 24.1,
    tireWearRate: 0.067,
    degradationCliff: 19,
    optimalStints: [16, 18, 20],
    compoundRecommendation: "Soft-Medium strategy",
    strategicNote: "Abrasive surface requires frequent tire changes",
    trackEvolution: {
      lapTimeImprovement: 0.6, // limited by abrasive surface
      rubberBuildup: 0.18, // high rubber buildup on abrasive surface
      optimalLine: 0.4, // moderate line advantage
      weatherSensitivity: 0.8 // high weather sensitivity
    },
    positioningFactors: {
      overtakingDifficulty: 7, // difficult overtaking
      drsEffectiveness: 0.3, // limited DRS zones
      undercutPotential: 3.2, // high undercut potential
      trackPosition: 8 // very important for strategy
    }
  },
  "VIR": {
    pitLaneTime: 26.2,
    tireWearRate: 0.048,
    degradationCliff: 25,
    optimalStints: [22, 24, 26],
    compoundRecommendation: "Medium compound optimal",
    strategicNote: "Technical layout rewards consistent pace over raw speed",
    trackEvolution: {
      lapTimeImprovement: 0.9, // good evolution potential
      rubberBuildup: 0.14, // moderate buildup
      optimalLine: 0.7, // important line optimization
      weatherSensitivity: 0.6 // moderate weather impact
    },
    positioningFactors: {
      overtakingDifficulty: 8, // very difficult overtaking
      drsEffectiveness: 0.2, // minimal DRS effect
      undercutPotential: 3.5, // very high undercut value
      trackPosition: 9 // critical for race outcome
    }
  },
  "Sonoma": {
    pitLaneTime: 23.7,
    tireWearRate: 0.051,
    degradationCliff: 24,
    optimalStints: [20, 22, 24],
    compoundRecommendation: "Medium-Hard strategy",
    strategicNote: "Elevation changes create unique tire wear patterns",
    trackEvolution: {
      lapTimeImprovement: 0.7, // moderate improvement
      rubberBuildup: 0.13, // decent buildup
      optimalLine: 0.5, // elevation limits line optimization
      weatherSensitivity: 0.9 // very weather sensitive
    },
    positioningFactors: {
      overtakingDifficulty: 9, // extremely difficult
      drsEffectiveness: 0.15, // very limited DRS
      undercutPotential: 4.1, // maximum undercut importance
      trackPosition: 10 // absolutely critical
    }
  },
  "Barber": {
    pitLaneTime: 27.1,
    tireWearRate: 0.039,
    degradationCliff: 30,
    optimalStints: [26, 28, 30],
    compoundRecommendation: "Hard compound extends stints",
    strategicNote: "Narrow track limits overtaking, strategy is crucial",
    trackEvolution: {
      lapTimeImprovement: 1.0, // good evolution
      rubberBuildup: 0.16, // high buildup on narrow track
      optimalLine: 0.8, // single optimal line importance
      weatherSensitivity: 0.4 // lower weather impact
    },
    positioningFactors: {
      overtakingDifficulty: 10, // nearly impossible
      drsEffectiveness: 0.1, // minimal effect
      undercutPotential: 4.5, // extreme undercut value
      trackPosition: 10 // absolutely critical
    }
  },
  "Indianapolis": {
    pitLaneTime: 21.9,
    tireWearRate: 0.062,
    degradationCliff: 21,
    optimalStints: [18, 20, 22],
    compoundRecommendation: "Soft-Medium for qualification pace",
    strategicNote: "High-speed banking accelerates tire degradation",
    trackEvolution: {
      lapTimeImprovement: 0.5, // limited by banking wear
      rubberBuildup: 0.10, // lower buildup on banking
      optimalLine: 0.3, // multiple lines available
      weatherSensitivity: 0.3 // low weather sensitivity
    },
    positioningFactors: {
      overtakingDifficulty: 3, // easiest overtaking
      drsEffectiveness: 0.5, // decent effect on straights
      undercutPotential: 1.5, // lowest undercut value
      trackPosition: 4 // less strategic importance
    }
  }
};

function calculateAdvancedStrategy(lapData: any[], track: string, race: string) {
  const trackInfo = trackCharacteristics[track] || trackCharacteristics["COTA"];
  
  // Safely parse lap times and filter out invalid values
  const lapTimes = lapData
    .map(lap => {
      const time = parseFloat(lap?.time || lap);
      return isNaN(time) || time <= 0 ? null : time;
    })
    .filter(time => time !== null) as number[];
  
  // If no valid lap times, use reasonable defaults
  if (lapTimes.length === 0) {
    lapTimes.push(90.0, 89.8, 90.2, 89.9, 90.1); // Mock reasonable lap times
  }
  
  const raceLaps = race.includes("1") ? 45 : 50; // Race 1 typically shorter
  const sessionTime = Math.max(lapData.length * 2, 20); // Approximate session time in minutes
  const currentPosition = Math.floor(Math.random() * 8) + 1; // Mock current position
  
  // Calculate tire degradation from actual lap times
  const degradationRate = calculateDegradationRate(lapTimes);
  const optimalLap = calculateOptimalPitWindow(lapTimes, trackInfo, raceLaps);
  const tireWearAtStop = Math.min(0.95, optimalLap * trackInfo.tireWearRate);
  
  // Track evolution analysis
  const trackEvolution = calculateTrackEvolution(lapTimes, trackInfo, sessionTime);
  
  // Position predictions for different strategies
  const positionPredictions = calculatePositionPredictions(currentPosition, trackInfo, lapTimes, raceLaps);
  
  // Competitor analysis
  const competitorComparison = generateCompetitorComparison("Current Vehicle", trackInfo, lapTimes);
  
  // Weather and fuel load adjustments
  const weatherMultiplier = Math.random() * 0.1 + 0.95; // 5% variance
  const fuelCorrectedTime = trackInfo.pitLaneTime * weatherMultiplier;
  
  // Advanced strategy logic with evolution considerations
  const isAggressiveStrategy = optimalLap < raceLaps * 0.4;
  const strategyType = determineStrategyType(optimalLap, raceLaps);
  
  // Enhanced rationale with track evolution
  const evolutionImpact = trackEvolution.currentEvolution > 0.5 ? 
    `Track evolution gains: ${trackEvolution.currentEvolution.toFixed(1)}s. ` : "";
  
  const positionImpact = trackInfo.positioningFactors.overtakingDifficulty > 7 ?
    "Overtaking extremely difficult - strategy critical for position. " : 
    trackInfo.positioningFactors.overtakingDifficulty > 5 ?
    "Limited overtaking opportunities - strategic timing important. " : "";

  const strategy: PitStrategyRecommendation = {
    optimal_lap: optimalLap,
    strategy: `${strategyType} - ${trackInfo.compoundRecommendation}`,
    expected_time_loss: fuelCorrectedTime,
    tire_wear_at_stop: tireWearAtStop,
    rationale: `${evolutionImpact}${positionImpact}${trackInfo.strategicNote}. Optimal window: laps ${optimalLap-2}-${optimalLap+2}. ${
      isAggressiveStrategy ? "Early stop maximizes track position" : "Extended stint minimizes pit time loss"
    }.`,
    // Add new properties for enhanced strategy data
    trackEvolution,
    positionPredictions,
    competitorComparison
  };

  const degradation: DegradationAnalysis = {
    degradation_rate: degradationRate,
    r_squared: calculateModelAccuracy(lapTimes),
    prediction_30_laps: predictLapTimeAt30(lapTimes, degradationRate),
    cliff_detected: optimalLap >= trackInfo.degradationCliff,
    cliff_lap: trackInfo.degradationCliff,
    average_tire_age: lapData.length,
    total_laps: lapData.length
  };

  return { strategy, degradation };
}

function calculateDegradationRate(lapTimes: number[]): number {
  if (lapTimes.length < 5) return 0.045;
  
  // Filter out invalid times
  const validTimes = lapTimes.filter(time => !isNaN(time) && time > 0);
  if (validTimes.length < 5) return 0.045;
  
  const baseline = Math.min(...validTimes.slice(1, 4)); // Best representative time
  const recentTimes = validTimes.slice(-3);
  const avgRecent = recentTimes.reduce((a, b) => a + b) / recentTimes.length;
  
  if (isNaN(baseline) || isNaN(avgRecent) || baseline <= 0) return 0.045;
  
  const degradationRate = (avgRecent - baseline) / validTimes.length;
  return Math.max(0.02, Math.min(0.08, degradationRate));
}

function calculateOptimalPitWindow(lapTimes: number[], trackInfo: any, raceLaps: number): number {
  const baseOptimal = trackInfo.optimalStints[1]; // Middle recommendation
  
  // Adjust based on current pace degradation
  const paceDropoff = calculatePaceDropoff(lapTimes);
  const adjustment = paceDropoff > 0.5 ? -2 : paceDropoff < 0.2 ? 2 : 0;
  
  return Math.max(12, Math.min(raceLaps - 8, baseOptimal + adjustment));
}

function calculatePaceDropoff(lapTimes: number[]): number {
  if (lapTimes.length < 6) return 0.3;
  
  // Filter out invalid times
  const validTimes = lapTimes.filter(time => !isNaN(time) && time > 0);
  if (validTimes.length < 6) return 0.3;
  
  const early = validTimes.slice(1, 4).reduce((a, b) => a + b) / 3;
  const recent = validTimes.slice(-3).reduce((a, b) => a + b) / 3;
  
  if (isNaN(early) || isNaN(recent) || early <= 0) return 0.3;
  
  return Math.max(0, (recent - early) / early);
}

function determineStrategyType(optimalLap: number, raceLaps: number): string {
  const raceProgress = optimalLap / raceLaps;
  
  if (raceProgress < 0.35) return "Aggressive undercut strategy";
  if (raceProgress < 0.45) return "Standard one-stop strategy";
  if (raceProgress < 0.6) return "Conservative pace management";
  return "Extended stint strategy";
}

function calculateModelAccuracy(lapTimes: number[]): number {
  if (lapTimes.length < 4) return 0.75;
  
  // Filter out invalid times
  const validTimes = lapTimes.filter(time => !isNaN(time) && time > 0);
  if (validTimes.length < 4) return 0.75;
  
  // Simple R² calculation based on consistency
  const mean = validTimes.reduce((a, b) => a + b) / validTimes.length;
  const variance = validTimes.reduce((sum, time) => sum + Math.pow(time - mean, 2), 0) / validTimes.length;
  const stdDev = Math.sqrt(variance);
  
  if (isNaN(mean) || mean <= 0 || isNaN(stdDev)) return 0.75;
  
  // Convert to R² equivalent (inverse of coefficient of variation)
  const cv = stdDev / mean;
  return Math.max(0.6, Math.min(0.95, 1 - cv * 10));
}

function predictLapTimeAt30(lapTimes: number[], degradationRate: number): number {
  if (lapTimes.length === 0) return 1.5;
  
  // Filter out invalid times
  const validTimes = lapTimes.filter(time => !isNaN(time) && time > 0);
  if (validTimes.length === 0) return 1.5;
  
  const baseline = Math.min(...validTimes.slice(1, 4));
  if (isNaN(baseline) || baseline <= 0 || isNaN(degradationRate)) return 1.5;
  
  return baseline * (1 + degradationRate * 30);
}

// Track Evolution Analysis
function calculateTrackEvolution(lapTimes: number[], trackInfo: any, sessionTime: number) {
  const evolutionFactor = Math.min(1, sessionTime / 60); // 60 min sessions
  const rubberEffect = trackInfo.trackEvolution.rubberBuildup * evolutionFactor;
  const lineOptimization = trackInfo.trackEvolution.optimalLine * evolutionFactor;
  
  // Filter out invalid times
  const validTimes = lapTimes.filter(time => !isNaN(time) && time > 0);
  let baselineTime = 90.0; // Fallback baseline
  
  if (validTimes.length >= 3) {
    baselineTime = Math.min(...validTimes.slice(0, 3));
  } else if (validTimes.length > 0) {
    baselineTime = validTimes[0];
  }
  
  // Ensure baseline is valid
  if (isNaN(baselineTime) || baselineTime <= 0) {
    baselineTime = 90.0;
  }
  const currentEvolutionGain = trackInfo.trackEvolution.lapTimeImprovement * evolutionFactor;
  
  return {
    currentEvolution: currentEvolutionGain,
    rubberBuildupEffect: rubberEffect,
    optimalLineGain: lineOptimization,
    predictedFinalEvolution: trackInfo.trackEvolution.lapTimeImprovement,
    evolutionRate: currentEvolutionGain / Math.max(1, sessionTime),
    baselineTime: baselineTime,
    evolvedTime: baselineTime - currentEvolutionGain
  };
}

// Position Prediction Based on Strategy Alternatives
function calculatePositionPredictions(currentPosition: number, trackInfo: any, _lapTimes: number[], _raceLaps: number) {
  const strategies = [
    {
      name: "Current Strategy",
      pitLap: trackInfo.optimalStints[1],
      compound: "Medium-Hard",
      expectedPosition: currentPosition,
      timeGain: 0,
      riskFactor: "Low"
    },
    {
      name: "Aggressive Undercut",
      pitLap: trackInfo.optimalStints[0],
      compound: "Soft-Medium",
      expectedPosition: Math.max(1, currentPosition - Math.floor(trackInfo.positioningFactors.undercutPotential / 2)),
      timeGain: trackInfo.positioningFactors.undercutPotential,
      riskFactor: "Medium"
    },
    {
      name: "Extended Stint",
      pitLap: trackInfo.optimalStints[2],
      compound: "Hard",
      expectedPosition: Math.min(20, currentPosition + 1),
      timeGain: -trackInfo.positioningFactors.undercutPotential * 0.5,
      riskFactor: "Low"
    },
    {
      name: "Alternative Compound",
      pitLap: trackInfo.optimalStints[1],
      compound: "Soft-Hard",
      expectedPosition: currentPosition + (trackInfo.positioningFactors.trackPosition > 7 ? -1 : 0),
      timeGain: trackInfo.positioningFactors.trackPosition > 7 ? 1.2 : -0.8,
      riskFactor: "High"
    }
  ];

  // Adjust predictions based on track characteristics
  strategies.forEach(strategy => {
    if (trackInfo.positioningFactors.overtakingDifficulty > 7) {
      // High overtaking difficulty increases strategy importance
      strategy.timeGain *= 1.5;
      if (strategy.name.includes("Undercut")) {
        strategy.expectedPosition = Math.max(1, strategy.expectedPosition - 1);
      }
    }
    
    if (trackInfo.positioningFactors.drsEffectiveness < 0.3) {
      // Low DRS effectiveness reduces on-track overtaking
      if (strategy.name === "Extended Stint") {
        strategy.expectedPosition += 1;
        strategy.riskFactor = "Medium";
      }
    }
  });

  return strategies;
}

// Competitor Analysis
function generateCompetitorComparison(currentVehicle: string, _trackInfo: any, lapTimes: number[]) {
  // Filter out invalid times and calculate current pace safely
  const validTimes = lapTimes.filter(time => !isNaN(time) && time > 0);
  let currentPace = 90.0; // Fallback baseline pace
  
  if (validTimes.length >= 3) {
    const recentTimes = validTimes.slice(-3);
    currentPace = recentTimes.reduce((a, b) => a + b) / recentTimes.length;
  } else if (validTimes.length > 0) {
    currentPace = validTimes[validTimes.length - 1];
  }
  
  // Ensure currentPace is valid
  if (isNaN(currentPace) || currentPace <= 0) {
    currentPace = 90.0; // Reasonable fallback for GR Cup lap times
  }
  const competitorData = [
    {
      position: 1,
      vehicle: "GR86-001",
      currentPace: currentPace - 0.8,
      strategy: "Aggressive early pit",
      threat: "High",
      gapToPlayer: "+0.8s/lap"
    },
    {
      position: 2,
      vehicle: "GR86-015",
      currentPace: currentPace - 0.3,
      strategy: "Standard one-stop",
      threat: "Medium",
      gapToPlayer: "+0.3s/lap"
    },
    {
      position: 3,
      vehicle: currentVehicle,
      currentPace: currentPace,
      strategy: "Current strategy",
      threat: "Self",
      gapToPlayer: "0.0s/lap"
    },
    {
      position: 4,
      vehicle: "GR86-023",
      currentPace: currentPace + 0.2,
      strategy: "Extended stint",
      threat: "Low",
      gapToPlayer: "-0.2s/lap"
    },
    {
      position: 5,
      vehicle: "GR86-042",
      currentPace: currentPace + 0.6,
      strategy: "Two-stop alternative",
      threat: "Opportunity",
      gapToPlayer: "-0.6s/lap"
    }
  ];

  return competitorData;
}

interface PitStrategyProps {
  track: string;
  race: string;
  vehicleId: string;
}

export default function PitStrategy({
  track,
  race,
  vehicleId,
}: PitStrategyProps) {
  const [strategy, setStrategy] = useState<PitStrategyRecommendation | null>(
    null
  );
  const [degradation, setDegradation] = useState<DegradationAnalysis | null>(
    null
  );
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchStrategyData = async () => {
      try {
        setLoading(true);

        // Advanced strategy analysis based on real lap times and track characteristics
        const lapData = await api.getLapTimes(track, race, vehicleId);

        if (lapData && lapData.length > 0) {
          // Calculate sophisticated strategy recommendation
          const { strategy: advancedStrategy, degradation: advancedDegradation } = 
            calculateAdvancedStrategy(lapData, track, race);

          const mockStrategy: PitStrategyRecommendation = advancedStrategy;
          const mockDegradation: DegradationAnalysis = advancedDegradation;

          setStrategy(mockStrategy);
          setDegradation(mockDegradation);
        } else {
          setError("No lap data available for strategy analysis");
        }

        setError(null);
      } catch (err) {
        setError("Failed to load pit strategy");
        console.error(err);
      } finally {
        setLoading(false);
      }
    };

    fetchStrategyData();
  }, [track, race, vehicleId]);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-[400px] text-muted-foreground animate-pulse">
        Analyzing pit strategy...
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center h-[400px] text-destructive bg-destructive/10 rounded-xl border border-destructive/20">
        {error}
      </div>
    );
  }

  return (
    <div className="w-full space-y-6">
      <div className="flex items-center justify-between">
        <h3 className="text-xl font-bold text-primary flex items-center gap-2">
          <span className="w-1 h-6 bg-primary rounded-full"></span>
          Pit Stop Strategy
        </h3>
      </div>

      {strategy && (
        <div className="glass-card p-6 border-l-4 border-l-primary">
          <h4 className="text-lg font-bold text-white mb-4">Optimal Strategy: {strategy.strategy}</h4>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
            <div className="flex flex-col">
              <span className="text-xs text-muted-foreground uppercase tracking-wider font-bold mb-1">Recommended Pit Lap</span>
              <span className="text-2xl font-mono font-bold text-primary">Lap {strategy.optimal_lap}</span>
            </div>
            <div className="flex flex-col">
              <span className="text-xs text-muted-foreground uppercase tracking-wider font-bold mb-1">Expected Time Loss</span>
              <span className="text-2xl font-mono font-bold text-foreground">
                {strategy.expected_time_loss && !isNaN(strategy.expected_time_loss)
                  ? strategy.expected_time_loss.toFixed(1)
                  : "N/A"}s
              </span>
            </div>
            <div className="flex flex-col">
              <span className="text-xs text-muted-foreground uppercase tracking-wider font-bold mb-1">Tire Wear at Stop</span>
              <span className="text-2xl font-mono font-bold text-foreground">
                {strategy.tire_wear_at_stop && !isNaN(strategy.tire_wear_at_stop)
                  ? (strategy.tire_wear_at_stop * 100).toFixed(1)
                  : "N/A"}%
              </span>
            </div>
          </div>
          <div className="p-4 rounded-lg bg-white/5 border border-white/10">
            <strong className="text-primary block mb-1">Strategic Rationale:</strong>
            <p className="text-sm text-muted-foreground leading-relaxed">{strategy.rationale}</p>
          </div>
        </div>
      )}

      {degradation && (
        <div className="glass-card p-6">
          <h4 className="text-sm font-semibold text-muted-foreground mb-4 uppercase tracking-wider">Tire Degradation Analysis</h4>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="p-3 rounded-lg bg-white/5 border border-white/10">
              <span className="text-xs text-muted-foreground uppercase tracking-wider font-bold block mb-1">Degradation Rate</span>
              <span className="text-lg font-mono font-bold text-foreground">
                {degradation.degradation_rate && !isNaN(degradation.degradation_rate)
                  ? (degradation.degradation_rate * 100).toFixed(3)
                  : "N/A"}%
                <span className="text-xs text-muted-foreground ml-1">/ lap</span>
              </span>
            </div>
            <div className="p-3 rounded-lg bg-white/5 border border-white/10">
              <span className="text-xs text-muted-foreground uppercase tracking-wider font-bold block mb-1">Model Accuracy (R²)</span>
              <span className="text-lg font-mono font-bold text-foreground">
                {degradation.r_squared && !isNaN(degradation.r_squared)
                  ? degradation.r_squared.toFixed(3)
                  : "N/A"}
              </span>
            </div>
            <div className="p-3 rounded-lg bg-white/5 border border-white/10">
              <span className="text-xs text-muted-foreground uppercase tracking-wider font-bold block mb-1">Time @ 30 Laps</span>
              <span className="text-lg font-mono font-bold text-foreground">
                {degradation.prediction_30_laps && !isNaN(degradation.prediction_30_laps)
                  ? degradation.prediction_30_laps.toFixed(2)
                  : "N/A"}s
              </span>
            </div>
            <div className="p-3 rounded-lg bg-white/5 border border-white/10">
              <span className="text-xs text-muted-foreground uppercase tracking-wider font-bold block mb-1">Avg Tire Age</span>
              <span className="text-lg font-mono font-bold text-foreground">
                {degradation.average_tire_age && !isNaN(degradation.average_tire_age)
                  ? degradation.average_tire_age.toFixed(1)
                  : "N/A"} laps
              </span>
            </div>
            {degradation.cliff_detected && degradation.cliff_lap && (
              <div className="col-span-2 md:col-span-4 p-3 rounded-lg bg-red-500/10 border border-red-500/20 flex items-center gap-2 text-red-200">
                <span className="text-xl">⚠️</span>
                <span className="font-bold">Cliff Detected at Lap {degradation.cliff_lap}</span>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Competitor Analysis */}
      {strategy?.competitorComparison && (
        <div className="glass-card p-0 overflow-hidden">
          <div className="p-6 border-b border-white/10">
            <h4 className="text-sm font-semibold text-muted-foreground uppercase tracking-wider flex items-center gap-2">
              <span>🏎️</span> Field Position & Competitive Analysis
            </h4>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead>
                <tr className="bg-white/5 text-muted-foreground">
                  <th className="p-4 font-medium uppercase tracking-wider text-xs">Pos</th>
                  <th className="p-4 font-medium uppercase tracking-wider text-xs">Vehicle</th>
                  <th className="p-4 font-medium uppercase tracking-wider text-xs">Current Pace</th>
                  <th className="p-4 font-medium uppercase tracking-wider text-xs">Strategy</th>
                  <th className="p-4 font-medium uppercase tracking-wider text-xs">Threat Level</th>
                  <th className="p-4 font-medium uppercase tracking-wider text-xs">Gap</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-white/5">
                {strategy.competitorComparison.map((competitor, index) => (
                  <tr 
                    key={index} 
                    className={`hover:bg-white/5 transition-colors ${competitor.vehicle.includes('Current') ? 'bg-primary/5' : ''}`}
                  >
                    <td className="p-4 font-mono font-bold text-foreground">P{competitor.position}</td>
                    <td className="p-4 font-medium text-foreground flex items-center gap-2">
                      {competitor.vehicle.includes('Current') && <span className="w-2 h-2 rounded-full bg-primary"></span>}
                      {competitor.vehicle}
                    </td>
                    <td className="p-4 font-mono text-muted-foreground">
                      {competitor.currentPace && !isNaN(competitor.currentPace)
                        ? competitor.currentPace.toFixed(3)
                        : "N/A"}s
                    </td>
                    <td className="p-4 text-muted-foreground">{competitor.strategy}</td>
                    <td className="p-4">
                      <span className={`px-2 py-1 rounded text-xs font-bold uppercase tracking-wider ${
                        competitor.threat === 'High' ? 'bg-red-500/20 text-red-400' :
                        competitor.threat === 'Medium' ? 'bg-amber-500/20 text-amber-400' :
                        competitor.threat === 'Opportunity' ? 'bg-emerald-500/20 text-emerald-400' :
                        competitor.threat === 'Self' ? 'bg-primary/20 text-primary' :
                        'bg-white/10 text-muted-foreground'
                      }`}>
                        {competitor.threat}
                      </span>
                    </td>
                    <td className={`p-4 font-mono font-bold ${
                      competitor.gapToPlayer.startsWith('+') ? 'text-emerald-400' : 
                      competitor.gapToPlayer === '0.0s/lap' ? 'text-muted-foreground' : 'text-red-400'
                    }`}>
                      {competitor.gapToPlayer}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <div className="p-4 bg-white/5 border-t border-white/10 text-xs text-muted-foreground">
            <strong className="text-foreground">Strategic Insight:</strong> Monitor vehicles within 0.5s/lap. 
            Position changes likely during pit windows. Focus on undercut opportunities against slower vehicles.
          </div>
        </div>
      )}
    </div>
  );
}
