import { useState, useEffect } from 'react';
import type { AlertEvent } from '../api/websocket';

interface AlertBannerProps {
  alerts: AlertEvent[];
  onDismiss?: (timestamp: number) => void;
}

export default function AlertBanner({ alerts, onDismiss }: AlertBannerProps) {
  const [visibleAlerts, setVisibleAlerts] = useState<AlertEvent[]>([]);

  useEffect(() => {
    // Keep only the 3 most recent alerts
    const recent = alerts.slice(-3).reverse();
    setVisibleAlerts(recent);
  }, [alerts]);

  const handleDismiss = (timestamp: number) => {
    setVisibleAlerts(prev => prev.filter(alert => alert.timestamp !== timestamp));
    onDismiss?.(timestamp);
  };

  if (visibleAlerts.length === 0) {
    return null;
  }

  const getSeverityStyles = (severity: string) => {
    switch (severity) {
      case 'critical':
        return 'bg-red-500/10 border-red-500/20 text-red-200 shadow-red-900/20';
      case 'warning':
        return 'bg-amber-500/10 border-amber-500/20 text-amber-200 shadow-amber-900/20';
      case 'info':
      default:
        return 'bg-blue-500/10 border-blue-500/20 text-blue-200 shadow-blue-900/20';
    }
  };

  const getTypeIcon = (type: string) => {
    switch (type) {
      case 'tire_wear':
        return '🛞';
      case 'pit_window':
        return '🏁';
      case 'consistency':
        return '📊';
      case 'prediction':
        return '🔮';
      default:
        return '📢';
    }
  };

  return (
    <div className="fixed top-24 right-6 z-50 flex flex-col gap-3 w-80 pointer-events-none">
      {visibleAlerts.map((alert) => (
        <div 
          key={alert.timestamp} 
          className={`pointer-events-auto flex items-start gap-3 p-4 rounded-xl border backdrop-blur-md shadow-lg animate-in slide-in-from-right duration-300 ${getSeverityStyles(alert.severity)}`}
        >
          <span className="text-xl leading-none mt-0.5">{getTypeIcon(alert.type)}</span>
          <div className="flex-1 min-w-0">
            <p className="text-sm font-medium leading-snug">{alert.message}</p>
            <p className="text-[10px] opacity-60 mt-1 uppercase tracking-wider font-bold">
              {new Date(alert.timestamp * 1000).toLocaleTimeString()}
            </p>
          </div>
          <button 
            className="shrink-0 w-6 h-6 flex items-center justify-center rounded-full hover:bg-white/10 transition-colors text-lg leading-none opacity-70 hover:opacity-100" 
            onClick={() => handleDismiss(alert.timestamp)}
            aria-label="Dismiss alert"
          >
            ×
          </button>
        </div>
      ))}
    </div>
  );
}
