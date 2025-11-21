import { useState, useEffect } from "react";
import TelemetryChart from "../components/TelemetryChart";
import LapTimeline from "../components/LapTimeline";
import PitStrategy from "../components/PitStrategy";
import { PitStopCalculator } from "../components/PitStopCalculator";
import AlertBanner from "../components/AlertBanner";
import TrackMap from "../components/TrackMap";
import PositionTracker from "../components/PositionTracker";
import VehiclePositionProvider from "../components/VehiclePositionProvider";
import SectorComparison from "../components/SectorComparison";
import DriverConsistency from "../components/DriverConsistency";
import { type AlertEvent } from "../api/websocket";
import { api } from "../api/client";
import { BarChart3, Flag, Car } from "lucide-react";


interface LiveTelemetryPageProps {
  track: string;
  race: string;
  vehicleId: string;
  onTrackChange: (track: string) => void;
  onRaceChange: (race: string) => void;
  onVehicleChange: (vehicleId: string) => void;
}

export default function LiveTelemetryPage({
  track,
  race,
  vehicleId,
  onTrackChange,
  onRaceChange,
  onVehicleChange,
}: LiveTelemetryPageProps) {
  const [selectedLap, setSelectedLap] = useState<number>(5);
  const [alerts, setAlerts] = useState<AlertEvent[]>([]);
  const [availableTracks, setAvailableTracks] = useState<string[]>([]);
  const [availableVehicles, setAvailableVehicles] = useState<string[]>([]);
  const [availableLaps, setAvailableLaps] = useState<number[]>([]);
  const [comparisonVehicles, setComparisonVehicles] = useState<string[]>([]);
  const [activeTab, setActiveTab] = useState<string>("results");
  const [raceResults, setRaceResults] = useState<any>(null);
  const [weatherData, setWeatherData] = useState<any>(null);

  // Load available tracks on mount
  useEffect(() => {
    const loadTracks = async () => {
      try {
        const tracks = await api.getTracks();
        setAvailableTracks(tracks);
      } catch (error) {
        console.error("Failed to load tracks:", error);
      }
    };
    loadTracks();
  }, []);

  // Load available vehicles when track/race changes
  useEffect(() => {
    const loadVehicles = async () => {
      try {
        const vehicles = await api.getVehicles(track, race);
        setAvailableVehicles(vehicles);
        if (vehicles.length > 0 && !vehicles.includes(vehicleId)) {
          onVehicleChange(vehicles[0]);
        }
      } catch (error) {
        console.error("Failed to load vehicles:", error);
      }
    };
    if (track && race) {
      loadVehicles();
    }
  }, [track, race]);

  // Load available laps
  useEffect(() => {
    const loadLaps = async () => {
      try {
        const lapResponse = await api.getLapTimes(track, race, vehicleId);
        if (lapResponse.length > 0) {
          const uniqueLaps = [
            ...new Set(lapResponse.map((lap) => lap.lap)),
          ].sort((a, b) => a - b);
          setAvailableLaps(uniqueLaps);

          // Set default lap to middle of available range
          if (uniqueLaps.length > 0 && !uniqueLaps.includes(selectedLap)) {
            setSelectedLap(uniqueLaps[Math.floor(uniqueLaps.length / 2)]);
          }
        }
      } catch (error) {
        console.error("Error loading laps:", error);
      }
    };

    if (track && race && vehicleId) {
      loadLaps();
    }
  }, [track, race, vehicleId]);

  // Load race results, weather, and vehicles data
  useEffect(() => {
    const loadRaceData = async () => {
      if (track && race) {
        try {
          const [results, weather] = await Promise.all([
            api.getRaceResults(track, race),
            api.getWeatherData(track, race),
          ]);

          setRaceResults(results);
          setWeatherData(weather);
        } catch (error) {
          console.error("Error loading race data:", error);
        }
      }
    };

    loadRaceData();
  }, [track, race]);



  return (
    
      <div className="min-h-screen w-full p-4 md:p-6 space-y-6 pb-20">
        {/* Header */}
        <AlertBanner
          alerts={alerts}
          onDismiss={(timestamp) => {
            setAlerts(alerts.filter((a) => a.timestamp !== timestamp));
          }}
        />

        {/* Control Panel */}
        <div className="glass-card p-4 md:p-6">
          <div className="flex flex-wrap gap-4 items-end">
            <div className="space-y-2 min-w-[200px]">
              <label htmlFor="track-select" className="text-xs font-bold text-muted-foreground uppercase tracking-wider flex items-center gap-2">
                <Car className="text-primary" /> Track
              </label>
              <select
                id="track-select"
                value={track}
                onChange={(e) => onTrackChange(e.target.value)}
                className="glass-input w-full px-4 py-2.5 text-sm font-medium appearance-none cursor-pointer hover:bg-white/5"
              >
                {availableTracks.map((t) => (
                  <option key={t} value={t} className="bg-card text-card-foreground">
                    {t}
                  </option>
                ))}
              </select>
            </div>

            <div className="space-y-2 min-w-[200px]">
              <label htmlFor="race-select" className="text-xs font-bold text-muted-foreground uppercase tracking-wider flex items-center gap-2">
                <Flag className="text-primary" /> Race
              </label>
              <select
                id="race-select"
                value={race}
                onChange={(e) => onRaceChange(e.target.value)}
                className="glass-input w-full px-4 py-2.5 text-sm font-medium appearance-none cursor-pointer hover:bg-white/5"
              >
                <option value="R1" className="bg-card text-card-foreground">Race 1</option>
                <option value="R2" className="bg-card text-card-foreground">Race 2</option>
              </select>
            </div>

            
          </div>
        </div>

        {/* Dashboard */}
        <div className="space-y-6">
          {/* Race Header */}
          <div className="flex flex-col md:flex-row justify-between items-end gap-4 mb-6">
            <div>
              <h2 className="text-3xl font-display font-bold text-white">{track} Grand Prix</h2>
            </div>
            <div className="flex gap-8 bg-black/20 backdrop-blur-md px-6 py-3 rounded-xl border border-white/10">
              <div className="flex flex-col items-center">
                <span className="text-2xl font-bold text-primary">
                  {raceResults?.total_entries || "0"}
                </span>
                <span className="text-xs uppercase tracking-widest text-muted-foreground">Entries</span>
              </div>
              <div className="flex flex-col items-center">
                <span className="text-2xl font-bold text-primary">
                  {raceResults?.race_distance || "0"}
                </span>
                <span className="text-xs uppercase tracking-widest text-muted-foreground">Laps</span>
              </div>
              <div className="flex flex-col items-center">
                <span className="text-2xl font-bold text-primary">
                  {weatherData?.air_temperature?.toFixed(0) || "--"}°C
                </span>
                <span className="text-xs uppercase tracking-widest text-muted-foreground">Air Temp</span>
              </div>
            </div>
          </div>

          {/* Winner Info */}
          {raceResults?.winner && (
            <div className="glass-card p-4 md:p-6 flex items-center gap-4 bg-primary/10 border-primary/20">
              <div className="text-4xl">🏆</div>
              <div>
                <h3 className="text-xl font-bold text-white">Race Winner: {raceResults.winner.driver}</h3>
                <p className="text-muted-foreground">
                  Vehicle #{raceResults.winner.number} •{" "}
                  {raceResults.winner.vehicle} • Time:{" "}
                  {raceResults.winner.total_time}
                </p>
              </div>
            </div>
          )}

          {/* Navigation Tabs */}
          <div className="flex flex-wrap gap-2 border-b border-white/10 mb-6">
            {["results", "positions", "lap-times", "strategy", "telemetry", "track-map"].map((tab) => (
              <button
                key={tab}
                className={`px-4 py-2 text-sm font-medium transition-all border-b-2 ${
                  activeTab === tab
                    ? "text-primary border-primary"
                    : "text-muted-foreground border-transparent hover:text-white hover:border-white/20"
                }`}
                onClick={() => setActiveTab(tab)}
              >
                {tab.replace("-", " ").replace(/\b\w/g, l => l.toUpperCase())}
              </button>
            ))}
          </div>

          {/* Tab Content */}
          {activeTab === "results" && (
            <section className="glass-card p-4 md:p-6 animate-in slide-in-from-bottom-4 duration-500">
              <div className="text-lg font-bold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
                <span>Session Results: Race</span>
              </div>
              {raceResults ? (
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr>
                        <th className="text-left py-3 px-4 text-xs font-bold text-muted-foreground uppercase tracking-wider border-b border-white/10">Pos</th>
                        <th className="text-left py-3 px-4 text-xs font-bold text-muted-foreground uppercase tracking-wider border-b border-white/10">Driver</th>
                        <th className="text-left py-3 px-4 text-xs font-bold text-muted-foreground uppercase tracking-wider border-b border-white/10">Vehicle</th>
                        <th className="text-left py-3 px-4 text-xs font-bold text-muted-foreground uppercase tracking-wider border-b border-white/10">Laps</th>
                        <th className="text-left py-3 px-4 text-xs font-bold text-muted-foreground uppercase tracking-wider border-b border-white/10">Total Time</th>
                        <th className="text-left py-3 px-4 text-xs font-bold text-muted-foreground uppercase tracking-wider border-b border-white/10">Gap</th>
                        <th className="text-left py-3 px-4 text-xs font-bold text-muted-foreground uppercase tracking-wider border-b border-white/10">Status</th>
                      </tr>
                    </thead>
                    <tbody>
                      {raceResults.results.map((result: any, index: number) => (
                        <tr key={index} className="hover:bg-white/5 transition-colors">
                          <td className="py-3 px-4 border-b border-white/5 font-mono font-bold text-primary">{result.position}</td>
                          <td className="py-3 px-4 border-b border-white/5 font-medium text-white">{result.driver}</td>
                          <td className="py-3 px-4 border-b border-white/5 text-muted-foreground">{result.vehicle}</td>
                          <td className="py-3 px-4 border-b border-white/5 text-muted-foreground">{result.laps}</td>
                          <td className="py-3 px-4 border-b border-white/5 font-mono text-white">{result.total_time}</td>
                          <td className="py-3 px-4 border-b border-white/5 font-mono text-muted-foreground">{result.gap_first}</td>
                          <td className="py-3 px-4 border-b border-white/5 text-muted-foreground">{result.status}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              ) : (
                <div className="flex items-center justify-center h-32 text-muted-foreground animate-pulse">Loading race results...</div>
              )}
            </section>
          )}

          {activeTab === "positions" && (
            <section className="glass-card p-4 md:p-6 animate-in slide-in-from-bottom-4 duration-500">
              <div className="text-lg font-bold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
                <span>Position Tracking - All Cars by Lap</span>
              </div>
              <div className="w-full overflow-x-auto">
                <PositionTracker
                  track={track}
                  race={race}
                  highlightVehicle={vehicleId}
                />
              </div>
            </section>
          )}

          {activeTab === "lap-times" && (
            <section className="glass-card p-4 md:p-6 animate-in slide-in-from-bottom-4 duration-500">
              <div className="text-lg font-bold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
                <span>Lap Time Comparison</span>
              </div>
              <div className="flex items-center gap-2 mb-4">
                <BarChart3 className="text-primary h-5 w-5" />
                <h3 className="font-bold text-white">Live Telemetry Overview</h3>
              </div>
              <div className="flex flex-wrap gap-4 mb-6">
                {/* Primary driver dropdown */}
                <div className="min-w-[200px]">
                  <select
                    className="glass-input w-full px-4 py-2 text-sm"
                    value={vehicleId}
                    onChange={(e) => onVehicleChange(e.target.value)}
                  >
                    {availableVehicles.map((vehicle) => (
                      <option key={vehicle} value={vehicle} className="bg-card text-card-foreground">
                        {vehicle}
                      </option>
                    ))}
                  </select>
                </div>

                {/* Comparison driver dropdowns */}
                {comparisonVehicles.map((vehicle, index) => (
                  <div key={vehicle} className="flex items-center gap-2 min-w-[200px]">
                    <select
                      className="glass-input flex-1 px-4 py-2 text-sm border-primary/30"
                      value={vehicle}
                      onChange={(e) => {
                        const newVehicles = [...comparisonVehicles];
                        newVehicles[index] = e.target.value;
                        setComparisonVehicles(newVehicles);
                      }}
                    >
                      {availableVehicles
                        .filter(
                          (v) =>
                            (v !== vehicleId &&
                              !comparisonVehicles.includes(v)) ||
                            v === vehicle
                        )
                        .map((v) => (
                          <option key={v} value={v} className="bg-card text-card-foreground">
                            {v}
                          </option>
                        ))}
                    </select>
                    <button
                      className="w-8 h-8 rounded-full bg-destructive/10 text-destructive hover:bg-destructive/20 flex items-center justify-center transition-colors"
                      onClick={() =>
                        setComparisonVehicles(
                          comparisonVehicles.filter((_, i) => i !== index)
                        )
                      }
                    >
                      ×
                    </button>
                  </div>
                ))}

                {/* Add driver button */}
                {comparisonVehicles.length < 3 && (
                  <button
                    type="button"
                    className="glass-button px-4 py-2 text-sm font-medium bg-primary/10 text-primary hover:bg-primary/20 border-primary/30"
                    onClick={(e) => {
                      e.preventDefault();
                      const availableToAdd = availableVehicles.filter(
                        (v) => v !== vehicleId && !comparisonVehicles.includes(v)
                      );
                      if (availableToAdd.length > 0) {
                        setComparisonVehicles([...comparisonVehicles, availableToAdd[0]]);
                      }
                    }}
                  >
                    + Add Driver
                  </button>
                )}
              </div>
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <LapTimeline
                  track={track}
                  race={race}
                  vehicleId={vehicleId}
                  comparisonVehicles={comparisonVehicles}
                />
                <SectorComparison
                  track={track}
                  race={race}
                  vehicleId={vehicleId}
                  comparisonLap={selectedLap}
                />
              </div>
            </section>
          )}

          {activeTab === "strategy" && (
            <div className="space-y-6">
              {/* Pit Stop Calculator */}
              <PitStopCalculator 
                currentLap={selectedLap}
                totalLaps={raceResults?.race_distance || 45}
                currentLapTime={92.5}
                fuelLevel={65}
                tireAge={selectedLap}
              />
              
              {/* Existing Pit Strategy */}
              <div className="glass-card p-4 md:p-6">
                <div className="mb-4">
                  <label className="text-xs font-bold text-muted-foreground uppercase tracking-wider block mb-2">🚗 Vehicle</label>
                  <select
                    value={vehicleId}
                    onChange={(e) => onVehicleChange(e.target.value)}
                    className="glass-input w-full md:w-1/3 px-4 py-2 text-sm"
                  >
                    {availableVehicles.map((v) => (
                      <option key={v} value={v} className="bg-card text-card-foreground">
                        {v}
                      </option>
                    ))}
                  </select>
                </div>
                <PitStrategy track={track} race={race} vehicleId={vehicleId} />
              </div>
              <div className="glass-card p-4 md:p-6">
                 <DriverConsistency
                  track={track}
                  race={race}
                  vehicleId={vehicleId}
                />
              </div>
            </div>
          )}

          {activeTab === "telemetry" && (
            <div className="space-y-6">
              <div className="glass-card p-4 md:p-6">
                <div className="flex flex-wrap gap-4 items-end mb-6">
                  <div className="space-y-2 min-w-[200px]">
                    <label className="text-xs font-bold text-muted-foreground uppercase tracking-wider block">🚗 Vehicle</label>
                    <select
                      value={vehicleId}
                      onChange={(e) => onVehicleChange(e.target.value)}
                      className="glass-input w-full px-4 py-2 text-sm"
                    >
                      {availableVehicles.map((v) => (
                        <option key={v} value={v} className="bg-card text-card-foreground">
                          {v}
                        </option>
                      ))}
                    </select>
                  </div>
                  <div className="space-y-2 flex-1">
                    <label className="text-xs font-bold text-muted-foreground uppercase tracking-wider flex items-center gap-2">
                      <BarChart3 className="h-4 w-4" /> Lap: {selectedLap}
                    </label>
                    {availableLaps.length > 0 ? (
                      <input
                        type="range"
                        min={Math.min(...availableLaps)}
                        max={Math.max(...availableLaps)}
                        value={selectedLap}
                        onChange={(e) => setSelectedLap(parseInt(e.target.value))}
                        className="w-full h-2 bg-white/10 rounded-lg appearance-none cursor-pointer accent-primary"
                      />
                    ) : (
                      <div className="text-sm text-muted-foreground">Loading laps...</div>
                    )}
                  </div>
                </div>
                <TelemetryChart
                  track={track}
                  race={race}
                  vehicleId={vehicleId}
                  lapNumber={selectedLap}
                  comparisonVehicles={comparisonVehicles}
                />
              </div>
              
              <section className="glass-card p-4 md:p-6">
                <div className="text-lg font-bold text-gray-900 dark:text-white mb-4">Track Position - All Cars</div>
                <VehiclePositionProvider
                  track={track}
                  race={race}
                  selectedLap={selectedLap}
                  highlightedVehicle={vehicleId}
                >
                  {(vehiclePositions) => (
                    <TrackMap
                      track={track}
                      selectedSector={1}
                      vehiclePositions={vehiclePositions}
                      highlightedVehicle={vehicleId}
                      telemetryData={[{ distance: 1200, speed: 285, sector: 1 }]}
                    />
                  )}
                </VehiclePositionProvider>
              </section>
            </div>
          )}

          {activeTab === "track-map" && (
            <div className="space-y-6">
              <div className="glass-card p-4 md:p-6">
                <div className="flex flex-wrap gap-4 items-end mb-6">
                  <div className="space-y-2 min-w-[200px]">
                    <label className="text-xs font-bold text-muted-foreground uppercase tracking-wider block">🚗 Vehicle</label>
                    <select
                      value={vehicleId}
                      onChange={(e) => onVehicleChange(e.target.value)}
                      className="glass-input w-full px-4 py-2 text-sm"
                    >
                      {availableVehicles.map((v) => (
                        <option key={v} value={v} className="bg-card text-card-foreground">
                          {v}
                        </option>
                      ))}
                    </select>
                  </div>
                  <div className="space-y-2 flex-1">
                    <label className="text-xs font-bold text-muted-foreground uppercase tracking-wider flex items-center gap-2">
                      <BarChart3 className="h-4 w-4" /> Lap: {selectedLap}
                    </label>
                    {availableLaps.length > 0 ? (
                      <input
                        type="range"
                        min={Math.min(...availableLaps)}
                        max={Math.max(...availableLaps)}
                        value={selectedLap}
                        onChange={(e) => setSelectedLap(parseInt(e.target.value))}
                        className="w-full h-2 bg-white/10 rounded-lg appearance-none cursor-pointer accent-primary"
                      />
                    ) : (
                      <div className="text-sm text-muted-foreground">Loading laps...</div>
                    )}
                  </div>
                </div>
                <div className="text-lg font-bold text-gray-900 dark:text-white mb-4">Interactive Track Map - {track}</div>
                <VehiclePositionProvider
                  track={track}
                  race={race}
                  selectedLap={selectedLap}
                  highlightedVehicle={vehicleId}
                >
                  {(vehiclePositions) => (
                    <TrackMap
                      track={track}
                      selectedSector={1}
                      onSectorSelect={(sector) => console.log(`Selected sector: ${sector}`)}
                      vehiclePositions={vehiclePositions}
                      highlightedVehicle={vehicleId}
                      telemetryData={[
                        { distance: 1200, speed: 285, sector: 1 },
                        { distance: 2400, speed: 220, sector: 2 },
                        { distance: 3600, speed: 195, sector: 3 },
                      ]}
                    />
                  )}
                </VehiclePositionProvider>
              </div>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <section className="glass-card p-4 md:p-6">
                  <div className="text-lg font-bold text-gray-900 dark:text-white mb-4">Track Information</div>
                  <div className="space-y-3 text-sm text-muted-foreground">
                    <p><strong className="text-white">Circuit Length:</strong> 4.2 km</p>
                    <p><strong className="text-white">Number of Turns:</strong> 15</p>
                    <p><strong className="text-white">Direction:</strong> Clockwise</p>
                    <p><strong className="text-white">Elevation Change:</strong> 42 meters</p>
                    <p><strong className="text-white">Track Surface:</strong> Asphalt</p>
                    <p><strong className="text-white">DRS Zones:</strong> 2 zones available</p>
                  </div>
                </section>
              </div>
            </div>
          )}
        </div>
      </div>
    
  );
}
