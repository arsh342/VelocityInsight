import { useState, useEffect } from "react";
import axios from "axios";
import { AlertTriangle, Flag, Lightbulb } from "lucide-react";

interface DriverTrainingProps {
  track: string;
  race: string;
  vehicleId: string;
}

interface TrainingInsights {
  vehicle_id: string;
  track: string;
  race: string;
  performance_summary: any;
  sector_analysis: any;
  telemetry_insights: any;
  ai_analysis: any;
}

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

function DriverTraining({ track, race, vehicleId }: DriverTrainingProps) {
  const [insights, setInsights] = useState<TrainingInsights | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const loadInsights = async () => {
      if (!track || !race || !vehicleId) return;
      
      setLoading(true);
      setError(null);

      try {
        const response = await axios.get(
          `${API_BASE_URL}/insights/driver-training/${track}/${race}/${vehicleId}`
        );
        setInsights(response.data);
      } catch (err: any) {
        setError(err.response?.data?.detail || "Failed to load training insights");
      } finally {
        setLoading(false);
      }
    };

    loadInsights();
  }, [track, race, vehicleId]);

  if (loading) {
    return (
      <div className="w-full space-y-6">
        <h3 className="text-xl font-bold text-primary flex items-center gap-2">
          <span className="w-1 h-6 bg-primary rounded-full"></span>
          Driver Training & Insights
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
          <span className="w-1 h-6 bg-primary rounded-full"></span>
          Driver Training & Insights
        </h3>
        <div className="w-full h-[200px] glass-card flex flex-col items-center justify-center text-destructive bg-destructive/10 border-destructive/20">
          <p className="text-lg font-bold mb-2">❌ {error}</p>
        </div>
      </div>
    );
  }

  if (!insights) return null;

  const aiAnalysis = insights.ai_analysis || {};

  return (
    <div className="w-full space-y-6">
      <h3 className="text-xl font-bold text-primary flex items-center gap-2">
        <span className="w-1 h-6 bg-primary rounded-full"></span>
        Driver Training & Insights
      </h3>

      {/* Performance Summary */}
      <div className="glass-card p-6">
        <h4 className="text-lg font-bold text-white mb-4">Performance Summary</h4>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="p-4 bg-white/5 rounded-lg border border-white/10 flex flex-col items-center text-center">
            <div className="text-xs text-muted-foreground uppercase tracking-wider font-bold mb-1">Average Lap Time</div>
            <div className="text-2xl font-mono font-bold text-foreground">
              {insights.performance_summary?.avg_lap_time?.toFixed(2)}s
            </div>
          </div>
          <div className="p-4 bg-white/5 rounded-lg border border-white/10 flex flex-col items-center text-center relative overflow-hidden">
            <div className="absolute top-0 right-0 w-12 h-12 bg-primary/20 rounded-bl-full -mr-6 -mt-6"></div>
            <div className="text-xs text-muted-foreground uppercase tracking-wider font-bold mb-1">Best Lap</div>
            <div className="text-2xl font-mono font-bold text-primary">
              {insights.performance_summary?.best_lap_time?.toFixed(2)}s
            </div>
          </div>
          <div className="p-4 bg-white/5 rounded-lg border border-white/10 flex flex-col items-center text-center">
            <div className="text-xs text-muted-foreground uppercase tracking-wider font-bold mb-1">Consistency</div>
            <div className="text-2xl font-mono font-bold text-foreground">
              {insights.performance_summary?.consistency?.toFixed(2)}s
            </div>
          </div>
        </div>
      </div>

      {/* Sector Analysis */}
      {insights.sector_analysis && Object.keys(insights.sector_analysis).length > 0 && (
        <div className="glass-card p-6">
          <h4 className="text-lg font-bold text-white mb-4">Sector Performance</h4>
          <div className="space-y-3">
            {Object.entries(insights.sector_analysis).map(([sector, data]: [string, any]) => (
              <div key={sector} className="flex flex-col md:flex-row items-center justify-between p-4 bg-white/5 rounded-lg border border-white/10 gap-4">
                <div className="font-bold text-lg text-primary">{sector.toUpperCase()}</div>
                <div className="flex flex-1 justify-around w-full md:w-auto gap-4">
                  <div className="flex flex-col items-center">
                    <span className="text-xs text-muted-foreground uppercase">Avg</span>
                    <span className="font-mono font-bold">{data.avg?.toFixed(2)}s</span>
                  </div>
                  <div className="flex flex-col items-center">
                    <span className="text-xs text-muted-foreground uppercase">Best</span>
                    <span className="font-mono font-bold text-emerald-400">{data.best?.toFixed(2)}s</span>
                  </div>
                  <div className="flex flex-col items-center">
                    <span className="text-xs text-muted-foreground uppercase">Consistency</span>
                    <span className="font-mono font-bold">{data.consistency?.toFixed(2)}s</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Areas for Improvement */}
      {aiAnalysis.areasForImprovement && (
        <div className="glass-card p-6 border-l-4 border-l-amber-500">
          <h4 className="text-lg font-bold text-white mb-4 flex items-center gap-2">
            <AlertTriangle className="inline-block h-5 w-5 text-amber-500" /> Areas for Improvement
          </h4>
          <ul className="space-y-2">
            {aiAnalysis.areasForImprovement.map((item: string, idx: number) => (
              <li key={idx} className="flex items-start gap-3 text-muted-foreground">
                <span className="mt-1.5 w-1.5 h-1.5 rounded-full bg-amber-500 flex-shrink-0"></span>
                <span>{item}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Racing Line Tips */}
      {aiAnalysis.racingLineTips && (
        <div className="glass-card p-6 border-l-4 border-l-blue-500">
          <h4 className="text-lg font-bold text-white mb-4 flex items-center gap-2">
            <Flag className="inline-block h-5 w-5 text-blue-500" /> Racing Line Optimization
          </h4>
          <ul className="space-y-2">
            {aiAnalysis.racingLineTips.map((tip: string, idx: number) => (
              <li key={idx} className="flex items-start gap-3 text-muted-foreground">
                <span className="mt-1.5 w-1.5 h-1.5 rounded-full bg-blue-500 flex-shrink-0"></span>
                <span>{tip}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Training Recommendations */}
      {aiAnalysis.trainingRecommendations && (
        <div className="glass-card p-6 border-l-4 border-l-emerald-500">
          <h4 className="text-lg font-bold text-white mb-4 flex items-center gap-2">
            <span className="text-emerald-500">💪</span> Training Recommendations
          </h4>
          <ul className="space-y-2">
            {aiAnalysis.trainingRecommendations.map((rec: string, idx: number) => (
              <li key={idx} className="flex items-start gap-3 text-muted-foreground">
                <span className="mt-1.5 w-1.5 h-1.5 rounded-full bg-emerald-500 flex-shrink-0"></span>
                <span>{rec}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Performance Insights */}
      {aiAnalysis.performanceInsights && (
        <div className="glass-card p-6 bg-primary/5 border-primary/20">
          <h4 className="text-lg font-bold text-primary mb-4 flex items-center gap-2">
            <Lightbulb className="inline-block h-5 w-5 text-primary" /> Performance Insights
          </h4>
          <p className="text-muted-foreground leading-relaxed">{aiAnalysis.performanceInsights}</p>
        </div>
      )}
    </div>
  );
}

export default DriverTraining;
