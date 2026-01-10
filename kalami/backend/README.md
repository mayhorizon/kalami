# Kalami Backend API

FastAPI-based backend server for Kalami - an AI-powered vocal language learning assistant.

## Features

- 🔐 **JWT Authentication** - Secure user registration and login
- 👤 **User Profiles** - Multi-language learning profile management
- 💬 **AI Conversations** - Claude/GPT-powered language tutoring
- 🎤 **Speech-to-Text** - OpenAI Whisper & Deepgram support
- 🔊 **Text-to-Speech** - ElevenLabs multilingual synthesis
- 📊 **Progress Tracking** - Vocabulary mastery, streaks, speaking time
- 🌍 **Multilingual** - Support for multiple target languages with CEFR levels

## Architecture

```
app/
├── main.py                 # FastAPI application and lifecycle
├── core/
│   ├── config.py          # Settings and environment variables
│   └── database.py        # SQLAlchemy async setup
├── models/                # SQLAlchemy ORM models
│   ├── user.py           # User accounts
│   ├── learning_profile.py
│   ├── conversation.py   # Sessions and messages
│   ├── vocabulary.py     # Vocabulary tracking
│   └── pronunciation.py  # Pronunciation analysis
├── routers/              # API endpoints
│   ├── auth.py          # Registration, login, JWT
│   ├── users.py         # Profile management
│   ├── conversations.py # Chat sessions
│   └── speech.py        # STT/TTS
└── services/            # Business logic
    ├── auth_service.py
    ├── conversation_service.py
    ├── stt_service.py   # Speech-to-Text
    └── tts_service.py   # Text-to-Speech
```

## Prerequisites

- **Python 3.7+** (tested with 3.12)
- **pip** - Python package manager
- **API Keys** (optional for testing):
  - OpenAI API key (for Whisper STT and GPT)
  - ElevenLabs API key (for TTS)
  - Anthropic API key (for Claude conversations)
  - Deepgram API key (optional, for alternative STT)

## Quick Start

### 1. Clone and Navigate

```bash
cd /home/savetheworld/kalami/backend
```

### 2. Install Dependencies

```bash
# Using the provided script (recommended)
chmod +x run_tests.sh start_server.sh
./run_tests.sh

# Or manually
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 3. Configure Environment

```bash
# Copy example configuration
cp .env.example .env

# Edit with your API keys
nano .env
```

**Minimum configuration for testing:**
```env
SECRET_KEY=your-random-secret-key-here
DEBUG=true
DATABASE_URL=sqlite+aiosqlite:///./kalami.db
```

**Full configuration with AI features:**
```env
SECRET_KEY=your-secret-key
OPENAI_API_KEY=sk-...
ELEVENLABS_API_KEY=...
ANTHROPIC_API_KEY=sk-ant-...
```

### 4. Run the Server

```bash
# Using the script
./start_server.sh

# Or manually
source venv/bin/activate
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Server will be available at:
- **API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Alternative Docs**: http://localhost:8000/redoc

## API Endpoints

### Authentication (`/auth`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/auth/register` | Register new user account |
| POST | `/auth/login` | Login and get JWT token |
| GET | `/auth/me` | Get current user profile |

### Users (`/users`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/users/profiles` | List learning profiles |
| POST | `/users/profiles` | Create learning profile |
| GET | `/users/profiles/{id}` | Get profile details |
| PATCH | `/users/profiles/{id}` | Update CEFR level |
| DELETE | `/users/profiles/{id}` | Delete profile |
| GET | `/users/stats` | Get user statistics |

### Conversations (`/conversations`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/conversations/sessions` | Start new session |
| GET | `/conversations/sessions` | List sessions |
| GET | `/conversations/sessions/{id}` | Get session details |
| POST | `/conversations/sessions/{id}/end` | End session |
| GET | `/conversations/sessions/{id}/messages` | Get messages |
| POST | `/conversations/sessions/{id}/audio` | Send audio message |
| POST | `/conversations/sessions/{id}/text` | Send text message |

### Speech (`/speech`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/speech/transcribe` | Transcribe audio to text |
| POST | `/speech/synthesize` | Synthesize text to speech |
| POST | `/speech/synthesize/stream` | Stream TTS for low latency |
| GET | `/speech/voices` | List available voices |

## Testing

### Run Test Suite

```bash
# All tests
./run_tests.sh

# Specific test file
pytest tests/test_auth.py -v

# With coverage
pytest tests/ --cov=app --cov-report=html
```

See [TESTING.md](TESTING.md) for comprehensive testing documentation.

### Test Coverage

- ✅ Authentication (registration, login, JWT)
- ✅ User management (profiles, CEFR levels)
- ✅ Learning profiles (create, update, delete)
- ✅ Conversation sessions (start, end, messages)
- ✅ Speech services (STT, TTS with mocks)
- ✅ Database operations
- ✅ Error handling

## Database

### Schema

- **users** - User accounts with authentication
- **learning_profiles** - Language learning progress per language
- **conversation_sessions** - Practice conversation sessions
- **conversation_messages** - Individual messages in sessions
- **user_vocabulary** - Vocabulary tracking
- **pronunciation_analysis** - Pronunciation assessment data

### Migrations

The application uses SQLAlchemy with auto-migration on startup. For production, consider using Alembic:

```bash
pip install alembic
alembic init alembic
alembic revision --autogenerate -m "Initial migration"
alembic upgrade head
```

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `APP_NAME` | Application name | Kalami |
| `DEBUG` | Debug mode | true |
| `DATABASE_URL` | Database connection string | sqlite+aiosqlite:///./kalami.db |
| `SECRET_KEY` | JWT secret key | (must set) |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | JWT expiration | 30 |
| `OPENAI_API_KEY` | OpenAI API key for Whisper | - |
| `ELEVENLABS_API_KEY` | ElevenLabs API key | - |
| `ANTHROPIC_API_KEY` | Anthropic Claude API key | - |
| `DEEPGRAM_API_KEY` | Deepgram API key (optional) | - |

### API Provider Selection

**Speech-to-Text:**
- Primary: OpenAI Whisper (high accuracy, 97+ languages)
- Alternative: Deepgram (real-time streaming, lower latency)

**Text-to-Speech:**
- Primary: ElevenLabs (natural voices, multilingual)
- Alternative: OpenAI TTS (included with Whisper API key)

**Conversation LLM:**
- Primary: Anthropic Claude (if `ANTHROPIC_API_KEY` set)
- Fallback: OpenAI GPT (if `OPENAI_API_KEY` set)

## Development

### Code Style

```bash
# Format code
black app/ tests/

# Lint
flake8 app/ tests/

# Type checking
mypy app/
```

### Adding New Endpoints

1. Define Pydantic models in router file
2. Create router function with `@router.post/get/...`
3. Implement business logic in service layer
4. Add tests in `tests/test_*.py`
5. Update this README

### Database Changes

1. Modify model in `app/models/`
2. Restart server (auto-migration will run)
3. For production, create Alembic migration

## Deployment

### Production Checklist

- [ ] Set strong `SECRET_KEY` (use `openssl rand -hex 32`)
- [ ] Set `DEBUG=false`
- [ ] Use production database (PostgreSQL recommended)
- [ ] Configure CORS for your mobile app domain
- [ ] Enable HTTPS with reverse proxy (nginx/Caddy)
- [ ] Set up monitoring and logging
- [ ] Configure rate limiting
- [ ] Backup database regularly
- [ ] Rotate API keys periodically

### Docker Deployment

```dockerfile
FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ app/

ENV DATABASE_URL=postgresql+asyncpg://user:pass@db:5432/kalami
ENV DEBUG=false

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", 8000"]
```

```bash
docker build -t kalami-backend .
docker run -p 8000:8000 --env-file .env kalami-backend
```

### Cloud Deployment

**AWS/GCP/Azure:**
- Use managed PostgreSQL for database
- Deploy with ECS/Cloud Run/App Service
- Use Secrets Manager for API keys
- Configure auto-scaling

**Serverless:**
- Use AWS Lambda with Mangum adapter
- DynamoDB or Aurora Serverless for database
- API Gateway for routing

## Troubleshooting

### Common Issues

**Issue: Module not found errors**
```bash
# Ensure virtual environment is activated
source venv/bin/activate
pip install -r requirements.txt
```

**Issue: Database locked**
```bash
# SQLite issue - use PostgreSQL for production
# Or ensure only one instance is running
```

**Issue: API key errors**
```bash
# Check .env file exists and has valid keys
cat .env
# Restart server after changing .env
```

**Issue: CORS errors from mobile app**
```python
# Update CORS origins in app/main.py
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "your-mobile-app-url"],
    ...
)
```

## Performance

### Benchmarks

- Authentication: ~50ms
- Profile operations: ~30ms
- STT (Whisper): ~2-4s for 10s audio
- TTS (ElevenLabs): ~1-2s for short text
- Conversation turn: ~3-6s (STT + LLM + TTS)

### Optimization Tips

1. Use connection pooling for database
2. Cache TTS audio for common phrases
3. Pre-load user context to reduce DB queries
4. Use Deepgram for streaming STT (lower latency)
5. Implement request rate limiting

## API Rate Limits

### External Services

- **OpenAI**: 3500 requests/min (paid tier)
- **ElevenLabs**: Varies by plan (10k chars/month free)
- **Anthropic**: 1000 requests/min (paid tier)
- **Deepgram**: Varies by plan

### Backend Limits

Consider implementing rate limiting:

```python
from slowapi import Limiter
limiter = Limiter(key_func=get_remote_address)

@app.post("/conversations/sessions")
@limiter.limit("10/minute")
async def start_session(...):
    ...
```

## Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Write tests for new functionality
4. Ensure all tests pass (`pytest tests/`)
5. Commit changes (`git commit -m 'Add amazing feature'`)
6. Push to branch (`git push origin feature/amazing-feature`)
7. Open Pull Request

## License

[Add your license here]

## Support

For issues, questions, or contributions:
- GitHub Issues: [Link to issues]
- Documentation: See TESTING.md for test documentation
- API Reference: http://localhost:8000/docs (when server is running)

## Roadmap

- [ ] WebSocket support for real-time conversations
- [ ] Pronunciation assessment with word-level feedback
- [ ] Spaced repetition vocabulary system
- [ ] Integration with language learning APIs
- [ ] Mobile app sync and offline support
- [ ] Admin dashboard for user management
- [ ] Analytics and progress visualization
- [ ] Multi-tenant support for schools/organizations
