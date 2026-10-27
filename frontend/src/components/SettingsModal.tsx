import React from "react";
import { X, Shield, Globe, Trash2 } from "lucide-react";
import type { UserPreferences } from "../types";

interface SettingsModalProps {
  isOpen: boolean;
  onClose: () => void;
  preferences: UserPreferences;
  onUpdatePreferences: (updates: Partial<UserPreferences>) => void;
  onClearSession: () => void;
}

export const SettingsModal: React.FC<SettingsModalProps> = ({
  isOpen,
  onClose,
  preferences,
  onUpdatePreferences,
  onClearSession,
}) => {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm animate-fade-in">
      <div className="w-full max-w-lg rounded-2xl glass-panel border border-slate-700 shadow-2xl overflow-hidden">
        {/* Modal Header */}
        <div className="px-6 py-4 border-b border-slate-800 flex items-center justify-between">
          <div className="flex items-center space-x-2.5">
            <Shield className="w-5 h-5 text-indigo-400" />
            <h2 className="text-base font-semibold text-white">Privacy & Companion Settings</h2>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg hover:bg-slate-800 text-slate-400 hover:text-white transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Modal Body */}
        <div className="p-6 space-y-6 max-h-[75vh] overflow-y-auto">
          {/* Privacy & Media Permissions */}
          <div>
            <h3 className="text-xs uppercase font-bold text-slate-400 tracking-wider mb-3">
              Modality Permissions
            </h3>
            <div className="space-y-3">
              <label className="flex items-center justify-between p-3.5 rounded-xl bg-slate-900/60 border border-slate-800 cursor-pointer hover:border-slate-700">
                <div>
                  <span className="text-sm font-medium text-white block">Microphone Analysis</span>
                  <span className="text-xs text-slate-400 block mt-0.5">
                    Process voice for STT & prosodic tone estimation. Raw audio is never stored.
                  </span>
                </div>
                <input
                  type="checkbox"
                  checked={preferences.microphoneAnalysisEnabled}
                  onChange={(e) =>
                    onUpdatePreferences({ microphoneAnalysisEnabled: e.target.checked })
                  }
                  className="w-4 h-4 rounded text-indigo-600 focus:ring-indigo-500 bg-slate-950 border-slate-700"
                />
              </label>

              <label className="flex items-center justify-between p-3.5 rounded-xl bg-slate-900/60 border border-slate-800 cursor-pointer hover:border-slate-700">
                <div>
                  <span className="text-sm font-medium text-white block">Camera Facial Signals</span>
                  <span className="text-xs text-slate-400 block mt-0.5">
                    Derive visual facial expressions on-device. No raw frames are saved or transmitted.
                  </span>
                </div>
                <input
                  type="checkbox"
                  checked={preferences.cameraAnalysisEnabled}
                  onChange={(e) =>
                    onUpdatePreferences({ cameraAnalysisEnabled: e.target.checked })
                  }
                  className="w-4 h-4 rounded text-indigo-600 focus:ring-indigo-500 bg-slate-950 border-slate-700"
                />
              </label>
            </div>
          </div>

          {/* Long-Term Memory Controls */}
          <div>
            <h3 className="text-xs uppercase font-bold text-slate-400 tracking-wider mb-3">
              Memory & Data Governance
            </h3>
            <div className="space-y-3">
              <label className="flex items-center justify-between p-3.5 rounded-xl bg-slate-900/60 border border-slate-800 cursor-pointer hover:border-slate-700">
                <div>
                  <span className="text-sm font-medium text-white block">Permission-Controlled Long-Term Memory</span>
                  <span className="text-xs text-slate-400 block mt-0.5">
                    Allow companion to recall preferences across sessions. Disable for ephemeral sessions.
                  </span>
                </div>
                <input
                  type="checkbox"
                  checked={preferences.longTermMemoryEnabled}
                  onChange={(e) =>
                    onUpdatePreferences({ longTermMemoryEnabled: e.target.checked })
                  }
                  className="w-4 h-4 rounded text-indigo-600 focus:ring-indigo-500 bg-slate-950 border-slate-700"
                />
              </label>

              <label className="flex items-center justify-between p-3.5 rounded-xl bg-slate-900/60 border border-slate-800 cursor-pointer hover:border-slate-700">
                <div>
                  <span className="text-sm font-medium text-white block">Emotion Event History</span>
                  <span className="text-xs text-slate-400 block mt-0.5">
                    Retain normalized emotion metrics for trend analysis.
                  </span>
                </div>
                <input
                  type="checkbox"
                  checked={preferences.emotionStorageEnabled}
                  onChange={(e) =>
                    onUpdatePreferences({ emotionStorageEnabled: e.target.checked })
                  }
                  className="w-4 h-4 rounded text-indigo-600 focus:ring-indigo-500 bg-slate-950 border-slate-700"
                />
              </label>
            </div>
          </div>

          {/* Language Selection */}
          <div>
            <h3 className="text-xs uppercase font-bold text-slate-400 tracking-wider mb-3">
              Language & Accessibility
            </h3>
            <div className="flex items-center justify-between p-3.5 rounded-xl bg-slate-900/60 border border-slate-800">
              <div className="flex items-center space-x-2">
                <Globe className="w-4 h-4 text-indigo-400" />
                <span className="text-sm font-medium text-white">Interface Language</span>
              </div>
              <select
                value={preferences.language}
                onChange={(e) => onUpdatePreferences({ language: e.target.value })}
                className="bg-slate-950 border border-slate-700 text-xs rounded-lg px-2.5 py-1.5 text-slate-200 focus:outline-none focus:border-indigo-500"
              >
                <option value="en">English (US)</option>
                <option value="es">Español</option>
                <option value="fr">Français</option>
                <option value="de">Deutsch</option>
                <option value="ja">日本語</option>
              </select>
            </div>
          </div>

          {/* Danger Zone */}
          <div className="pt-2">
            <button
              onClick={() => {
                if (confirm("Reset current session messages?")) {
                  onClearSession();
                  onClose();
                }
              }}
              className="w-full flex items-center justify-center space-x-2 px-4 py-2.5 rounded-xl border border-rose-500/30 text-rose-400 hover:bg-rose-500/10 text-xs font-semibold transition-colors"
            >
              <Trash2 className="w-4 h-4" />
              <span>Clear Current Session Data</span>
            </button>
          </div>
        </div>

        {/* Modal Footer */}
        <div className="px-6 py-3.5 bg-slate-950/80 border-t border-slate-800 flex justify-end">
          <button
            onClick={onClose}
            className="px-4 py-1.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-medium transition-colors"
          >
            Done
          </button>
        </div>
      </div>
    </div>
  );
};
