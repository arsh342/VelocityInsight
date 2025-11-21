import { useState, useEffect, useRef } from "react";

interface VehiclePosition {
  vehicleId: string;
  position: number;
  lapProgress: number; // 0-1 representing progress around track
  speed: number;
  sector: number;
  color?: string;
  isHighlighted?: boolean;
}

interface TrackMapProps {
  track: string;
  onSectorSelect?: (sector: number) => void;
  selectedSector?: number;
  telemetryData?: Array<{
    distance: number;
    speed: number;
    sector: number;
    VBOX_Lat_Min?: number;
    VBOX_Long_Minutes?: number;
    [key: string]: any; // Allow additional telemetry fields
  }>;
  vehiclePositions?: VehiclePosition[];
  highlightedVehicle?: string;
}

const trackMapFiles: { [key: string]: string } = {
  barber: "barber.svg",
  COTA: "cota.svg",
  indianapolis: "indianpolis.svg",
  "Road America": "Road_America.svg",
  Sebring: "sebring.svg",
  Sonoma: "sonoma.svg",
  VIR: "vir.svg",
};

export default function TrackMap({
  track,
  onSectorSelect,
  selectedSector,
  telemetryData,
  vehiclePositions = [],
  highlightedVehicle,
}: TrackMapProps) {
  const [svgContent, setSvgContent] = useState<string>("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [hoveredSector, setHoveredSector] = useState<number | null>(null);
  const svgRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const loadTrackMap = async () => {
      try {
        setLoading(true);
        setError(null);

        const mapFile = trackMapFiles[track];
        if (!mapFile) {
          setError(`Track map not available for ${track}`);
          return;
        }

        const response = await fetch(`/maps/${mapFile}`);
        if (!response.ok) {
          throw new Error(`Failed to load track map: ${response.statusText}`);
        }

        const svgText = await response.text();
        setSvgContent(svgText);
      } catch (err) {
        setError(
          err instanceof Error ? err.message : "Failed to load track map"
        );
        console.error("Error loading track map:", err);
      } finally {
        setLoading(false);
      }
    };

    if (track) {
      loadTrackMap();
    }
  }, [track]);

  useEffect(() => {
    if (svgContent && svgRef.current) {
      // Enhance SVG with interactive features
      const trackMapContainer = svgRef.current;
      trackMapContainer.innerHTML = svgContent;

      const svgElement = trackMapContainer.querySelector("svg");
      if (svgElement) {
        // Get original dimensions
        const originalWidth =
          svgElement.getAttribute("width") || svgElement.clientWidth || "1000";
        const originalHeight =
          svgElement.getAttribute("height") || svgElement.clientHeight || "600";

        const width = parseFloat(
          originalWidth.toString().replace(/[^0-9.]/g, "")
        );
        const height = parseFloat(
          originalHeight.toString().replace(/[^0-9.]/g, "")
        );

        // Set viewBox
        const existingViewBox = svgElement.getAttribute("viewBox");
        if (!existingViewBox) {
          svgElement.setAttribute("viewBox", `0 0 ${width} ${height}`);
        }

        svgElement.setAttribute("preserveAspectRatio", "xMidYMid meet");
        svgElement.removeAttribute("width");
        svgElement.removeAttribute("height");

        // Set responsive styles
        svgElement.style.width = "100%";
        svgElement.style.height = "auto";
        svgElement.style.maxWidth = "100%";
        svgElement.style.maxHeight = "500px";
        svgElement.style.display = "block";
        svgElement.style.margin = "0 auto";

        // Add speed gradient and interactive features
        setTimeout(() => {
          addSpeedGradient(svgElement);
          addInteractiveSectors(svgElement);
        }, 200);
      }
    }
  }, [svgContent, selectedSector, hoveredSector, vehiclePositions, highlightedVehicle, telemetryData]);

  const addSpeedGradient = (svg: SVGElement) => {
    // Remove existing speed gradients
    svg.querySelectorAll(".speed-gradient").forEach((el) => el.remove());

    // Add gradient definitions
    const defs = svg.querySelector("defs") || document.createElementNS("http://www.w3.org/2000/svg", "defs");
    if (!svg.querySelector("defs")) {
      svg.insertBefore(defs, svg.firstChild);
    }

    // Create speed-based gradient (red to blue)
    const speedGradient = document.createElementNS("http://www.w3.org/2000/svg", "linearGradient");
    speedGradient.id = "speedGradient";
    speedGradient.setAttribute("x1", "0%");
    speedGradient.setAttribute("y1", "0%");
    speedGradient.setAttribute("x2", "100%");
    speedGradient.setAttribute("y2", "0%");

    // Red to Blue gradient (high speed to low speed)
    const stops = [
      { offset: "0%", color: "#ef4444", opacity: "0.8" },   // Red - High speed
      { offset: "50%", color: "#8b5cf6", opacity: "0.8" },  // Purple - Medium
      { offset: "100%", color: "#3b82f6", opacity: "0.8" }, // Blue - Low speed
    ];

    stops.forEach(stop => {
      const stopElement = document.createElementNS("http://www.w3.org/2000/svg", "stop");
      stopElement.setAttribute("offset", stop.offset);
      stopElement.setAttribute("stop-color", stop.color);
      stopElement.setAttribute("stop-opacity", stop.opacity);
      speedGradient.appendChild(stopElement);
    });

    defs.appendChild(speedGradient);

    // Apply gradient to all track paths
    const paths = svg.querySelectorAll("path");
    paths.forEach((path) => {
      if (!path.classList.contains("interactive-sector") && !path.classList.contains("vehicle-position")) {
        path.classList.add("speed-gradient");
        path.setAttribute("stroke", "url(#speedGradient)");
        path.setAttribute("stroke-width", "4");
        path.setAttribute("fill", "none");
        path.style.filter = "drop-shadow(0 0 8px rgba(6, 182, 212, 0.6))";
        path.style.transition = "all 0.3s ease";
        
        // Add hover effect
        path.addEventListener("mouseenter", () => {
          path.setAttribute("stroke-width", "6");
          path.style.filter = "drop-shadow(0 0 12px rgba(6, 182, 212, 0.9))";
        });
        
        path.addEventListener("mouseleave", () => {
          path.setAttribute("stroke-width", "4");
          path.style.filter = "drop-shadow(0 0 8px rgba(6, 182, 212, 0.6))";
        });
      }
    });
  };

  const addInteractiveSectors = (svg: SVGElement) => {
    // Remove existing interactive elements
    svg
      .querySelectorAll(".interactive-sector, .vehicle-position")
      .forEach((el) => el.remove());

    // Get SVG dimensions
    const viewBox = svg.getAttribute("viewBox");
    let svgWidth = 1000;
    let svgHeight = 600;

    if (viewBox) {
      const [, , width, height] = viewBox.split(" ").map(Number);
      svgWidth = width;
      svgHeight = height;
    }

    // Create interactive sectors with speed indicators
    const sectors = [
      {
        id: 1,
        name: "Sector 1",
        avgSpeed: 245,
        color: "#ef4444", // Red - High speed
        position: { x: svgWidth * 0.2, y: svgHeight * 0.15 },
      },
      {
        id: 2,
        name: "Sector 2",
        avgSpeed: 210,
        color: "#8b5cf6", // Purple - Medium
        position: { x: svgWidth * 0.6, y: svgHeight * 0.15 },
      },
      {
        id: 3,
        name: "Sector 3",
        avgSpeed: 190,
        color: "#3b82f6", // Blue - Low speed
        position: { x: svgWidth * 0.8, y: svgHeight * 0.85 },
      },
    ];

    sectors.forEach((sector) => {
      // Create sector group
      const sectorGroup = document.createElementNS(
        "http://www.w3.org/2000/svg",
        "g"
      );
      sectorGroup.classList.add("interactive-sector");
      sectorGroup.setAttribute("data-sector", sector.id.toString());

      // Clickable area
      const clickArea = document.createElementNS(
        "http://www.w3.org/2000/svg",
        "circle"
      );
      clickArea.setAttribute("cx", sector.position.x.toString());
      clickArea.setAttribute("cy", sector.position.y.toString());
      clickArea.setAttribute("r", "30");
      clickArea.setAttribute("fill", "transparent");
      clickArea.setAttribute("cursor", "pointer");
      clickArea.setAttribute("stroke", sector.color);
      clickArea.setAttribute("stroke-width", "3");
      clickArea.setAttribute("stroke-dasharray", "6,4");
      clickArea.setAttribute("opacity", "0.6");
      clickArea.style.transition = "all 0.3s ease";

      // Sector indicator
      const indicator = document.createElementNS(
        "http://www.w3.org/2000/svg",
        "circle"
      );
      indicator.setAttribute("cx", sector.position.x.toString());
      indicator.setAttribute("cy", sector.position.y.toString());
      indicator.setAttribute("r", selectedSector === sector.id ? "14" : "10");
      indicator.setAttribute("fill", sector.color);
      indicator.setAttribute(
        "opacity",
        selectedSector === sector.id ? "0.9" : "0.7"
      );
      indicator.setAttribute("stroke", "#ffffff");
      indicator.setAttribute("stroke-width", "2");
      indicator.style.filter = "drop-shadow(0 2px 6px rgba(0,0,0,0.6))";
      indicator.style.transition = "all 0.3s ease";

      // Speed info background
      const speedBg = document.createElementNS(
        "http://www.w3.org/2000/svg",
        "rect"
      );
      speedBg.setAttribute("x", (sector.position.x - 35).toString());
      speedBg.setAttribute("y", (sector.position.y + 22).toString());
      speedBg.setAttribute("width", "70");
      speedBg.setAttribute("height", "20");
      speedBg.setAttribute("rx", "10");
      speedBg.setAttribute("fill", "rgba(0,0,0,0.9)");
      speedBg.setAttribute("stroke", sector.color);
      speedBg.setAttribute("stroke-width", "1.5");

      // Sector label
      const label = document.createElementNS(
        "http://www.w3.org/2000/svg",
        "text"
      );
      label.setAttribute("x", sector.position.x.toString());
      label.setAttribute("y", (sector.position.y + 36).toString());
      label.setAttribute("text-anchor", "middle");
      label.setAttribute("fill", "#ffffff");
      label.setAttribute("font-size", "11");
      label.setAttribute("font-weight", "bold");
      label.setAttribute("font-family", "Inter, sans-serif");
      label.textContent = `${sector.avgSpeed}km/h`;

      sectorGroup.appendChild(clickArea);
      sectorGroup.appendChild(speedBg);
      sectorGroup.appendChild(indicator);
      sectorGroup.appendChild(label);

      // Hover effects
      sectorGroup.addEventListener("mouseenter", () => {
        setHoveredSector(sector.id);
        indicator.setAttribute("r", "16");
        indicator.setAttribute("opacity", "1");
        clickArea.setAttribute("opacity", "1");
        clickArea.setAttribute("r", "35");
        clickArea.setAttribute("stroke-width", "4");
      });

      sectorGroup.addEventListener("mouseleave", () => {
        setHoveredSector(null);
        indicator.setAttribute("r", selectedSector === sector.id ? "14" : "10");
        indicator.setAttribute(
          "opacity",
          selectedSector === sector.id ? "0.9" : "0.7"
        );
        clickArea.setAttribute("opacity", "0.6");
        clickArea.setAttribute("r", "30");
        clickArea.setAttribute("stroke-width", "3");
      });

      sectorGroup.addEventListener("click", () => {
        onSectorSelect?.(sector.id);
      });

      svg.appendChild(sectorGroup);
    });

    // Add vehicle positions
    addVehiclePositions(svg, svgWidth, svgHeight);
  };

  const addVehiclePositions = (svg: SVGElement, svgWidth: number, svgHeight: number) => {
    svg.querySelectorAll(".vehicle-position").forEach((el) => el.remove());

    if (!vehiclePositions || vehiclePositions.length === 0) return;

    const trackPaths: { [key: string]: Array<{ x: number; y: number }> } = {
      COTA: [
        { x: 0.1, y: 0.5 }, { x: 0.15, y: 0.3 }, { x: 0.25, y: 0.15 }, { x: 0.4, y: 0.1 },
        { x: 0.6, y: 0.15 }, { x: 0.75, y: 0.25 }, { x: 0.85, y: 0.4 }, { x: 0.9, y: 0.6 },
        { x: 0.85, y: 0.8 }, { x: 0.7, y: 0.9 }, { x: 0.5, y: 0.85 }, { x: 0.3, y: 0.8 },
        { x: 0.15, y: 0.7 }, { x: 0.1, y: 0.5 }
      ],
      barber: [
        { x: 0.15, y: 0.4 }, { x: 0.25, y: 0.2 }, { x: 0.4, y: 0.15 }, { x: 0.6, y: 0.2 },
        { x: 0.75, y: 0.35 }, { x: 0.8, y: 0.55 }, { x: 0.75, y: 0.75 }, { x: 0.6, y: 0.85 },
        { x: 0.4, y: 0.8 }, { x: 0.25, y: 0.65 }, { x: 0.15, y: 0.4 }
      ],
      default: [
        { x: 0.2, y: 0.5 }, { x: 0.3, y: 0.2 }, { x: 0.5, y: 0.15 }, { x: 0.7, y: 0.2 },
        { x: 0.8, y: 0.5 }, { x: 0.7, y: 0.8 }, { x: 0.5, y: 0.85 }, { x: 0.3, y: 0.8 },
        { x: 0.2, y: 0.5 }
      ]
    };

    const trackPath = trackPaths[track] || trackPaths.default;

    vehiclePositions.forEach((vehicle, index) => {
      const progress = Math.max(0, Math.min(1, vehicle.lapProgress));
      const pathIndex = Math.floor(progress * (trackPath.length - 1));
      const nextIndex = Math.min(pathIndex + 1, trackPath.length - 1);
      const segmentProgress = (progress * (trackPath.length - 1)) - pathIndex;

      const currentPoint = trackPath[pathIndex];
      const nextPoint = trackPath[nextIndex];
      
      const x = svgWidth * (currentPoint.x + (nextPoint.x - currentPoint.x) * segmentProgress);
      const y = svgHeight * (currentPoint.y + (nextPoint.y - currentPoint.y) * segmentProgress);

      const vehicleGroup = document.createElementNS("http://www.w3.org/2000/svg", "g");
      vehicleGroup.classList.add("vehicle-position");
      vehicleGroup.setAttribute("data-vehicle", vehicle.vehicleId);

      const isHighlighted = vehicle.vehicleId === highlightedVehicle || vehicle.isHighlighted;
      const vehicleColor = vehicle.color || `hsl(${(index * 360) / vehiclePositions.length}, 70%, 60%)`;

      const vehicleDot = document.createElementNS("http://www.w3.org/2000/svg", "circle");
      vehicleDot.setAttribute("cx", x.toString());
      vehicleDot.setAttribute("cy", y.toString());
      vehicleDot.setAttribute("r", isHighlighted ? "9" : "7");
      vehicleDot.setAttribute("fill", vehicleColor);
      vehicleDot.setAttribute("stroke", isHighlighted ? "#ffffff" : "#000000");
      vehicleDot.setAttribute("stroke-width", isHighlighted ? "3" : "2");
      vehicleDot.style.filter = "drop-shadow(0 2px 6px rgba(0,0,0,0.7))";
      vehicleDot.style.transition = "all 0.3s ease";

      const positionText = document.createElementNS("http://www.w3.org/2000/svg", "text");
      positionText.setAttribute("x", x.toString());
      positionText.setAttribute("y", (y + 1).toString());
      positionText.setAttribute("text-anchor", "middle");
      positionText.setAttribute("dominant-baseline", "middle");
      positionText.setAttribute("fill", "#ffffff");
      positionText.setAttribute("font-size", isHighlighted ? "10" : "8");
      positionText.setAttribute("font-weight", "bold");
      positionText.setAttribute("font-family", "Inter, sans-serif");
      positionText.textContent = vehicle.position.toString();

      const tooltipBg = document.createElementNS("http://www.w3.org/2000/svg", "rect");
      tooltipBg.setAttribute("x", (x - 40).toString());
      tooltipBg.setAttribute("y", (y - 28).toString());
      tooltipBg.setAttribute("width", "80");
      tooltipBg.setAttribute("height", "18");
      tooltipBg.setAttribute("rx", "9");
      tooltipBg.setAttribute("fill", "rgba(0,0,0,0.95)");
      tooltipBg.setAttribute("stroke", vehicleColor);
      tooltipBg.setAttribute("stroke-width", "1.5");
      tooltipBg.style.opacity = "0";
      tooltipBg.style.transition = "opacity 0.2s ease";

      const tooltipText = document.createElementNS("http://www.w3.org/2000/svg", "text");
      tooltipText.setAttribute("x", x.toString());
      tooltipText.setAttribute("y", (y - 19).toString());
      tooltipText.setAttribute("text-anchor", "middle");
      tooltipText.setAttribute("fill", "#ffffff");
      tooltipText.setAttribute("font-size", "10");
      tooltipText.setAttribute("font-weight", "bold");
      tooltipText.setAttribute("font-family", "Inter, sans-serif");
      tooltipText.textContent = `${vehicle.vehicleId} | ${vehicle.speed}km/h`;
      tooltipText.style.opacity = "0";
      tooltipText.style.transition = "opacity 0.2s ease";

      vehicleGroup.addEventListener("mouseenter", () => {
        vehicleDot.setAttribute("r", "11");
        tooltipBg.style.opacity = "1";
        tooltipText.style.opacity = "1";
      });

      vehicleGroup.addEventListener("mouseleave", () => {
        vehicleDot.setAttribute("r", isHighlighted ? "9" : "7");
        tooltipBg.style.opacity = "0";
        tooltipText.style.opacity = "0";
      });

      vehicleGroup.appendChild(tooltipBg);
      vehicleGroup.appendChild(tooltipText);
      vehicleGroup.appendChild(vehicleDot);
      vehicleGroup.appendChild(positionText);

      svg.appendChild(vehicleGroup);
    });
  };

  if (loading) {
    return (
      <div className="w-full h-[400px] glass-card flex flex-col items-center justify-center text-muted-foreground animate-pulse">
        <div className="w-12 h-12 border-4 border-primary border-t-transparent rounded-full animate-spin mb-4"></div>
        <p>Loading track map...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="w-full h-[400px] glass-card flex flex-col items-center justify-center text-destructive bg-destructive/10 border-destructive/20">
        <p className="text-lg font-bold mb-2">❌ {error}</p>
        <p className="text-sm opacity-80">Available tracks: {Object.keys(trackMapFiles).join(", ")}</p>
      </div>
    );
  }

  return (
    <div className="w-full space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-bold text-primary flex items-center gap-2">
          <span className="w-1 h-5 bg-primary rounded-full"></span>
          {track} Circuit - Speed Trace
        </h3>
        {hoveredSector && (
          <div className="px-3 py-1 rounded-full bg-primary/20 text-primary text-xs font-bold uppercase tracking-wider border border-primary/30">
            Sector {hoveredSector} - Click to analyze
          </div>
        )}
      </div>

      <div className="relative w-full aspect-video bg-gradient-to-br from-black/40 to-black/20 backdrop-blur-sm rounded-xl border border-white/10 overflow-hidden">
        <div
          ref={svgRef}
          className="w-full h-full transition-all duration-300"
          style={{
            filter: hoveredSector ? "brightness(1.2)" : "brightness(1.05)",
          }}
        />
        
        {telemetryData && (
          <div className="absolute top-4 right-4 glass-card p-4 min-w-[200px]">
            <h4 className="text-xs font-bold text-muted-foreground uppercase tracking-wider mb-2">Live Data</h4>
            <div className="space-y-2">
              <div className="flex justify-between items-center">
                <span className="text-sm text-muted-foreground">Speed</span>
                <span className="text-lg font-mono font-bold text-red-400">{telemetryData[0]?.speed || 0} <span className="text-xs text-muted-foreground">km/h</span></span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm text-muted-foreground">Sector</span>
                <span className="text-lg font-mono font-bold text-white">{telemetryData[0]?.sector || 1}</span>
              </div>
            </div>
          </div>
        )}
      </div>

      <div className="glass-card p-4">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <h4 className="text-xs font-bold text-muted-foreground uppercase tracking-wider mb-3">Speed Zones</h4>
            <div className="flex gap-4">
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 rounded-full bg-red-500"></div>
                <span className="text-sm text-muted-foreground">High Speed</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 rounded-full bg-purple-500"></div>
                <span className="text-sm text-muted-foreground">Medium</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 rounded-full bg-blue-500"></div>
                <span className="text-sm text-muted-foreground">Low Speed</span>
              </div>
            </div>
          </div>
          
          {vehiclePositions && vehiclePositions.length > 0 && (
            <div>
              <h4 className="text-xs font-bold text-muted-foreground uppercase tracking-wider mb-3">Live Positions</h4>
              <div className="flex flex-wrap gap-2">
                {vehiclePositions.slice(0, 8).map((vehicle) => (
                  <div 
                    key={vehicle.vehicleId} 
                    className={`flex items-center gap-2 px-2 py-1 rounded border ${
                      vehicle.vehicleId === highlightedVehicle 
                        ? 'bg-primary/20 border-primary/50 text-white' 
                        : 'bg-white/5 border-white/10 text-muted-foreground'
                    }`}
                  >
                    <div 
                      className="w-2 h-2 rounded-full"
                      style={{ backgroundColor: vehicle.color }}
                    ></div>
                    <span className="text-xs font-mono font-bold">{vehicle.vehicleId}</span>
                  </div>
                ))}
                {vehiclePositions.length > 8 && (
                  <div className="px-2 py-1 text-xs text-muted-foreground">
                    +{vehiclePositions.length - 8} more
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
