import { useState, useEffect } from "react";
import { api } from "../api/client";
import { generatePostEventInsights } from "../api/gemini";
import { Target, Bot, Car } from "lucide-react";



interface PostEventPageProps {
  track: string;
  race: string;
}

export default function PostEventPage({}: PostEventPageProps) {
  // Selection state
  const [selectedTrack, setSelectedTrack] = useState("");
  const [selectedRace, setSelectedRace] = useState("");
  const [selectedVehicles, setSelectedVehicles] = useState<string[]>([]);
  const [availableTracks, setAvailableTracks] = useState<string[]>([]);
  const [availableVehicles, setAvailableVehicles] = useState<string[]>([]);
  const [showVehicleDropdown, setShowVehicleDropdown] = useState(false);

  // Data state
  const [loading, setLoading] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [analysis, setAnalysis] = useState<any>(null);
  const [vehicleAnalysis, setVehicleAnalysis] = useState<Map<string, any>>(
    new Map()
  );
  const [aiInsights, setAiInsights] = useState<string>("");
  const [selectedFile, setSelectedFile] = useState<File | null>(null);

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
    } catch (error) {
      console.error("Error loading vehicles:", error);
    }
  };

  const toggleVehicleSelection = (vehicle: string) => {
    setSelectedVehicles((prev) => {
      if (prev.includes(vehicle)) {
        return prev.filter((v) => v !== vehicle);
      } else {
        return [...prev, vehicle];
      }
    });
  };

  const handleAnalyze = () => {
    if (selectedTrack && selectedRace) {
      loadAnalysis();
    }
  };

  const loadAnalysis = async () => {
    setLoading(true);
    try {
      const data = await api.getPostEventAnalysis(selectedTrack, selectedRace);
      setAnalysis(data);

      // Generate AI insights
      const insights = await generatePostEventInsights(
        selectedTrack,
        selectedRace,
        data
      );
      setAiInsights(insights);

      // If vehicles selected, load individual vehicle data
      if (selectedVehicles.length > 0) {
        const vehicleData = new Map();
        for (const vehicleId of selectedVehicles) {
          try {
            const vData = await api.getDriverTraining(
              selectedTrack,
              selectedRace,
              vehicleId
            );
            vehicleData.set(vehicleId, vData);
          } catch (error) {
            console.error(
              `Error loading data for vehicle ${vehicleId}:`,
              error
            );
          }
        }
        setVehicleAnalysis(vehicleData);
      }
    } catch (error) {
      console.error("Error loading analysis:", error);
    } finally {
      setLoading(false);
    }
  };

  const handleFileUpload = async () => {
    if (!selectedFile) return;

    setUploading(true);
    try {
      const result = await api.uploadPostEventData(
        selectedFile,
        selectedTrack,
        selectedRace
      );
      setAnalysis(result);

      // Generate AI insights for uploaded data
      const insights = await generatePostEventInsights(
        selectedTrack,
        selectedRace,
        result
      );
      setAiInsights(insights);

      setSelectedFile(null);
    } catch (error) {
      console.error("Error uploading data:", error);
    } finally {
      setUploading(false);
    }
  };

  if (loading) {
    return (
      
        <div className="min-h-screen w-full flex items-center justify-center">
          <div className="flex flex-col items-center gap-4">
            <div className="w-12 h-12 border-4 border-primary/30 border-t-primary rounded-full animate-spin"></div>
            <p className="text-muted-foreground animate-pulse">Analyzing race data...</p>
          </div>
        </div>
      
    );
  }

  return (
    
      <div className="min-h-screen w-full p-6 space-y-6 pb-20">
        <div className="text-center space-y-4 mb-8">
          <h1 className="text-4xl md:text-5xl font-display font-bold text-white flex items-center justify-center gap-4">
            <Car className="text-primary h-10 w-10" /> Post-Event Analysis
          </h1>
          <p className="text-xl text-muted-foreground max-w-2xl mx-auto">
            Comprehensive race story revealing key moments and decisions
          </p>
        </div>

        <div className="glass-card p-6 relative z-50">
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

            <div className="space-y-2 min-w-[250px]">
              <label className="text-xs font-bold text-muted-foreground uppercase tracking-wider">Vehicles (Optional)</label>
              <div className="relative">
                <button
                  className="glass-input w-full px-4 py-2.5 text-sm font-medium text-left flex justify-between items-center hover:bg-white/5"
                  onClick={() => setShowVehicleDropdown(!showVehicleDropdown)}
                  disabled={availableVehicles.length === 0}
                >
                  {selectedVehicles.length === 0
                    ? "Select vehicles to compare"
                    : `${selectedVehicles.length} vehicle(s) selected`}
                </button>
                {showVehicleDropdown && (
                  <div className="absolute top-full left-0 w-full mt-2 p-2 glass-card z-[100] max-h-60 overflow-y-auto bg-black/90 backdrop-blur-xl border border-white/10 shadow-xl">
                    {availableVehicles.map((vehicle) => (
                      <label key={vehicle} className="flex items-center gap-3 p-2 hover:bg-white/10 rounded cursor-pointer transition-colors">
                        <input
                          type="checkbox"
                          checked={selectedVehicles.includes(vehicle)}
                          onChange={() => toggleVehicleSelection(vehicle)}
                          className="rounded border-white/20 bg-white/5 text-primary focus:ring-primary/50"
                        />
                        <span className="text-sm text-white">{vehicle}</span>
                      </label>
                    ))}
                  </div>
                )}
              </div>
            </div>

            <button
              className="glass-button px-6 py-2.5 font-bold bg-primary/20 hover:bg-primary/30 text-primary border-primary/30 ml-auto"
              onClick={handleAnalyze}
              disabled={!selectedTrack || !selectedRace}
            >
              Analyze Race
            </button>
          </div>
        </div>

        {analysis && (
          <div className="space-y-6 animate-in slide-in-from-bottom-4 duration-500">
            {/* Upload Section */}
            <div className="glass-card p-6 border-dashed border-white/20">
              <h2 className="text-lg font-bold text-white mb-4">Upload Race Data</h2>
              <div className="flex flex-col items-center gap-4 p-8 border-2 border-dashed border-white/10 rounded-xl bg-white/5 hover:bg-white/10 transition-colors">
                <input
                  type="file"
                  accept=".csv,.xlsx"
                  onChange={(e) => setSelectedFile(e.target.files?.[0] || null)}
                  className="block w-full text-sm text-muted-foreground file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-primary/10 file:text-primary hover:file:bg-primary/20"
                />
                <button
                  onClick={handleFileUpload}
                  disabled={!selectedFile || uploading}
                  className="glass-button px-6 py-2 font-bold"
                >
                  {uploading ? "Uploading..." : "Upload & Analyze"}
                </button>
                {selectedFile && (
                  <p className="text-sm text-primary font-medium">{selectedFile.name}</p>
                )}
              </div>
            </div>

            {/* Race Summary */}
            {analysis && (
              <>
                <div className="glass-card p-6">
                  <div className="flex items-center gap-2 mb-2">
                <Target className="text-primary h-5 w-5" />
                <h3 className="font-bold text-white">Key Insights</h3>
              </div>
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    <div className="p-4 rounded-lg bg-white/5 border border-white/10 flex flex-col items-center hover:bg-white/10 transition-colors">
                      <span className="text-xs uppercase tracking-widest text-muted-foreground mb-1">Winner</span>
                      <span className="text-xl font-bold text-primary">{analysis.winner || "N/A"}</span>
                    </div>
                    <div className="p-4 rounded-lg bg-white/5 border border-white/10 flex flex-col items-center hover:bg-white/10 transition-colors">
                      <span className="text-xs uppercase tracking-widest text-muted-foreground mb-1">Total Laps</span>
                      <span className="text-xl font-bold text-white">{analysis.total_laps}</span>
                    </div>
                    <div className="p-4 rounded-lg bg-white/5 border border-white/10 flex flex-col items-center hover:bg-white/10 transition-colors">
                      <span className="text-xs uppercase tracking-widest text-muted-foreground mb-1">Fastest Lap</span>
                      <span className="text-xl font-bold text-white">
                        {analysis.fastest_lap?.toFixed(3)}s
                      </span>
                    </div>
                    <div className="p-4 rounded-lg bg-white/5 border border-white/10 flex flex-col items-center hover:bg-white/10 transition-colors">
                      <span className="text-xs uppercase tracking-widest text-muted-foreground mb-1">Avg Lap Time</span>
                      <span className="text-xl font-bold text-white">
                        {analysis.avg_lap_time?.toFixed(3)}s
                      </span>
                    </div>
                  </div>
                </div>

                {/* Key Moments */}
                {analysis.key_moments && (
                  <div className="glass-card p-6">
                    <h2 className="text-lg font-bold text-white mb-4 flex items-center gap-2">
                      <Target className="text-primary h-5 w-5" /> Key Race Moments
                    </h2>
                    <div className="space-y-4">
                      {analysis.key_moments.map((moment: any, idx: number) => (
                        <div key={idx} className="p-4 rounded-lg bg-white/5 border-l-4 border-primary flex flex-col gap-2 hover:bg-white/10 transition-colors">
                          <div className="text-xs font-bold text-primary uppercase tracking-wider">Lap {moment.lap}</div>
                          <div className="text-white font-medium">
                            {moment.description}
                          </div>
                          {moment.impact && (
                            <div className="text-sm text-muted-foreground italic">{moment.impact}</div>
                          )}
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* AI-Generated Race Story */}
                <div className="glass-card p-6">
                  <h2 className="text-lg font-bold text-white mb-4 flex items-center gap-2">
                    <Bot className="text-primary h-5 w-5" /> AI-Generated Race Story
                  </h2>
                  <div className="text-sm leading-relaxed text-muted-foreground whitespace-pre-line">
                    {aiInsights || "Generating race narrative..."}
                  </div>
                </div>

                {/* Strategic Decisions */}
                {analysis.ai_story?.strategicDecisions && (
                  <div className="glass-card p-6">
                    <h2 className="text-lg font-bold text-white mb-4">Strategic Decisions</h2>
                    <ul className="space-y-2">
                      {Array.isArray(analysis.ai_story.strategicDecisions) ? (
                        analysis.ai_story.strategicDecisions.map(
                          (decision: string, idx: number) => (
                            <li key={idx} className="flex items-start gap-2 text-sm text-muted-foreground">
                              <span className="text-primary mt-1">•</span>
                              <span>{decision}</span>
                            </li>
                          )
                        )
                      ) : (
                        <li className="flex items-start gap-2 text-sm text-muted-foreground">
                          <span className="text-primary mt-1">•</span>
                          <span>{analysis.ai_story.strategicDecisions}</span>
                        </li>
                      )}
                    </ul>
                  </div>
                )}

                {/* Vehicle Comparison */}
                {selectedVehicles.length > 0 && vehicleAnalysis.size > 0 && (
                  <div className="glass-card p-6">
                    <h2 className="text-lg font-bold text-white mb-4 flex items-center gap-2">
                      <Car className="text-primary h-5 w-5" /> Vehicle Comparison
                    </h2>
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                      {Array.from(vehicleAnalysis.entries()).map(
                        ([vehicleId, data]) => (
                          <div
                            key={vehicleId}
                            className="glass-card p-4 bg-white/5"
                          >
                            <h3 className="text-md font-bold text-white mb-3 border-b border-white/10 pb-2">{vehicleId}</h3>
                            <div className="grid grid-cols-2 gap-4">
                              <div className="flex flex-col">
                                <span className="text-xs text-muted-foreground">Best Lap</span>
                                <span className="font-mono font-bold text-primary">
                                  {data.performance_summary?.best_lap_time?.toFixed(3) || "N/A"}s
                                </span>
                              </div>
                              <div className="flex flex-col">
                                <span className="text-xs text-muted-foreground">Avg Lap</span>
                                <span className="font-mono font-bold text-white">
                                  {data.performance_summary?.avg_lap_time?.toFixed(3) || "N/A"}s
                                </span>
                              </div>
                              <div className="flex flex-col">
                                <span className="text-xs text-muted-foreground">Consistency</span>
                                <span className="font-mono font-bold text-white">
                                  {data.performance_summary?.consistency?.toFixed(3) || "N/A"}s
                                </span>
                              </div>
                              <div className="flex flex-col">
                                <span className="text-xs text-muted-foreground">Total Laps</span>
                                <span className="font-mono font-bold text-white">
                                  {data.performance_summary?.total_laps || "N/A"}
                                </span>
                              </div>
                            </div>
                          </div>
                        )
                      )}
                    </div>
                  </div>
                )}
              </>
            )}
          </div>
        )}
      </div>
    
  );
}
