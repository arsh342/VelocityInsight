import React, { useState, useEffect } from "react";
import { api } from "../api/client";
import type { LapTimeData } from "../api/client";

interface VehiclePosition {
  vehicleId: string;
  position: number;
  lapProgress: number; // 0-1 representing progress around track
  speed: number;
  sector: number;
  color?: string;
  isHighlighted?: boolean;
}

interface VehiclePositionProviderProps {
  track: string;
  race: string;
  selectedLap: number;
  highlightedVehicle?: string;
  children: (positions: VehiclePosition[]) => React.ReactNode;
}

// Color palette for different vehicles
const vehicleColors = [
  "#FF6B6B", "#4ECDC4", "#45B7D1", "#FFA07A", "#98D8C8", 
  "#F7DC6F", "#BB8FCE", "#85C1E9", "#F8C471", "#82E0AA",
  "#F1948A", "#85C1E9", "#D7BDE2", "#A9DFBF", "#F9E79F",
  "#CD6155", "#AF7AC5", "#5DADE2", "#58D68D", "#F4D03F"
];

const VehiclePositionProvider: React.FC<VehiclePositionProviderProps> = ({
  track,
  race,
  selectedLap,
  highlightedVehicle,
  children,
}) => {
  const [vehiclePositions, setVehiclePositions] = useState<VehiclePosition[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (track && race && selectedLap > 0) {
      loadVehiclePositions();
    }
  }, [track, race, selectedLap]);

  const loadVehiclePositions = async () => {
    try {
      setLoading(true);
      
      // Get all available vehicles
      const vehicles = await api.getRaceVehicles(track, race);
      const vehicleIds = vehicles.map(v => v.vehicle_id);

      // Fetch lap times for all vehicles up to the selected lap
      const allLapTimes: { [vehicle: string]: LapTimeData[] } = {};
      
      for (const vehicleId of vehicleIds) {
        try {
          const lapTimes = await api.getLapTimes(track, race, vehicleId);
          // Filter valid lap times up to selected lap
          allLapTimes[vehicleId] = lapTimes
            .filter(lap => 
              lap.lap_time && 
              lap.lap_time > 0 && 
              lap.lap <= selectedLap
            )
            .sort((a, b) => a.lap - b.lap);
        } catch (error) {
          console.warn(`Could not load lap times for vehicle ${vehicleId}:`, error);
          allLapTimes[vehicleId] = [];
        }
      }

      // Calculate positions at selected lap
      const positions = calculateVehiclePositions(allLapTimes, selectedLap, vehicleIds);
      setVehiclePositions(positions);

    } catch (error) {
      console.error("Error loading vehicle positions:", error);
      setVehiclePositions([]);
    } finally {
      setLoading(false);
    }
  };

  const calculateVehiclePositions = (
    allLapTimes: { [vehicle: string]: LapTimeData[] },
    targetLap: number,
    vehicleIds: string[]
  ): VehiclePosition[] => {
    const positions: Array<{
      vehicleId: string;
      totalTime: number;
      lapProgress: number;
      currentSpeed: number;
      sector: number;
    }> = [];

    for (const vehicleId of vehicleIds) {
      const vehicleLaps = allLapTimes[vehicleId] || [];
      
      if (vehicleLaps.length === 0) continue;

      // Calculate total time up to target lap
      let totalTime = 0;
      let lapProgress = 0;
      let currentSpeed = 0;
      let sector = 1;

      // Sum up complete laps
      const completeLaps = vehicleLaps.filter(lap => lap.lap < targetLap);
      totalTime = completeLaps.reduce((sum, lap) => sum + (lap.lap_time || 0), 0);

      // Handle progress within the target lap
      const targetLapData = vehicleLaps.find(lap => lap.lap === targetLap);
      
      if (targetLapData) {
        // Vehicle has completed the target lap
        totalTime += targetLapData.lap_time || 0;
        lapProgress = 1.0; // Completed the lap
        currentSpeed = calculateSpeedFromLapTime(targetLapData.lap_time || 0);
        sector = 1; // Starting next lap
      } else {
        // Vehicle hasn't completed target lap yet, estimate progress
        const lastLap = vehicleLaps[vehicleLaps.length - 1];
        if (lastLap && lastLap.lap === targetLap - 1) {
          // Assume some progress into current lap (rough estimation)
          lapProgress = Math.min(0.8, Math.random() * 0.6 + 0.2); // 20-80% progress
          currentSpeed = calculateSpeedFromLapTime(lastLap.lap_time || 0);
          sector = Math.floor(lapProgress * 3) + 1;
        } else {
          // Vehicle is behind
          lapProgress = 0;
          currentSpeed = lastLap ? calculateSpeedFromLapTime(lastLap.lap_time || 0) : 0;
          sector = 1;
        }
      }

      positions.push({
        vehicleId,
        totalTime,
        lapProgress,
        currentSpeed,
        sector
      });
    }

    // Sort by total time (position)
    positions.sort((a, b) => a.totalTime - b.totalTime);

    // Convert to VehiclePosition format
    return positions.map((pos, index): VehiclePosition => ({
      vehicleId: pos.vehicleId,
      position: index + 1,
      lapProgress: pos.lapProgress,
      speed: Math.round(pos.currentSpeed),
      sector: pos.sector,
      color: vehicleColors[index % vehicleColors.length],
      isHighlighted: pos.vehicleId === highlightedVehicle
    }));
  };

  const calculateSpeedFromLapTime = (lapTime: number): number => {
    // Rough estimation: assuming average track length of 4-5km
    // This is a simplified calculation
    if (!lapTime || lapTime <= 0) return 0;
    
    const avgTrackLength = 4.5; // km
    const speedKmh = (avgTrackLength / (lapTime / 3600)); // Convert seconds to hours
    
    // Clamp to reasonable racing speeds
    return Math.max(120, Math.min(280, speedKmh));
  };

  if (loading) {
    return children([]);
  }

  return <>{children(vehiclePositions)}</>;
};

export default VehiclePositionProvider;
export type { VehiclePosition };
