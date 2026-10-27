import React, { useState, useEffect } from "react";
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
  TextEmotionResponse,
  VoiceEmotionResponse,
  VisionSignalResponse,
} from "./types";

export const App: React.FC = () => {
  const { health, isRefreshing, refetch } = useHealth();
  const [showTelemetry, setShowTelemetry] = useState(false);
  const [showSettings, setShowSettings] = useState(false);
  const [isGenerating, setIsGenerating] = useState(false);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [lastTextSignal, setLastTextSignal] = useState<TextEmotionResponse | null>(null);
  const [activeStrategy, setActiveStrategy] = useState<string>("balanced_conversational");

  // User preferences
  const [preferences, setPreferences] = useState<UserPreferences>({
    language: "en",
    voiceAutoPlay: true,
    cameraAnalysisEnabled: true,
    microphoneAnalysisEnabled: true,
    longTermMemoryEnabled: false,
    emotionStorageEnabled: false,
  });

  // Speech custom hook (Phase 3 & Phase 5 Voice Prosody)
  const {
    micStatus,
    isRecording,
    isSpeaking,
    speechError,
    lastVoiceSignal,
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

  // Normalized emotional state (fused by Emotion Engine)
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
    sources: ["text"],
    timestamp: new Date().toISOString(),
    modality_status: {
      text: true,
      voice: micStatus.permission === "granted",
      face: isCameraActive,
    },
    uncertainty: 0.12,
  });

  // Multimodal Emotion Fusion (Phase 6)
  const fuseSignals = async (
    textSig: TextEmotionResponse | null = lastTextSignal,
    voiceSig: VoiceEmotionResponse | null = lastVoiceSignal,
    faceSig: VisionSignalResponse | null = lastVisionSignal
  ) => {
    if (!textSig && !voiceSig && !faceSig) return;

    try {
      const fused = await api.fuseEmotions({
        text_signal: textSig,
        voice_signal: voiceSig,
        face_signal: faceSig,
        session_id: sessionId,
        previous_state: emotionalState,
        persist: preferences.emotionStorageEnabled,
      });

      setEmotionalState(fused);
    } catch (err) {
      console.warn("Multimodal emotion fusion error:", err);
    }
  };

  // Re-fuse when facial vision signal changes
  useEffect(() => {
    if (lastVisionSignal && isCameraActive) {
      fuseSignals(lastTextSignal, lastVoiceSignal, lastVisionSignal);
    }
  }, [lastVisionSignal, isCameraActive]);

  // Re-fuse when voice prosody signal changes
  useEffect(() => {
    if (lastVoiceSignal) {
      fuseSignals(lastTextSignal, lastVoiceSignal, lastVisionSignal);
    }
  }, [lastVoiceSignal]);

  // Sync user consents on mount (Phase 8)
  useEffect(() => {
    const syncConsents = async () => {
      try {
        const consents = await api.getConsents();
        const ltm = consents.find((c) => c.scope === "long_term_memory");
        const emo = consents.find((c) => c.scope === "emotion_storage");
        setPreferences((prev) => ({
          ...prev,
          longTermMemoryEnabled: ltm ? ltm.granted : prev.longTermMemoryEnabled,
          emotionStorageEnabled: emo ? emo.granted : prev.emotionStorageEnabled,
        }));
      } catch (e) {
        console.warn("Failed to fetch consents on startup:", e);
      }
    };
    syncConsents();
  }, []);

  // Welcome announcement message
  const [messages, setMessages] = useState<Message[]>([
    {
      id: "welcome-phase-9",
      role: "assistant",
      content:
        "Hello! I am your AI Companion. Phase 9 — Security, Privacy & Safety Hardening is active.\n\n" +
        "• High-Risk Safety Circuit Breaker: Immediate, non-clinical crisis grounding and vetted lifeline resources (988 Lifeline, Crisis Text Line 741741) automatically intervene on crisis triggers.\n" +
        "• Rate Limiting & Abuse Defense: In-memory sliding-window request throttling with Retry-After headers safeguards compute-heavy endpoints.\n" +
        "• Audit Logging & Compliance: Security-critical actions (consent grants, memory purges, safety interventions) are recorded to the immutable audit trail visible in Settings.",
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
      // 1. Analyze text sentiment & intent and fuse with active modalities (Phase 7)
      let resolvedTextSig: TextEmotionResponse | null = null;
      try {
        resolvedTextSig = await api.analyzeTextEmotion(text, preferences.language);
        setLastTextSignal(resolvedTextSig);
      } catch (e) {
        console.warn("Text signal analysis failed:", e);
      }

      let stateToUse = emotionalState;
      if (resolvedTextSig || lastVoiceSignal || lastVisionSignal) {
        try {
          const fused = await api.fuseEmotions({
            text_signal: resolvedTextSig,
            voice_signal: lastVoiceSignal,
            face_signal: lastVisionSignal,
            session_id: sessionId,
            previous_state: emotionalState,
            persist: preferences.emotionStorageEnabled,
          });
          setEmotionalState(fused);
          stateToUse = fused;
        } catch (e) {
          console.warn("Pre-chat fusion skipped:", e);
        }
      }

      // 2. Dispatch message to backend RLPI layer guided by normalized emotional state
      const response = await api.sendMessage(text, sessionId || undefined, stateToUse);

      if (response.session_id) {
        setSessionId(response.session_id);
      }

      if (response.response_strategy) {
        setActiveStrategy(response.response_strategy);
      }

      const assistantMsg: Message = {
        id: response.message.id || `assistant-${Date.now()}`,
        role: "assistant",
        content: response.message.content,
        timestamp: response.created_at || new Date().toISOString(),
        emotional_state: {
          dominant_emotion: stateToUse.dominant_emotion,
          confidence: stateToUse.confidence,
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
            lastTextSignal={lastTextSignal}
            lastVoiceSignal={lastVoiceSignal}
            activeStrategy={activeStrategy}
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
