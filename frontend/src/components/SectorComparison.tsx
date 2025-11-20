import { useEffect, useState } from "react";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";
import { api } from "../api/client";

interface SectorComparisonProps {
  track: string;
  race: string;
  vehicleId: string;
  comparisonLap?: number; // Compare against a specific lap
}

interface LapComparisonData {
  lap: string;
  lapTime: number;
  delta: number;
  isBest: boolean;
}

export default function SectorComparison({
  track,
  race,
  vehicleId,
  comparisonLap,
}: SectorComparisonProps) {
  const [data, setData] = useState<LapComparisonData[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchLapComparison = async () => {
      try {
        setLoading(true);
        const lapData = await api.getLapTimes(track, race, vehicleId);

        if (!lapData || lapData.length === 0) {
          setError("No lap data available");
          return;
        }

        const laps = lapData;

        // Find best lap time
        const validLaps = laps.filter(
          (lap: any) => lap.lap_time && lap.lap_time > 0
        );
        if (validLaps.length === 0) {
          setError("No valid lap times found");
          return;
        }

        const bestTime = Math.min(...validLaps.map((lap: any) => lap.lap_time));

        // Create comparison data for recent laps
        const recentLaps = validLaps.slice(-10); // Last 10 laps
        const comparisonData: LapComparisonData[] = recentLaps.map(
          (lap: any) => ({
            lap: `Lap ${lap.lap}`,
            lapTime: lap.lap_time,
            delta: lap.lap_time - bestTime,
            isBest: lap.lap_time === bestTime,
          })
        );

        setData(comparisonData);
        setError(null);
      } catch (err) {
        setError("Failed to load lap data");
        console.error(err);
      } finally {
        setLoading(false);
      }
    };

    fetchLapComparison();
  }, [track, race, vehicleId, comparisonLap]);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-[300px] text-muted-foreground animate-pulse">
        Loading sector comparison...
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center h-[300px] text-destructive bg-destructive/10 rounded-xl border border-destructive/20">
        {error}
      </div>
    );
  }

  return (
    <div className="w-full space-y-6">
      <div className="glass-card p-4 border-white/5 bg-white/5">
        <h3 className="text-lg font-bold text-primary mb-4 flex items-center gap-2">
          <span className="w-1 h-5 bg-primary rounded-full"></span>
          Lap Time Comparison
        </h3>

        <ResponsiveContainer width="100%" height={300}>
          <BarChart
            data={data}
            margin={{ top: 20, right: 30, left: 20, bottom: 5 }}
          >
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />
            <XAxis dataKey="lap" stroke="rgba(255,255,255,0.3)" fontSize={12} />
            <YAxis
              label={{ value: "Time (s)", angle: -90, position: "insideLeft", fill: 'rgba(255,255,255,0.3)', fontSize: 12 }}
              stroke="rgba(255,255,255,0.3)"
              fontSize={12}
            />
            <Tooltip 
              formatter={(value: number) => value.toFixed(3) + "s"}
              contentStyle={{
                backgroundColor: "rgba(15, 23, 42, 0.9)",
                backdropFilter: "blur(8px)",
                border: "1px solid rgba(255, 255, 255, 0.1)",
                borderRadius: "8px",
                color: "#ffffff",
              }}
            />
            <Legend wrapperStyle={{ paddingTop: '10px' }} />
            <Bar dataKey="lapTime" fill="#8884d8" name="Lap Time" radius={[4, 4, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>

      <div className="glass-card p-6">
        <h4 className="text-sm font-semibold text-muted-foreground mb-4 uppercase tracking-wider">Time Delta to Best Lap</h4>
        <div className="space-y-2">
          {data.map((lapData) => (
            <div
              key={lapData.lap}
              className={`flex items-center justify-between p-3 rounded-lg border bg-white/5 transition-all hover:bg-white/10 ${
                lapData.delta > 0
                  ? "border-l-4 border-l-red-500 border-white/10"
                  : lapData.isBest
                  ? "border-l-4 border-l-amber-500 bg-amber-500/10 border-amber-500/20"
                  : "border-l-4 border-l-emerald-500 border-white/10"
              }`}
            >
              <span className="font-medium text-foreground">{lapData.lap}:</span>
              <span className={`font-mono font-bold ${
                lapData.isBest ? "text-amber-400" : lapData.delta > 0 ? "text-red-400" : "text-emerald-400"
              }`}>
                {lapData.isBest
                  ? "BEST"
                  : `${lapData.delta > 0 ? "+" : ""}${lapData.delta.toFixed(
                      3
                    )}s`}
              </span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
