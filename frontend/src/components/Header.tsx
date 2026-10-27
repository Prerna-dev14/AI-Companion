import React from "react";
import { Activity, Database, Sparkles, SlidersHorizontal, RefreshCw } from "lucide-react";
import type { HealthStatus } from "../types";

interface HeaderProps {
  health: HealthStatus;
  isRefreshing: boolean;
  onRefreshHealth: () => void;
  onOpenSettings: () => void;
  onToggleTelemetry: () => void;
  showTelemetry: boolean;
}

export const Header: React.FC<HeaderProps> = ({
  health,
  isRefreshing,
  onRefreshHealth,
  onOpenSettings,
  onToggleTelemetry,
  showTelemetry,
}) => {
  const isHealthy = health.status === "ok";
  const isDegraded = health.status === "degraded";

  return (
    <header className="glass-panel sticky top-0 z-40 px-6 py-3.5 border-b border-slate-800/80 flex items-center justify-between">
      {/* Brand & Concept Identity */}
      <div className="flex items-center space-x-3.5">
        <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-indigo-600 via-indigo-500 to-cyan-400 p-[1.5px] shadow-lg shadow-indigo-500/20">
          <div className="w-full h-full bg-slate-950 rounded-[10px] flex items-center justify-center">
            <Sparkles className="w-5 h-5 text-cyan-400 animate-pulse" />
          </div>
        </div>
        <div>
          <div className="flex items-center space-x-2">
            <h1 className="text-lg font-bold tracking-tight text-white flex items-center">
              AI Companion
              <span className="ml-2 text-[10px] uppercase font-semibold px-2 py-0.5 rounded-full bg-indigo-500/20 text-indigo-300 border border-indigo-500/30">
                Phase 1 Foundation
              </span>
            </h1>
          </div>
          <p className="text-xs text-slate-400">Emotion-Aware Multimodal Conversational Platform</p>
        </div>
      </div>

      {/* Connectivity & Diagnostic Badges */}
      <div className="flex items-center space-x-3">
        {/* Backend Connectivity Status */}
        <div
          onClick={onRefreshHealth}
          className={`flex items-center space-x-2 px-3 py-1.5 rounded-lg text-xs font-medium border cursor-pointer transition-all ${
            isHealthy
              ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/30 hover:bg-emerald-500/20"
              : isDegraded
              ? "bg-amber-500/10 text-amber-400 border-amber-500/30 hover:bg-amber-500/20"
              : "bg-rose-500/10 text-rose-400 border-rose-500/30 hover:bg-rose-500/20"
          }`}
          title="Click to re-check backend /api/health"
        >
          <span
            className={`w-2 h-2 rounded-full ${
              isHealthy ? "bg-emerald-400 animate-ping" : isDegraded ? "bg-amber-400" : "bg-rose-500"
            }`}
          />
          <span className="capitalize">{health.status === "ok" ? "Backend Connected" : health.status}</span>
          {health.latencyMs !== undefined && (
            <span className="text-[10px] opacity-75">({health.latencyMs}ms)</span>
          )}
          <RefreshCw className={`w-3 h-3 ml-1 ${isRefreshing ? "animate-spin" : ""}`} />
        </div>

        {/* Database Diagnostic Badge */}
        <div
          className={`hidden md:flex items-center space-x-1.5 px-2.5 py-1.5 rounded-lg text-xs font-medium border ${
            health.database?.connected
              ? "bg-slate-800/80 text-slate-300 border-slate-700"
              : "bg-amber-950/40 text-amber-300 border-amber-700/50"
          }`}
          title={health.database?.details || "Database connection status"}
        >
          <Database className="w-3.5 h-3.5 text-indigo-400" />
          <span className="capitalize">{health.database?.dialect || "DB"}:</span>
          <span className={health.database?.connected ? "text-emerald-400" : "text-amber-400"}>
            {health.database?.connected ? "Ready" : "Disconnected"}
          </span>
        </div>

        {/* Emotion Engine Telemetry Toggle */}
        <button
          onClick={onToggleTelemetry}
          className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-colors border ${
            showTelemetry
              ? "bg-indigo-600/30 text-indigo-200 border-indigo-500/50"
              : "bg-slate-800/80 text-slate-400 border-slate-700 hover:text-white"
          }`}
        >
          <Activity className="w-3.5 h-3.5" />
          <span className="hidden sm:inline">Telemetry</span>
        </button>

        {/* Settings Button */}
        <button
          onClick={onOpenSettings}
          className="p-2 rounded-lg bg-slate-800/80 hover:bg-slate-700 text-slate-300 hover:text-white border border-slate-700 transition-colors"
          title="Privacy & System Settings"
        >
          <SlidersHorizontal className="w-4 h-4" />
        </button>
      </div>
    </header>
  );
};
