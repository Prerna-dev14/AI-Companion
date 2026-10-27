# AI Companion — Controlled Implementation Sequence

| Phase | Title | Status | Scope / Boundary |
|---|---|---|---|
| **Phase 1** | **Project Foundation** | **Completed** | Repo layout, React+TS+Vite, Tailwind, FastAPI, /api/health, modular service stubs, PostgreSQL schema models, unit tests, README. No emotion models or STT/TTS. |
| **Phase 2** | **Basic RLPI / LLM Conversation** | **Completed** | `POST /api/chat`, `GET/POST /api/sessions`, modular LLM adapter (OpenAI & local fallback), context window manager, server-side RLPI response strategy, end-to-end verified with live multi-turn chat and database persistence. No emotion-driven adaptation. |
| **Phase 3** | **Speech AI** | **Completed** | `POST /api/speech/transcribe` (Whisper & fallback STT), `POST /api/speech/synthesize` (gTTS, OpenAI, synthetic WAV), Web Audio / MediaRecorder voice capture, explicit microphone permission UX, TTS playback on assistant messages, and graceful text fallback. Raw audio is never retained. No voice emotion classification yet. |
| **Phase 4** | **Computer Vision Signals** | **Completed** | `POST /api/emotion/face` (OpenCV & MediaPipe vision adapter), explicit camera permission handling, in-memory frame processing, face detection (handling single face, multiple faces, no face, low lighting), anonymous geometric feature extraction (smile ratio, eye openness, lighting score), floating `CameraPreview` monitor, and strict zero raw frame retention. No identity recognition; no emotion fusion yet. |
| **Phase 5** | Text and Voice Emotion Signals | *Next* | NLP intent/sentiment and acoustic/prosodic feature extraction. |
| **Phase 6** | Emotion Engine & Signal Fusion | *Pending* | Normalized EmotionalState fusion with confidence and uncertainty tracking across active modalities. |
| **Phase 7** | Emotion-Aware RLPI Strategy | *Pending* | Adapting conversational responses based on normalized emotional state without diagnosing or asserting emotion as fact. |
| **Phase 8** | Consent-Gated Memory | *Pending* | Session context, permission-controlled long-term memory, emotion event history, review/delete controls. |
| **Phase 9** | Security, Privacy & Safety Hardening | *Pending* | Auth/authz, rate limits, audit logging, high-risk safety classification (self-harm/abuse defense). |
| **Phase 10** | Validation, Observability & Deployment | *Pending* | E2E integration test suite, telemetry metrics, production build and deployment documentation. |
