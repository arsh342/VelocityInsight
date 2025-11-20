import React, { useState, useEffect } from "react";
import { api } from "../api/client";
import type { LapTimeData } from "../api/client";

interface PositionTrackerProps {
  track: string;
  race: string;
  highlightVehicle?: string;
}

interface LapPosition {
  lap: number;
  vehicle: string;
  position: number;
  lapTime: number;
  totalTime: number;
  gap: number;
}

interface VehiclePositionHistory {
  vehicle: string;
  positions: LapPosition[];
  color: string;
}

const PositionTracker: React.FC<PositionTrackerProps> = ({
  track,
  race,
  highlightVehicle,
}) => {
  const [positionHistory, setPositionHistory] = useState<VehiclePositionHistory[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedLap, setSelectedLap] = useState<number>(1);
  const [maxLaps, setMaxLaps] = useState<number>(0);
  const [availableVehicles, setAvailableVehicles] = useState<string[]>([]);

  // Color palette for different vehicles
  const colors = [
    "#FF6B6B", "#4ECDC4", "#45B7D1", "#FFA07A", "#98D8C8", 
    "#F7DC6F", "#BB8FCE", "#85C1E9", "#F8C471", "#82E0AA",
    "#F1948A", "#85C1E9", "#D7BDE2", "#A9DFBF", "#F9E79F"
  ];

  useEffect(() => {
    if (track && race) {
      loadPositionData();
    }
  }, [track, race]);

  const loadPositionData = async () => {
    setLoading(true);
    try {
      // First get all available vehicles
      const vehicles = await api.getRaceVehicles(track, race);
      const vehicleIds = vehicles.map(v => v.vehicle_id);
      setAvailableVehicles(vehicleIds);

      // Fetch lap times for all vehicles
      const allLapTimes: { [vehicle: string]: LapTimeData[] } = {};
      
      for (const vehicleId of vehicleIds) {
        try {
          const lapTimes = await api.getLapTimes(track, race, vehicleId);
          allLapTimes[vehicleId] = lapTimes.filter(lap => lap.lap_time && lap.lap_time > 0);
        } catch (error) {
          console.warn(`Could not load lap times for vehicle ${vehicleId}:`, error);
          allLapTimes[vehicleId] = [];
        }
      }

      // Calculate positions for each lap
      const positionsByLap = calculatePositions(allLapTimes);
      
      // Create position history for each vehicle
      const history: VehiclePositionHistory[] = vehicleIds.map((vehicle, index) => ({
        vehicle,
        positions: positionsByLap.filter(pos => pos.vehicle === vehicle),
        color: colors[index % colors.length]
      }));

      setPositionHistory(history);
      
      // Set max laps
      const allLaps = Object.values(allLapTimes)
        .flat()
        .map(lap => lap.lap)
        .filter(lap => lap > 0);
      
      if (allLaps.length > 0) {
        setMaxLaps(Math.max(...allLaps));
        setSelectedLap(1);
      }

    } catch (error) {
      console.error("Error loading position data:", error);
    } finally {
      setLoading(false);
    }
  };

  const calculatePositions = (allLapTimes: { [vehicle: string]: LapTimeData[] }): LapPosition[] => {
    const positionsByLap: LapPosition[] = [];
    const vehicleIds = Object.keys(allLapTimes);
    
    // Get maximum lap number across all vehicles
    const maxLap = Math.max(
      ...Object.values(allLapTimes)
        .flat()
        .map(lap => lap.lap)
        .filter(lap => lap > 0)
    );

    // Calculate positions for each lap
    for (let lapNum = 1; lapNum <= maxLap; lapNum++) {
      const lapData: Array<{
        vehicle: string;
        lapTime: number;
        totalTime: number;
      }> = [];

      // Get lap times for this lap from each vehicle
      for (const vehicle of vehicleIds) {
        const vehicleLaps = allLapTimes[vehicle] || [];
        const currentLap = vehicleLaps.find(lap => lap.lap === lapNum);
        
        if (currentLap && currentLap.lap_time && currentLap.lap_time > 0) {
          // Calculate total time up to this lap
          const previousLaps = vehicleLaps
            .filter(lap => lap.lap < lapNum && lap.lap_time && lap.lap_time > 0)
            .sort((a, b) => a.lap - b.lap);
          
          const totalTime = previousLaps.reduce((sum, lap) => sum + (lap.lap_time || 0), 0) + currentLap.lap_time;
          
          lapData.push({
            vehicle,
            lapTime: currentLap.lap_time,
            totalTime
          });
        }
      }

      // Sort by total time to determine positions
      lapData.sort((a, b) => a.totalTime - b.totalTime);

      // Create position objects
      lapData.forEach((data, index) => {
        const leader = lapData[0];
        const gap = data.totalTime - leader.totalTime;
        
        positionsByLap.push({
          lap: lapNum,
          vehicle: data.vehicle,
          position: index + 1,
          lapTime: data.lapTime,
          totalTime: data.totalTime,
          gap
        });
      });
    }

    return positionsByLap;
  };

  const formatTime = (seconds: number): string => {
    if (!seconds || seconds <= 0) return "N/A";
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    return `${minutes}:${remainingSeconds.toFixed(3).padStart(6, '0')}`;
  };

  const formatGap = (gap: number): string => {
    if (!gap || gap <= 0) return "Leader";
    if (gap < 60) return `+${gap.toFixed(3)}s`;
    const minutes = Math.floor(gap / 60);
    const seconds = gap % 60;
    return `+${minutes}:${seconds.toFixed(3).padStart(6, '0')}`;
  };

  const getCurrentLapPositions = (): LapPosition[] => {
    return positionHistory
      .map(vehicle => 
        vehicle.positions.find(pos => pos.lap === selectedLap)
      )
      .filter((pos): pos is LapPosition => pos !== undefined)
      .sort((a, b) => a.position - b.position);
  };

  if (loading) {
    return (
      <div className="w-full h-[400px] glass-card flex flex-col items-center justify-center text-muted-foreground animate-pulse">
        <div className="w-12 h-12 border-4 border-primary border-t-transparent rounded-full animate-spin mb-4"></div>
        <p>Loading position data...</p>
      </div>
    );
  }

  if (positionHistory.length === 0) {
    return (
      <div className="w-full h-[200px] glass-card flex items-center justify-center text-muted-foreground">
        <p>No position data available for this race.</p>
      </div>
    );
  }

  const currentPositions = getCurrentLapPositions();

  return (
    <div className="w-full space-y-6">
      {/* Lap Selector */}
      <div className="glass-card p-6 flex flex-col md:flex-row items-center gap-6">
        <label htmlFor="lap-slider" className="text-lg font-bold text-primary whitespace-nowrap min-w-[150px]">
          Lap {selectedLap} <span className="text-muted-foreground font-normal text-sm">of {maxLaps}</span>
        </label>
        <div className="flex-1 w-full flex items-center gap-4">
          <span className="text-xs font-mono text-muted-foreground">1</span>
          <input
            id="lap-slider"
            type="range"
            min={1}
            max={maxLaps}
            value={selectedLap}
            onChange={(e) => setSelectedLap(parseInt(e.target.value))}
            className="w-full h-2 bg-white/10 rounded-lg appearance-none cursor-pointer accent-primary hover:accent-primary/80 transition-all"
          />
          <span className="text-xs font-mono text-muted-foreground">{maxLaps}</span>
        </div>
      </div>

      {/* Position Table for Selected Lap */}
      <div className="glass-card overflow-hidden">
        <div className="p-4 border-b border-white/10">
          <h3 className="text-lg font-bold text-white">Positions at Lap {selectedLap}</h3>
        </div>
        <div className="w-full overflow-x-auto">
          <div className="min-w-[800px]">
            <div className="grid grid-cols-12 gap-4 p-4 bg-white/5 border-b border-white/10 text-xs font-bold text-muted-foreground uppercase tracking-wider">
              <div className="col-span-1 text-center">Pos</div>
              <div className="col-span-3">Vehicle</div>
              <div className="col-span-3 text-right">Lap Time</div>
              <div className="col-span-3 text-right">Total Time</div>
              <div className="col-span-2 text-right">Gap</div>
            </div>
            <div className="divide-y divide-white/5">
              {currentPositions.map((position) => {
                const vehicleData = positionHistory.find(v => v.vehicle === position.vehicle);
                const isHighlighted = position.vehicle === highlightVehicle;
                
                return (
                  <div 
                    key={position.vehicle} 
                    className={`grid grid-cols-12 gap-4 p-4 items-center hover:bg-white/5 transition-colors ${
                      isHighlighted ? 'bg-primary/10' : ''
                    }`}
                    style={{ borderLeft: `4px solid ${vehicleData?.color || '#ccc'}` }}
                  >
                    <div className="col-span-1 flex justify-center">
                      <span className={`w-8 h-8 rounded-full flex items-center justify-center font-bold text-sm ${
                        position.position <= 3 ? 'bg-primary text-white' : 'bg-white/10 text-muted-foreground'
                      }`}>
                        {position.position}
                      </span>
                    </div>
                    <div className="col-span-3 font-bold text-foreground">
                      {position.vehicle}
                      {isHighlighted && <span className="ml-2 text-xs bg-primary/20 text-primary px-2 py-0.5 rounded-full">YOU</span>}
                    </div>
                    <div className="col-span-3 text-right font-mono text-muted-foreground">
                      {formatTime(position.lapTime)}
                    </div>
                    <div className="col-span-3 text-right font-mono text-muted-foreground">
                      {formatTime(position.totalTime)}
                    </div>
                    <div className="col-span-2 text-right font-mono font-bold text-emerald-400">
                      {formatGap(position.gap)}
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      </div>

      {/* Position Changes Chart */}
      <div className="glass-card p-6">
        <h3 className="text-lg font-bold text-white mb-6">Position Changes Over Race</h3>
        <div className="w-full h-[400px] relative">
          <div className="absolute inset-0 flex">
            {/* Y-axis (positions) */}
            <div className="w-10 flex flex-col justify-between text-xs text-muted-foreground py-4 border-r border-white/10 pr-2">
              {Array.from({ length: Math.min(availableVehicles.length, 20) }, (_, i) => (
                <div key={i + 1} className="h-6 flex items-center justify-end">
                  {i + 1}
                </div>
              ))}
            </div>
            
            {/* Chart area */}
            <div className="flex-1 relative overflow-hidden ml-2">
              <svg 
                viewBox={`0 0 ${maxLaps * 20} ${Math.min(availableVehicles.length, 20) * 30}`} 
                className="w-full h-full"
                preserveAspectRatio="none"
              >
                {positionHistory.map((vehicleHistory) => {
                  const points = vehicleHistory.positions
                    .sort((a, b) => a.lap - b.lap)
                    .map(pos => `${(pos.lap - 1) * 20},${(pos.position - 1) * 30}`)
                    .join(' ');
                  
                  const isHighlighted = vehicleHistory.vehicle === highlightVehicle;
                  
                  return (
                    <g key={vehicleHistory.vehicle} className="transition-opacity duration-300 hover:opacity-100 opacity-80">
                      <polyline
                        points={points}
                        fill="none"
                        stroke={vehicleHistory.color}
                        strokeWidth={isHighlighted ? 3 : 1.5}
                        strokeOpacity={isHighlighted ? 1 : 0.6}
                        vectorEffect="non-scaling-stroke"
                      />
                      {isHighlighted && vehicleHistory.positions.map((pos) => (
                        <circle
                          key={`${vehicleHistory.vehicle}-${pos.lap}`}
                          cx={(pos.lap - 1) * 20}
                          cy={(pos.position - 1) * 30}
                          r={4}
                          fill={vehicleHistory.color}
                          stroke="#000"
                          strokeWidth={1}
                        />
                      ))}
                    </g>
                  );
                })}
              </svg>
            </div>
          </div>
          
          {/* X-axis (laps) */}
          <div className="absolute bottom-0 left-12 right-0 h-6 flex justify-between text-xs text-muted-foreground px-2">
            <span>Lap 1</span>
            <span>Lap {Math.floor(maxLaps / 2)}</span>
            <span>Lap {maxLaps}</span>
          </div>
        </div>
      </div>

      {/* Legend */}
      <div className="glass-card p-4">
        <h4 className="text-xs font-bold text-muted-foreground uppercase tracking-wider mb-3">Vehicles</h4>
        <div className="flex flex-wrap gap-3">
          {positionHistory.slice(0, 10).map((vehicleHistory) => (
            <div 
              key={vehicleHistory.vehicle} 
              className={`flex items-center gap-2 px-2 py-1 rounded border transition-colors ${
                vehicleHistory.vehicle === highlightVehicle 
                  ? 'bg-primary/20 border-primary/50 text-white' 
                  : 'bg-white/5 border-white/10 text-muted-foreground hover:bg-white/10'
              }`}
            >
              <div 
                className="w-3 h-3 rounded-full" 
                style={{ backgroundColor: vehicleHistory.color }}
              ></div>
              <span className="text-xs font-mono font-bold">{vehicleHistory.vehicle}</span>
            </div>
          ))}
          {positionHistory.length > 10 && (
            <div className="px-2 py-1 text-xs text-muted-foreground">
              +{positionHistory.length - 10} more
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default PositionTracker;
