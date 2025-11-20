import axios from "axios";

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 120000, // Increase timeout to 2 minutes for ML endpoints
  headers: {
    "Content-Type": "application/json",
  },
});

// API Response Types
export interface LapTimeData {
  vehicle_id: string;
  lap: number; // backend uses 'lap' not 'lap_number'
  timestamp: string;
  vehicle_number: number;
  outing: number;
  meta_session: string;
  meta_event: string;
  // Optional fields for extended data
  lap_time?: number;
  sector1?: number;
  sector2?: number;
  sector3?: number;
  tire_age?: number;
}

export interface TelemetryData {
  timestamp: number;
  speed: number;
  throttle: number;
  brake: number;
  steering: number;
  gear: number;
  rpm: number;
  accx_can?: number;
  accy_can?: number;
  lap_distance?: number;
}

export interface PitStrategyRecommendation {
  optimal_lap: number;
  strategy: string;
  expected_time_loss: number;
  tire_wear_at_stop: number;
  rationale: string;
  trackEvolution?: {
    currentEvolution: number;
    rubberBuildupEffect: number;
    optimalLineGain: number;
    predictedFinalEvolution: number;
    evolutionRate: number;
    baselineTime: number;
    evolvedTime: number;
  };
  positionPredictions?: Array<{
    name: string;
    pitLap: number;
    compound: string;
    expectedPosition: number;
    timeGain: number;
    riskFactor: string;
  }>;
  competitorComparison?: Array<{
    position: number;
    vehicle: string;
    currentPace: number;
    strategy: string;
    threat: string;
    gapToPlayer: string;
  }>;
}

export interface DegradationAnalysis {
  degradation_rate: number;
  r_squared: number;
  prediction_30_laps: number;
  cliff_detected: boolean;
  cliff_lap?: number;
  average_tire_age: number;
  total_laps: number;
}

export interface ConsistencyScore {
  consistency_score: number;
  rating: string;
  total_laps: number;
  lap_time_cv?: number;
  strengths?: string[];
}

export interface LapPrediction {
  vehicle_id: string;
  predicted_lap_time: number;
  actual_lap_time?: number;
  error?: number;
}

export interface RaceSimulationRequest {
  vehicle_id: string;
  track: string;
  race: string;
  total_laps: number;
  strategies: string[];
}

export interface RaceSimulationResult {
  strategy: string;
  total_time: number;
  pit_laps: number[];
  tire_compounds: string[];
  final_position?: number;
}

export interface RaceResult {
  position: number;
  number: string;
  driver: string;
  team: string;
  vehicle: string;
  status: string;
  laps: number;
  total_time: string;
  gap_first: string;
  gap_previous: string;
  fastest_lap_time: string;
  fastest_lap_number: number;
  fastest_lap_speed: number;
  class: string;
  points: number;
}

export interface RaceResults {
  track: string;
  race: string;
  results: RaceResult[];
  winner: RaceResult;
  total_entries: number;
  race_distance: number;
}

export interface WeatherData {
  track: string;
  race: string;
  air_temperature: number | null;
  track_temperature: number | null;
  humidity: number | null;
  wind_speed: number | null;
  wind_direction: number | null;
  barometric_pressure: number | null;
  rain: number | null;
}

export interface RaceVehicle {
  vehicle_id: string;
  total_laps: number;
  first_lap: number;
  last_lap: number;
}

// API Methods
export const api = {
  // Race Results
  getRaceResults: async (
    track: string,
    race: string
  ): Promise<RaceResults | null> => {
    try {
      const response = await apiClient.get(
        `/results/${encodeURIComponent(track)}/${race}`
      );
      return response.data as RaceResults;
    } catch (error) {
      console.error("Error fetching race results:", error);
      return null;
    }
  },

  // Weather Data
  getWeatherData: async (
    track: string,
    race: string
  ): Promise<WeatherData | null> => {
    try {
      const response = await apiClient.get(
        `/results/weather/${encodeURIComponent(track)}/${race}`
      );
      return response.data as WeatherData;
    } catch (error) {
      console.error("Error fetching weather data:", error);
      return null;
    }
  },

  // Race Vehicles
  getRaceVehicles: async (
    track: string,
    race: string
  ): Promise<RaceVehicle[]> => {
    const response = await apiClient.get(`/results/${track}/${race}/vehicles`);
    return response.data.vehicles;
  },

  // Lap Times
  getLapTimes: async (
    track: string,
    race: string,
    vehicleId: string
  ): Promise<LapTimeData[]> => {
    const response = await apiClient.get(`/laps/times`, {
      params: { track, race, vehicle_id: vehicleId },
    });
    return response.data.lap_times || [];
  },

  // Telemetry
  getTelemetry: async (
    track: string,
    race: string,
    vehicleId: string,
    lapNumber?: number
  ): Promise<TelemetryData[]> => {
    const params: any = { track, race, vehicle_id: vehicleId };
    if (lapNumber !== undefined) {
      params.lap_number = lapNumber;
    }
    const response = await apiClient.get(`/telemetry`, { params });

    // Backend now returns rows as objects directly
    const data = response.data;
    if (data.rows && Array.isArray(data.rows)) {
      return data.rows as TelemetryData[];
    }
    return [];
  },

  // Pit Strategy
  getPitStrategy: async (
    track: string,
    race: string,
    vehicleId: string,
    currentLap: number = 1,
    totalRaceLaps: number = 40,
    currentTireAge: number = 0,
    trackPosition: number = 1
  ): Promise<PitStrategyRecommendation> => {
    const response = await apiClient.get(
      `/strategy/pit/${track}/${race}/${vehicleId}`,
      {
        params: {
          current_lap: currentLap,
          total_race_laps: totalRaceLaps,
          current_tire_age: currentTireAge,
          track_position: trackPosition,
        },
      }
    );
    return response.data;
  },

  // Degradation Analysis (Note: backend doesn't require vehicle_id in path)
  getDegradation: async (
    track: string,
    race: string,
    _vehicleId?: string
  ): Promise<DegradationAnalysis> => {
    // Backend endpoint is /analytics/degradation/{track}/{race} without vehicle_id
    const response = await apiClient.get(
      `/analytics/degradation/${track}/${race}`
    );
    return response.data;
  },

  // Consistency
  getConsistency: async (
    track: string,
    race: string,
    vehicleId: string
  ): Promise<ConsistencyScore> => {
    const response = await apiClient.get(
      `/consistency/${track}/${race}/${vehicleId}`
    );
    return response.data;
  },

  // Lap Prediction
  predictLapTime: async (
    track: string,
    race: string,
    vehicleId: string,
    lapNumber: number
  ): Promise<LapPrediction> => {
    const response = await apiClient.get(
      `/predictions/laptime/${track}/${race}/${vehicleId}?lap_number=${lapNumber}`
    );
    return response.data;
  },

  predictNextLap: async (
    track: string,
    race: string,
    vehicleId: string
  ): Promise<LapPrediction> => {
    const response = await apiClient.get(
      `/predictions/laptime/next/${track}/${race}/${vehicleId}`
    );
    return response.data;
  },

  // Race Simulation
  simulateRace: async (
    request: RaceSimulationRequest
  ): Promise<RaceSimulationResult[]> => {
    const response = await apiClient.post("/simulation/race", request);
    return response.data.results;
  },

  // Tracks
  getTracks: async (): Promise<string[]> => {
    const response = await apiClient.get("/tracks");
    return response.data.tracks.map((track: any) => track.name);
  },

  // Vehicles
  getVehicles: async (track: string, race: string): Promise<string[]> => {
    const response = await apiClient.get(`/laps`, {
      params: { track, race },
    });
    // Extract unique vehicle IDs from the laps_by_vehicle object
    const lapsData = response.data.laps_by_vehicle || {};
    return Object.keys(lapsData);
  },

  // Laps
  getAvailableLaps: async (
    track: string,
    race: string,
    vehicleId: string
  ): Promise<number[]> => {
    const response = await apiClient.get(`/laps`, {
      params: { track, race, vehicle_id: vehicleId },
    });
    const lapsData = response.data.laps_by_vehicle || {};
    const vehicleData = lapsData[vehicleId];
    return vehicleData?.lap_numbers || [];
  },

  // Insights
  getDriverTraining: async (
    track: string,
    race: string,
    vehicleId: string
  ): Promise<any> => {
    const response = await apiClient.get(
      `/insights/driver-training/${track}/${race}/${vehicleId}`
    );
    return response.data;
  },

  getPreEventPrediction: async (
    track: string,
    weather?: string,
    trackTemp?: number
  ): Promise<any> => {
    const params: any = {};
    if (weather) params.weather = weather;
    if (trackTemp) params.track_temp = trackTemp;
    const response = await apiClient.get(
      `/insights/pre-event-prediction/${track}`,
      { params }
    );
    return response.data;
  },

  // Real-time Weather
  getWeather: async (track: string): Promise<{
    track: string;
    temperature: number;
    weather: string;
    humidity?: number;
    wind_speed?: number;
    timestamp: string;
  }> => {
    const response = await apiClient.get(`/weather/${encodeURIComponent(track)}`);
    return response.data;
  },

  uploadPostEventData: async (
    file: File,
    track?: string,
    race?: string
  ): Promise<any> => {
    const formData = new FormData();
    formData.append("file", file);
    const params: any = {};
    if (track) params.track = track;
    if (race) params.race = race;
    const response = await apiClient.post(
      `/insights/post-event-analysis`,
      formData,
      { params, headers: { "Content-Type": "multipart/form-data" } }
    );
    const data = response.data;
    // Transform to match expected format
    return {
      winner: data.key_moments?.find((m: any) => m.type === "fastest_lap")
        ?.vehicle,
      total_laps: data.data_analysis?.rows_analyzed || 0,
      fastest_lap: data.key_moments?.find((m: any) => m.type === "fastest_lap")
        ?.time,
      avg_lap_time: data.data_analysis?.rows_analyzed
        ? data.key_moments[0]?.time
        : 0,
      key_moments:
        data.key_moments?.map((m: any) => ({
          lap: m.lap,
          description: m.description,
          impact: m.type,
        })) || [],
      strategic_decisions: data.ai_story?.strategicDecisions || [],
    };
  },

  getPostEventAnalysis: async (track: string, race: string): Promise<any> => {
    const response = await apiClient.get(
      `/insights/post-event-analysis/${track}/${race}`
    );
    const data = response.data;
    // Transform to match expected format
    return {
      winner: data.key_moments?.find((m: any) => m.type === "fastest_lap")
        ?.vehicle,
      total_laps: data.race_summary?.total_laps || 0,
      fastest_lap: data.race_summary?.fastest_lap_time,
      avg_lap_time: data.race_summary?.fastest_lap_time,
      key_moments:
        data.key_moments?.map((m: any) => ({
          lap: m.lap,
          description: m.description,
          impact: m.type,
        })) || [],
      strategic_decisions: data.ai_story?.strategicDecisions || [],
    };
  },
};

export default apiClient;
