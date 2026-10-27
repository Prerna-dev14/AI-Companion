import React from "react";
import { Cpu, ShieldCheck, Layers, X, Camera, Sun } from "lucide-react";
import type { EmotionalState, VisionSignalResponse } from "../types";
import { formatPercentage, getEmotionColor } from "../utils/formatters";

interface TelemetryDrawerProps {
  emotionalState: EmotionalState;
  onClose: () => void;
  lastVisionSignal?: VisionSignalResponse | null;
}

export const TelemetryDrawer: React.FC<TelemetryDrawerProps> = ({
  emotionalState,
  onClose,
  lastVisionSignal,
}) => {
  return (
    <aside className="w-80 border-l border-slate-800 bg-slate-950/70 backdrop-blur-xl p-5 flex flex-col justify-between overflow-y-auto">
      <div>
        {/* Drawer Header */}
        <div className="flex items-center justify-between pb-4 border-b border-slate-800">
          <div className="flex items-center space-x-2">
            <Cpu className="w-4 h-4 text-indigo-400" />
            <h2 className="text-sm font-semibold text-white">Emotion Telemetry</h2>
          </div>
          <button
            onClick={onClose}
            className="p-1 rounded-lg hover:bg-slate-800 text-slate-400 hover:text-white"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Emotion Engine Independence Architecture Note */}
        <div className="mt-4 p-3 rounded-xl bg-indigo-950/30 border border-indigo-500/20 text-[11px] text-slate-300">
          <div className="flex items-center space-x-1.5 font-semibold text-indigo-300 mb-1">
            <Layers className="w-3.5 h-3.5" />
            <span>Emotion Engine Independence</span>
          </div>
          Signals are derived per modality, fused by the independent Emotion Engine, and passed as controlled context to the RLPI layer.
        </div>

        {/* Dominant Emotion Card */}
        <div className="mt-4 p-4 rounded-xl glass-card border border-slate-800">
          <span className="text-[10px] uppercase font-bold text-slate-400 tracking-wider">
            Dominant State
          </span>
          <div className="mt-2 flex items-center justify-between">
            <span
              className={`text-base font-bold capitalize px-3 py-1 rounded-lg border ${getEmotionColor(
                emotionalState.dominant_emotion
              )}`}
            >
              {emotionalState.dominant_emotion}
            </span>
            <span className="text-xs font-mono text-slate-300">
              {formatPercentage(emotionalState.confidence)} Conf.
            </span>
          </div>

          {/* Confidence Bar */}
          <div className="mt-3">
            <div className="flex justify-between text-[10px] text-slate-400 mb-1 font-mono">
              <span>Confidence</span>
              <span>{formatPercentage(emotionalState.confidence)}</span>
            </div>
            <div className="w-full h-1.5 rounded-full bg-slate-800 overflow-hidden">
              <div
                className="h-full bg-gradient-to-r from-indigo-500 to-cyan-400 rounded-full transition-all duration-500"
                style={{ width: `${emotionalState.confidence * 100}%` }}
              />
            </div>
          </div>

          {/* Intensity Meter */}
          <div className="mt-3">
            <div className="flex justify-between text-[10px] text-slate-400 mb-1 font-mono">
              <span>Intensity</span>
              <span>{formatPercentage(emotionalState.intensity)}</span>
            </div>
            <div className="w-full h-1.5 rounded-full bg-slate-800 overflow-hidden">
              <div
                className="h-full bg-gradient-to-r from-cyan-500 to-emerald-400 rounded-full transition-all duration-500"
                style={{ width: `${emotionalState.intensity * 100}%` }}
              />
            </div>
          </div>

          {/* Uncertainty Meter */}
          <div className="mt-3">
            <div className="flex justify-between text-[10px] text-slate-400 mb-1 font-mono">
              <span>Uncertainty</span>
              <span>{formatPercentage(emotionalState.uncertainty)}</span>
            </div>
            <div className="w-full h-1.5 rounded-full bg-slate-800 overflow-hidden">
              <div
                className="h-full bg-gradient-to-r from-amber-500 to-rose-500 rounded-full transition-all duration-500"
                style={{ width: `${emotionalState.uncertainty * 100}%` }}
              />
            </div>
          </div>
        </div>

        {/* Phase 4 Computer Vision Derived Signals Card */}
        {lastVisionSignal && (
          <div className="mt-4 p-3.5 rounded-xl bg-slate-900/60 border border-slate-800 text-xs">
            <div className="flex items-center justify-between font-semibold text-slate-200 mb-2">
              <span className="flex items-center space-x-1.5">
                <Camera className="w-3.5 h-3.5 text-cyan-400" />
                <span>Facial Vision Signals</span>
              </span>
              <span
                className={`text-[9px] uppercase px-1.5 py-0.2 rounded font-bold ${
                  lastVisionSignal.face_detected
                    ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/30"
                    : "bg-amber-500/10 text-amber-400 border border-amber-500/30"
                }`}
              >
                {lastVisionSignal.status}
              </span>
            </div>

            <div className="space-y-1.5 text-[11px] text-slate-400">
              <div className="flex justify-between">
                <span>Face Presence:</span>
                <span className="text-slate-200 font-medium">
                  {lastVisionSignal.face_detected
                    ? `Detected (${lastVisionSignal.face_count} face)`
                    : "No face detected"}
                </span>
              </div>
              <div className="flex justify-between items-center">
                <span className="flex items-center space-x-1">
                  <Sun className="w-3 h-3 text-amber-400" />
                  <span>Lighting Quality:</span>
                </span>
                <span className="text-slate-200 font-mono">
                  {Math.round(lastVisionSignal.lighting_score * 100)}%
                </span>
              </div>

              {lastVisionSignal.facial_features && (
                <div className="pt-1.5 border-t border-slate-800 grid grid-cols-2 gap-1 text-[10px] font-mono text-slate-300">
                  <div>
                    Smile: {Math.round((lastVisionSignal.facial_features.smile_ratio || 0) * 100)}%
                  </div>
                  <div>
                    Eyes: {Math.round((lastVisionSignal.facial_features.eye_openness || 0) * 100)}%
                  </div>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Modality Provenance */}
        <div className="mt-5">
          <h3 className="text-xs font-semibold text-slate-300 mb-2.5">Active Signal Sources</h3>
          <div className="space-y-2">
            {[
              { id: "text", name: "Text Sentiment & Intent", enabled: emotionalState.sources.includes("text") },
              { id: "voice", name: "Voice Acoustic Prosody", enabled: emotionalState.sources.includes("voice") },
              { id: "face", name: "Facial Expression Vision", enabled: emotionalState.sources.includes("face") },
            ].map((source) => (
              <div
                key={source.id}
                className="flex items-center justify-between px-3 py-2 rounded-lg bg-slate-900/60 border border-slate-800 text-xs"
              >
                <span className="text-slate-300">{source.name}</span>
                <span
                  className={`text-[10px] font-semibold px-2 py-0.5 rounded ${
                    source.enabled
                      ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20"
                      : "bg-slate-800 text-slate-500"
                  }`}
                >
                  {source.enabled ? "Active" : "Inactive"}
                </span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Safety Policy Reminder */}
      <div className="mt-6 pt-4 border-t border-slate-800 text-[11px] text-slate-400 flex items-start space-x-2">
        <ShieldCheck className="w-4 h-4 text-emerald-400 flex-shrink-0 mt-0.5" />
        <p>
          AI Companion is not a diagnostic tool. Inferred emotion states are probabilistic guides for conversational tone adaptation.
        </p>
      </div>
    </aside>
  );
};
