# AI Companion — Architecture & Engineering Specification

## 1. High-Level Architecture

```text
USER → TEXT / MICROPHONE / OPTIONAL CAMERA
       ↓
SIGNAL SERVICES (NLP / SPEECH / VISION)
       ↓
INDEPENDENT EMOTION ENGINE
       ↓
NORMALIZED EMOTIONAL STATE
       ↓
CONVERSATION CONTEXT + PERMITTED MEMORY
       ↓
RLPI / LLM CONVERSATIONAL LAYER
       ↓
RESPONSE STRATEGY
       ↓
TEXT / TTS → USER
```

## 2. Core Principle: Emotion Engine Independence

Under no circumstances should the system use a direct `Camera → LLM → 'you are sad'` pipeline. 
Each input modality produces structured signal measurements independently:
1. **NLP Service**: Intent, sentiment vector, keyword emotion signals.
2. **Speech Service**: Acoustic pitch, tempo, intensity, and prosodic markers.
3. **Vision Service**: Face landmark ratios, action units, approved expression probabilities.

The independent **Emotion Engine** fuses these available signals and outputs a normalized, probabilistic `EmotionalState`:
```typescript
interface EmotionalState {
  dominant_emotion: "happy" | "sad" | "angry" | "bored" | "neutral" | "surprised" | "confused";
  probabilities: Record<EmotionCategory, number>;
  confidence: number;      // 0.0 to 1.0
  intensity: number;       // 0.0 to 1.0
  uncertainty: number;     // 0.0 to 1.0
  sources: ModalityType[]; // ["text", "voice", "face"]
  timestamp: string;
  modality_status: Record<ModalityType, boolean>;
}
```

The RLPI/LLM layer consumes this normalized state as structured conversational context; the LLM is **never** the primary emotion classifier.

## 3. Privacy & Biometric Data Governance

- **Explicit Opt-in**: Camera and microphone access require explicit user permissions and visual indicators.
- **No Raw Media Retention**: Raw camera frames and raw audio streams are processed in memory and immediately discarded. Never written to databases, disk, or remote logs.
- **Permission-Controlled Memory**: Long-term memories and emotion histories are gated by user consent flags (`allow_long_term_memory`, `allow_emotion_storage`).
- **Non-Diagnostic Policy**: Emotion estimates are probabilistic guides for conversational tone adaptation; AI Companion is not a medical or psychological diagnostic tool.
