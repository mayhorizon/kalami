# Kalami - AI Language Learning Assistant

## Project Overview

**Kalami** is an AI-powered vocal assistant for interactive language learning through natural conversation. Users can practice speaking new languages through real-time voice conversations on iOS and Android mobile apps.

## Development Environment

- Python 3.7+ (for backend services)
- Node.js via nvm (v24.12.0 installed)
- Flutter 3.x (mobile app development)
- PostgreSQL (user data & progress tracking)
- Redis (session management & caching)

## Architecture

### System Overview

Kalami uses a modular pipeline architecture with three main components:

```
┌─────────────────────────────────────────────────────────┐
│                     Mobile App (Flutter)                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │ Voice Input  │  │   UI/UX      │  │ Local Cache  │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
└─────────────────────────────────────────────────────────┘
                            │
                    WebSocket Connection
                            │
┌─────────────────────────────────────────────────────────┐
│                    API Gateway / Backend                 │
│                                                           │
│  ┌─────────────────────────────────────────────────┐    │
│  │  Real-Time Voice Processing Pipeline           │    │
│  │                                                 │    │
│  │  1. Speech-to-Text (STT)                       │    │
│  │     ↓  ▸ AssemblyAI / OpenAI Whisper          │    │
│  │                                                 │    │
│  │  2. AI Conversation Engine                     │    │
│  │     ↓  ▸ OpenAI GPT-4 / Anthropic Claude      │    │
│  │        ▸ Custom language learning prompts      │    │
│  │        ▸ Pronunciation analysis                 │    │
│  │        ▸ Grammar correction                     │    │
│  │                                                 │    │
│  │  3. Text-to-Speech (TTS)                       │    │
│  │     ↓  ▸ ElevenLabs / OpenAI TTS              │    │
│  │        ▸ Native speaker voices                  │    │
│  │        ▸ Multiple dialects                      │    │
│  └─────────────────────────────────────────────────┘    │
│                                                           │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │  User DB     │  │ Session DB   │  │  Analytics   │  │
│  │ (PostgreSQL) │  │   (Redis)    │  │   (Events)   │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
└─────────────────────────────────────────────────────────┘
```

### Technology Stack

#### Mobile Frontend
- **Framework**: Flutter 3.x
- **State Management**: Riverpod or Provider
- **Voice Integration**: flutter_sound, speech_to_text packages
- **Real-time Communication**: WebSocket (socket_io_client)
- **Local Storage**: Hive or SQLite

#### Backend
- **API Framework**: FastAPI (Python) - for async WebSocket handling
- **Database**: PostgreSQL (user data, progress tracking)
- **Cache/Session**: Redis (session management, real-time state)
- **Authentication**: Firebase Auth or Auth0
- **File Storage**: AWS S3 or Google Cloud Storage

#### AI Services
- **Speech-to-Text**: AssemblyAI (real-time) or OpenAI Whisper
- **LLM**: OpenAI GPT-4 Turbo or Anthropic Claude
- **Text-to-Speech**: ElevenLabs (natural voices) or OpenAI TTS
- **Pronunciation Analysis**: Azure Speech Services or custom model

#### Infrastructure
- **Hosting**: AWS (ECS/Fargate) or Google Cloud Run
- **CDN**: CloudFront or Cloudflare
- **Monitoring**: Sentry, DataDog
- **CI/CD**: GitHub Actions

### Key Features

#### Phase 1 (MVP)
1. Voice conversation in 2-3 languages (Spanish, French, German)
2. Real-time speech recognition & response
3. Basic pronunciation feedback
4. Simple lesson structure (greetings, common phrases)
5. User progress tracking
6. Session history

#### Phase 2 (Enhancement)
1. Advanced pronunciation analysis
2. Grammar correction with explanations
3. Cultural context integration
4. Roleplay scenarios (restaurant, airport, etc.)
5. Spaced repetition system
6. Vocabulary builder

#### Phase 3 (Advanced)
1. Multiple native speaker voices
2. Dialect variations
3. Real-world conversation simulations
4. Community features
5. Gamification elements
6. Offline mode support

## Project Structure

```
kalami/
├── backend/              # FastAPI backend services
│   ├── app/
│   │   ├── api/         # API endpoints
│   │   ├── core/        # Configuration, security
│   │   ├── models/      # Database models
│   │   ├── services/    # Business logic
│   │   │   ├── stt/     # Speech-to-text service
│   │   │   ├── llm/     # LLM conversation engine
│   │   │   └── tts/     # Text-to-speech service
│   │   └── websocket/   # WebSocket handlers
│   ├── tests/
│   └── requirements.txt
│
├── mobile/              # Flutter mobile app
│   ├── lib/
│   │   ├── models/      # Data models
│   │   ├── providers/   # State management
│   │   ├── screens/     # UI screens
│   │   ├── services/    # API & WebSocket clients
│   │   └── widgets/     # Reusable UI components
│   ├── test/
│   └── pubspec.yaml
│
├── docs/                # Documentation
├── scripts/             # Deployment & utility scripts
└── docker-compose.yml   # Local development setup
```

## Development Workflow

### Backend Development

Start backend server:
```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Run tests:
```bash
pytest
```

### Mobile Development

Run Flutter app:
```bash
cd mobile
flutter pub get
flutter run
```

Run tests:
```bash
flutter test
```

### Local Development with Docker

Start all services:
```bash
docker-compose up -d
```

## Critical Technical Challenges

### 1. Latency (<2s target)
- Use streaming WebSockets instead of HTTP requests
- Implement parallel processing (STT + LLM preparation)
- Edge caching for common responses
- Consider on-device STT for initial transcription

### 2. Pronunciation Accuracy
- Integrate phoneme-level analysis (not just transcription)
- Use Azure Cognitive Services or custom model
- Provide visual feedback (waveform comparison)

### 3. Cost Optimization
- Cache common TTS responses
- Use streaming responses from LLM
- Implement usage tiers
- Consider on-device models for basic features

### 4. Natural Conversation Flow
- Fine-tune prompts for each language/level
- Maintain conversation context across turns
- Use AI to adapt to user's proficiency level
- Implement turn-taking detection

## Competitive Landscape

**Key Competitors:**
- **Speak** (~$15/month) - OpenAI-powered, focuses on speaking practice
- **Duolingo Max** ($30/month) - AI roleplay & video calls
- **Langua** - Human-like conversations with YouTuber voices
- **TalkPal** - Conversation practice with roleplay
- **Jumpspeak** - Active immersion method

**Kalami Differentiators:**
1. Authentic conversation feel (avoiding robotic responses)
2. Real-time, low-latency responses (< 2 seconds)
3. Accurate pronunciation feedback
4. Cultural context integration

## Configuration

Environment variables (.env):
```
# Backend
DATABASE_URL=postgresql://user:password@localhost/kalami
REDIS_URL=redis://localhost:6379
SECRET_KEY=your-secret-key

# AI Services
OPENAI_API_KEY=your-openai-key
ANTHROPIC_API_KEY=your-anthropic-key
ASSEMBLYAI_API_KEY=your-assemblyai-key
ELEVENLABS_API_KEY=your-elevenlabs-key

# Firebase
FIREBASE_PROJECT_ID=your-project-id
FIREBASE_PRIVATE_KEY=your-private-key
```

## Common Commands

### Database Management

Initialize database:
```bash
alembic upgrade head
```

Create migration:
```bash
alembic revision --autogenerate -m "description"
```

### Deployment

Deploy backend:
```bash
./scripts/deploy-backend.sh
```

Build mobile app:
```bash
cd mobile
flutter build apk  # Android
flutter build ios  # iOS
```

## Notes for Development

- All API keys should be stored in environment variables, never committed
- Follow Flutter best practices for widget composition
- Use type hints in Python code
- Write tests for critical voice processing pipeline
- Monitor latency metrics closely
- Keep WebSocket connections alive with heartbeat messages
- Implement proper error handling for AI service failures
- Cache TTS responses to reduce costs
- Use feature flags for gradual rollout of new languages

## Resources

- [Flutter AI Toolkit](https://docs.flutter.dev/ai/ai-toolkit)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [OpenAI API](https://platform.openai.com/docs)
- [AssemblyAI Real-time](https://www.assemblyai.com/docs/walkthroughs#realtime-streaming-transcription)
- [ElevenLabs API](https://elevenlabs.io/docs)
