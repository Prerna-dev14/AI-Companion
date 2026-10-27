import type {
  HealthStatus,
  ChatResponse,
  Session,
  Message,
  TranscriptionResponse,
  VisionSignalResponse,
  TextEmotionResponse,
  VoiceEmotionResponse,
  MultimodalFusionRequest,
  MultimodalFusionResponse,
  EmotionalState,
} from "../types";

const API_BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

class ApiService {
  private baseUrl: string;

  constructor(baseUrl: string = API_BASE_URL) {
    this.baseUrl = baseUrl.replace(/\/$/, "");
  }

  /**
   * Pings the backend health endpoint and measures round-trip latency.
   */
  async checkHealth(): Promise<HealthStatus> {
    const startTime = performance.now();
    try {
      const response = await fetch(`${this.baseUrl}/api/health`, {
        method: "GET",
        headers: {
          "Content-Type": "application/json",
          "Accept": "application/json",
        },
      });

      const latencyMs = Math.round(performance.now() - startTime);

      if (!response.ok) {
        return {
          status: "degraded",
          app_name: "AI Companion",
          version: "unknown",
          environment: "unknown",
          timestamp: new Date().toISOString(),
          database: { connected: false, dialect: "unknown", details: `HTTP ${response.status}` },
          services: {},
          latencyMs,
        };
      }

      const data = await response.json();
      return {
        ...data,
        latencyMs,
      };
    } catch (error) {
      const latencyMs = Math.round(performance.now() - startTime);
      return {
        status: "down",
        app_name: "AI Companion",
        version: "offline",
        environment: "offline",
        timestamp: new Date().toISOString(),
        database: { connected: false, dialect: "none", details: (error as Error).message },
        services: {},
        latencyMs,
      };
    }
  }

  /**
   * Sends a user chat message to the live backend conversation/RLPI layer,
   * injecting the fused emotional state to drive adaptive conversational strategies.
   */
  async sendMessage(
    message: string,
    sessionId?: string,
    emotionalState?: EmotionalState | null
  ): Promise<ChatResponse> {
    const response = await fetch(`${this.baseUrl}/api/chat`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "Accept": "application/json",
      },
      body: JSON.stringify({
        message,
        session_id: sessionId || null,
        emotional_state: emotionalState || null,
      }),
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.message || `Chat request failed with status ${response.status}`);
    }

    return response.json();
  }

  /**
   * Transcribes voice audio blob into text via POST /api/speech/transcribe.
   * Raw audio stream is discarded in memory.
   */
  async transcribeAudio(audioBlob: Blob): Promise<string> {
    const formData = new FormData();
    formData.append("file", audioBlob, "user_voice.wav");

    const response = await fetch(`${this.baseUrl}/api/speech/transcribe`, {
      method: "POST",
      body: formData,
    });

    if (!response.ok) {
      throw new Error(`Speech transcription failed with status ${response.status}`);
    }

    const data: TranscriptionResponse = await response.json();
    return data.text;
  }

  /**
   * Synthesizes text into spoken audio stream via POST /api/speech/synthesize.
   */
  async synthesizeSpeech(text: string, language: string = "en"): Promise<Blob> {
    const response = await fetch(`${this.baseUrl}/api/speech/synthesize`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        text,
        language,
        voice: "default",
      }),
    });

    if (!response.ok) {
      throw new Error(`Speech synthesis failed with status ${response.status}`);
    }

    return response.blob();
  }

  /**
   * Analyzes an in-memory webcam frame to extract anonymous face signals.
   * Raw frames are never retained.
   */
  async analyzeFace(imageBlob: Blob): Promise<VisionSignalResponse> {
    const formData = new FormData();
    formData.append("file", imageBlob, "frame.jpg");

    const response = await fetch(`${this.baseUrl}/api/emotion/face`, {
      method: "POST",
      body: formData,
    });

    if (!response.ok) {
      throw new Error(`Vision facial analysis failed with status ${response.status}`);
    }

    return response.json();
  }

  /**
   * Analyzes text for intent and sentiment/emotion signals (Phase 5).
   * Operates independently of LLM conversational response.
   */
  async analyzeTextEmotion(text: string, language: string = "en"): Promise<TextEmotionResponse> {
    const response = await fetch(`${this.baseUrl}/api/emotion/text`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "Accept": "application/json",
      },
      body: JSON.stringify({
        text,
        language,
      }),
    });

    if (!response.ok) {
      throw new Error(`Text emotion analysis failed with status ${response.status}`);
    }

    return response.json();
  }

  /**
   * Extracts acoustic prosody signals from voice audio bytes (Phase 5).
   * Audio is processed in-memory and immediately discarded.
   */
  async analyzeVoiceEmotion(audioBlob: Blob): Promise<VoiceEmotionResponse> {
    const formData = new FormData();
    formData.append("file", audioBlob, "voice_sample.wav");

    const response = await fetch(`${this.baseUrl}/api/emotion/voice`, {
      method: "POST",
      body: formData,
    });

    if (!response.ok) {
      throw new Error(`Voice prosody analysis failed with status ${response.status}`);
    }

    return response.json();
  }

  /**
   * Fuses active multimodal signals (text, voice, face) via the independent
   * Emotion Engine into a normalized EmotionalState (Phase 6).
   */
  async fuseEmotions(request: MultimodalFusionRequest): Promise<MultimodalFusionResponse> {
    const response = await fetch(`${this.baseUrl}/api/emotion/fuse`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "Accept": "application/json",
      },
      body: JSON.stringify(request),
    });

    if (!response.ok) {
      throw new Error(`Multimodal emotion fusion failed with status ${response.status}`);
    }

    return response.json();
  }

  /**
   * Lists available conversation sessions.
   */
  async getSessions(): Promise<Session[]> {
    const response = await fetch(`${this.baseUrl}/api/sessions`, {
      method: "GET",
      headers: {
        "Accept": "application/json",
      },
    });

    if (!response.ok) {
      return [];
    }
    return response.json();
  }

  /**
   * Creates a new conversation session.
   */
  async createSession(title?: string): Promise<Session> {
    const response = await fetch(`${this.baseUrl}/api/sessions`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "Accept": "application/json",
      },
      body: JSON.stringify({ title: title || "New Conversation" }),
    });

    if (!response.ok) {
      throw new Error("Failed to create new session");
    }
    return response.json();
  }

  /**
   * Gets message history for a session.
   */
  async getSessionMessages(sessionId: string): Promise<Message[]> {
    const response = await fetch(`${this.baseUrl}/api/sessions/${sessionId}/messages`, {
      method: "GET",
      headers: {
        "Accept": "application/json",
      },
    });

    if (!response.ok) {
      return [];
    }
    const data = await response.json();
    return data.map((m: any) => ({
      id: m.id,
      role: m.role,
      content: m.content,
      timestamp: m.created_at,
      metadata_payload: m.metadata_payload,
    }));
  }

  /**
   * Consent-Gated Long-Term Memory (Phase 8)
   */
  async getMemories(userId?: string): Promise<import("../types").MemoryItem[]> {
    const url = userId ? `${this.baseUrl}/api/memory?user_id=${encodeURIComponent(userId)}` : `${this.baseUrl}/api/memory`;
    const response = await fetch(url, {
      method: "GET",
      headers: { "Accept": "application/json" },
    });
    if (!response.ok) {
      return [];
    }
    return response.json();
  }

  async createMemory(content: string, category: string = "general", userId?: string): Promise<import("../types").MemoryItem> {
    const response = await fetch(`${this.baseUrl}/api/memory`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "Accept": "application/json",
      },
      body: JSON.stringify({
        content,
        category,
        user_id: userId || null,
      }),
    });
    if (!response.ok) {
      const err = await response.json().catch(() => ({}));
      throw new Error(err.message || `Failed to create memory (${response.status})`);
    }
    return response.json();
  }

  async deleteMemory(memoryId: string, userId?: string): Promise<void> {
    const url = userId
      ? `${this.baseUrl}/api/memory/${memoryId}?user_id=${encodeURIComponent(userId)}`
      : `${this.baseUrl}/api/memory/${memoryId}`;
    const response = await fetch(url, {
      method: "DELETE",
      headers: { "Accept": "application/json" },
    });
    if (!response.ok) {
      throw new Error("Failed to delete memory item");
    }
  }

  async clearAllMemories(userId?: string): Promise<void> {
    const url = userId
      ? `${this.baseUrl}/api/memory?user_id=${encodeURIComponent(userId)}`
      : `${this.baseUrl}/api/memory`;
    const response = await fetch(url, {
      method: "DELETE",
      headers: { "Accept": "application/json" },
    });
    if (!response.ok) {
      throw new Error("Failed to purge memories");
    }
  }

  /**
   * User Privacy Consents (Phase 8)
   */
  async getConsents(userId?: string): Promise<import("../types").ConsentItem[]> {
    const url = userId ? `${this.baseUrl}/api/consents?user_id=${encodeURIComponent(userId)}` : `${this.baseUrl}/api/consents`;
    const response = await fetch(url, {
      method: "GET",
      headers: { "Accept": "application/json" },
    });
    if (!response.ok) {
      return [];
    }
    return response.json();
  }

  async updateConsent(scope: string, granted: boolean, userId?: string): Promise<import("../types").ConsentItem> {
    const response = await fetch(`${this.baseUrl}/api/consents`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "Accept": "application/json",
      },
      body: JSON.stringify({
        scope,
        granted,
        user_id: userId || null,
      }),
    });
    if (!response.ok) {
      throw new Error(`Failed to update consent for ${scope}`);
    }
    return response.json();
  }

  /**
   * Emotion Event History (Phase 8)
   */
  async getEmotionHistory(sessionId?: string, limit: number = 20): Promise<import("../types").EmotionHistoryResponse> {
    let url = `${this.baseUrl}/api/emotion/history?limit=${limit}`;
    if (sessionId) {
      url += `&session_id=${encodeURIComponent(sessionId)}`;
    }
    const response = await fetch(url, {
      method: "GET",
      headers: { "Accept": "application/json" },
    });
    if (!response.ok) {
      return { events: [], total: 0 };
    }
    return response.json();
  }

  async clearEmotionHistory(sessionId?: string): Promise<void> {
    let url = `${this.baseUrl}/api/emotion/history`;
    if (sessionId) {
      url += `?session_id=${encodeURIComponent(sessionId)}`;
    }
    const response = await fetch(url, {
      method: "DELETE",
      headers: { "Accept": "application/json" },
    });
    if (!response.ok) {
      throw new Error("Failed to clear emotion history");
    }
  }

  getBaseUrl(): string {
    return this.baseUrl;
  }
}

export const api = new ApiService();
