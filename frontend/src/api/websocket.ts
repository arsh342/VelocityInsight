const WS_BASE_URL = import.meta.env.VITE_WS_BASE_URL || "ws://localhost:8000";

export interface LiveTelemetryUpdate {
  timestamp: number;
  vehicle_id: string;
  lap_number: number;
  speed: number;
  throttle: number;
  brake: number;
  steering: number;
  gear: number;
  rpm: number;
  lap_distance: number;
  position?: number;
}

export interface LapCompletedEvent {
  vehicle_id: string;
  lap_number: number;
  lap_time: number;
  sector1: number;
  sector2: number;
  sector3: number;
  tire_age: number;
  position: number;
}

export interface AlertEvent {
  vehicle_id: string;
  type: "tire_wear" | "pit_window" | "consistency" | "prediction";
  severity: "info" | "warning" | "critical";
  message: string;
  timestamp: number;
}

class WebSocketClient {
  private ws: WebSocket | null = null;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectTimeout: number | null = null;
  private track: string = "";
  private race: string = "";
  private listeners: Map<string, Set<Function>> = new Map();

  connect(track: string, race: string): void {
    this.track = track;
    this.race = race;

    if (this.ws?.readyState === WebSocket.OPEN) {
      console.warn("WebSocket already connected");
      return;
    }

    // Use native WebSocket instead of Socket.io
    const wsUrl = `${WS_BASE_URL}/ws/live/${track}/${race}`;
    console.log("Connecting to WebSocket:", wsUrl);

    this.ws = new WebSocket(wsUrl);

    this.ws.onopen = () => {
      console.log("WebSocket connected");
      this.reconnectAttempts = 0;
      this.emit("connect", {});
    };

    this.ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);

        // Emit telemetry updates
        if (data.timestamp && data.vehicle_id) {
          this.emit("telemetry_update", data);
        }

        // Detect lap completion (you can enhance this logic)
        if (data.lap_time !== undefined) {
          this.emit("lap_completed", data);
        }
      } catch (error) {
        console.error("Error parsing WebSocket message:", error);
      }
    };

    this.ws.onerror = (error) => {
      console.error("WebSocket error:", error);
    };

    this.ws.onclose = () => {
      console.log("WebSocket disconnected");
      this.emit("disconnect", {});

      // Attempt reconnection
      if (this.reconnectAttempts < this.maxReconnectAttempts) {
        this.reconnectAttempts++;
        console.log(
          `Reconnecting... (attempt ${this.reconnectAttempts}/${this.maxReconnectAttempts})`
        );
        this.reconnectTimeout = window.setTimeout(() => {
          this.connect(this.track, this.race);
        }, 1000 * this.reconnectAttempts);
      } else {
        console.error("Max reconnection attempts reached");
      }
    };
  }

  disconnect(): void {
    if (this.reconnectTimeout) {
      clearTimeout(this.reconnectTimeout);
      this.reconnectTimeout = null;
    }

    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }

    this.listeners.clear();
  }

  private emit(event: string, data: any): void {
    const handlers = this.listeners.get(event);
    if (handlers) {
      handlers.forEach((handler) => handler(data));
    }
  }

  private on(event: string, callback: Function): void {
    if (!this.listeners.has(event)) {
      this.listeners.set(event, new Set());
    }
    this.listeners.get(event)!.add(callback);
  }

  private off(event: string, callback: Function): void {
    const handlers = this.listeners.get(event);
    if (handlers) {
      handlers.delete(callback);
    }
  }

  onTelemetryUpdate(callback: (data: LiveTelemetryUpdate) => void): void {
    this.on("telemetry_update", callback);
  }

  onLapCompleted(callback: (data: LapCompletedEvent) => void): void {
    this.on("lap_completed", callback);
  }

  onAlert(callback: (data: AlertEvent) => void): void {
    this.on("alert", callback);
  }

  offTelemetryUpdate(callback: (data: LiveTelemetryUpdate) => void): void {
    this.off("telemetry_update", callback);
  }

  offLapCompleted(callback: (data: LapCompletedEvent) => void): void {
    this.off("lap_completed", callback);
  }

  offAlert(callback: (data: AlertEvent) => void): void {
    this.off("alert", callback);
  }

  isConnected(): boolean {
    return this.ws?.readyState === WebSocket.OPEN;
  }
}

export const wsClient = new WebSocketClient();
