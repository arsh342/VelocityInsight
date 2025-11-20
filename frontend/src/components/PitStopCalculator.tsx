import { useState, useEffect } from "react";
import { Calculator, Clock, Fuel, TrendingDown, AlertCircle, CheckCircle2 } from "lucide-react";

interface PitStopCalculatorProps {
  currentLap?: number;
  totalLaps?: number;
  currentLapTime?: number;
  fuelLevel?: number;
  tireAge?: number;
}

interface PitWindow {
  lapStart: number;
  lapEnd: number;
  reason: string;
  priority: "optimal" | "acceptable" | "emergency";
}

export function PitStopCalculator({
  currentLap = 10,
  totalLaps = 45,
  currentLapTime = 92.5,
  fuelLevel = 75,
  tireAge = 10,
}: PitStopCalculatorProps) {
  const [pitWindows, setPitWindows] = useState<PitWindow[]>([]);
  const [recommendation, setRecommendation] = useState<string>("");

  useEffect(() => {
    calculatePitStrategy();
  }, [currentLap, totalLaps, fuelLevel, tireAge]);

  const calculatePitStrategy = () => {
    const windows: PitWindow[] = [];
    const lapsRemaining = totalLaps - currentLap;

    // Calculate fuel-based pit window
    const fuelLapsRemaining = Math.floor(fuelLevel / 2.2); // Assuming 2.2% fuel per lap
    if (fuelLapsRemaining < lapsRemaining) {
      const fuelPitLap = currentLap + fuelLapsRemaining - 2; // 2-lap buffer
      windows.push({
        lapStart: Math.max(currentLap + 1, fuelPitLap - 2),
        lapEnd: fuelPitLap,
        reason: "Fuel critical",
        priority: fuelLevel < 20 ? "emergency" : "optimal",
      });
    }

    // Calculate tire-based pit window
    const tyreDegradation = tireAge > 15 ? "high" : tireAge > 10 ? "medium" : "low";
    if (tyreDegradation !== "low") {
      const tirePitLap = currentLap + (20 - tireAge);
      windows.push({
        lapStart: Math.max(currentLap + 1, tirePitLap - 3),
        lapEnd: Math.min(totalLaps - 5, tirePitLap + 2),
        reason: `Tire degradation (${tyreDegradation})`,
        priority: tireAge > 18 ? "emergency" : tireAge > 15 ? "optimal" : "acceptable",
      });
    }

    // Strategic undercut window (typically 1/3 through race)
    const strategicLap = Math.floor(totalLaps * 0.4);
    if (currentLap < strategicLap && strategicLap < totalLaps - 10) {
      windows.push({
        lapStart: strategicLap - 2,
        lapEnd: strategicLap + 2,
        reason: "Strategic undercut opportunity",
        priority: "acceptable",
      });
    }

    // Sort by priority
    const priorityOrder = { emergency: 0, optimal: 1, acceptable: 2 };
    windows.sort((a, b) => priorityOrder[a.priority] - priorityOrder[b.priority]);

    setPitWindows(windows);

    // Generate recommendation
    if (windows.length > 0) {
      const nextWindow = windows[0];
      if (nextWindow.priority === "emergency") {
        setRecommendation(`⚠️ PIT NOW! ${nextWindow.reason} - Box this lap or next!`);
      } else if (currentLap >= nextWindow.lapStart && currentLap <= nextWindow.lapEnd) {
        setRecommendation(`✅ In optimal pit window (Lap ${nextWindow.lapStart}-${nextWindow.lapEnd}). ${nextWindow.reason}.`);
      } else if (currentLap < nextWindow.lapStart) {
        setRecommendation(`⏱️ Next pit window: Lap ${nextWindow.lapStart}-${nextWindow.lapEnd}. ${nextWindow.reason}.`);
      } else {
        setRecommendation(`Evaluating strategy... Monitor fuel and tire conditions.`);
      }
    } else {
      setRecommendation(`✅ No immediate pit stop required. Continue current strategy.`);
    }
  };

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case "emergency":
        return "border-red-500 bg-red-500/10";
      case "optimal":
        return "border-emerald-500 bg-emerald-500/10";
      case "acceptable":
        return "border-blue-500 bg-blue-500/10";
      default:
        return "border-white/10 bg-white/5";
    }
  };

  const getPriorityIcon = (priority: string) => {
    switch (priority) {
      case "emergency":
        return <AlertCircle className="h-5 w-5 text-red-500" />;
      case "optimal":
        return <CheckCircle2 className="h-5 w-5 text-emerald-500" />;
      default:
        return <Clock className="h-5 w-5 text-blue-500" />;
    }
  };

  return (
    <div className="glass-card p-6 space-y-6">
      <div className="flex items-center gap-3 border-b border-white/10 pb-4">
        <Calculator className="h-6 w-6 text-primary" />
        <h3 className="text-xl font-bold text-white">Pit Stop Strategy Calculator</h3>
      </div>

      {/* Current Status */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="p-4 bg-white/5 rounded-lg border border-white/10">
          <div className="flex items-center gap-2 mb-2">
            <Clock className="h-4 w-4 text-muted-foreground" />
            <span className="text-xs text-muted-foreground uppercase tracking-wider">Current Lap</span>
          </div>
          <div className="text-2xl font-bold text-foreground">
            {currentLap}/{totalLaps}
          </div>
        </div>

        <div className="p-4 bg-white/5 rounded-lg border border-white/10">
          <div className="flex items-center gap-2 mb-2">
            <Fuel className="h-4 w-4 text-muted-foreground" />
            <span className="text-xs text-muted-foreground uppercase tracking-wider">Fuel Level</span>
          </div>
          <div className="text-2xl font-bold text-foreground">{fuelLevel}%</div>
          <div className="text-xs text-muted-foreground mt-1">
            ~{Math.floor(fuelLevel / 2.2)} laps
          </div>
        </div>

        <div className="p-4 bg-white/5 rounded-lg border border-white/10">
          <div className="flex items-center gap-2 mb-2">
            <TrendingDown className="h-4 w-4 text-muted-foreground" />
            <span className="text-xs text-muted-foreground uppercase tracking-wider">Tire Age</span>
          </div>
          <div className="text-2xl font-bold text-foreground">{tireAge} laps</div>
          <div className="text-xs text-muted-foreground mt-1">
            {tireAge > 15 ? "High wear" : tireAge > 10 ? "Medium wear" : "Fresh"}
          </div>
        </div>

        <div className="p-4 bg-white/5 rounded-lg border border-white/10">
          <div className="flex items-center gap-2 mb-2">
            <Clock className=" h-4 w-4 text-muted-foreground" />
            <span className="text-xs text-muted-foreground uppercase tracking-wider">Lap Time</span>
          </div>
          <div className="text-2xl font-bold font-mono text-foreground">{currentLapTime.toFixed(2)}s</div>
        </div>
      </div>

      {/* Recommendation Banner */}
      <div className={`p-4 rounded-lg border-2 ${recommendation.includes("⚠️") ? "border-red-500 bg-red-500/10" : recommendation.includes("✅") ? "border-emerald-500 bg-emerald-500/10" : "border-blue-500 bg-blue-500/10"}`}>
        <div className="flex items-start gap-3">
          {recommendation.includes("⚠️") ? (
            <AlertCircle className="h-6 w-6 text-red-500 flex-shrink-0 mt-0.5" />
          ) : recommendation.includes("✅") ? (
            <CheckCircle2 className="h-6 w-6 text-emerald-500 flex-shrink-0 mt-0.5" />
          ) : (
            <Clock className="h-6 w-6 text-blue-500 flex-shrink-0 mt-0.5" />
          )}
          <div>
            <div className="font-bold text-white mb-1">Strategic Recommendation</div>
            <div className="text-sm text-foreground">{recommendation}</div>
          </div>
        </div>
      </div>

      {/* Pit Windows */}
      {pitWindows.length > 0 && (
        <div className="space-y-3">
          <h4 className="text-sm font-bold text-muted-foreground uppercase tracking-wider">Calculated Pit Windows</h4>
          {pitWindows.map((window, idx) => (
            <div key={idx} className={`p-4 rounded-lg border-2 ${getPriorityColor(window.priority)}`}>
              <div className="flex items-start justify-between gap-4">
                <div className="flex items-start gap-3 flex-1">
                  {getPriorityIcon(window.priority)}
                  <div className="flex-1">
                    <div className="flex items-baseline gap-2 mb-1">
                      <span className="font-bold text-white">
                        Lap {window.lapStart}-{window.lapEnd}
                      </span>
                      <span className="text-xs uppercase tracking-wider font-bold" style={{ color: window.priority === "emergency" ? "#ef4444" : window.priority === "optimal" ? "#10b981" : "#3b82f6" }}>
                        {window.priority}
                      </span>
                    </div>
                    <div className="text-sm text-muted-foreground">{window.reason}</div>
                  </div>
                </div>
                <div className="text-xs text-muted-foreground whitespace-nowrap">
                  {currentLap >= window.lapStart && currentLap <= window.lapEnd ? (
                    <span className="px-2 py-1 bg-white/10 rounded-full font-bold">ACTIVE</span>
                  ) : currentLap < window.lapStart ? (
                    <span>{window.lapStart - currentLap} laps</span>
                  ) : (
                    <span className="opacity-50">Passed</span>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Additional Info */}
      <div className="pt-4 border-t border-white/10 text-xs text-muted-foreground space-y-1">
        <p>• Calculations based on current fuel consumption (~2.2% per lap) and tire wear patterns</p>
        <p>• Strategic windows consider track position and undercut opportunities</p>
        <p>• Monitor real-time telemetry for dynamic adjustments</p>
      </div>
    </div>
  );
}
