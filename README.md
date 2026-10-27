# AI Companion

**AI Companion** is a web-based, emotion-aware conversational platform. It supports text and voice interaction and, with explicit permission, camera-based facial signal analysis. It estimates emotional state from available text, voice, and visual signals, then adapts responses using conversation context and permission-controlled memory.

---

## Architecture Principle: Emotion Engine Independence

Under no circumstances does AI Companion use a direct `Camera → LLM → 'you are sad'` pipeline. 
Each input modality produces structured signal measurements independently. An independent **Emotion Engine** fuses active modality signals into a normalized `EmotionalState` (dominant emotion, probabilities, confidence, intensity, uncertainty, sources). The RLPI / LLM layer consumes this normalized state as controlled context.

```text
USER → TEXT / MICROPHONE / CAMERA
       ↓
SIGNAL SERVICES (NLP / SPEECH / VISION)
       ↓
INDEPENDENT EMOTION ENGINE (Fused Normalized State)
       ↓
CONVERSATION CONTEXT + PERMITTED MEMORY
       ↓
RLPI / CONVERSATIONAL AI LAYER
       ↓
RESPONSE STRATEGY → TEXT / TTS → USER
```

---

## Repository Structure

```text
ai-companion/
├── frontend/
│   ├── src/
│   │   ├── components/       # Header, ChatArea, ModalityControls, Avatar, Telemetry, Settings
│   │   ├── hooks/            # useHealth, custom React hooks
│   │   ├── services/         # Typed API client
│   │   ├── types/            # TypeScript domain types (EmotionalState, ModalityStatus, etc.)
│   │   ├── utils/            # Formatters, color utilities
│   │   ├── App.tsx           # Main application shell
│   │   ├── main.tsx          # React DOM entry point
│   │   └── index.css         # Tailwind CSS & theme tokens
│   ├── package.json
│   └── vite.config.ts        # Vite configuration with API proxy
├── backend/
│   ├── app/
│   │   ├── api/              # API router, dependencies, and v1 endpoints
│   │   ├── core/             # Configuration (Pydantic Settings), logging
│   │   ├── database/         # Async SQLAlchemy engine, session generator, Base
│   │   ├── models/           # Declarative DB models (User, Session, Message, EmotionEvent, etc.)
│   │   ├── schemas/          # Pydantic schemas (Health, ApiResponse, etc.)
│   │   ├── services/         # Modular service directories:
│   │   │   ├── conversation/ # Session & message routing stubs
│   │   │   ├── speech/       # STT/TTS adapter stubs
│   │   │   ├── vision/       # Face detection & expression stubs
│   │   │   ├── emotion/      # Multimodal Emotion Engine stubs
│   │   │   ├── rlpi/         # Response policy & LLM generation stubs
│   │   │   └── memory/       # Consent-gated memory stubs
│   │   └── main.py           # FastAPI application entrypoint with CORS & error handlers
│   └── requirements.txt
├── tests/
│   └── backend/              # Pytest async test suite (health, models, config)
├── models/                   # Directory for model checkpoints and weights
├── deployment/               # Dockerfile and docker-compose configurations
├── docs/                     # Architecture & phased roadmap documentation
├── .env.example              # Environment variables template
├── .gitignore
└── README.md
```

---

## Getting Started

### Prerequisites
- Python 3.11+
- Node.js 18+ and npm 9+
- (Optional) PostgreSQL 15+ (SQLite fallback is configured out-of-the-box for rapid development)

### 1. Environment Setup
Copy the example environment configuration:
```bash
cp .env.example .env
```

### 2. Backend Setup
```bash
# Navigate to backend and install dependencies
pip install -r backend/requirements.txt

# Run backend development server (defaults to http://localhost:8000)
uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload
```

Interactive API documentation will be available at:
- Swagger UI: `http://localhost:8000/docs`
- Health check: `http://localhost:8000/api/health`

### 3. Frontend Setup
```bash
# Navigate to frontend and install dependencies
cd frontend
npm install

# Start Vite dev server (defaults to http://localhost:5173)
npm run dev
```

The frontend connects directly to the backend via Vite's proxy (`/api` -> `http://localhost:8000`).

---

## Running Verification & Tests

### Backend Tests (Pytest)
```bash
python -m pytest tests/backend/ -v
```

### Frontend Typecheck & Production Build
```bash
cd frontend
npm run build
```

---

## Current Status: Phase 1 (Project Foundation)
- [x] React + TypeScript + Vite + Tailwind CSS shell setup
- [x] FastAPI application with `/api/health` endpoint and CORS middleware
- [x] Relational schema definitions (users, sessions, messages, emotion_events, consents, memory_items)
- [x] Modular service interfaces (conversation, speech, vision, emotion, rlpi, memory)
- [x] Live UI shell with Companion Avatar, Modality permission controls, and Emotion Telemetry Drawer
- [x] Comprehensive automated test suite passing

**Next Phase**: **Phase 2 — Basic RLPI/LLM Conversation** (Chat endpoint, LLM provider adapter, session message flow).
