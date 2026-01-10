# Kalami Backend - Quick Start Guide

## TL;DR - Get Running in 3 Minutes

```bash
# 1. Install pip (if needed)
sudo apt-get update && sudo apt-get install -y python3-pip

# 2. Navigate to backend
cd /home/savetheworld/kalami/backend

# 3. Run tests (automatically sets up everything)
./run_tests.sh

# 4. Start server
./start_server.sh
```

Visit http://localhost:8000/docs to see the API documentation.

## Prerequisites Check

```bash
# Check Python version (need 3.7+)
python3 --version
# Should show: Python 3.12.3 or higher

# Check if pip is installed
python3 -m pip --version
# If error, install pip:
sudo apt-get install python3-pip
```

## Installation Steps

### Step 1: Install Dependencies

```bash
cd /home/savetheworld/kalami/backend

# Option A: Automated (recommended)
./run_tests.sh
# This will:
# - Install pip if needed
# - Create virtual environment
# - Install all dependencies
# - Run test suite

# Option B: Manual
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Step 2: Configure Environment

```bash
# Copy example config
cp .env.example .env

# For basic testing (no AI features)
cat > .env << EOF
SECRET_KEY=$(openssl rand -hex 32)
DEBUG=true
DATABASE_URL=sqlite+aiosqlite:///./kalami.db
EOF

# For full features, edit .env and add API keys:
nano .env
```

**Required API Keys for Full Functionality:**
- OpenAI: https://platform.openai.com/api-keys
- ElevenLabs: https://elevenlabs.io/
- Anthropic: https://console.anthropic.com/

### Step 3: Run Tests

```bash
# All tests
./run_tests.sh

# Or manually
source venv/bin/activate
pytest tests/ -v

# With coverage
pytest tests/ --cov=app --cov-report=html
# View: open htmlcov/index.html
```

### Step 4: Start Server

```bash
# Using script
./start_server.sh

# Or manually
source venv/bin/activate
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

**Access Points:**
- API: http://localhost:8000
- Interactive Docs: http://localhost:8000/docs
- Alternative Docs: http://localhost:8000/redoc

## Testing the API

### 1. Health Check

```bash
curl http://localhost:8000/health
```

Expected response:
```json
{
  "status": "healthy",
  "services": {
    "database": "connected",
    "stt": "whisper",
    "tts": "elevenlabs",
    "llm": "anthropic"
  }
}
```

### 2. Register a User

```bash
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "securepassword123",
    "native_language": "en"
  }'
```

### 3. Login

```bash
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=test@example.com&password=securepassword123"
```

Save the `access_token` from response.

### 4. Create Learning Profile

```bash
TOKEN="your-token-here"

curl -X POST http://localhost:8000/users/profiles \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "target_language": "es",
    "cefr_level": "A1"
  }'
```

## Common Issues

### Issue: "No module named pip"

**Solution:**
```bash
sudo apt-get update
sudo apt-get install python3-pip
```

### Issue: "Permission denied" on scripts

**Solution:**
```bash
chmod +x run_tests.sh start_server.sh
```

### Issue: "Port 8000 already in use"

**Solution:**
```bash
# Find and kill process using port 8000
lsof -ti:8000 | xargs kill -9

# Or use different port
uvicorn app.main:app --port 8001
```

### Issue: API key errors

**Solution:**
```bash
# Check .env file exists and has keys
cat .env

# Restart server after changing .env
# Keys are loaded on startup
```

### Issue: Database locked

**Solution:**
```bash
# Stop all running instances
pkill -f uvicorn

# Remove database file
rm kalami.db

# Restart server (will recreate DB)
./start_server.sh
```

## File Structure

```
kalami/backend/
├── app/                    # Application code
│   ├── main.py            # FastAPI app
│   ├── core/              # Config, database
│   ├── models/            # SQLAlchemy models
│   ├── routers/           # API endpoints
│   └── services/          # Business logic
├── tests/                 # Test suite
│   ├── conftest.py       # Test fixtures
│   ├── test_auth.py      # Auth tests
│   ├── test_users.py     # User tests
│   ├── test_conversations.py
│   └── test_speech.py
├── requirements.txt       # Dependencies
├── .env.example          # Config template
├── run_tests.sh          # Test runner
├── start_server.sh       # Server starter
├── README.md             # Full documentation
├── TESTING.md            # Test documentation
└── QUICKSTART.md         # This file
```

## Next Steps

1. ✅ Get server running
2. ✅ Test API with curl or Postman
3. ✅ Explore interactive docs at /docs
4. ✅ Connect mobile app (separate project)
5. ✅ Deploy to production

## Resources

- **Full Documentation:** [README.md](README.md)
- **Testing Guide:** [TESTING.md](TESTING.md)
- **Test Report:** [TEST_REPORT.md](TEST_REPORT.md)
- **API Docs:** http://localhost:8000/docs (when running)
- **FastAPI Docs:** https://fastapi.tiangolo.com/
- **SQLAlchemy Docs:** https://docs.sqlalchemy.org/

## Support

Need help? Check:
1. Error logs in terminal
2. API docs at /docs
3. Test output: `pytest tests/ -v`
4. Database: `sqlite3 kalami.db .schema`

## Production Deployment

See [README.md](README.md#deployment) for:
- Docker deployment
- Cloud deployment (AWS, GCP, Azure)
- Security checklist
- Performance optimization

---

**Happy coding!** 🚀
