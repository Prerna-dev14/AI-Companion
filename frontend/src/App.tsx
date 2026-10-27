import React, { useState } from "react";
import { Header } from "./components/Header";
import { ModalityControls } from "./components/ModalityControls";
import { CompanionAvatar } from "./components/CompanionAvatar";
import { ChatArea } from "./components/ChatArea";
import { TelemetryDrawer } from "./components/TelemetryDrawer";
import { CameraPreview } from "./components/CameraPreview";
import { SettingsModal } from "./components/SettingsModal";
import { useHealth } from "./hooks/useHealth";
import { useSpeech } from "./hooks/useSpeech";
import { useVision } from "./hooks/useVision";
import { api } from "./services/api";
import type {
  Message,
  EmotionalState,
  UserPreferences,
} from "./types";

export const App: React.FC = () => {
  const { health, isRefreshing, refetch } = useHealth();
  const [showTelemetry, setShowTelemetry] = useState(false);
  const [showSettings, setShowSettings] = useState(false);
  const [isGenerating, setIsGenerating] = useState(false);
  const [sessionId, setSessionId] = useState<string | null>(null);

  // User preferences
  const [preferences, setPreferences] = useState<UserPreferences>({
    language: "en",
    voiceAutoPlay: true,
    cameraAnalysisEnabled: true,
    microphoneAnalysisEnabled: true,
    longTermMemoryEnabled: false,
    emotionStorageEnabled: false,
  });

  // Speech custom hook (Phase 3)
  const {
    micStatus,
    isRecording,
    isSpeaking,
    speechError,
    requestPermission: requestMicPermission,
    startRecording,
    stopRecording,
    speakText,
  } = useSpeech(preferences.language);

  // Vision custom hook (Phase 4)
  const {
    cameraStatus,
    videoRef,
    lastSignal: lastVisionSignal,
    isAnalyzing: isAnalyzingVision,
    toggleCamera,
    stopCamera,
  } = useVision();

  // Normalized emotional state
  const isCameraActive = cameraStatus.active && cameraStatus.permission === "granted";
  const [emotionalState, setEmotionalState] = useState<EmotionalState>({
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
    sources: ["text", "voice", "face"],
    timestamp: new Date().toISOString(),
    modality_status: {
      text: true,
      voice: micStatus.permission === "granted",
      face: isCameraActive,
    },
    uncertainty: 0.12,
  });

  // Welcome announcement message
  const [messages, setMessages] = useState<Message[]>([
    {
      id: "welcome-phase-4",
      role: "assistant",
      content:
        "Hello! I am your AI Companion. Phase 4 — Computer Vision Signals is active.\n\n" +
        "• Camera Vision Signals: Click 'Camera' to enable optional, permission-gated face detection and lighting analysis.\n" +
        "• Privacy Assurance: Frames are processed strictly in-memory and discarded immediately. No raw frames or face biometric identities are stored.\n" +
        "• Resilient Fallback: If camera access is denied or lighting is poor, conversation continues seamlessly in text and voice.",
      timestamp: new Date().toISOString(),
      emotional_state: {
        dominant_emotion: "neutral",
        confidence: 0.9,
      },
    },
  ]);

  // Handle sending a message
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

      // If voiceAutoPlay is enabled, speak the reply aloud
      if (preferences.voiceAutoPlay) {
        speakText(response.message.content);
      }
    } catch (error) {
      console.error("Chat error:", error);
      const errorMsg: Message = {
        id: `err-${Date.now()}`,
        role: "assistant",
        content:
          "I apologize, but I had trouble processing that response. Text fallback is active.",
        timestamp: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, errorMsg]);
    } finally {
      setIsGenerating(false);
    }
  };

  const handleToggleMic = async () => {
    if (micStatus.permission !== "granted") {
      const granted = await requestMicPermission();
      if (granted) {
        setEmotionalState((prev) => ({
          ...prev,
          modality_status: { ...prev.modality_status, voice: true },
        }));
      }
    } else if (isRecording) {
      stopRecording();
    } else {
      startRecording((text) => {
        if (text) {
          handleSendMessage(text);
        }
      });
    }
  };

  const handleToggleCamera = () => {
    toggleCamera();
    setEmotionalState((prev) => ({
      ...prev,
      modality_status: { ...prev.modality_status, face: !cameraStatus.active },
    }));
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
      <div className="flex-1 flex overflow-hidden relative">
        {/* Central Companion & Chat Layout */}
        <div className="flex-1 flex flex-col h-full overflow-hidden">
          {/* Top Modality Controls Bar */}
          <div className="px-4 py-2.5 bg-slate-950/40 border-b border-slate-900">
            <ModalityControls
              micStatus={micStatus}
              cameraStatus={cameraStatus}
              onToggleMic={handleToggleMic}
              onToggleCamera={handleToggleCamera}
              isRecording={isRecording}
            />
          </div>

          {/* Interactive Companion Avatar Stage */}
          <div className="bg-gradient-to-b from-indigo-950/20 via-slate-950/20 to-transparent border-b border-slate-900/60">
            <CompanionAvatar
              emotion={emotionalState.dominant_emotion}
              intensity={emotionalState.intensity}
              isThinking={isGenerating || isSpeaking}
            />
          </div>

          {/* Chat Conversation Area */}
          <ChatArea
            messages={messages}
            onSendMessage={handleSendMessage}
            isGenerating={isGenerating}
            activeEmotion={emotionalState}
            onSpeakMessage={speakText}
            isSpeaking={isSpeaking}
            isRecording={isRecording}
            onStartVoiceInput={() =>
              startRecording((text) => {
                if (text) handleSendMessage(text);
              })
            }
            onStopVoiceInput={stopRecording}
            speechError={speechError}
          />
        </div>

        {/* Emotion Telemetry Inspector Drawer */}
        {showTelemetry && (
          <TelemetryDrawer
            emotionalState={emotionalState}
            onClose={() => setShowTelemetry(false)}
            lastVisionSignal={lastVisionSignal}
          />
        )}

        {/* Floating In-Memory Camera Preview (Phase 4) */}
        <CameraPreview
          videoRef={videoRef}
          isActive={cameraStatus.active}
          onClose={stopCamera}
          lastSignal={lastVisionSignal}
          isAnalyzing={isAnalyzingVision}
        />
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
