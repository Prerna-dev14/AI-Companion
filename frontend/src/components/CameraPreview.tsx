import React from "react";
import { Camera, X, Eye, AlertTriangle, ShieldCheck, Sun, CheckCircle2 } from "lucide-react";
import type { VisionSignalResponse } from "../types";

interface CameraPreviewProps {
  videoRef: React.RefObject<HTMLVideoElement | null>;
  isActive: boolean;
  onClose: () => void;
  lastSignal: VisionSignalResponse | null;
  isAnalyzing: boolean;
}

export const CameraPreview: React.FC<CameraPreviewProps> = ({
  videoRef,
  isActive,
  onClose,
  lastSignal,
  isAnalyzing,
}) => {
  if (!isActive) return null;

  const faceDetected = lastSignal?.face_detected ?? false;
  const isPoorLighting = lastSignal?.status === "poor_lighting";
  const isMultipleFaces = lastSignal?.status === "multiple_faces";

  return (
    <div className="fixed bottom-20 right-6 z-40 w-72 rounded-2xl glass-panel border border-slate-700/80 shadow-2xl overflow-hidden animate-fade-in select-none">
      {/* Header */}
      <div className="px-3.5 py-2.5 bg-slate-950/80 border-b border-slate-800 flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <Camera className="w-3.5 h-3.5 text-cyan-400" />
          <span className="text-xs font-semibold text-white">Vision Signal Monitor</span>
        </div>
        <button
          onClick={onClose}
          className="p-1 rounded-lg hover:bg-slate-800 text-slate-400 hover:text-white transition-colors"
          title="Turn off camera"
        >
          <X className="w-3.5 h-3.5" />
        </button>
      </div>

      {/* Video Viewport Container */}
      <div className="relative aspect-video bg-slate-950 overflow-hidden flex items-center justify-center">
        <video
          ref={videoRef}
          autoPlay
          playsInline
          muted
          className="w-full h-full object-cover transform scale-x-[-1]"
        />

        {/* Anonymous Face Tracking Reticle Overlay */}
        {faceDetected && (
          <div className="absolute inset-x-12 inset-y-6 border-2 border-cyan-400/60 rounded-xl pointer-events-none animate-pulse">
            <span className="absolute -top-5 left-1 text-[9px] font-bold bg-cyan-950/90 text-cyan-300 px-1.5 py-0.5 rounded border border-cyan-500/40">
              Face Tracked ({Math.round((lastSignal?.confidence || 0.9) * 100)}%)
            </span>
          </div>
        )}

        {/* Analyzing Pulse Pill */}
        {isAnalyzing && (
          <div className="absolute top-2 right-2 px-2 py-0.5 rounded-full bg-cyan-950/80 border border-cyan-500/30 text-[9px] text-cyan-300 flex items-center space-x-1">
            <span className="w-1.5 h-1.5 rounded-full bg-cyan-400 animate-ping" />
            <span>Deriving...</span>
          </div>
        )}
      </div>

      {/* Real-time Diagnostics & Quality Status */}
      <div className="p-3 bg-slate-950/90 space-y-2 text-xs">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-1.5">
            {faceDetected ? (
              <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
            ) : isPoorLighting ? (
              <Sun className="w-3.5 h-3.5 text-amber-400" />
            ) : isMultipleFaces ? (
              <AlertTriangle className="w-3.5 h-3.5 text-amber-400" />
            ) : (
              <Eye className="w-3.5 h-3.5 text-slate-400" />
            )}
            <span className="font-medium text-slate-200">
              {faceDetected
                ? `1 Face Detected`
                : isMultipleFaces
                ? "Multiple Faces"
                : isPoorLighting
                ? "Low Lighting"
                : "No Face in View"}
            </span>
          </div>

          {lastSignal?.lighting_score !== undefined && (
            <span className="text-[10px] text-slate-400 font-mono">
              Light: {Math.round(lastSignal.lighting_score * 100)}%
            </span>
          )}
        </div>

        {/* Expression Features Derived */}
        {lastSignal?.facial_features && (
          <div className="grid grid-cols-2 gap-1.5 pt-1.5 border-t border-slate-800/80 text-[10px] font-mono text-slate-400">
            <div>
              <span>Smile: </span>
              <span className="text-slate-200">
                {Math.round((lastSignal.facial_features.smile_ratio || 0) * 100)}%
              </span>
            </div>
            <div>
              <span>Eyes: </span>
              <span className="text-slate-200">
                {Math.round((lastSignal.facial_features.eye_openness || 0) * 100)}%
              </span>
            </div>
          </div>
        )}

        {/* Privacy Enforcement Notice */}
        <div className="pt-1 flex items-center space-x-1 text-[10px] text-slate-400">
          <ShieldCheck className="w-3 h-3 text-cyan-400 flex-shrink-0" />
          <span>Derived anonymous signals only &bull; Zero frame retention</span>
        </div>
      </div>
    </div>
  );
};
