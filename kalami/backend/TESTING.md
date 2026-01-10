# Kalami Backend Testing Guide

## Overview

This document describes the comprehensive test suite for the Kalami backend API, covering authentication, user management, conversation sessions, and speech services.

## Test Structure

```
tests/
├── __init__.py              # Test package marker
├── conftest.py              # Pytest fixtures and configuration
├── test_auth.py             # Authentication and JWT tests
├── test_users.py            # User and learning profile tests
├── test_conversations.py    # Conversation session tests
└── test_speech.py           # STT/TTS service tests
```

## Prerequisites

### System Requirements
- Python 3.7+
- pip (Python package manager)
- Virtual environment (recommended)

### API Keys (for integration tests)
- **OpenAI API Key** - For Whisper STT and GPT fallback
- **ElevenLabs API Key** - For TTS synthesis
- **Anthropic API Key** - For Claude-powered conversations (optional)
- **Deepgram API Key** - For alternative STT (optional)

## Setup

### 1. Install Dependencies

```bash
cd /home/savetheworld/kalami/backend

# Option A: Use the provided script (recommended)
./run_tests.sh

# Option B: Manual installation
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
# Copy example environment file
cp .env.example .env

# Edit .env with your API keys
nano .env
```

For testing without external APIs, you can use mock mode (tests will mock API calls).

## Running Tests

### Run All Tests

```bash
# Using the script (recommended)
./run_tests.sh

# Or using pytest directly
source venv/bin/activate
pytest tests/ -v
```

### Run Specific Test Files

```bash
# Test authentication only
pytest tests/test_auth.py -v

# Test user management
pytest tests/test_users.py -v

# Test conversations
pytest tests/test_conversations.py -v

# Test speech services
pytest tests/test_speech.py -v
```

### Run Specific Test Classes

```bash
# Test only registration
pytest tests/test_auth.py::TestRegistration -v

# Test only learning profiles
pytest tests/test_users.py::TestLearningProfiles -v
```

### Run Specific Test Methods

```bash
# Test a single function
pytest tests/test_auth.py::TestLogin::test_login_success -v
```

### Run with Coverage

```bash
# Install coverage
pip install pytest-cov

# Run tests with coverage report
pytest tests/ --cov=app --cov-report=html --cov-report=term

# View HTML report
open htmlcov/index.html
```

## Test Categories

### 1. Authentication Tests (`test_auth.py`)

#### TestRegistration
- ✓ `test_register_new_user` - Successful user registration
- ✓ `test_register_duplicate_email` - Duplicate email handling
- ✓ `test_register_invalid_email` - Email validation
- ✓ `test_register_missing_password` - Required field validation

#### TestLogin
- ✓ `test_login_success` - Successful login with valid credentials
- ✓ `test_login_wrong_password` - Invalid password handling
- ✓ `test_login_nonexistent_user` - Non-existent user handling
- ✓ `test_login_missing_credentials` - Missing credentials validation

#### TestJWTAuthentication
- ✓ `test_get_current_user` - Get user from valid token
- ✓ `test_invalid_token` - Invalid token rejection
- ✓ `test_missing_token` - Missing token handling
- ✓ `test_expired_token` - Expired token rejection

#### TestPasswordHashing
- ✓ `test_password_is_hashed` - Password hashing verification
- ✓ `test_different_passwords_different_hashes` - Salt uniqueness

### 2. User & Profile Tests (`test_users.py`)

#### TestUserProfiles
- ✓ `test_get_user_stats` - User statistics retrieval

#### TestLearningProfiles
- ✓ `test_create_learning_profile` - Create new language profile
- ✓ `test_list_learning_profiles` - List user's profiles
- ✓ `test_get_learning_profile` - Get specific profile
- ✓ `test_update_learning_profile` - Update CEFR level
- ✓ `test_delete_learning_profile` - Delete profile
- ✓ `test_create_duplicate_language_profile` - Duplicate prevention

### 3. Conversation Tests (`test_conversations.py`)

#### TestConversationSessions
- ✓ `test_start_conversation_session` - Start new session
- ✓ `test_list_conversation_sessions` - List user's sessions
- ✓ `test_get_conversation_session` - Get session details
- ✓ `test_end_conversation_session` - End active session

#### TestConversationMessages
- ✓ `test_get_session_messages` - Retrieve session messages

### 4. Speech Service Tests (`test_speech.py`)

#### TestSpeechToText
- ✓ `test_transcribe_audio_success` - Successful transcription (mocked)
- ✓ `test_transcribe_audio_no_auth` - Authentication requirement
- ✓ `test_transcribe_audio_invalid_format` - Format validation
- ✓ `test_transcribe_multiple_languages` - Multi-language support

#### TestTextToSpeech
- ✓ `test_synthesize_speech_success` - Successful synthesis (mocked)
- ✓ `test_synthesize_speech_no_auth` - Authentication requirement
- ✓ `test_synthesize_empty_text` - Empty text validation
- ✓ `test_synthesize_long_text` - Long text handling
- ✓ `test_synthesize_different_voices` - Voice selection

#### TestSpeechServices
- ✓ `test_stt_service_whisper_api_call` - Whisper API integration
- ✓ `test_tts_service_elevenlabs_api_call` - ElevenLabs integration
- ✓ `test_stt_service_no_api_key_error` - Missing API key handling
- ✓ `test_tts_service_no_api_key_error` - Missing API key handling

#### TestPronunciationAssessment
- ✓ `test_assess_pronunciation` - Pronunciation scoring (mocked)

## Test Fixtures

### Database Fixtures
- **`db_session`** - Clean in-memory SQLite database for each test
- **`client`** - AsyncClient with database override

### Authentication Fixtures
- **`test_user`** - Pre-created test user account
- **`auth_token`** - Valid JWT token for test user
- **`auth_headers`** - Authorization headers with token

## Mocking Strategy

### External API Calls
All external API calls (OpenAI, ElevenLabs, Anthropic) are mocked by default using `unittest.mock.patch`:

```python
@patch("app.services.stt_service.STTService.transcribe_audio")
async def test_transcribe_audio_success(self, mock_transcribe, client):
    mock_transcribe.return_value = {
        "text": "Hola, ¿cómo estás?",
        "language": "es",
        "confidence": 0.95
    }
    # Test logic...
```

This ensures:
- ✓ Tests run without API keys
- ✓ Tests are fast (no network calls)
- ✓ Tests are deterministic
- ✓ No API costs during testing

### Database
- Uses in-memory SQLite (`sqlite+aiosqlite:///:memory:`)
- Fresh database for each test function
- Automatic cleanup after tests

## Common Issues & Solutions

### Issue: ModuleNotFoundError
```
Solution: Ensure virtual environment is activated and dependencies are installed
$ source venv/bin/activate
$ pip install -r requirements.txt
```

### Issue: Database Locked
```
Solution: Use separate database sessions per test (already configured in conftest.py)
```

### Issue: Async Test Errors
```
Solution: Ensure pytest-asyncio is installed and tests use @pytest.mark.asyncio
$ pip install pytest-asyncio
```

### Issue: API Key Errors During Tests
```
Solution: Tests mock external APIs. If integration tests are needed, set API keys in .env
```

## Writing New Tests

### Test Template

```python
import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
class TestFeatureName:
    """Test description."""

    async def test_specific_behavior(
        self,
        client: AsyncClient,
        test_user,
        auth_headers
    ):
        \"\"\"Test case description.\"\"\"
        # Arrange
        request_data = {"field": "value"}

        # Act
        response = await client.post(
            "/api/endpoint",
            headers=auth_headers,
            json=request_data
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["field"] == "expected_value"
```

### Best Practices

1. **Use descriptive test names** - `test_login_with_invalid_password` not `test_login_2`
2. **One assertion concept per test** - Test one behavior at a time
3. **Arrange-Act-Assert pattern** - Clear test structure
4. **Use fixtures** - Avoid duplicating setup code
5. **Mock external services** - Keep tests fast and reliable
6. **Test edge cases** - Empty strings, missing fields, invalid data
7. **Test authentication** - Both authenticated and unauthenticated requests

## Continuous Integration

### GitHub Actions Example

```yaml
name: Backend Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.12'
      - name: Install dependencies
        run: |
          cd kalami/backend
          pip install -r requirements.txt
      - name: Run tests
        run: |
          cd kalami/backend
          pytest tests/ -v --cov=app
```

## Performance Benchmarks

Typical test execution times:
- **Authentication tests** - ~2-3 seconds
- **User profile tests** - ~3-4 seconds
- **Conversation tests** - ~4-5 seconds
- **Speech service tests** - ~2-3 seconds
- **Total suite** - ~12-15 seconds

## Next Steps

1. Run the test suite: `./run_tests.sh`
2. Check coverage: `pytest --cov=app --cov-report=html`
3. Add integration tests for real API calls (optional)
4. Set up CI/CD pipeline
5. Add load testing for production readiness

## Resources

- [Pytest Documentation](https://docs.pytest.org/)
- [FastAPI Testing](https://fastapi.tiangolo.com/tutorial/testing/)
- [pytest-asyncio](https://pytest-asyncio.readthedocs.io/)
- [HTTPX Testing](https://www.python-httpx.org/async/)
