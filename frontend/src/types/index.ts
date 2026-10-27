// Emotion types matching Master Specification Section 6 & 7.6
export type EmotionCategory = 
  | "neutral" 
  | "happy" 
  | "sad" 
  | "angry" 
  | "bored" 
  | "surprised" 
  | "confused";

export type ModalityType = "text" | "voice" | "face";

export interface ModalityStatus {
  available: boolean;
  active: boolean;
  permission: "granted" | "denied" | "prompt" | "unsupported";
  lastSignalTimestamp?: string;
  confidence?: number;
  error?: string;
}

export interface EmotionalState {
  dominant_emotion: EmotionCategory;
  probabilities: Record<EmotionCategory, number>;
  confidence: number; // 0.0 to 1.0
  intensity: number;  // 0.0 to 1.0
  sources: ModalityType[];
  timestamp: string;
  modality_status: Record<ModalityType, boolean>;
  uncertainty: number; // 0.0 to 1.0
}

export interface Message {
  id: string;
  role: "user" | "assistant" | "system";
  content: string;
  timestamp: string;
  emotional_state?: Partial<EmotionalState>;
  metadata_payload?: Record<string, unknown>;
}

export interface Session {
  id: string;
  title: string;
  created_at: string;
  updated_at: string;
  is_active: boolean;
}

export interface ChatResponse {
  session_id: string;
  message: {
    id: string;
    role: "assistant";
    content: string;
    created_at: string;
    metadata_payload?: {
      response_strategy?: string;
      model_name?: string;
    };
  };
  response_strategy: string;
  model_name: string;
  created_at: string;
}

export interface HealthStatus {
  status: "ok" | "degraded" | "down" | "connecting";
  app_name: string;
  version: string;
  environment: string;
  timestamp: string;
  database: {
    connected: boolean;
    dialect: string;
    details?: string | null;
  };
  services: Record<string, string>;
  latencyMs?: number;
}

export interface UserPreferences {
  language: string;
  voiceAutoPlay: boolean;
  cameraAnalysisEnabled: boolean;
  microphoneAnalysisEnabled: boolean;
  longTermMemoryEnabled: boolean;
  emotionStorageEnabled: boolean;
}
