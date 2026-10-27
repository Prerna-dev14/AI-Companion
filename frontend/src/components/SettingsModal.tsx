import React, { useState, useEffect } from "react";
import { X, Shield, Globe, Trash2, Brain, Plus, Check, AlertCircle } from "lucide-react";
import type { UserPreferences, MemoryItem, EmotionHistoryResponse } from "../types";
import { api } from "../services/api";

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
  const [memories, setMemories] = useState<MemoryItem[]>([]);
  const [newMemoryContent, setNewMemoryContent] = useState("");
  const [newMemoryCategory, setNewMemoryCategory] = useState("preference");
  const [isAddingMemory, setIsAddingMemory] = useState(false);
  const [emotionCount, setEmotionCount] = useState<number>(0);
  const [feedbackMsg, setFeedbackMsg] = useState<{ type: "success" | "error"; text: string } | null>(null);

  // Load memories and emotion history when modal opens
  useEffect(() => {
    if (isOpen) {
      loadMemories();
      loadEmotionStats();
    }
  }, [isOpen]);

  const showFeedback = (text: string, type: "success" | "error" = "success") => {
    setFeedbackMsg({ text, type });
    setTimeout(() => setFeedbackMsg(null), 3000);
  };

  const loadMemories = async () => {
    try {
      const items = await api.getMemories();
      setMemories(items);
    } catch (e) {
      console.warn("Failed to load memories:", e);
    }
  };

  const loadEmotionStats = async () => {
    try {
      const history: EmotionHistoryResponse = await api.getEmotionHistory(undefined, 1);
      setEmotionCount(history.total);
    } catch (e) {
      console.warn("Failed to load emotion stats:", e);
    }
  };

  const handleToggleConsent = async (scope: "long_term_memory" | "emotion_storage", checked: boolean) => {
    try {
      await api.updateConsent(scope, checked);
      if (scope === "long_term_memory") {
        onUpdatePreferences({ longTermMemoryEnabled: checked });
        if (checked) {
          loadMemories();
        }
      } else {
        onUpdatePreferences({ emotionStorageEnabled: checked });
      }
      showFeedback(`Consent for ${scope.replace(/_/g, " ")} updated to ${checked ? "granted" : "revoked"}`);
    } catch (e) {
      showFeedback((e as Error).message, "error");
    }
  };

  const handleAddMemory = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newMemoryContent.trim()) return;

    if (!preferences.longTermMemoryEnabled) {
      showFeedback("Cannot store memories without active long_term_memory consent.", "error");
      return;
    }

    try {
      setIsAddingMemory(true);
      const created = await api.createMemory(newMemoryContent.trim(), newMemoryCategory);
      setMemories((prev) => [created, ...prev]);
      setNewMemoryContent("");
      showFeedback("Memory item remembered successfully.");
    } catch (e) {
      showFeedback((e as Error).message, "error");
    } finally {
      setIsAddingMemory(false);
    }
  };

  const handleDeleteMemory = async (id: string) => {
    try {
      await api.deleteMemory(id);
      setMemories((prev) => prev.filter((m) => m.id !== id));
      showFeedback("Memory item deleted.");
    } catch (e) {
      showFeedback("Failed to delete memory item.", "error");
    }
  };

  const handleClearAllMemories = async () => {
    if (!confirm("Are you sure you want to permanently erase all remembered facts? (Right to be Forgotten)")) {
      return;
    }
    try {
      await api.clearAllMemories();
      setMemories([]);
      showFeedback("All long-term memories have been purged.");
    } catch (e) {
      showFeedback("Failed to clear memories.", "error");
    }
  };

  const handleClearEmotionHistory = async () => {
    if (!confirm("Clear all recorded emotion events from server history?")) {
      return;
    }
    try {
      await api.clearEmotionHistory();
      setEmotionCount(0);
      showFeedback("Emotion event history cleared.");
    } catch (e) {
      showFeedback("Failed to clear emotion history.", "error");
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm animate-fade-in">
      <div className="w-full max-w-xl rounded-2xl glass-panel border border-slate-700 shadow-2xl overflow-hidden flex flex-col max-h-[85vh]">
        {/* Modal Header */}
        <div className="px-6 py-4 border-b border-slate-800 flex items-center justify-between bg-slate-900/40">
          <div className="flex items-center space-x-2.5">
            <Shield className="w-5 h-5 text-indigo-400" />
            <div>
              <h2 className="text-base font-semibold text-white">Privacy & Companion Settings</h2>
              <p className="text-xs text-slate-400">Phase 8 — Consent-Gated Memory & History</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg hover:bg-slate-800 text-slate-400 hover:text-white transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Feedback Alert */}
        {feedbackMsg && (
          <div
            className={`px-6 py-2.5 text-xs flex items-center space-x-2 ${
              feedbackMsg.type === "success"
                ? "bg-emerald-500/10 text-emerald-400 border-b border-emerald-500/20"
                : "bg-rose-500/10 text-rose-400 border-b border-rose-500/20"
            }`}
          >
            {feedbackMsg.type === "success" ? <Check className="w-3.5 h-3.5" /> : <AlertCircle className="w-3.5 h-3.5" />}
            <span>{feedbackMsg.text}</span>
          </div>
        )}

        {/* Modal Body */}
        <div className="p-6 space-y-6 overflow-y-auto flex-1">
          {/* Modality Permissions */}
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

          {/* Consent Toggles */}
          <div>
            <h3 className="text-xs uppercase font-bold text-slate-400 tracking-wider mb-3">
              Data Privacy & Consent Controls
            </h3>
            <div className="space-y-3">
              <label className="flex items-center justify-between p-3.5 rounded-xl bg-slate-900/60 border border-slate-800 cursor-pointer hover:border-slate-700">
                <div>
                  <div className="flex items-center space-x-2">
                    <Brain className="w-4 h-4 text-indigo-400" />
                    <span className="text-sm font-medium text-white">Long-Term Memory Persistence</span>
                  </div>
                  <span className="text-xs text-slate-400 block mt-1">
                    Allows companion to retain preferences and context across sessions. When disabled, fact creation is strictly blocked (HTTP 403).
                  </span>
                </div>
                <input
                  type="checkbox"
                  checked={preferences.longTermMemoryEnabled}
                  onChange={(e) => handleToggleConsent("long_term_memory", e.target.checked)}
                  className="w-4 h-4 rounded text-indigo-600 focus:ring-indigo-500 bg-slate-950 border-slate-700"
                />
              </label>

              <label className="flex items-center justify-between p-3.5 rounded-xl bg-slate-900/60 border border-slate-800 cursor-pointer hover:border-slate-700">
                <div>
                  <span className="text-sm font-medium text-white block">Emotion Event History Logging</span>
                  <span className="text-xs text-slate-400 block mt-0.5">
                    Persist fused emotional telemetry in PostgreSQL for longitudinal attunement.
                  </span>
                </div>
                <input
                  type="checkbox"
                  checked={preferences.emotionStorageEnabled}
                  onChange={(e) => handleToggleConsent("emotion_storage", e.target.checked)}
                  className="w-4 h-4 rounded text-indigo-600 focus:ring-indigo-500 bg-slate-950 border-slate-700"
                />
              </label>
            </div>
          </div>

          {/* Remembered Facts (Consent-Gated Long-Term Memory) */}
          <div>
            <div className="flex items-center justify-between mb-2">
              <h3 className="text-xs uppercase font-bold text-slate-400 tracking-wider flex items-center space-x-1.5">
                <Brain className="w-3.5 h-3.5 text-indigo-400" />
                <span>Remembered Facts ({memories.length})</span>
              </h3>
              {memories.length > 0 && (
                <button
                  onClick={handleClearAllMemories}
                  className="text-xs text-rose-400 hover:text-rose-300 font-medium transition-colors"
                >
                  Clear All
                </button>
              )}
            </div>

            {/* List of active memories */}
            <div className="space-y-2 mb-3 max-h-40 overflow-y-auto">
              {memories.length === 0 ? (
                <div className="p-3 rounded-xl bg-slate-900/40 border border-slate-800 text-xs text-slate-500 text-center">
                  {preferences.longTermMemoryEnabled
                    ? "No remembered facts stored yet. Add one below or converse with the companion."
                    : "Long-term memory is currently disabled. Grant consent above to activate."}
                </div>
              ) : (
                memories.map((m) => (
                  <div
                    key={m.id}
                    className="p-2.5 rounded-xl bg-slate-900/70 border border-slate-800 flex items-center justify-between space-x-3 text-xs"
                  >
                    <div className="flex-1 truncate">
                      <span className="px-1.5 py-0.5 rounded bg-indigo-500/20 text-indigo-300 font-mono text-[10px] uppercase mr-2">
                        {m.category}
                      </span>
                      <span className="text-slate-200">{m.content}</span>
                    </div>
                    <button
                      onClick={() => handleDeleteMemory(m.id)}
                      className="p-1 rounded text-slate-500 hover:text-rose-400 hover:bg-rose-500/10 transition-colors"
                      title="Delete memory item"
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                    </button>
                  </div>
                ))
              )}
            </div>

            {/* Add memory input */}
            {preferences.longTermMemoryEnabled && (
              <form onSubmit={handleAddMemory} className="flex space-x-2">
                <input
                  type="text"
                  placeholder="e.g., Prefers structured explanations; works as bioinformatician..."
                  value={newMemoryContent}
                  onChange={(e) => setNewMemoryContent(e.target.value)}
                  className="flex-1 bg-slate-950 border border-slate-700 text-xs rounded-xl px-3 py-2 text-slate-200 placeholder-slate-500 focus:outline-none focus:border-indigo-500"
                />
                <select
                  value={newMemoryCategory}
                  onChange={(e) => setNewMemoryCategory(e.target.value)}
                  className="bg-slate-950 border border-slate-700 text-xs rounded-xl px-2 py-2 text-slate-300 focus:outline-none focus:border-indigo-500"
                >
                  <option value="preference">Preference</option>
                  <option value="goal">Goal</option>
                  <option value="habit">Habit</option>
                  <option value="general">General</option>
                </select>
                <button
                  type="submit"
                  disabled={isAddingMemory || !newMemoryContent.trim()}
                  className="px-3 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white text-xs font-medium flex items-center space-x-1"
                >
                  <Plus className="w-3.5 h-3.5" />
                  <span>Add</span>
                </button>
              </form>
            )}
          </div>

          {/* Emotion History Governance */}
          <div className="p-3.5 rounded-xl bg-slate-900/60 border border-slate-800 flex items-center justify-between">
            <div>
              <span className="text-sm font-medium text-white block">Emotion Telemetry Events</span>
              <span className="text-xs text-slate-400 block mt-0.5">
                {emotionCount} normalized emotional states logged in history database.
              </span>
            </div>
            {emotionCount > 0 && (
              <button
                onClick={handleClearEmotionHistory}
                className="px-3 py-1.5 rounded-lg border border-slate-700 text-slate-300 hover:text-rose-400 hover:border-rose-500/30 text-xs font-medium transition-colors"
              >
                Clear History
              </button>
            )}
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
