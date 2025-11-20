import { useState, useEffect } from "react";
import { api } from "../api/client";
import { generateDriverTrainingInsights } from "../api/gemini";
import { Car, Bot, AlertTriangle, Flag, Lightbulb, Car as CarIcon } from "lucide-react";
import Loading from "../components/Loading";
import AlertBanner from "../components/AlertBanner";
import { type AlertEvent } from "../api/websocket";



interface DriverTrainingPageProps {
  track: string;
  race: string;
  vehicleId: string;
}

export default function DriverTrainingPage({}: DriverTrainingPageProps) {
  // User selection state
  const [selectedTrack, setSelectedTrack] = useState("");
  const [selectedRace, setSelectedRace] = useState("");
  const [selectedVehicle, setSelectedVehicle] = useState("");
  const [availableTracks, setAvailableTracks] = useState<string[]>([]);
  const [availableVehicles, setAvailableVehicles] = useState<string[]>([]);

  const [loading, setLoading] = useState(false);
  const [trainingData, setTrainingData] = useState<any>(null);
  const [aiInsights, setAiInsights] = useState<string>("");
  const [alerts, setAlerts] = useState<AlertEvent[]>([]);
  const [activeTab, setActiveTab] = useState<string>("analysis");

  // Load available tracks on mount
  useEffect(() => {
    loadTracks();
  }, []);

  // Load vehicles when track/race changes
  useEffect(() => {
    if (selectedTrack && selectedRace) {
      loadVehicles();
    }
  }, [selectedTrack, selectedRace]);

  const loadTracks = async () => {
    try {
      const tracks = await api.getTracks();
      setAvailableTracks(tracks);
      if (tracks.length > 0) {
        setSelectedTrack(tracks[0]);
        setSelectedRace("R1");
      }
    } catch (error) {
      console.error("Error loading tracks:", error);
    }
  };

  const loadVehicles = async () => {
    try {
      const vehicles = await api.getVehicles(selectedTrack, selectedRace);
      setAvailableVehicles(vehicles);
      if (vehicles.length > 0) {
        setSelectedVehicle(vehicles[0]);
      }
    } catch (error) {
      console.error("Error loading vehicles:", error);
    }
  };

  const handleAnalyze = () => {
    if (selectedTrack && selectedRace && selectedVehicle) {
      loadTrainingData();
    }
  };

  const loadTrainingData = async () => {
    setLoading(true);
    try {
      const data = await api.getDriverTraining(
        selectedTrack,
        selectedRace,
        selectedVehicle
      );
      setTrainingData(data);

      // Generate AI insights
      const insights = await generateDriverTrainingInsights(
        selectedTrack,
        selectedRace,
        selectedVehicle,
        data
      );
      setAiInsights(insights);
    } catch (error) {
      console.error("Error loading training data:", error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      
        <div className="min-h-screen w-full flex items-center justify-center">
          <Loading
            size="lg"
            variant="spinner"
            text="Analyzing driver performance..."
          />
        </div>
      
    );
  }

  return (
    
      <div className="min-h-screen w-full p-6 space-y-6 pb-20">
        <div className="text-center space-y-4 mb-8">
          <h1 className="text-4xl md:text-5xl font-display font-bold text-white flex items-center justify-center gap-4">
            <Car className="text-primary h-10 w-10" /> Driver Training
          </h1>
          <p className="text-xl text-muted-foreground max-w-2xl mx-auto">
            Identify areas for improvement and optimize racing line with AI-powered insights
          </p>
        </div>

        <div className="glass-card p-6">
          <div className="flex flex-wrap gap-4 items-end">
            <div className="space-y-2 min-w-[200px]">
              <label className="text-xs font-bold text-muted-foreground uppercase tracking-wider">Track</label>
              <select
                value={selectedTrack}
                onChange={(e) => setSelectedTrack(e.target.value)}
                className="glass-input w-full px-4 py-2.5 text-sm font-medium appearance-none cursor-pointer hover:bg-white/5"
              >
                {availableTracks.map((track) => (
                  <option key={track} value={track} className="bg-card text-card-foreground">
                    {track}
                  </option>
                ))}
              </select>
            </div>

            <div className="space-y-2 min-w-[200px]">
              <label className="text-xs font-bold text-muted-foreground uppercase tracking-wider">Race</label>
              <select
                value={selectedRace}
                onChange={(e) => setSelectedRace(e.target.value)}
                className="glass-input w-full px-4 py-2.5 text-sm font-medium appearance-none cursor-pointer hover:bg-white/5"
              >
                <option value="R1" className="bg-card text-card-foreground">Race 1</option>
                <option value="R2" className="bg-card text-card-foreground">Race 2</option>
              </select>
            </div>

            <div className="space-y-2 min-w-[200px]">
              <label className="text-xs font-bold text-muted-foreground uppercase tracking-wider flex items-center gap-2"><CarIcon className="h-3 w-3" /> Vehicle</label>
              <select
                value={selectedVehicle}
                onChange={(e) => setSelectedVehicle(e.target.value)}
                className="glass-input w-full px-4 py-2.5 text-sm font-medium appearance-none cursor-pointer hover:bg-white/5"
                disabled={availableVehicles.length === 0}
              >
                {availableVehicles.map((vehicle) => (
                  <option key={vehicle} value={vehicle} className="bg-card text-card-foreground">
                    {vehicle}
                  </option>
                ))}
              </select>
            </div>

            <button
              className="glass-button px-6 py-2.5 font-bold bg-primary/20 hover:bg-primary/30 text-primary border-primary/30 ml-auto"
              onClick={handleAnalyze}
              disabled={!selectedTrack || !selectedRace || !selectedVehicle || loading}
            >
              {loading ? "Analyzing..." : "Analyze Performance"}
            </button>
          </div>
        </div>

        {!trainingData && (
          <div className="flex items-center justify-center h-64">
            <p className="text-muted-foreground text-lg">Select track, race, and vehicle to analyze performance</p>
          </div>
        )}


        {trainingData && (
          <>
            {/* Alert Banner */}
            <AlertBanner
              alerts={alerts}
              onDismiss={(timestamp) => {
                setAlerts(alerts.filter((a) => a.timestamp !== timestamp));
              }}
            />

            {/* Dashboard */}
            <div className="space-y-6">
          {/* Race Header */}
          <div className="flex flex-col md:flex-row justify-between items-end gap-4 mb-6">
            <div className="glass-card p-8 text-center space-y-4">
            <Bot className="h-12 w-12 text-primary mx-auto animate-pulse" />
            <h3 className="text-xl font-bold text-white">AI Training Assistant Ready</h3>
            <p className="text-muted-foreground">
              Select a track and vehicle to begin your personalized driver training session.
            </p>
          </div>
            <div className="space-y-1">
              <h2 className="text-3xl font-display font-bold text-white">
                Driver Training & Performance Insights
              </h2>
              <p className="text-muted-foreground">
                {selectedTrack
                  ? `${selectedTrack} - ${selectedRace}`
                  : "Select track and race to begin"}
              </p>
            </div>
            <div className="flex gap-8 bg-black/20 backdrop-blur-md px-6 py-3 rounded-xl border border-white/10">
              <div className="flex flex-col items-center">
                <span className="text-2xl font-bold text-primary">
                  {trainingData?.performance_summary?.best_lap_time?.toFixed(3) ||
                    "--"}
                  s
                </span>
                <span className="text-xs uppercase tracking-widest text-muted-foreground">Best Lap</span>
              </div>
              <div className="flex flex-col items-center">
                <span className="text-2xl font-bold text-primary">
                  {trainingData?.performance_summary?.avg_lap_time?.toFixed(3) ||
                    "--"}
                  s
                </span>
                <span className="text-xs uppercase tracking-widest text-muted-foreground">Average Lap</span>
              </div>
              <div className="flex flex-col items-center">
                <span className="text-2xl font-bold text-primary">
                  {trainingData?.performance_summary?.total_laps || "--"}
                </span>
                <span className="text-xs uppercase tracking-widest text-muted-foreground">Total Laps</span>
              </div>
            </div>
          </div>

          {/* Navigation Tabs */}
          <div className="flex flex-wrap gap-2 border-b border-white/10 mb-6">
            {[
              { id: "analysis", label: "Performance Analysis" },
              { id: "sectors", label: "Sector Analysis" },
              { id: "ai-insights", label: "AI Insights" },
              { id: "telemetry", label: "Telemetry Data" }
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
          {activeTab === "analysis" && (
            <section className="glass-card p-6 animate-in slide-in-from-bottom-4 duration-500">
              <div className="text-lg font-bold text-white mb-4 flex items-center gap-2">
                <span>Performance Overview</span>
              </div>
              {trainingData ? (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <section className="glass-card p-6 bg-white/5">
                    <div className="text-lg font-bold text-white mb-4">
                      <span>Performance Summary</span>
                    </div>
                    <div className="grid grid-cols-2 gap-4">
                      <div className="p-4 rounded-lg bg-white/5 border border-white/10 flex flex-col items-center hover:bg-white/10 transition-colors">
                        <span className="text-xs uppercase tracking-widest text-muted-foreground mb-1">Best Lap Time</span>
                        <span className="text-xl font-bold text-white">
                          {trainingData.performance_summary?.best_lap_time?.toFixed(
                            3
                          ) || "N/A"}
                          s
                        </span>
                      </div>
                      <div className="p-4 rounded-lg bg-white/5 border border-white/10 flex flex-col items-center hover:bg-white/10 transition-colors">
                        <span className="text-xs uppercase tracking-widest text-muted-foreground mb-1">Average Lap Time</span>
                        <span className="text-xl font-bold text-white">
                          {trainingData.performance_summary?.avg_lap_time?.toFixed(
                            3
                          ) || "N/A"}
                          s
                        </span>
                      </div>
                      <div className="p-4 rounded-lg bg-white/5 border border-white/10 flex flex-col items-center hover:bg-white/10 transition-colors">
                        <span className="text-xs uppercase tracking-widest text-muted-foreground mb-1">Consistency</span>
                        <span className="text-xl font-bold text-white">
                          {trainingData.performance_summary?.consistency?.toFixed(
                            3
                          ) || "N/A"}
                          s
                        </span>
                      </div>
                      <div className="p-4 rounded-lg bg-white/5 border border-white/10 flex flex-col items-center hover:bg-white/10 transition-colors">
                        <span className="text-xs uppercase tracking-widest text-muted-foreground mb-1">Total Laps</span>
                        <span className="text-xl font-bold text-white">
                          {trainingData.performance_summary?.total_laps || "N/A"}
                        </span>
                      </div>
                    </div>
                  </section>
                </div>
              ) : (
                <div className="flex items-center justify-center h-32 text-muted-foreground animate-pulse">
                  Select track, race, and vehicle to analyze performance
                </div>
              )}
            </section>
          )}

          {activeTab === "sectors" && (
            <section className="glass-card p-6 animate-in slide-in-from-bottom-4 duration-500">
              <div className="text-lg font-bold text-white mb-4 flex items-center gap-2">
                <span>Sector Performance Analysis</span>
              </div>
              {trainingData?.sector_analysis &&
              Object.keys(trainingData.sector_analysis).length > 0 ? (
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                  {Object.entries(trainingData.sector_analysis).map(
                    ([sector, data]: [string, any]) => (
                      <section key={sector} className="glass-card p-6 bg-white/5">
                        <div className="text-lg font-bold text-white mb-4 border-b border-white/10 pb-2">
                          <span>{sector.toUpperCase()}</span>
                        </div>
                        <div className="space-y-4">
                          <div className="flex justify-between items-center">
                            <span className="text-sm text-muted-foreground">Best Time</span>
                            <span className="font-mono font-bold text-primary">
                              {data.best?.toFixed(3) || "N/A"}s
                            </span>
                          </div>
                          <div className="flex justify-between items-center">
                            <span className="text-sm text-muted-foreground">Average Time</span>
                            <span className="font-mono font-bold text-white">
                              {data.avg?.toFixed(3) || "N/A"}s
                            </span>
                          </div>
                          <div className="flex justify-between items-center">
                            <span className="text-sm text-muted-foreground">Consistency</span>
                            <span className="font-mono font-bold text-white">
                              {data.consistency?.toFixed(3) || "N/A"}s
                            </span>
                          </div>
                        </div>
                      </section>
                    )
                  )}
                </div>
              ) : (
                <div className="flex items-center justify-center h-32 text-muted-foreground animate-pulse">
                  No sector data available. Run performance analysis first.
                </div>
              )}
            </section>
          )}

          {activeTab === "ai-insights" && (
            <section className="glass-card p-6 animate-in slide-in-from-bottom-4 duration-500">
              <div className="text-lg font-bold text-white mb-4 flex items-center gap-2">
                <span>
                  <FaRobot className="text-primary" /> AI-Powered Training Recommendations
                </span>
              </div>
              {trainingData ? (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <section className="glass-card p-6 bg-white/5">
                    <div className="text-lg font-bold text-white mb-4">
                      <span>AI Analysis</span>
                    </div>
                    <div className="text-sm leading-relaxed text-muted-foreground">
                      {aiInsights || "Generating AI insights..."}
                    </div>
                  </section>

                  {trainingData.ai_analysis?.areasForImprovement && (
                    <section className="glass-card p-6 bg-white/5">
                      <div className="text-lg font-bold text-white mb-4">
                        <span>Areas for Improvement</span>
                      </div>
                      <div className="space-y-2">
                        {trainingData.ai_analysis.areasForImprovement.map(
                          (area: string, idx: number) => (
                            <div key={idx} className="flex items-start gap-2 text-sm text-muted-foreground">
                              <span className="text-primary mt-1">•</span>
                              <span>{area}</span>
                            </div>
                          )
                        )}
                      </div>
                    </section>
                  )}
                </div>
              ) : (
                <div className="flex items-center justify-center h-32 text-muted-foreground animate-pulse">
                  Run performance analysis to get AI insights
                </div>
              )}
            </section>
          )}

          {activeTab === "telemetry" && (
            <section className="glass-card p-6 animate-in slide-in-from-bottom-4 duration-500">
              <div className="text-lg font-bold text-white mb-4 flex items-center gap-2">
                <span>Telemetry Insights</span>
              </div>
              {trainingData?.telemetry_insights ? (
                <div className="grid grid-cols-1 gap-6">
                  <section className="glass-card p-6 bg-white/5">
                    <div className="text-lg font-bold text-white mb-4">
                      <span>Speed Analysis</span>
                    </div>
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                      <div className="p-4 rounded-lg bg-white/5 border border-white/10 flex flex-col items-center hover:bg-white/10 transition-colors">
                        <span className="text-xs uppercase tracking-widest text-muted-foreground mb-1">Average Speed</span>
                        <span className="text-xl font-bold text-white">
                          {trainingData.telemetry_insights.avg_speed?.toFixed(
                            1
                          ) || "N/A"}{" "}
                          km/h
                        </span>
                      </div>
                      <div className="p-4 rounded-lg bg-white/5 border border-white/10 flex flex-col items-center hover:bg-white/10 transition-colors">
                        <span className="text-xs uppercase tracking-widest text-muted-foreground mb-1">Maximum Speed</span>
                        <span className="text-xl font-bold text-white">
                          {trainingData.telemetry_insights.max_speed?.toFixed(
                            1
                          ) || "N/A"}{" "}
                          km/h
                        </span>
                      </div>
                      <div className="p-4 rounded-lg bg-white/5 border border-white/10 flex flex-col items-center hover:bg-white/10 transition-colors">
                        <span className="text-xs uppercase tracking-widest text-muted-foreground mb-1">Average Throttle</span>
                        <span className="text-xl font-bold text-white">
                          {trainingData.telemetry_insights.avg_throttle?.toFixed(
                            1
                          ) || "N/A"}
                          %
                        </span>
                      </div>
                      <div className="p-4 rounded-lg bg-white/5 border border-white/10 flex flex-col items-center hover:bg-white/10 transition-colors">
                        <span className="text-xs uppercase tracking-widest text-muted-foreground mb-1">Average Brake</span>
                        <span className="text-xl font-bold text-white">
                          {trainingData.telemetry_insights.avg_brake?.toFixed(
                            1
                          ) || "N/A"}
                          %
                        </span>
                      </div>
                    </div>
                  </section>
                </div>
              ) : (
                <div className="flex items-center justify-center h-32 text-muted-foreground animate-pulse">
                  No telemetry data available. Run performance analysis first.
                </div>
              )}
            </section>
          )}
        </div>
          </>
        )}
      </div>
    
  );
}
