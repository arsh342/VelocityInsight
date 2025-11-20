import { useEffect, useState } from "react";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";
import { api } from "../api/client";

interface TelemetryChartProps {
  track: string;
  race: string;
  vehicleId: string;
  lapNumber?: number;
  comparisonVehicles?: string[]; // Array of vehicle IDs to overlay
}

interface ChartData {
  index: number;
  speed: number;
  throttle: number;
  brake: number;
  gear: number;
  steering: number;
  vehicleId?: string;
  // Comparison vehicle data
  speed_comp?: number[];
  throttle_comp?: number[];
  brake_comp?: number[];
  gear_comp?: number[];
  steering_comp?: number[];
  vehicleIds?: string[];
}

export default function TelemetryChart({
  track,
  race,
  vehicleId,
  lapNumber,
  comparisonVehicles = [],
}: TelemetryChartProps) {
  const [data, setData] = useState<ChartData[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Define colors for different vehicles
  const vehicleColors = [
    "#8884d8",
    "#82ca9d",
    "#ff4444",
    "#ffc658",
    "#ff8c00",
    "#8dd1e1",
    "#d084d0",
    "#87d068",
    "#ffb347",
    "#ff6b6b",
  ];

  useEffect(() => {
    const fetchTelemetry = async () => {
      try {
        setLoading(true);

        // Fetch data for primary vehicle
        const primaryData = await api.getTelemetry(
          track,
          race,
          vehicleId,
          lapNumber
        );
        console.log(
          "Primary telemetry data received:",
          primaryData.length,
          "rows"
        );

        // Fetch data for comparison vehicles
        const comparisonData: any[] = [];
        for (const compVehicleId of comparisonVehicles) {
          try {
            const compData = await api.getTelemetry(
              track,
              race,
              compVehicleId,
              lapNumber
            );
            comparisonData.push({ vehicleId: compVehicleId, data: compData });
            console.log(
              `Comparison data for ${compVehicleId}:`,
              compData.length,
              "rows"
            );
          } catch (err) {
            console.warn(
              `Failed to fetch data for vehicle ${compVehicleId}:`,
              err
            );
          }
        }

        // Process primary vehicle data
        const primaryFiltered = primaryData.filter(
          (point: any) => point.speed != null
        );

        // Create base chart data from primary vehicle
        const chartData = primaryFiltered.map((point: any, index: number) => {
          const baseData: ChartData = {
            index: index,
            speed: point.speed || 0,
            throttle: point.aps || 0,
            brake: point.pbrake_f || 0,
            gear: point.gear || 0,
            steering: point.Steering_Angle || 0,
            vehicleId: vehicleId,
          };

          // Add comparison data for each vehicle at this data point
          comparisonData.forEach((comp) => {
            const compFiltered = comp.data.filter((p: any) => p.speed != null);
            if (compFiltered[index]) {
              const compPoint = compFiltered[index];
              // Store comparison data with vehicle-specific keys
              (baseData as any)[`speed_${comp.vehicleId}`] =
                compPoint.speed || 0;
              (baseData as any)[`throttle_${comp.vehicleId}`] =
                compPoint.aps || 0;
              (baseData as any)[`brake_${comp.vehicleId}`] =
                compPoint.pbrake_f || 0;
              (baseData as any)[`gear_${comp.vehicleId}`] = compPoint.gear || 0;
              (baseData as any)[`steering_${comp.vehicleId}`] =
                compPoint.Steering_Angle || 0;
            }
          });

          return baseData;
        });

        console.log(
          "Chart data processed:",
          chartData.length,
          "points for",
          1 + comparisonVehicles.length,
          "vehicles"
        );
        setData(chartData);
        setError(null);
      } catch (err) {
        setError("Failed to load telemetry data");
        console.error("Telemetry fetch error:", err);
      } finally {
        setLoading(false);
      }
    };

    fetchTelemetry();
  }, [track, race, vehicleId, lapNumber, comparisonVehicles]);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-[400px] text-muted-foreground animate-pulse">
        Loading telemetry data...
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center h-[400px] text-destructive bg-destructive/10 rounded-xl border border-destructive/20">
        {error}
      </div>
    );
  }

  // Helper function to render lines for all vehicles
  const renderVehicleLines = (parameter: string, baseColor: string) => {
    const lines = [];

    // Primary vehicle line
    lines.push(
      <Line
        key={`${parameter}_${vehicleId}`}
        type="monotone"
        dataKey={parameter}
        stroke={baseColor}
        name={`${
          parameter.charAt(0).toUpperCase() + parameter.slice(1)
        } (${vehicleId})`}
        dot={false}
        strokeWidth={2}
      />
    );

    // Comparison vehicle lines
    comparisonVehicles.forEach((compVehicleId, index) => {
      const compColor = vehicleColors[(index + 1) % vehicleColors.length];
      lines.push(
        <Line
          key={`${parameter}_${compVehicleId}`}
          type="monotone"
          dataKey={`${parameter}_${compVehicleId}`}
          stroke={compColor}
          name={`${
            parameter.charAt(0).toUpperCase() + parameter.slice(1)
          } (${compVehicleId})`}
          dot={false}
          strokeWidth={2}
          strokeDasharray="5 5" // Dashed line for comparison vehicles
        />
      );
    });

    return lines;
  };

  const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-black/80 backdrop-blur-md border border-white/10 p-3 rounded-lg shadow-xl text-xs">
          <p className="font-bold text-white mb-2">Index: {label}</p>
          {payload.map((entry: any, index: number) => (
            <div key={index} className="flex items-center gap-2 mb-1" style={{ color: entry.color }}>
              <span className="w-2 h-2 rounded-full" style={{ backgroundColor: entry.color }} />
              <span>{entry.name}: {entry.value.toFixed(2)}</span>
            </div>
          ))}
        </div>
      );
    }
    return null;
  };

  return (
    <div className="w-full space-y-6">
      <div className="flex items-center justify-between">
        <h3 className="text-xl font-bold text-primary flex items-center gap-2">
          <span className="w-1 h-6 bg-primary rounded-full"></span>
          Telemetry Data {lapNumber ? `- Lap ${lapNumber}` : ""}
        </h3>
      </div>
      
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Speed Chart */}
        <div className="glass-card p-4 border-white/5 bg-white/5">
          <h4 className="text-sm font-semibold text-muted-foreground mb-4 uppercase tracking-wider">Speed (km/h)</h4>
          <ResponsiveContainer width="100%" height={200}>
            <LineChart
              data={data}
              margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
            >
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />
              <XAxis dataKey="index" stroke="rgba(255,255,255,0.3)" fontSize={12} />
              <YAxis domain={["dataMin - 5", "dataMax + 5"]} stroke="rgba(255,255,255,0.3)" fontSize={12} />
              <Tooltip content={<CustomTooltip />} />
              <Legend wrapperStyle={{ paddingTop: '10px' }} />
              {renderVehicleLines("speed", "#8884d8")}
            </LineChart>
          </ResponsiveContainer>
        </div>

        {/* Throttle Chart */}
        <div className="glass-card p-4 border-white/5 bg-white/5">
          <h4 className="text-sm font-semibold text-muted-foreground mb-4 uppercase tracking-wider">Throttle Position (%)</h4>
          <ResponsiveContainer width="100%" height={200}>
            <LineChart
              data={data}
              margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
            >
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />
              <XAxis dataKey="index" stroke="rgba(255,255,255,0.3)" fontSize={12} />
              <YAxis domain={[0, "dataMax + 5"]} stroke="rgba(255,255,255,0.3)" fontSize={12} />
              <Tooltip content={<CustomTooltip />} />
              <Legend wrapperStyle={{ paddingTop: '10px' }} />
              {renderVehicleLines("throttle", "#82ca9d")}
            </LineChart>
          </ResponsiveContainer>
        </div>

        {/* Brake Chart */}
        <div className="glass-card p-4 border-white/5 bg-white/5">
          <h4 className="text-sm font-semibold text-muted-foreground mb-4 uppercase tracking-wider">Brake Pressure</h4>
          <ResponsiveContainer width="100%" height={200}>
            <LineChart
              data={data}
              margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
            >
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />
              <XAxis dataKey="index" stroke="rgba(255,255,255,0.3)" fontSize={12} />
              <YAxis domain={[0, "dataMax + 2"]} stroke="rgba(255,255,255,0.3)" fontSize={12} />
              <Tooltip content={<CustomTooltip />} />
              <Legend wrapperStyle={{ paddingTop: '10px' }} />
              {renderVehicleLines("brake", "#ff4444")}
            </LineChart>
          </ResponsiveContainer>
        </div>

        {/* Gear Chart */}
        <div className="glass-card p-4 border-white/5 bg-white/5">
          <h4 className="text-sm font-semibold text-muted-foreground mb-4 uppercase tracking-wider">Gear Position</h4>
          <ResponsiveContainer width="100%" height={200}>
            <LineChart
              data={data}
              margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
            >
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />
              <XAxis dataKey="index" stroke="rgba(255,255,255,0.3)" fontSize={12} />
              <YAxis domain={[0, 6]} tickCount={7} stroke="rgba(255,255,255,0.3)" fontSize={12} />
              <Tooltip content={<CustomTooltip />} />
              <Legend wrapperStyle={{ paddingTop: '10px' }} />
              {renderVehicleLines("gear", "#ffc658")}
            </LineChart>
          </ResponsiveContainer>
        </div>

        {/* Steering Chart */}
        <div className="glass-card p-4 border-white/5 bg-white/5">
          <h4 className="text-sm font-semibold text-muted-foreground mb-4 uppercase tracking-wider">Steering Angle (°)</h4>
          <ResponsiveContainer width="100%" height={200}>
            <LineChart
              data={data}
              margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
            >
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />
              <XAxis dataKey="index" stroke="rgba(255,255,255,0.3)" fontSize={12} />
              <YAxis domain={["dataMin - 10", "dataMax + 10"]} stroke="rgba(255,255,255,0.3)" fontSize={12} />
              <Tooltip content={<CustomTooltip />} />
              <Legend wrapperStyle={{ paddingTop: '10px' }} />
              {renderVehicleLines("steering", "#ff8c00")}
            </LineChart>
          </ResponsiveContainer>
        </div>

        {/* Combined Overview Chart */}
        <div className="glass-card p-4 border-white/5 bg-white/5 lg:col-span-2">
          <h4 className="text-sm font-semibold text-muted-foreground mb-4 uppercase tracking-wider">Combined Overview (Normalized)</h4>
          <ResponsiveContainer width="100%" height={250}>
            <LineChart
              data={data}
              margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
            >
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />
              <XAxis dataKey="index" stroke="rgba(255,255,255,0.3)" fontSize={12} />
              <YAxis stroke="rgba(255,255,255,0.3)" fontSize={12} />
              <Tooltip content={<CustomTooltip />} />
              <Legend wrapperStyle={{ paddingTop: '10px' }} />
              <Line
                type="monotone"
                dataKey="speed"
                stroke="#8884d8"
                name="Speed"
                dot={false}
                strokeWidth={1}
              />
              <Line
                type="monotone"
                dataKey="throttle"
                stroke="#82ca9d"
                name="Throttle"
                dot={false}
                strokeWidth={1}
              />
              <Line
                type="monotone"
                dataKey="brake"
                stroke="#ff4444"
                name="Brake"
                dot={false}
                strokeWidth={1}
              />
              <Line
                type="monotone"
                dataKey="gear"
                stroke="#ffc658"
                name="Gear"
                dot={false}
                strokeWidth={1}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
}
