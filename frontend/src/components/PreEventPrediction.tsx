import { useState, useEffect } from "react";
import axios from "axios";
import { useDynamicLoadingMessage } from "../hooks/useDynamicLoadingMessage";

interface PreEventPredictionProps {
  track: string;
}

interface PredictionData {
  track: string;
  predictions: any;
  ai_analysis: any;
  timestamp: string;
}

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

function PreEventPrediction({ track }: PreEventPredictionProps) {
  const [predictions, setPredictions] = useState<PredictionData | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [weather, setWeather] = useState("");
  const [trackTemp, setTrackTemp] = useState("");

  // Dynamic loading messages
  const predictionMessages = [
    "Analyzing historical race data...",
    "Processing track conditions...",
    "Calculating performance metrics...",
    "Generating qualifying predictions...",
    "Computing race pace forecasts...",
    "Evaluating strategic recommendations...",
    "Compiling AI analysis...",
  ];
  
  const loadingMessage = useDynamicLoadingMessage(predictionMessages, 3000);

  const loadPredictions = async () => {
    if (!track) return;

    setLoading(true);
    setError(null);

    try {
      const params: any = {};
      if (weather) params.weather = weather;
      if (trackTemp) params.track_temp = parseFloat(trackTemp);

      const response = await axios.get(
        `${API_BASE_URL}/insights/pre-event-prediction/${track}`,
        { params }
      );
      setPredictions(response.data);
    } catch (err: any) {
      setError(err.response?.data?.detail || "Failed to load predictions");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (track) {
      loadPredictions();
    }
  }, [track]);

  const aiAnalysis = predictions?.ai_analysis || {};

  return (
    <div className="w-full space-y-6">
      <h3 className="text-xl font-bold text-primary flex items-center gap-2">
        <span className="text-2xl">🔮</span> Pre-Event Prediction
      </h3>

      {/* Input Controls */}
      <div className="glass-card p-6">
        <h4 className="text-lg font-bold text-white mb-4">Simulation Parameters</h4>
        <div className="flex flex-col md:flex-row gap-4 items-end">
          <div className="flex-1 w-full space-y-2">
            <label className="text-xs font-bold text-muted-foreground uppercase">Weather Conditions</label>
            <input
              type="text"
              value={weather}
              onChange={(e) => setWeather(e.target.value)}
              placeholder="e.g., Sunny, Cloudy, Rain"
              className="glass-input w-full px-3 py-2 text-sm"
            />
          </div>
          <div className="flex-1 w-full space-y-2">
            <label className="text-xs font-bold text-muted-foreground uppercase">Track Temperature (°C)</label>
            <input
              type="number"
              value={trackTemp}
              onChange={(e) => setTrackTemp(e.target.value)}
              placeholder="e.g., 25"
              className="glass-input w-full px-3 py-2 text-sm"
            />
          </div>
          <button 
            onClick={loadPredictions} 
            className="glass-button px-6 py-2 h-[42px] font-bold whitespace-nowrap bg-primary text-white hover:bg-primary/90 border-primary/50"
            disabled={loading}
          >
            {loading ? (
              <span className="flex items-center gap-2">
                <span className="inline-block w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></span>
                Updating...
              </span>
            ) : (
              "Update Predictions"
            )}
          </button>
        </div>
      </div>

      {loading && (
        <div className="w-full min-h-[200px] glass-card flex flex-col items-center justify-center text-muted-foreground">
          <div className="w-12 h-12 border-4 border-primary border-t-transparent rounded-full animate-spin mb-4"></div>
          <p className="text-lg font-medium animate-pulse transition-all duration-500">{loadingMessage}</p>
        </div>
      )}

      
      {error && (
        <div className="w-full p-4 glass-card bg-destructive/10 border-destructive/20 text-destructive flex items-center gap-3">
          <span className="text-xl">❌</span>
          <span className="font-medium">{error}</span>
        </div>
      )}

      {predictions && (
        <>
          {/* Prediction Summary */}
          <div className="glass-card p-6">
            <h4 className="text-lg font-bold text-white mb-4">Race Predictions</h4>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {Object.entries(predictions.predictions).map(([race, data]: [string, any]) => (
                <div key={race} className="p-4 bg-white/5 rounded-lg border border-white/10">
                  <div className="text-sm font-bold text-primary mb-3 pb-2 border-b border-white/10">{race}</div>
                  <div className="space-y-2">
                    <div className="flex justify-between items-center text-sm">
                      <span className="text-muted-foreground">Qualifying Pace:</span>
                      <span className="font-mono font-bold text-white">{data.predicted_qualifying_pace?.toFixed(2)}s</span>
                    </div>
                    <div className="flex justify-between items-center text-sm">
                      <span className="text-muted-foreground">Race Pace:</span>
                      <span className="font-mono font-bold text-white">{data.predicted_race_pace?.toFixed(2)}s</span>
                    </div>
                    <div className="flex justify-between items-center text-sm">
                      <span className="text-muted-foreground">Degradation (30L):</span>
                      <span className="font-mono font-bold text-white">{data.predicted_degradation_30_laps?.toFixed(2)}%</span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* AI Analysis */}
          {aiAnalysis.qualifyingPredictions && (
            <div className="glass-card p-6 border-l-4 border-l-purple-500">
              <h4 className="text-lg font-bold text-white mb-4 flex items-center gap-2">
                <span className="text-purple-500">⏱️</span> Qualifying Predictions
              </h4>
              <ul className="space-y-2">
                {Array.isArray(aiAnalysis.qualifyingPredictions) ? (
                  aiAnalysis.qualifyingPredictions.map((item: string, idx: number) => (
                    <li key={idx} className="flex items-start gap-3 text-muted-foreground">
                      <span className="mt-1.5 w-1.5 h-1.5 rounded-full bg-purple-500 flex-shrink-0"></span>
                      <span>{item}</span>
                    </li>
                  ))
                ) : (
                  <li className="flex items-start gap-3 text-muted-foreground">
                    <span className="mt-1.5 w-1.5 h-1.5 rounded-full bg-purple-500 flex-shrink-0"></span>
                    <span>{String(aiAnalysis.qualifyingPredictions)}</span>
                  </li>
                )}
              </ul>
            </div>
          )}

          {aiAnalysis.racePaceForecast && (
            <div className="glass-card p-6 border-l-4 border-l-blue-500">
              <h4 className="text-lg font-bold text-white mb-4 flex items-center gap-2">
                <span className="text-blue-500">🏎️</span> Race Pace Forecast
              </h4>
              <ul className="space-y-2">
                {Array.isArray(aiAnalysis.racePaceForecast) ? (
                  aiAnalysis.racePaceForecast.map((item: string, idx: number) => (
                    <li key={idx} className="flex items-start gap-3 text-muted-foreground">
                      <span className="mt-1.5 w-1.5 h-1.5 rounded-full bg-blue-500 flex-shrink-0"></span>
                      <span>{item}</span>
                    </li>
                  ))
                ) : (
                  <li className="flex items-start gap-3 text-muted-foreground">
                    <span className="mt-1.5 w-1.5 h-1.5 rounded-full bg-blue-500 flex-shrink-0"></span>
                    <span>{String(aiAnalysis.racePaceForecast)}</span>
                  </li>
                )}
              </ul>
            </div>
          )}

          {aiAnalysis.strategicRecommendations && (
            <div className="glass-card p-6 border-l-4 border-l-emerald-500">
              <h4 className="text-lg font-bold text-white mb-4 flex items-center gap-2">
                <span className="text-emerald-500">🧠</span> Strategic Recommendations
              </h4>
              <ul className="space-y-2">
                {Array.isArray(aiAnalysis.strategicRecommendations) ? (
                  aiAnalysis.strategicRecommendations.map((item: string, idx: number) => (
                    <li key={idx} className="flex items-start gap-3 text-muted-foreground">
                      <span className="mt-1.5 w-1.5 h-1.5 rounded-full bg-emerald-500 flex-shrink-0"></span>
                      <span>{item}</span>
                    </li>
                  ))
                ) : (
                  <li className="flex items-start gap-3 text-muted-foreground">
                    <span className="mt-1.5 w-1.5 h-1.5 rounded-full bg-emerald-500 flex-shrink-0"></span>
                    <span>{String(aiAnalysis.strategicRecommendations)}</span>
                  </li>
                )}
              </ul>
            </div>
          )}
        </>
      )}
    </div>
  );
}

export default PreEventPrediction;
