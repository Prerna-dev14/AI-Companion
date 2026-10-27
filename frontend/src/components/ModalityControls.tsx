import React from "react";
import { Mic, MicOff, Camera, CameraOff, Shield } from "lucide-react";
import type { ModalityStatus } from "../types";

interface ModalityControlsProps {
  micStatus: ModalityStatus;
  cameraStatus: ModalityStatus;
  onToggleMic: () => void;
  onToggleCamera: () => void;
}

export const ModalityControls: React.FC<ModalityControlsProps> = ({
  micStatus,
  cameraStatus,
  onToggleMic,
  onToggleCamera,
}) => {
  return (
    <div className="glass-card px-4 py-3 rounded-2xl flex flex-wrap items-center justify-between gap-3 border border-slate-800">
      {/* Input Modality Toggles */}
      <div className="flex items-center space-x-3">
        {/* Microphone Control */}
        <div className="flex items-center space-x-2">
          <button
            onClick={onToggleMic}
            className={`flex items-center space-x-2 px-3 py-1.5 rounded-xl text-xs font-medium border transition-all ${
              micStatus.active
                ? "bg-indigo-600 text-white border-indigo-400 shadow-lg shadow-indigo-600/30"
                : "bg-slate-900/80 text-slate-400 border-slate-700/80 hover:border-slate-600 hover:text-slate-200"
            }`}
            title="Speech STT/Prosody (Phase 3)"
          >
            {micStatus.active ? <Mic className="w-4 h-4 text-white" /> : <MicOff className="w-4 h-4" />}
            <span>Microphone</span>
          </button>
          <span
            className={`text-[10px] uppercase font-bold px-1.5 py-0.5 rounded border ${
              micStatus.permission === "granted"
                ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/30"
                : micStatus.permission === "denied"
                ? "bg-rose-500/10 text-rose-400 border-rose-500/30"
                : "bg-slate-800 text-slate-400 border-slate-700"
            }`}
          >
            {micStatus.permission}
          </span>
        </div>

        {/* Camera Control */}
        <div className="flex items-center space-x-2">
          <button
            onClick={onToggleCamera}
            className={`flex items-center space-x-2 px-3 py-1.5 rounded-xl text-xs font-medium border transition-all ${
              cameraStatus.active
                ? "bg-cyan-600 text-white border-cyan-400 shadow-lg shadow-cyan-600/30"
                : "bg-slate-900/80 text-slate-400 border-slate-700/80 hover:border-slate-600 hover:text-slate-200"
            }`}
            title="Facial Signal Analysis (Phase 4)"
          >
            {cameraStatus.active ? <Camera className="w-4 h-4 text-white" /> : <CameraOff className="w-4 h-4" />}
            <span>Camera</span>
          </button>
          <span
            className={`text-[10px] uppercase font-bold px-1.5 py-0.5 rounded border ${
              cameraStatus.permission === "granted"
                ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/30"
                : cameraStatus.permission === "denied"
                ? "bg-rose-500/10 text-rose-400 border-rose-500/30"
                : "bg-slate-800 text-slate-400 border-slate-700"
            }`}
          >
            {cameraStatus.permission}
          </span>
        </div>
      </div>

      {/* Privacy Guarantee Notice */}
      <div className="flex items-center space-x-2 text-xs text-slate-400 bg-slate-950/60 px-3 py-1.5 rounded-xl border border-slate-800">
        <Shield className="w-3.5 h-3.5 text-indigo-400 flex-shrink-0" />
        <span className="hidden sm:inline">
          Explicit permissions required. Derived signals only; raw frames & audio are never retained.
        </span>
        <span className="sm:hidden">Explicit permission required</span>
      </div>
    </div>
  );
};
