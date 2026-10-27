import React, { useState } from "react";
import { Header } from "./components/Header";
import { ModalityControls } from "./components/ModalityControls";
import { CompanionAvatar } from "./components/CompanionAvatar";
import { ChatArea } from "./components/ChatArea";
import { TelemetryDrawer } from "./components/TelemetryDrawer";
import { SettingsModal } from "./components/SettingsModal";
import { useHealth } from "./hooks/useHealth";
import { api } from "./services/api";
import type {
  Message,
  EmotionalState,
  ModalityStatus,
  UserPreferences,
} from "./types";

export const App: React.FC = () => {
  const { health, isRefreshing, refetch } = useHealth();
  const [showTelemetry, setShowTelemetry] = useState(false);
  const [showSettings, setShowSettings] = useState(false);
  const [isGenerating, setIsGenerating] = useState(false);
  const [sessionId, setSessionId] = useState<string | null>(null);

  // Initial emotional state (baseline neutral)
  const [emotionalState] = useState<EmotionalState>({
    dominant_emotion: "neutral",
    probabilities: {
      neutral: 0.85,
      happy: 0.08,
      sad: 0.02,
      angry: 0.01,
      bored: 0.03,
      surprised: 0.01,
      confused: 0.0,
    },
    confidence: 0.88,
    intensity: 0.45,
    sources: ["text"],
    timestamp: new Date().toISOString(),
    modality_status: {
      text: true,
      voice: false,
      face: false,
    },
    uncertainty: 0.12,
  });

  // Modality permission & active states
  const [micStatus, setMicStatus] = useState<ModalityStatus>({
    available: true,
    active: false,
    permission: "prompt",
  });

  const [cameraStatus, setCameraStatus] = useState<ModalityStatus>({
    available: true,
    active: false,
    permission: "prompt",
  });

  // User preferences & consents
  const [preferences, setPreferences] = useState<UserPreferences>({
    language: "en",
    voiceAutoPlay: false,
    cameraAnalysisEnabled: false,
    microphoneAnalysisEnabled: false,
    longTermMemoryEnabled: false,
    emotionStorageEnabled: false,
  });

  // Conversation messages
  const [messages, setMessages] = useState<Message[]>([
    {
      id: "welcome-phase-2",
      role: "assistant",
      content:
        "Hello! I am your AI Companion. Phase 2 — Basic Conversation & RLPI is active.\n\n" +
        "You can chat with me naturally. Every message is processed through our server-side RLPI layer with persistent session history, while keeping your privacy safe.",
      timestamp: new Date().toISOString(),
      emotional_state: {
        dominant_emotion: "neutral",
        confidence: 0.9,
      },
    },
  ]);

  // Handle sending a live message to the backend
  const handleSendMessage = async (text: string) => {
    const tempUserId = `user-${Date.now()}`;
    const userMsg: Message = {
      id: tempUserId,
      role: "user",
      content: text,
      timestamp: new Date().toISOString(),
    };

    setMessages((prev) => [...prev, userMsg]);
    setIsGenerating(true);

    try {
      // Call live backend /api/chat endpoint
      const response = await api.sendMessage(text, sessionId || undefined);

      if (response.session_id) {
        setSessionId(response.session_id);
      }

      const assistantMsg: Message = {
        id: response.message.id || `assistant-${Date.now()}`,
        role: "assistant",
        content: response.message.content,
        timestamp: response.created_at || new Date().toISOString(),
        emotional_state: {
          dominant_emotion: emotionalState.dominant_emotion,
          confidence: emotionalState.confidence,
        },
        metadata_payload: {
          response_strategy: response.response_strategy,
          model_name: response.model_name,
        },
      };

      setMessages((prev) => [...prev, assistantMsg]);
    } catch (error) {
      console.error("Chat error:", error);
      const errorMsg: Message = {
        id: `err-${Date.now()}`,
        role: "assistant",
        content:
          "I apologize, but I had trouble processing that response. " +
          "Please check that the backend is running and try again.",
        timestamp: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, errorMsg]);
    } finally {
      setIsGenerating(false);
    }
  };

  const handleToggleMic = () => {
    if (micStatus.permission === "prompt") {
      setMicStatus({
        available: true,
        active: true,
        permission: "granted",
      });
      setPreferences((p) => ({ ...p, microphoneAnalysisEnabled: true }));
    } else {
      setMicStatus((m) => ({ ...m, active: !m.active }));
    }
  };

  const handleToggleCamera = () => {
    if (cameraStatus.permission === "prompt") {
      setCameraStatus({
        available: true,
        active: true,
        permission: "granted",
      });
      setPreferences((p) => ({ ...p, cameraAnalysisEnabled: true }));
    } else {
      setCameraStatus((c) => ({ ...c, active: !c.active }));
    }
  };

  const handleClearSession = async () => {
    setMessages([]);
    setSessionId(null);
    try {
      const newSession = await api.createSession("New Conversation");
      setSessionId(newSession.id);
    } catch (e) {
      console.error("Session reset error:", e);
    }
  };

  return (
    <div className="flex flex-col h-screen bg-[#0b0f19] text-slate-100 font-sans overflow-hidden">
      {/* Top Application Header */}
      <Header
        health={health}
        isRefreshing={isRefreshing}
        onRefreshHealth={refetch}
        onOpenSettings={() => setShowSettings(true)}
        onToggleTelemetry={() => setShowTelemetry((v) => !v)}
        showTelemetry={showTelemetry}
      />

      {/* Main Workspace Area */}
      <div className="flex-1 flex overflow-hidden">
        {/* Central Companion & Chat Layout */}
        <div className="flex-1 flex flex-col h-full overflow-hidden">
          {/* Top Modality Controls Bar */}
          <div className="px-4 py-2.5 bg-slate-950/40 border-b border-slate-900">
            <ModalityControls
              micStatus={micStatus}
              cameraStatus={cameraStatus}
              onToggleMic={handleToggleMic}
              onToggleCamera={handleToggleCamera}
            />
          </div>

          {/* Interactive Companion Avatar Stage */}
          <div className="bg-gradient-to-b from-indigo-950/20 via-slate-950/20 to-transparent border-b border-slate-900/60">
            <CompanionAvatar
              emotion={emotionalState.dominant_emotion}
              intensity={emotionalState.intensity}
              isThinking={isGenerating}
            />
          </div>

          {/* Chat Conversation Area */}
          <ChatArea
            messages={messages}
            onSendMessage={handleSendMessage}
            isGenerating={isGenerating}
            activeEmotion={emotionalState}
          />
        </div>

        {/* Emotion Telemetry Inspector Drawer */}
        {showTelemetry && (
          <TelemetryDrawer
            emotionalState={emotionalState}
            onClose={() => setShowTelemetry(false)}
          />
        )}
      </div>

      {/* Settings Modal */}
      <SettingsModal
        isOpen={showSettings}
        onClose={() => setShowSettings(false)}
        preferences={preferences}
        onUpdatePreferences={(updates) => setPreferences((p) => ({ ...p, ...updates }))}
        onClearSession={handleClearSession}
      />
    </div>
  );
};

export default App;
