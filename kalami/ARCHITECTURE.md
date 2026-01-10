# Kalami - AI Language Learning Assistant

## Project Overview

**Kalami** is an AI-powered vocal assistant for interactive language learning through natural conversation. Users can practice speaking new languages through real-time voice conversations on iOS and Android mobile apps.

## Development Environment

- Python 3.7+ (for backend services)
- Node.js v18+ (for API gateway)
- React Native with Expo (mobile app development)
- SQLite (development) / PostgreSQL (production)
- Redis (session management & caching - production)

## Architecture

### System Overview

Kalami uses a modular pipeline architecture with four main components:

```
┌─────────────────────────────────────────────────────────────┐
│                 Mobile App (React Native/Expo)               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ Audio Record │  │ Conversation │  │ Progress     │      │
│  │ (expo-av)    │  │ UI           │  │ Tracking     │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
                            │
                   WebSocket / REST API
                            │
┌─────────────────────────────────────────────────────────────┐
│                   API Gateway (Node.js)                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ WebSocket    │  │ REST Proxy   │  │ JWT Auth     │      │
│  │ Handler      │  │ to Backend   │  │ Middleware   │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
                            │
                        HTTP/REST
                            │
┌─────────────────────────────────────────────────────────────┐
│                    Backend (FastAPI/Python)                  │
│                                                              │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  Voice Processing Pipeline                           │   │
│  │                                                       │   │
│  │  1. Speech-to-Text (STT)                             │   │
│  │     ▸ OpenAI Whisper API (primary)                   │   │
│  │     ▸ Deepgram (real-time streaming alternative)     │   │
│  │                                                       │   │
│  │  2. AI Conversation Engine                           │   │
│  │     ▸ Anthropic Claude / OpenAI GPT-4                │   │
│  │     ▸ Custom language learning prompts               │   │
│  │     ▸ Grammar correction & feedback                  │   │
│  │     ▸ Adaptive difficulty (CEFR levels A1-C2)        │   │
│  │                                                       │   │
│  │  3. Text-to-Speech (TTS)                             │   │
│  │     ▸ ElevenLabs (primary - natural voices)          │   │
│  │     ▸ OpenAI TTS (fallback)                          │   │
│  │     ▸ Multi-language voice selection                 │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ User DB      │  │ Sessions     │  │ Vocabulary   │      │
│  │ (SQLite/PG)  │  │ & Messages   │  │ Tracking     │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
```

### Technology Stack

#### Mobile Frontend
- **Framework**: React Native with Expo SDK 50
- **Audio**: expo-av for recording/playback
- **State Management**: Zustand (local) + TanStack Query (server)
- **Navigation**: Expo Router
- **Real-time**: WebSocket connection to gateway

#### API Gateway (Node.js)
- **Framework**: Express.js with TypeScript
- **WebSocket**: ws library for real-time audio streaming
- **Proxy**: http-proxy-middleware to backend
- **Auth**: JWT validation middleware

#### Backend (Python)
- **Framework**: FastAPI with async support
- **Database**: SQLAlchemy 2.0 with async SQLite/PostgreSQL
- **Auth**: JWT with python-jose, passlib for password hashing

#### AI Services
- **Speech-to-Text**: OpenAI Whisper API, Deepgram (streaming)
- **LLM**: Anthropic Claude / OpenAI GPT-4
- **Text-to-Speech**: ElevenLabs, OpenAI TTS

## Project Structure

```
kalami/
├── backend/                    # FastAPI backend services
│   ├── app/
│   │   ├── core/              # Configuration, database setup
│   │   │   ├── config.py      # Environment settings
│   │   │   └── database.py    # SQLAlchemy async setup
│   │   ├── models/            # SQLAlchemy models
│   │   │   ├── user.py
│   │   │   ├── learning_profile.py
│   │   │   ├── conversation.py
│   │   │   ├── vocabulary.py
│   │   │   └── pronunciation.py
│   │   ├── routers/           # API endpoints
│   │   │   ├── auth.py        # Registration, login, JWT
│   │   │   ├── users.py       # User profiles, stats
│   │   │   ├── conversations.py # Sessions, messages
│   │   │   └── speech.py      # Direct STT/TTS access
│   │   ├── services/          # Business logic
│   │   │   ├── auth_service.py
│   │   │   ├── conversation_service.py
│   │   │   ├── stt_service.py  # Whisper, Deepgram
│   │   │   └── tts_service.py  # ElevenLabs, OpenAI
│   │   └── main.py            # FastAPI app entry
│   ├── tests/
│   └── requirements.txt
│
├── gateway/                    # Node.js API Gateway
│   ├── src/
│   │   ├── index.ts           # Express app entry
│   │   ├── config.ts          # Environment config
│   │   ├── logger.ts          # Pino logger
│   │   ├── middleware/
│   │   │   └── auth.ts        # JWT validation
│   │   ├── routes/
│   │   │   ├── health.ts      # Health checks
│   │   │   └── proxy.ts       # Backend proxy
│   │   └── services/
│   │       └── websocket.ts   # WebSocket handler
│   ├── package.json
│   └── tsconfig.json
│
├── mobile/                     # React Native Expo app
│   ├── app/                   # Expo Router screens
│   ├── components/            # Reusable UI components
│   ├── hooks/                 # Custom React hooks
│   ├── services/              # API & WebSocket clients
│   ├── store/                 # Zustand stores
│   ├── types/                 # TypeScript types
│   ├── package.json
│   └── tsconfig.json
│
└── shared/                     # Shared types/configs
    └── types/
```

## API Endpoints

### Authentication
- `POST /auth/register` - Create new user
- `POST /auth/login` - Get JWT token
- `GET /auth/me` - Get current user

### User Management
- `GET /users/profiles` - List learning profiles
- `POST /users/profiles` - Create learning profile
- `GET /users/stats` - Get user statistics

### Conversations
- `POST /conversations/sessions` - Start conversation session
- `POST /conversations/sessions/{id}/end` - End session
- `GET /conversations/sessions/{id}/messages` - Get session messages
- `POST /conversations/sessions/{id}/audio` - Send audio, get response
- `POST /conversations/sessions/{id}/text` - Send text, get response

### Speech (Direct Access)
- `POST /speech/transcribe` - Transcribe audio to text
- `POST /speech/synthesize` - Convert text to speech
- `GET /speech/voices` - List available TTS voices

## Database Schema

### Core Tables
- **users** - User accounts with native language
- **learning_profiles** - Per-language learning progress (CEFR level, streak)
- **conversation_sessions** - Practice sessions with metrics
- **conversation_messages** - Individual messages with corrections
- **vocabulary_items** - Language vocabulary database
- **user_vocabulary** - Spaced repetition progress
- **pronunciation_analyses** - Phoneme-level feedback

## Development Commands

### Backend
```bash
cd backend
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

### Gateway
```bash
cd gateway
npm install
npm run dev  # Development with hot reload
```

### Mobile
```bash
cd mobile
npm install
npx expo start
```

### Run All Services
```bash
# Terminal 1 - Backend
cd backend && uvicorn app.main:app --reload --port 8000

# Terminal 2 - Gateway
cd gateway && npm run dev

# Terminal 3 - Mobile
cd mobile && npx expo start
```

## Environment Variables

### Backend (.env)
```
DATABASE_URL=sqlite+aiosqlite:///./kalami.db
SECRET_KEY=your-secret-key-change-in-production
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
ELEVENLABS_API_KEY=...
DEEPGRAM_API_KEY=...
```

### Gateway (.env)
```
GATEWAY_PORT=3000
BACKEND_URL=http://localhost:8000
JWT_SECRET=your-secret-key-change-in-production
```

## Key Features

### Phase 1 (MVP) - Current
- [x] User authentication (JWT)
- [x] Learning profiles (multiple languages)
- [x] Voice conversation sessions
- [x] STT with Whisper API
- [x] TTS with ElevenLabs
- [x] LLM conversation with Claude/GPT-4
- [x] Grammar correction feedback
- [x] WebSocket real-time streaming
- [ ] Mobile app UI
- [ ] Progress tracking dashboard

### Phase 2 (Enhancement)
- [ ] Phoneme-level pronunciation analysis
- [ ] Spaced repetition vocabulary review
- [ ] Cultural context integration
- [ ] Roleplay scenarios
- [ ] Push notifications

### Phase 3 (Scale)
- [ ] Multiple native speaker voices
- [ ] Offline mode support
- [ ] Community features
- [ ] Gamification

## Voice Processing Flow

```
User speaks → Mobile records audio (expo-av)
                    ↓
            WebSocket to Gateway
                    ↓
            Gateway forwards to Backend
                    ↓
            STT (Whisper) → Text transcript
                    ↓
            LLM (Claude) → Response + corrections
                    ↓
            TTS (ElevenLabs) → Audio response
                    ↓
            Stream back to mobile → Playback

Target latency: < 800ms end-to-end
```

## Notes

- All API keys in environment variables, never committed
- WebSocket heartbeat every 30 seconds to maintain connection
- TTS responses can be cached for common phrases
- Use streaming for LLM responses to reduce perceived latency
- Mobile app handles offline gracefully with queued messages
