import type {
  HealthStatus,
  ChatResponse,
  Session,
  Message,
  TranscriptionResponse,
  VisionSignalResponse,
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
   * Sends a user chat message to the live backend conversation/RLPI layer.
   */
  async sendMessage(message: string, sessionId?: string): Promise<ChatResponse> {
    const response = await fetch(`${this.baseUrl}/api/chat`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "Accept": "application/json",
      },
      body: JSON.stringify({
        message,
        session_id: sessionId || null,
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

  getBaseUrl(): string {
    return this.baseUrl;
  }
}

export const api = new ApiService();
