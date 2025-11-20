import { useEffect, useState } from "react";
import { api, type ConsistencyScore } from "../api/client";

interface DriverConsistencyProps {
  track: string;
  race: string;
  vehicleId: string;
}

export default function DriverConsistency({
  track,
  race,
  vehicleId,
}: DriverConsistencyProps) {
  const [consistency, setConsistency] = useState<ConsistencyScore | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchConsistency = async () => {
      try {
        setLoading(true);

        // Get lap data to calculate basic consistency
        const lapData = await api.getLapTimes(track, race, vehicleId);

        if (lapData && lapData.length > 0) {
          // Calculate basic consistency metrics
          const validLaps = lapData.filter(
            (lap: any) => lap.lap_time && lap.lap_time > 0
          );
          const lapTimes = validLaps.map((lap: any) => lap.lap_time);

          if (lapTimes.length > 0) {
            const mean =
              lapTimes.reduce((a: number, b: number) => a + b, 0) /
              lapTimes.length;
            const variance =
              lapTimes.reduce(
                (sum: number, time: number) => sum + Math.pow(time - mean, 2),
                0
              ) / lapTimes.length;
            const stdDev = Math.sqrt(variance);
            const cv = stdDev / mean; // Coefficient of variation

            // Convert CV to a 0-100 consistency score (lower CV = higher consistency)
            const consistencyScore = Math.max(0, 100 - cv * 1000);

            let rating = "Excellent";
            if (consistencyScore < 40) rating = "Poor";
            else if (consistencyScore < 60) rating = "Fair";
            else if (consistencyScore < 80) rating = "Good";

            const mockConsistency: ConsistencyScore = {
              consistency_score: consistencyScore,
              rating: rating,
              total_laps: validLaps.length,
              lap_time_cv: cv,
              strengths:
                consistencyScore > 80
                  ? ["Very consistent lap times", "Good pace management"]
                  : ["Room for improvement in consistency"],
            };

            setConsistency(mockConsistency);
          } else {
            setError("No valid lap times found");
          }
        } else {
          setError("No lap data available");
        }

        setError(null);
      } catch (err) {
        setError("Failed to load consistency data");
        console.error(err);
      } finally {
        setLoading(false);
      }
    };

    fetchConsistency();
  }, [track, race, vehicleId]);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-[300px] text-muted-foreground animate-pulse">
        Analyzing driver consistency...
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

  if (!consistency) {
    return null;
  }

  const getScoreColor = (score: number): string => {
    if (score >= 80) return "#22c55e"; // green
    if (score >= 60) return "#eab308"; // yellow
    if (score >= 40) return "#f97316"; // orange
    return "#ef4444"; // red
  };

  const getRatingEmoji = (rating: string): string => {
    switch (rating.toLowerCase()) {
      case "excellent":
        return "🌟";
      case "good":
        return "✅";
      case "fair":
        return "⚠️";
      case "poor":
        return "❌";
      default:
        return "📊";
    }
  };

  return (
    <div className="w-full space-y-6">
      <div className="glass-card p-4 border-white/5 bg-white/5">
        <h3 className="text-lg font-bold text-primary mb-6 flex items-center gap-2">
          <span className="w-1 h-5 bg-primary rounded-full"></span>
          Driver Consistency Analysis
        </h3>

        <div className="flex flex-col md:flex-row items-center gap-8">
          <div
            className="w-32 h-32 rounded-full border-8 flex flex-col items-center justify-center relative shadow-[0_0_20px_rgba(0,0,0,0.3)] bg-black/20 backdrop-blur-sm"
            style={{ borderColor: getScoreColor(consistency.consistency_score) }}
          >
            <div className="text-3xl font-bold text-white">
              {consistency.consistency_score.toFixed(1)}
            </div>
            <div className="text-xs font-medium text-muted-foreground uppercase tracking-wider">/ 100</div>
          </div>

          <div className="flex-1 space-y-4 w-full">
            <div className="flex items-center gap-3 p-3 rounded-lg bg-white/5 border border-white/10">
              <span className="text-2xl">
                {getRatingEmoji(consistency.rating)}
              </span>
              <div>
                <div className="text-xs text-muted-foreground uppercase tracking-wider font-bold">Rating</div>
                <div className="text-lg font-bold text-foreground">{consistency.rating}</div>
              </div>
            </div>
            
            <div className="grid grid-cols-2 gap-4">
              <div className="p-3 rounded-lg bg-white/5 border border-white/10">
                 <div className="text-xs text-muted-foreground uppercase tracking-wider font-bold mb-1">Laps Analyzed</div>
                 <div className="text-lg font-mono font-bold text-foreground">{consistency.total_laps}</div>
              </div>
              {consistency.lap_time_cv !== undefined && (
                <div className="p-3 rounded-lg bg-white/5 border border-white/10">
                  <div className="text-xs text-muted-foreground uppercase tracking-wider font-bold mb-1">Lap Time CV</div>
                  <div className="text-lg font-mono font-bold text-foreground">{(consistency.lap_time_cv * 100).toFixed(2)}%</div>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>

      {consistency.strengths && consistency.strengths.length > 0 && (
        <div className="glass-card p-6">
          <h4 className="text-sm font-semibold text-muted-foreground mb-4 uppercase tracking-wider">Driver Strengths</h4>
          <ul className="space-y-2">
            {consistency.strengths.map((strength, index) => (
              <li key={index} className="flex items-center gap-3 text-foreground p-2 rounded-lg hover:bg-white/5 transition-colors">
                <span className="w-5 h-5 rounded-full bg-emerald-500/20 text-emerald-400 flex items-center justify-center text-xs">✓</span>
                {strength}
              </li>
            ))}
          </ul>
        </div>
      )}

      <div className="glass-card p-6 bg-primary/5 border-primary/20">
        <h4 className="text-sm font-semibold text-primary mb-2 uppercase tracking-wider flex items-center gap-2">
          <span className="text-lg">💡</span> Analysis Insight
        </h4>
        <p className="text-sm text-muted-foreground leading-relaxed">
          {consistency.consistency_score >= 80 &&
            "Excellent consistency! This driver maintains very stable lap times with minimal variation."}
          {consistency.consistency_score >= 60 &&
            consistency.consistency_score < 80 &&
            "Good consistency. The driver shows reliable performance with some minor variations."}
          {consistency.consistency_score >= 40 &&
            consistency.consistency_score < 60 &&
            "Fair consistency. There is noticeable variation in lap times that could be improved."}
          {consistency.consistency_score < 40 &&
            "Inconsistent performance detected. Focus on smoothing inputs and maintaining rhythm."}
        </p>
      </div>
    </div>
  );
}
