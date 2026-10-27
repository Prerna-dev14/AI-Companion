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

export interface TranscriptionResponse {
  text: string;
  language: string;
  duration_sec?: number;
}

export interface SynthesisRequest {
  text: string;
  language?: string;
  voice?: string;
}

export interface BoundingBox {
  x: number;
  y: number;
  width: number;
  height: number;
}

export interface VisionSignalResponse {
  face_detected: boolean;
  face_count: number;
  status: "ok" | "no_face" | "multiple_faces" | "poor_lighting" | "low_confidence";
  confidence: number;
  lighting_score: number;
  facial_features?: {
    smile_ratio?: number;
    eye_openness?: number;
    face_coverage?: number;
  } | null;
  expression_signals?: Record<string, number> | null;
  bounding_box?: BoundingBox | null;
  timestamp: string;
}

export interface TextEmotionResponse {
  modality: "text";
  intent: string;
  sentiment_score: number;
  probabilities: Record<EmotionCategory, number>;
  confidence: number;
  detected_language: string;
  timestamp: string;
}

export interface VoiceEmotionResponse {
  modality: "voice";
  acoustic_features: {
    pitch_hz: number;
    rms_energy: number;
    tempo_estimate: number;
    spectral_brightness: number;
    duration_sec?: number;
  };
  probabilities: Record<EmotionCategory, number>;
  confidence: number;
  speaking_rate: "slow" | "normal" | "fast";
  energy_level: "low" | "medium" | "high";
  timestamp: string;
}

export interface MultimodalFusionRequest {
  text_signal?: TextEmotionResponse | null;
  voice_signal?: VoiceEmotionResponse | null;
  face_signal?: VisionSignalResponse | null;
  session_id?: string | null;
  previous_state?: EmotionalState | null;
  persist?: boolean;
}

export interface MultimodalFusionResponse extends EmotionalState {
  event_id?: string | null;
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

export interface MemoryItem {
  id: string;
  user_id: string;
  content: string;
  category: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface ConsentItem {
  id: string;
  user_id: string;
  scope: string;
  granted: boolean;
  user_agent?: string | null;
  created_at: string;
  updated_at: string;
}

export interface EmotionHistoryItem {
  id: string;
  session_id?: string | null;
  dominant_emotion: EmotionCategory;
  confidence: number;
  intensity: number;
  uncertainty: number;
  sources: string[];
  created_at: string;
}

export interface EmotionHistoryResponse {
  events: EmotionHistoryItem[];
  total: number;
}
