# Kalami - AI Language Learning Assistant

<p align="center">
  <strong>Learn languages through natural conversations with AI</strong>
</p>

## Overview

Kalami is an AI-powered vocal assistant that helps you learn new languages through real-time voice conversations. Practice speaking naturally with an AI tutor that adapts to your level, provides pronunciation feedback, and makes language learning engaging and effective.

## Features

- **Real-time Voice Conversations**: Speak naturally and get instant responses
- **Multiple Languages**: Start with Spanish, French, and German (more coming soon)
- **Pronunciation Feedback**: Get accurate feedback on your pronunciation
- **Adaptive Learning**: AI adapts to your proficiency level
- **Progress Tracking**: Monitor your improvement over time
- **Mobile Apps**: Available on both iOS and Android

## Technology Stack

- **Mobile**: Flutter 3.x (iOS & Android)
- **Backend**: FastAPI (Python)
- **Database**: PostgreSQL
- **Cache**: Redis
- **AI Services (100% FREE - runs locally)**:
  - Speech-to-Text: **OpenAI Whisper** (local, MIT license)
  - LLM: **Ollama + Llama 3.2** (local, free)
  - Text-to-Speech: **Piper TTS** (local, fast, neural voices)

> **Zero API Costs!** All AI runs on your machine. No monthly fees.
>
> *Optional paid alternatives available: OpenAI, Anthropic, AssemblyAI, ElevenLabs*

## Quick Start

> **🎉 Want zero cost?** See [FREE_SETUP.md](FREE_SETUP.md) for complete guide using 100% free local AI models!

### Prerequisites

- Python 3.7+
- Flutter 3.x (for mobile app)
- PostgreSQL (for production)
- Redis (for production)

### FREE AI Setup (Recommended)

1. **Install Ollama** (for LLM):
   ```bash
   curl -fsSL https://ollama.com/install.sh | sh
   ollama pull llama3.2:3b
   ollama serve
   ```

2. **Install Whisper** (for STT):
   ```bash
   pip install openai-whisper faster-whisper
   ```

3. **Download Piper TTS** voices from:
   https://github.com/rhasspy/piper/releases

See [FREE_SETUP.md](FREE_SETUP.md) for detailed instructions.

### Backend Setup

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your API keys

# Run migrations
alembic upgrade head

# Start the server
uvicorn app.main:app --reload
```

### Mobile App Setup

```bash
cd mobile
flutter pub get
flutter run
```

## Project Structure

```
kalami/
├── backend/              # FastAPI backend services
│   ├── app/
│   │   ├── api/         # API endpoints
│   │   ├── core/        # Configuration, security
│   │   ├── models/      # Database models
│   │   ├── services/    # Business logic
│   │   └── websocket/   # WebSocket handlers
│   └── tests/
├── mobile/              # Flutter mobile app
│   ├── lib/
│   │   ├── models/
│   │   ├── screens/
│   │   ├── services/
│   │   └── widgets/
│   └── test/
├── docs/                # Documentation
└── scripts/             # Deployment scripts
```

## Development

See [ARCHITECTURE.md](ARCHITECTURE.md) for detailed technical architecture and development guidelines.

### Running Tests

Backend:
```bash
cd backend
pytest
```

Mobile:
```bash
cd mobile
flutter test
```

## API Documentation

Once the backend is running, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## Roadmap

### Phase 1 (MVP) - Current
- [x] Basic project structure
- [ ] Real-time voice pipeline (STT → LLM → TTS)
- [ ] User authentication
- [ ] Basic conversation engine
- [ ] Mobile app with voice recording
- [ ] Support for 3 languages (Spanish, French, German)

### Phase 2 (Enhancement)
- [ ] Advanced pronunciation analysis
- [ ] Grammar correction with explanations
- [ ] Roleplay scenarios
- [ ] Spaced repetition system
- [ ] Vocabulary builder

### Phase 3 (Advanced)
- [ ] Multiple voice options
- [ ] Dialect variations
- [ ] Community features
- [ ] Gamification
- [ ] Offline mode

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Built with [Flutter](https://flutter.dev/)
- Powered by [FastAPI](https://fastapi.tiangolo.com/)
- AI services from [OpenAI](https://openai.com/), [Anthropic](https://anthropic.com/), and [ElevenLabs](https://elevenlabs.io/)

## Support

For questions or issues, please open an issue on GitHub or contact us at support@kalami.app

---

Made with ❤️ for language learners
