import { useState, useEffect } from "react";

/**
 * Custom hook for cycling through loading messages at a specified interval
 * @param messages - Array of messages to cycle through
 * @param interval - Time in milliseconds between message changes (default: 3000ms)
 * @returns Current message to display
 */
export function useDynamicLoadingMessage(
  messages: string[],
  interval: number = 3000
): string {
  const [currentIndex, setCurrentIndex] = useState(0);

  useEffect(() => {
    if (!messages || messages.length === 0) return;

    // Reset index when messages array changes
    setCurrentIndex(0);

    const timer = setInterval(() => {
      setCurrentIndex((prevIndex) => (prevIndex + 1) % messages.length);
    }, interval);

    return () => clearInterval(timer);
  }, [messages, interval]);

  return messages[currentIndex] || messages[0] || "";
}
