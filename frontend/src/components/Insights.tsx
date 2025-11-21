import { useState, useEffect } from "react";
import { api } from "../api/client";
import { generateRaceInsights, generateStrategicInstructions } from "../api/gemini";

interface InsightsProps {
  track: string;
  race: string;
  vehicleId: string;
  currentLap?: number;
}

interface RaceInsights {
  summary: string;
  keyInsights: string[];
  recommendations: string[];
  strategicAdvice: string;
}

function Insights({ track, race, vehicleId, currentLap = 5 }: InsightsProps) {
  const [insights, setInsights] = useState<RaceInsights | null>(null);
  const [strategicInstruction, setStrategicInstruction] = useState<string>("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const loadInsights = async () => {
      setLoading(true);
      setError(null);

      try {
        // Load all performance data in parallel
        const [lapTimes, degradation, consistency, pitStrategy, prediction] = await Promise.all([
          api.getLapTimes(track, race, vehicleId).catch(() => []),
          api.getDegradation(track, race, vehicleId).catch(() => null),
          api.getConsistency(track, race, vehicleId).catch(() => null),
          api.getPitStrategy(track, race, vehicleId, currentLap, 30, 5, 1).catch(() => null),
          api.predictLapTime(track, race, vehicleId, currentLap).catch(() => null),
        ]);

        const performanceData = {
          lapTimes: lapTimes.slice(0, 20), // Last 20 laps
          degradation,
          consistency,
          pitStrategy,
          prediction,
        };

        // Generate insights
        const aiInsights = await generateRaceInsights(track, race, vehicleId, performanceData);
        setInsights(aiInsights);

        // Generate strategic instruction
        const tireAge = degradation?.average_tire_age || currentLap;
        const instruction = await generateStrategicInstructions(
          track,
          race,
          vehicleId,
          currentLap,
          tireAge,
          1,
          0
        );
        setStrategicInstruction(instruction);
      } catch (err) {
        console.error("Error loading insights:", err);
        setError("Failed to load insights. Please try again.");
      } finally {
        setLoading(false);
      }
    };

    if (track && race && vehicleId) {
      loadInsights();
    }
  }, [track, race, vehicleId, currentLap]);

  if (loading) {
    return (
      <div className="w-full space-y-6">
        <h3 className="text-xl font-bold text-primary flex items-center gap-2">
          <span className="text-2xl">🏎️</span> Race Insights
        </h3>
        <div className="w-full h-[300px] glass-card flex flex-col items-center justify-center text-muted-foreground animate-pulse">
          <div className="w-12 h-12 border-4 border-primary border-t-transparent rounded-full animate-spin mb-4"></div>
          <p>Analyzing performance data...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="w-full space-y-6">
        <h3 className="text-xl font-bold text-primary flex items-center gap-2">
          <span className="text-2xl">🏎️</span> Race Insights
        </h3>
        <div className="w-full h-[200px] glass-card flex flex-col items-center justify-center text-destructive bg-destructive/10 border-destructive/20">
          <p className="text-lg font-bold mb-2">❌ {error}</p>
        </div>
      </div>
    );
  }

  if (!insights) {
    return null;
  }

  return (
    <div className="w-full space-y-6">
      <h3 className="text-xl font-bold text-primary flex items-center gap-2">
        <span className="text-2xl">🏎️</span> Race Insights
      </h3>

      {/* Strategic Instruction Card */}
      {strategicInstruction && (
        <div className="glass-card p-6 border-l-4 border-l-primary bg-primary/5 relative overflow-hidden">
          <div className="absolute top-0 right-0 w-24 h-24 bg-primary/10 rounded-bl-full -mr-10 -mt-10"></div>
          <div className="flex items-center gap-3 mb-3">
            <span className="text-2xl animate-pulse">📢</span>
            <span className="text-xs font-bold text-primary uppercase tracking-wider border border-primary/30 px-2 py-0.5 rounded-full bg-primary/10">LIVE INSTRUCTION</span>
          </div>
          <p className="text-lg font-medium text-white leading-relaxed">{strategicInstruction}</p>
        </div>
      )}

      {/* Summary */}
      <div className="glass-card p-6">
        <h4 className="text-lg font-bold text-white mb-4">Performance Summary</h4>
        <p className="text-muted-foreground leading-relaxed">{insights.summary}</p>
      </div>

      {/* Key Insights */}
      {insights.keyInsights.length > 0 && (
        <div className="glass-card p-6">
          <h4 className="text-lg font-bold text-white mb-4">Key Insights</h4>
          <ul className="space-y-3">
            {insights.keyInsights.map((insight, idx) => (
              <li key={idx} className="flex items-start gap-3 text-muted-foreground">
                <span className="mt-2 w-1.5 h-1.5 rounded-full bg-primary flex-shrink-0"></span>
                <span>{insight}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Recommendations */}
      {insights.recommendations.length > 0 && (
        <div className="glass-card p-6 border-l-4 border-l-emerald-500">
          <h4 className="text-lg font-bold text-white mb-4 flex items-center gap-2">
            <span className="text-emerald-500">✓</span> Recommendations
          </h4>
          <ul className="space-y-3">
            {insights.recommendations.map((rec, idx) => (
              <li key={idx} className="flex items-start gap-3 text-muted-foreground">
                <span className="w-5 h-5 rounded-full bg-emerald-500/20 text-emerald-400 flex items-center justify-center text-xs flex-shrink-0 mt-0.5">✓</span>
                <span>{rec}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Strategic Advice */}
      {insights.strategicAdvice && (
        <div className="glass-card p-6 bg-gradient-to-br from-white/5 to-primary/5 border-primary/20">
          <h4 className="text-lg font-bold text-primary mb-4">Strategic Advice</h4>
          <p className="text-muted-foreground leading-relaxed italic border-l-2 border-primary/30 pl-4">
            "{insights.strategicAdvice}"
          </p>
        </div>
      )}
    </div>
  );
}

export default Insights;
