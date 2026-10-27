import { useState, useEffect, useCallback } from "react";
import type { HealthStatus } from "../types";
import { api } from "../services/api";

export function useHealth(pollIntervalMs: number = 10000) {
  const [health, setHealth] = useState<HealthStatus>({
    status: "connecting",
    app_name: "AI Companion",
    version: "...",
    environment: "...",
    timestamp: new Date().toISOString(),
    database: { connected: false, dialect: "checking..." },
    services: {},
  });
  const [isRefreshing, setIsRefreshing] = useState<boolean>(false);

  const fetchHealth = useCallback(async () => {
    setIsRefreshing(true);
    try {
      const data = await api.checkHealth();
      setHealth(data);
    } finally {
      setIsRefreshing(false);
    }
  }, []);

  useEffect(() => {
    fetchHealth();
    const interval = setInterval(fetchHealth, pollIntervalMs);
    return () => clearInterval(interval);
  }, [fetchHealth, pollIntervalMs]);

  return { health, isRefreshing, refetch: fetchHealth };
}
