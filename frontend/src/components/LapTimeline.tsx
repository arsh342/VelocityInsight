import { useEffect, useState } from "react";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine,
} from "recharts";
import { api, type LapTimeData } from "../api/client";

interface LapTimelineProps {
  track: string;
  race: string;
  vehicleId: string;
  comparisonVehicles?: string[];
}

interface TimelineData {
  lap: number;
  [key: string]: number; // Dynamic keys for different drivers
}

export default function LapTimeline({
  track,
  race,
  vehicleId,
  comparisonVehicles = [],
}: LapTimelineProps) {
  const [data, setData] = useState<TimelineData[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [bestLaps, setBestLaps] = useState<Record<string, number>>({});

  const allVehicles = [vehicleId, ...comparisonVehicles];
  const colors = ["#06b6d4", "#f59e0b", "#ef4444", "#8b5cf6"];

  useEffect(() => {
    const fetchAllLapTimes = async () => {
      try {
        setLoading(true);

        // Fetch lap times for all vehicles
        const lapTimePromises = allVehicles.map(async (vehicle) => {
          try {
            const laps = await api.getLapTimes(track, race, vehicle);
            return { vehicle, laps };
          } catch (err) {
            console.error(`Failed to fetch laps for ${vehicle}:`, err);
            return { vehicle, laps: [] };
          }
        });

        const allLapData = await Promise.all(lapTimePromises);

        // Process and merge data
        const lapMap = new Map<number, TimelineData>();
        const bestLapTimes: Record<string, number> = {};

        allLapData.forEach(({ vehicle, laps }) => {
          // Calculate best lap for this vehicle
          const validLapTimes = laps
            .filter((l) => l.lap_time != null && l.lap_time > 0)
            .map((l) => l.lap_time!);

          if (validLapTimes.length > 0) {
            bestLapTimes[vehicle] = Math.min(...validLapTimes);
          }

          // Add lap times to the merged data
          laps
            .filter((lap) => lap.lap_time != null && lap.lap_time > 0)
            .forEach((lap: LapTimeData) => {
              if (!lapMap.has(lap.lap)) {
                lapMap.set(lap.lap, { lap: lap.lap });
              }
              const existing = lapMap.get(lap.lap)!;
              existing[`driver_${vehicle}`] = lap.lap_time!;
            });
        });

        // Convert map to array and sort by lap number
        const timelineData = Array.from(lapMap.values()).sort(
          (a, b) => a.lap - b.lap
        );

        setData(timelineData);
        setBestLaps(bestLapTimes);
        setError(null);
      } catch (err) {
        setError("Failed to load lap times");
        console.error(err);
      } finally {
        setLoading(false);
      }
    };

    if (allVehicles.length > 0) {
      fetchAllLapTimes();
    }
  }, [track, race, vehicleId, JSON.stringify(comparisonVehicles)]);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-[400px] text-muted-foreground animate-pulse">
        Loading lap times...
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

  const getDriverName = (vehicle: string) => `Driver #${vehicle}`;
  const getDriverColor = (index: number) => colors[index % colors.length];

  // Get overall best lap time across all drivers
  const overallBest =
    Object.values(bestLaps).length > 0
      ? Math.min(...Object.values(bestLaps))
      : null;

  // Calculate Y-axis domain centered around best lap time
  const getYAxisDomain = () => {
    if (!overallBest || data.length === 0) {
      return ["dataMin - 0.5", "dataMax + 0.5"];
    }

    // Get all lap time values from the data
    const allValues: number[] = [];
    data.forEach((row) => {
      allVehicles.forEach((vehicle) => {
        const value = row[`driver_${vehicle}`];
        if (typeof value === "number" && !isNaN(value)) {
          allValues.push(value);
        }
      });
    });

    if (allValues.length === 0) {
      return ["dataMin - 0.5", "dataMax + 0.5"];
    }

    const dataMin = Math.min(...allValues);
    const dataMax = Math.max(...allValues);

    // Calculate range needed above and below best lap
    const rangeAbove = dataMax - overallBest;
    const rangeBelow = overallBest - dataMin;
    const maxRange = Math.max(rangeAbove, rangeBelow);

    // Add some padding (20% of the range)
    const padding = maxRange * 0.2;
    const totalRange = maxRange + padding;

    // Center the domain around the best lap time
    const yMin = overallBest - totalRange;
    const yMax = overallBest + totalRange;

    return [yMin, yMax];
  };

  return (
    <div className="w-full space-y-6">
      <div className="glass-card p-4 border-white/5 bg-white/5">
        <h3 className="text-lg font-bold text-primary mb-4 flex items-center gap-2">
          <span className="w-1 h-5 bg-primary rounded-full"></span>
          Lap Time Progression
        </h3>
        <ResponsiveContainer width="100%" height={400}>
          <LineChart
            data={data}
            margin={{ top: 20, right: 30, left: 20, bottom: 20 }}
          >
            <CartesianGrid
              strokeDasharray="3 3"
              stroke="rgba(255, 255, 255, 0.05)"
            />
            <XAxis
              dataKey="lap"
              tick={{ fill: "#94a3b8", fontSize: 12 }}
              axisLine={{ stroke: "rgba(255, 255, 255, 0.1)" }}
              tickLine={{ stroke: "rgba(255, 255, 255, 0.1)" }}
              label={{ value: 'Lap Number', position: 'insideBottom', offset: -10, fill: '#94a3b8', fontSize: 12 }}
            />
            <YAxis
              domain={getYAxisDomain()}
              tick={{ fill: "#94a3b8", fontSize: 12 }}
              axisLine={{ stroke: "rgba(255, 255, 255, 0.1)" }}
              tickLine={{ stroke: "rgba(255, 255, 255, 0.1)" }}
              tickFormatter={(value) => `${value.toFixed(1)}`}
              label={{ value: 'Time (s)', angle: -90, position: 'insideLeft', fill: '#94a3b8', fontSize: 12 }}
            />
            <Tooltip
              contentStyle={{
                backgroundColor: "rgba(15, 23, 42, 0.9)",
                backdropFilter: "blur(8px)",
                border: "1px solid rgba(255, 255, 255, 0.1)",
                borderRadius: "8px",
                color: "#ffffff",
                fontSize: "12px",
                boxShadow: "0 4px 6px -1px rgba(0, 0, 0, 0.1)",
              }}
              formatter={(value: any, name: string) => {
                const vehicleId = name.replace("driver_", "");
                return [`${Number(value).toFixed(3)}s`, vehicleId];
              }}
              labelFormatter={(label) => `Lap ${label}`}
              labelStyle={{ color: "#06b6d4", fontWeight: "600" }}
            />

            {/* Reference line for overall best lap */}
            {overallBest && (
              <ReferenceLine
                y={overallBest}
                stroke="#10b981"
                strokeDasharray="5 5"
                strokeWidth={2}
                label={{
                  value: `Best: ${overallBest.toFixed(3)}s`,
                  position: "top",
                  fill: "#10b981",
                  fontSize: 12,
                  fontWeight: 600,
                }}
              />
            )}

            {/* Render lines for each driver */}
            {allVehicles.map((vehicle, index) => (
              <Line
                key={vehicle}
                type="monotone"
                dataKey={`driver_${vehicle}`}
                stroke={getDriverColor(index)}
                strokeWidth={3}
                name={`driver_${vehicle}`}
                dot={false}
                activeDot={{
                  r: 6,
                  fill: getDriverColor(index),
                  stroke: "#ffffff",
                  strokeWidth: 2,
                }}
                connectNulls={false}
              />
            ))}
          </LineChart>
        </ResponsiveContainer>
      </div>

      {/* Best Times Summary */}
      {Object.keys(bestLaps).length > 0 && (
        <div className="glass-card p-6">
          <h4 className="text-sm font-semibold text-muted-foreground mb-4 uppercase tracking-wider">Best Lap Times</h4>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {Object.entries(bestLaps)
              .sort(([, a], [, b]) => a - b)
              .map(([vehicle, time], index) => (
                <div key={vehicle} className="flex items-center gap-4 p-3 rounded-xl bg-white/5 border border-white/10 hover:border-primary/50 transition-all hover:bg-white/10 group">
                  <div
                    className="w-10 h-10 rounded-full flex items-center justify-center text-sm font-bold text-white shadow-lg transition-transform group-hover:scale-110"
                    style={{
                      backgroundColor: getDriverColor(
                        allVehicles.indexOf(vehicle)
                      ),
                    }}
                  >
                    #{index + 1}
                  </div>
                  <div className="flex flex-col">
                    <span className="text-xs font-medium text-muted-foreground">
                      {getDriverName(vehicle)}
                    </span>
                    <span className="text-lg font-mono font-bold text-foreground group-hover:text-primary transition-colors">{time.toFixed(3)}s</span>
                  </div>
                </div>
              ))}
          </div>
        </div>
      )}
    </div>
  );
}
