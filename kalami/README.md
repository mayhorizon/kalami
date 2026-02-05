# Kalami - AI Language Learning Assistant

Kalami is a voice-powered language learning app that uses AI to provide natural conversation practice. Speak in your target language, get real-time feedback, grammar corrections, and hear native-quality responses powered by ElevenLabs TTS.

## Features

- **Voice Conversations** - Record audio and have natural conversations with an AI tutor
- **Multi-Language Support** - Practice French, Spanish, Japanese, Chinese, Korean, German, Italian, Portuguese, Arabic, Russian
- **Smart Tutoring** - Level-adapted responses based on CEFR proficiency (A1-C2)
  - A1-A2: Bilingual explanations with translations
  - B1: Transitional mix of target and native language
  - B2-C2: Full immersion in target language
- **Pronunciation Guides** - Pinyin for Chinese, romaji for Japanese, romanization for Korean/Arabic
- **Grammar Corrections** - Real-time feedback with explanations
- **Voice Responses** - AI speaks back using ElevenLabs text-to-speech
- **Progress Tracking** - Practice time, conversation count, and day streaks
- **Multi-Platform** - Works on Web, iOS (Expo Go), and Android

## Architecture

```
Mobile App (React Native/Expo)
      |
      | REST API + WebSocket
      |
Gateway (Express + WebSocket server)
      |
      | HTTP
      |
Backend (FastAPI + Python)
      |
      +-- OpenAI Whisper (Speech-to-Text)
      +-- OpenAI GPT / Anthropic Claude (LLM)
      +-- ElevenLabs (Text-to-Speech)
      +-- SQLite (Database)
```

### Components

| Component | Tech Stack | Port |
|-----------|-----------|------|
| **Mobile App** | React Native, Expo, TypeScript | 8081 |
| **Gateway** | Express, WebSocket (ws), TypeScript | 3000 |
| **Backend** | FastAPI, SQLAlchemy, Python | 8000 |

## Prerequisites

- Python 3.10+
- Node.js 18+
- npm or yarn

### API Keys Required

- **OpenAI API Key** - For Whisper STT and GPT chat
- **ElevenLabs API Key** - For text-to-speech
- (Optional) **Anthropic API Key** - Alternative LLM provider

## Quick Start

### 1. Backend

```bash
cd kalami/backend

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your API keys

# Start backend
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 2. Gateway

```bash
cd kalami/gateway

# Install dependencies
npm install

# Start gateway
npm run dev
```

### 3. Mobile App

```bash
cd kalami/mobile

# Install dependencies
npm install

# Start Expo dev server
npx expo start
```

#### Running on iPhone/Android

1. Install **Expo Go** from the App Store / Play Store
2. Start the Expo dev server: `npx expo start`
3. Scan the QR code with your phone camera (iPhone) or Expo Go app (Android)

#### WSL2 Setup (Windows)

If running in WSL2, set up port forwarding in PowerShell (Admin):

```powershell
netsh interface portproxy add v4tov4 listenport=8081 listenaddress=0.0.0.0 connectport=8081 connectaddress=<WSL_IP>
netsh interface portproxy add v4tov4 listenport=3000 listenaddress=0.0.0.0 connectport=3000 connectaddress=<WSL_IP>
netsh interface portproxy add v4tov4 listenport=8000 listenaddress=0.0.0.0 connectport=8000 connectaddress=<WSL_IP>
netsh advfirewall firewall add rule name="Kalami Dev" dir=in action=allow protocol=TCP localport=3000,8000,8081
```

Replace `<WSL_IP>` with the output of `hostname -I` in WSL.

Then update the `LOCAL_IP` in `mobile/services/api.ts` and `mobile/services/websocket.ts` to your Windows WiFi IP.

## Configuration

### Backend Environment Variables (.env)

```env
OPENAI_API_KEY=sk-...
ELEVENLABS_API_KEY=...
ELEVENLABS_VOICE_ID=...
JWT_SECRET_KEY=your-secret-key
DATABASE_URL=sqlite+aiosqlite:///./kalami.db
```

### Network IPs for Mobile Testing

Update `LOCAL_IP` in these files to match your development machine:
- `mobile/services/api.ts`
- `mobile/services/websocket.ts`

## Conversation Flow

1. User records audio on mobile app
2. Audio sent via WebSocket to gateway
3. Gateway forwards to backend as multipart form data
4. Backend pipeline:
   - **Whisper** transcribes audio to text
   - **LLM** generates tutor response (with corrections, vocabulary)
   - **ElevenLabs** synthesizes voice response
5. Response sent back through WebSocket
6. Mobile app displays text and plays audio

## API Endpoints

### Auth
- `POST /auth/register` - Create account
- `POST /auth/login` - Login
- `GET /auth/me` - Current user

### Profiles
- `GET /users/profiles` - List learning profiles
- `POST /users/profiles` - Create learning profile
- `GET /users/stats` - User statistics

### Conversations
- `POST /conversations/sessions` - Start session
- `PUT /conversations/sessions/:id/end` - End session
- `POST /conversations/sessions/:id/audio` - Process audio
- `GET /conversations/sessions/:id/messages` - Get messages

## License

MIT
