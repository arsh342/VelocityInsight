import { useState, useEffect } from "react";
import { api } from "../api/client";
import { generatePreEventInsights } from "../api/gemini";
import { Sun, Car, RefreshCw } from "lucide-react";
import { Thermometer } from "lucide-react";
import AlertBanner from "../components/AlertBanner";
import { type AlertEvent } from "../api/websocket";
import { useDynamicLoadingMessage } from "../hooks/useDynamicLoadingMessage";
import { HelmetIcon } from "../components/icons/HelmetIcon";



export default function PreEventPage() {
  const [track, setTrack] = useState("");
  const [weather, setWeather] = useState("sunny");
  const [trackTemp, setTrackTemp] = useState(25);
  const [loading, setLoading] = useState(false);
  const [fetchingWeather, setFetchingWeather] = useState(false);
  const [weatherFetched, setWeatherFetched] = useState(false);
  const [predictions, setPredictions] = useState<any>(null);
  const [aiInsights, setAiInsights] = useState<string>("");
  const [tracks, setTracks] = useState<string[]>([]);
  const [alerts, setAlerts] = useState<AlertEvent[]>([]);
  const [activeTab, setActiveTab] = useState<string>("conditions");

  // Helper to extract average prediction from R1/R2 data
  const getAvgPrediction = (field: string): number | null => {
    if (!predictions?.predictions) return null;
    const values = Object.values(predictions.predictions).map((p: any) => p[field]).filter((v: any) => v != null);
    return values.length > 0 ? values.reduce((a: number, b: number) => a + b, 0) / values.length : null;
  };

  // Helper to format lap time from seconds to MM:SS.SSS
  const formatLapTime = (seconds: number | null): string => {
    if (!seconds) return "--";
    const minutes = Math.floor(seconds / 60);
    const secs = (seconds % 60).toFixed(3);
    return `${minutes}:${secs.padStart(6, '0')}`;
  };

  // Dynamic loading messages for predictions
  const predictionMessages = [
    "Analyzing track conditions...",
    "Processing weather data...",
    "Calculating lap time predictions...",
    "Generating insights...",
    "Computing race pace forecast...",
    "Evaluating tire degradation...",
    "Finalizing predictions...",
  ];
  
  const loadingMessage = useDynamicLoadingMessage(predictionMessages, 3000);

  useEffect(() => {
    api.getTracks().then(setTracks).catch(console.error);
  }, []);

  const handleFetchWeather = async () => {
    if (!track) return;

    setFetchingWeather(true);
    setWeatherFetched(false);
    try {
      const weatherData = await api.getWeather(track);
      
      // Auto-populate weather fields
      setWeather(weatherData.weather);
      setTrackTemp(Math.round(weatherData.temperature));
      setWeatherFetched(true);
      
      // Show success message briefly
      setTimeout(() => setWeatherFetched(false), 3000);
    } catch (error) {
      console.error("Error fetching weather:", error);
      alert("Failed to fetch weather data. Please try again or enter manually.");
    } finally {
      setFetchingWeather(false);
    }
  };

  const handlePredict = async () => {
    if (!track) return;

    setLoading(true);
    try {
      // Get predictions from backend
      const data = await api.getPreEventPrediction(track, weather, trackTemp);
      setPredictions(data);

      // Generate insights separately - don't let this fail the whole process
      try {
        const insights = await generatePreEventInsights(
          track,
          weather,
          trackTemp,
          data
        );
        setAiInsights(insights);
      } catch (aiError) {
        console.error("Error generating insights (predictions still available):", aiError);
        setAiInsights("Insights temporarily unavailable. Please try again later.");
      }
    } catch (error) {
      console.error("Error generating predictions:", error);
      alert("Failed to generate predictions. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  return (
    
      <div className="min-h-screen w-full p-4 md:p-6 space-y-6 pb-20">
        {/* Alert Banner */}
        <AlertBanner
          alerts={alerts}
          onDismiss={(timestamp) => {
            setAlerts(alerts.filter((a) => a.timestamp !== timestamp));
          }}
        />

        {/* Control Panel */}
        <div className="glass-card p-4 md:p-6">
          <div className="flex flex-col gap-4">
            {/* Track Selection and Update Button */}
            <div className="flex flex-wrap gap-4 items-end">
              <div className="space-y-2 min-w-[200px] flex-1">
                <label htmlFor="track-select" className="text-xs font-bold text-muted-foreground uppercase tracking-wider flex items-center gap-2">
                  <Car className="text-primary h-4 w-4" /> Track
                </label>
                <select
                  id="track-select"
                  value={track}
                  onChange={(e) => setTrack(e.target.value)}
                  className="glass-input w-full px-4 py-2.5 text-sm font-medium appearance-none cursor-pointer hover:bg-white/5"
                >
                  <option value="" className="bg-card text-card-foreground">Select Track</option>
                  {tracks.map((t) => (
                    <option key={t} value={t} className="bg-card text-card-foreground">
                      {t}
                    </option>
                  ))}
                </select>
              </div>

              <button
                onClick={handleFetchWeather}
                disabled={!track || fetchingWeather}
                className="glass-button px-5 py-2.5 font-bold bg-blue-500/20 hover:bg-blue-500/30 text-blue-400 border-blue-500/30 flex items-center gap-2"
              >
                {fetchingWeather ? (
                  <>
                    <span className="inline-block w-4 h-4 border-2 border-blue-400 border-t-transparent rounded-full animate-spin"></span>
                    Updating...
                  </>
                ) : (
                  <>
                    <RefreshCw className="h-4 w-4" /> Update
                  </>
                )}
              </button>

              <button
                onClick={handlePredict}
                disabled={!track || loading}
                className="glass-button px-6 py-2.5 font-bold bg-primary/20 hover:bg-primary/30 text-primary border-primary/30"
              >
                {loading ? (
                  <span className="flex items-center gap-2">
                    <span className="inline-block w-4 h-4 border-2 border-primary border-t-transparent rounded-full animate-spin"></span>
                    {loadingMessage}
                  </span>
                ) : (
                  "Generate Predictions"
                )}
              </button>
            </div>

            {/* Current Weather Display (Read-only) */}
            {weatherFetched && (
              <div className="flex flex-wrap gap-4 p-4 bg-white/5 rounded-lg border border-white/10">
                <div className="flex items-center gap-3 mb-4">
              <HelmetIcon className="text-primary h-6 w-6" />
              <h3 className="text-xl font-bold text-white">Strategy Recommendation</h3>
            </div>
                <div className="flex items-center gap-2">
                  <Sun className="text-primary h-5 w-5" />
                  <div>
                    <div className="text-xs text-muted-foreground uppercase tracking-wider">Weather</div>
                    <div className="text-sm font-bold text-white">
                      {weather.charAt(0).toUpperCase() + weather.slice(1)}
                    </div>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <Thermometer className="h-5 w-5 text-primary" />
                  <div>
                    <div className="text-xs text-muted-foreground uppercase tracking-wider">Track Temp</div>
                    <div className="text-sm font-bold text-white">{trackTemp}°C</div>
                  </div>
                </div>
                <div className="flex items-center gap-2 ml-auto">
                  <span className="text-xs text-green-400 flex items-center gap-1">
                    ✓ Real-time weather for {track}
                  </span>
                </div>
              </div>
            )}
          </div>
        </div>


        {/* Dashboard */}
        <div className="space-y-6">
          {/* Race Header */}
          <div className="flex flex-col md:flex-row justify-between items-end gap-4 mb-6">
            <div className="space-y-1">
              <h1 className="text-4xl md:text-5xl font-display font-bold text-white flex items-center justify-center gap-4">
            <Car className="text-primary h-10 w-10" /> Pre-Event Prediction
          </h1>
              <p className="text-muted-foreground">
                {track
                  ? `${track} - ${weather} conditions`
                  : "Select track and conditions to begin"}
              </p>
            </div>
            <div className="flex gap-8 bg-black/20 backdrop-blur-md px-6 py-3 rounded-xl border border-white/10">
              <div className="flex flex-col items-center">
                <span className="text-2xl font-bold text-primary">
                  {formatLapTime(getAvgPrediction("predicted_qualifying_pace"))}
                </span>
                <span className="text-xs uppercase tracking-widest text-muted-foreground">Expected Lap Time</span>
              </div>
              <div className="flex flex-col items-center">
                <span className="text-2xl font-bold text-primary">{trackTemp}°C</span>
                <span className="text-xs uppercase tracking-widest text-muted-foreground">Track Temp</span>
              </div>
              <div className="flex flex-col items-center">
                <span className="text-2xl font-bold text-primary">
                  {weather.charAt(0).toUpperCase() + weather.slice(1)}
                </span>
                <span className="text-xs uppercase tracking-widest text-muted-foreground">Weather</span>
              </div>
            </div>
          </div>

          {/* Navigation Tabs */}
          <div className="flex flex-wrap gap-2 border-b border-white/10 mb-6">
            {[
              { id: "conditions", label: "Race Conditions" },
              { id: "predictions", label: "Performance Predictions" },
              { id: "ai-insights", label: "Strategy Insights" },
              { id: "qualifying", label: "Qualifying Forecast" }
            ].map((tab) => (
              <button
                key={tab.id}
                className={`px-4 py-2 text-sm font-medium transition-all border-b-2 ${
                  activeTab === tab.id
                    ? "text-primary border-primary"
                    : "text-muted-foreground border-transparent hover:text-white hover:border-white/20"
                }`}
                onClick={() => setActiveTab(tab.id)}
              >
                {tab.label}
              </button>
            ))}
          </div>

          {/* Tab Content */}
          {activeTab === "conditions" && (
            <section className="glass-card p-4 md:p-6 animate-in slide-in-from-bottom-4 duration-500">
              <div className="text-lg font-bold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
                <span>Race Conditions Analysis</span>
              </div>
              {predictions ? (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  {/* Current Conditions Card */}
                  <section className="glass-card p-4 md:p-6 bg-white/5">
                    <div className="text-lg font-bold text-gray-900 dark:text-white mb-4">
                      <span>Current Conditions</span>
                    </div>
                    <div className="space-y-4">
                      <div className="flex justify-between items-center p-3 bg-white/5 rounded-lg">
                        <span className="text-muted-foreground">Track</span>
                        <span className="text-white font-bold">{track}</span>
                      </div>
                      <div className="flex justify-between items-center p-3 bg-white/5 rounded-lg">
                        <span className="text-muted-foreground">Weather</span>
                        <span className="text-white font-bold">{weather.charAt(0).toUpperCase() + weather.slice(1)}</span>
                      </div>
                      <div className="flex justify-between items-center p-3 bg-white/5 rounded-lg">
                        <span className="text-muted-foreground">Track Temperature</span>
                        <span className="text-white font-bold">{trackTemp}°C</span>
                      </div>
                      <div className="flex justify-between items-center p-3 bg-white/5 rounded-lg">
                        <span className="text-muted-foreground">Expected Pace</span>
                        <span className="text-white font-bold">
                          {formatLapTime(getAvgPrediction("predicted_qualifying_pace"))}
                        </span>
                      </div>
                    </div>
                  </section>

                  {/* Track Characteristics Card */}
                  <section className="glass-card p-4 md:p-6 bg-white/5">
                    <div className="text-lg font-bold text-gray-900 dark:text-white mb-4">
                      <span>Setup Recommendations</span>
                    </div>
                    <div className="space-y-3">
                      {predictions.ai_analysis?.strategicRecommendations ? (
                        predictions.ai_analysis.strategicRecommendations.slice(0, 4).map((rec: string, idx: number) => (
                          <div key={idx} className="flex items-start gap-2 text-sm text-muted-foreground">
                            <span className="text-primary mt-1">•</span>
                            <span>{rec}</span>
                          </div>
                        ))
                      ) : (
                        <>
                          <div className="flex items-start gap-2 text-sm text-muted-foreground">
                            <span className="text-primary mt-1">•</span>
                            <span>Monitor tire temperatures in {weather} conditions</span>
                          </div>
                          <div className="flex items-start gap-2 text-sm text-muted-foreground">
                            <span className="text-primary mt-1">•</span>
                            <span>Adjust setup for {trackTemp}°C track temperature</span>
                          </div>
                          <div className="flex items-start gap-2 text-sm text-muted-foreground">
                            <span className="text-primary mt-1">•</span>
                            <span>Focus on consistency and tire management</span>
                          </div>
                        </>
                      )}
                    </div>
                  </section>

                  {/* Historical Performance */}
                  <section className="glass-card p-4 md:p-6 bg-white/5 md:col-span-2">
                    <div className="text-lg font-bold text-gray-900 dark:text-white mb-4">
                      <span>Historical Data Analysis</span>
                    </div>
                    <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-4">
                      <div className="p-4 rounded-lg bg-white/5 border border-white/10 flex flex-col items-center">
                        <span className="text-xs uppercase tracking-widest text-muted-foreground mb-1">Best Historical</span>
                        <span className="text-lg font-bold text-white">
                          {formatLapTime(Object.values(predictions.predictions || {}).map((p: any) => p.best_historical_lap).filter(Boolean)[0])}
                        </span>
                      </div>
                      <div className="p-4 rounded-lg bg-white/5 border border-white/10 flex flex-col items-center">
                        <span className="text-xs uppercase tracking-widest text-muted-foreground mb-1">Avg Baseline</span>
                        <span className="text-lg font-bold text-white">
                          {formatLapTime(Object.values(predictions.predictions || {}).map((p: any) => p.baseline_lap_time).filter(Boolean)[0])}
                        </span>
                      </div>
                      <div className="p-4 rounded-lg bg-white/5 border border-white/10 flex flex-col items-center">
                        <span className="text-xs uppercase tracking-widest text-muted-foreground mb-1">Tire Deg/Lap</span>
                        <span className="text-lg font-bold text-white">
                          {getAvgPrediction("predicted_tire_degradation_per_lap")?.toFixed(3) || "N/A"}s
                        </span>
                      </div>
                      <div className="p-4 rounded-lg bg-white/5 border border-white/10 flex flex-col items-center">
                        <span className="text-xs uppercase tracking-widest text-muted-foreground mb-1">30-Lap Total</span>
                        <span className="text-lg font-bold text-white">
                          {getAvgPrediction("predicted_degradation_30_laps")?.toFixed(2) || "N/A"}s
                        </span>
                      </div>
                    </div>
                  </section>
                </div>
              ) : (
                <div className="text-center p-12 border border-dashed border-white/10 rounded-lg">
                  <Sun className="text-primary h-10 w-10 mx-auto mb-4" />
                  <h3 className="text-white font-bold text-xl mb-2">Ready to Analyze Conditions</h3>
                  <p className="text-muted-foreground mb-4">
                    Select a track and click "🔄 Update" to fetch current weather,<br />
                    then click "Generate Predictions" to see detailed analysis.
                  </p>
                </div>
              )}
            </section>
          )}

          {activeTab === "predictions" && predictions && (
            <section className="glass-card p-4 md:p-6 animate-in slide-in-from-bottom-4 duration-500">
              <div className="text-lg font-bold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
                <span>Performance Predictions</span>
              </div>
              <section className="glass-card p-4 md:p-6 bg-white/5">
                <div className="text-lg font-bold text-gray-900 dark:text-white mb-4">
                  <span>Expected Performance</span>
                </div>
                <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-4">
                  <div className="p-4 rounded-lg bg-white/5 border border-white/10 flex flex-col items-center hover:bg-white/10 transition-colors">
                    <span className="text-xs uppercase tracking-widest text-muted-foreground mb-1">Qualifying Pace</span>
                    <span className="text-xl font-bold text-white">
                      {formatLapTime(getAvgPrediction("predicted_qualifying_pace"))}
                    </span>
                  </div>
                  <div className="p-4 rounded-lg bg-white/5 border border-white/10 flex flex-col items-center hover:bg-white/10 transition-colors">
                    <span className="text-xs uppercase tracking-widest text-muted-foreground mb-1">Race Pace</span>
                    <span className="text-xl font-bold text-white">
                      {formatLapTime(getAvgPrediction("predicted_race_pace"))}
                    </span>
                  </div>
                  <div className="p-4 rounded-lg bg-white/5 border border-white/10 flex flex-col items-center hover:bg-white/10 transition-colors">
                    <span className="text-xs uppercase tracking-widest text-muted-foreground mb-1">Degradation (30 laps)</span>
                    <span className="text-xl font-bold text-white">
                      {getAvgPrediction("predicted_degradation_30_laps")?.toFixed(2) || "N/A"}s
                    </span>
                  </div>
                  <div className="p-4 rounded-lg bg-white/5 border border-white/10 flex flex-col items-center hover:bg-white/10 transition-colors">
                    <span className="text-xs uppercase tracking-widest text-muted-foreground mb-1">Tire Deg/Lap</span>
                    <span className="text-xl font-bold text-white">
                      {getAvgPrediction("predicted_tire_degradation_per_lap")?.toFixed(3) || "N/A"}s
                    </span>
                  </div>
                </div>
              </section>
            </section>
          )}

          {activeTab === "ai-insights" && (
            <section className="glass-card p-4 md:p-6 animate-in slide-in-from-bottom-4 duration-500">
              <div className="text-lg font-bold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
                <span>
                  <HelmetIcon className="text-primary h-5 w-5" /> Race Strategy Insights
                </span>
              </div>
              {predictions ? (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <section className="glass-card p-4 md:p-6 bg-white/5">
                    <div className="text-lg font-bold text-gray-900 dark:text-white mb-4">
                      <span>Analysis</span>
                    </div>
                    <div className="space-y-2">
                      {aiInsights ? (
                        aiInsights
                          .split('\n')
                          .filter((line: string) => line.trim())
                          .map((line: string, idx: number) => {
                            // Remove asterisks and clean up the line
                            const cleanLine = line.replace(/\*\*/g, '').replace(/\*/g, '').trim();
                            // Skip section headers (lines that are all caps or very short)
                            if (cleanLine.length < 10 || cleanLine === cleanLine.toUpperCase()) {
                              return null;
                            }
                            // Check if it's a bullet point
                            const isBullet = cleanLine.startsWith('•') || cleanLine.startsWith('-');
                            const text = isBullet ? cleanLine.substring(1).trim() : cleanLine;
                            
                            return (
                              <div key={idx} className="flex items-start gap-2 text-sm text-muted-foreground leading-relaxed">
                                <span className="text-primary mt-1">•</span>
                                <span>{text}</span>
                              </div>
                            );
                          })
                      ) : (
                        <div className="text-muted-foreground">Generating insights...</div>
                      )}
                    </div>
                  </section>

                  {predictions.ai_analysis?.strategicRecommendations && (
                    <section className="glass-card p-4 md:p-6 bg-white/5">
                      <div className="text-lg font-bold text-gray-900 dark:text-white mb-4">
                        <span>Strategic Recommendations</span>
                      </div>
                      <div className="space-y-2">
                        {predictions.ai_analysis.strategicRecommendations.map(
                          (rec: string, idx: number) => (
                            <div key={idx} className="flex items-start gap-2 text-sm text-muted-foreground">
                              <span className="text-primary mt-1">•</span>
                              <span>{rec}</span>
                            </div>
                          )
                        )}
                      </div>
                    </section>
                  )}
                </div>
              ) : (
                <div className="flex items-center justify-center h-32 text-muted-foreground animate-pulse">
                  Generate predictions first to get insights
                </div>
              )}
            </section>
          )}

          {activeTab === "qualifying" && (
            <section className="glass-card p-4 md:p-6 animate-in slide-in-from-bottom-4 duration-500">
              <div className="text-lg font-bold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
                <span>Qualifying & Race Forecast</span>
              </div>
              {predictions ? (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  {predictions.ai_analysis?.qualifyingPredictions && (
                    <section className="glass-card p-4 md:p-6 bg-white/5">
                      <div className="text-lg font-bold text-gray-900 dark:text-white mb-4">
                        <span>Qualifying Predictions</span>
                      </div>
                      <div className="space-y-2">
                        {predictions.ai_analysis.qualifyingPredictions.map(
                          (pred: string, idx: number) => (
                            <div key={idx} className="flex items-start gap-2 text-sm text-muted-foreground">
                              <span className="text-primary mt-1">•</span>
                              <span>{pred}</span>
                            </div>
                          )
                        )}
                      </div>
                    </section>
                  )}

                  {predictions.ai_analysis?.racePaceForecast && (
                    <section className="glass-card p-4 md:p-6 bg-white/5">
                      <div className="text-lg font-bold text-gray-900 dark:text-white mb-4">
                        <span>Race Pace Forecast</span>
                      </div>
                      <div className="space-y-2">
                        {predictions.ai_analysis.racePaceForecast.map(
                          (forecast: string, idx: number) => (
                            <div key={idx} className="flex items-start gap-2 text-sm text-muted-foreground">
                              <span className="text-primary mt-1">•</span>
                              <span>{forecast}</span>
                            </div>
                          )
                        )}
                      </div>
                    </section>
                  )}
                </div>
              ) : (
                <div className="flex items-center justify-center h-32 text-muted-foreground animate-pulse">
                  Generate predictions first to see qualifying and race forecasts
                </div>
              )}
            </section>
          )}

          {!predictions && activeTab !== "conditions" && (
            <section className="glass-card p-4 md:p-6 animate-in slide-in-from-bottom-4 duration-500">
              <div className="text-lg font-bold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
                <span>No Predictions Available</span>
              </div>
              <div className="text-muted-foreground p-8 text-center border border-dashed border-white/10 rounded-lg">
                Please select track conditions and generate predictions to view
                this section.
              </div>
            </section>
          )}
        </div>
      </div>
    
  );
}
