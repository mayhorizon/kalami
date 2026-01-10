"""Tests for speech-to-text and text-to-speech endpoints."""
import pytest
from httpx import AsyncClient
from unittest.mock import AsyncMock, MagicMock, patch
import io


@pytest.mark.asyncio
class TestSpeechToText:
    """Test speech-to-text (STT) endpoints."""

    @patch("app.services.stt_service.STTService.transcribe_audio")
    async def test_transcribe_audio_success(
        self, mock_transcribe, client: AsyncClient, test_user, auth_headers
    ):
        """Test successful audio transcription."""
        # Mock the transcription response
        mock_transcribe.return_value = {
            "text": "Hola, ¿cómo estás?",
            "language": "es",
            "confidence": 0.95
        }

        # Create fake audio file
        audio_data = b"fake audio data"
        files = {"audio": ("test.wav", io.BytesIO(audio_data), "audio/wav")}

        response = await client.post(
            "/speech/transcribe",
            headers=auth_headers,
            files=files,
            data={"language": "es"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["text"] == "Hola, ¿cómo estás?"
        assert data["language"] == "es"
        assert data["confidence"] == 0.95
        mock_transcribe.assert_called_once()

    @patch("app.services.stt_service.STTService.transcribe_audio")
    async def test_transcribe_audio_no_auth(self, mock_transcribe, client: AsyncClient):
        """Test transcription without authentication fails."""
        audio_data = b"fake audio data"
        files = {"audio": ("test.wav", io.BytesIO(audio_data), "audio/wav")}

        response = await client.post(
            "/speech/transcribe",
            files=files,
            data={"language": "es"}
        )

        assert response.status_code == 401
        mock_transcribe.assert_not_called()

    @patch("app.services.stt_service.STTService.transcribe_audio")
    async def test_transcribe_audio_invalid_format(
        self, mock_transcribe, client: AsyncClient, test_user, auth_headers
    ):
        """Test transcription with invalid audio format."""
        # Mock error
        mock_transcribe.side_effect = ValueError("Unsupported audio format")

        files = {"audio": ("test.txt", io.BytesIO(b"not audio"), "text/plain")}

        response = await client.post(
            "/speech/transcribe",
            headers=auth_headers,
            files=files,
            data={"language": "es"}
        )

        assert response.status_code in [400, 422, 500]

    @patch("app.services.stt_service.STTService.transcribe_audio")
    async def test_transcribe_multiple_languages(
        self, mock_transcribe, client: AsyncClient, test_user, auth_headers
    ):
        """Test transcription for different languages."""
        languages = [
            ("Hello, how are you?", "en"),
            ("Bonjour, comment allez-vous?", "fr"),
            ("Guten Tag, wie geht es Ihnen?", "de")
        ]

        for expected_text, lang in languages:
            mock_transcribe.return_value = {
                "text": expected_text,
                "language": lang,
                "confidence": 0.9
            }

            audio_data = b"fake audio data"
            files = {"audio": (f"test_{lang}.wav", io.BytesIO(audio_data), "audio/wav")}

            response = await client.post(
                "/speech/transcribe",
                headers=auth_headers,
                files=files,
                data={"language": lang}
            )

            assert response.status_code == 200
            data = response.json()
            assert data["text"] == expected_text
            assert data["language"] == lang


@pytest.mark.asyncio
class TestTextToSpeech:
    """Test text-to-speech (TTS) endpoints."""

    @patch("app.services.tts_service.TTSService.synthesize_speech")
    async def test_synthesize_speech_success(
        self, mock_synthesize, client: AsyncClient, test_user, auth_headers
    ):
        """Test successful speech synthesis."""
        # Mock the synthesis response
        fake_audio = b"fake audio data"
        mock_synthesize.return_value = fake_audio

        response = await client.post(
            "/speech/synthesize",
            headers=auth_headers,
            json={
                "text": "Hola, buenos días",
                "language": "es",
                "voice": "female"
            }
        )

        assert response.status_code == 200
        assert response.headers["content-type"] == "audio/mpeg"
        assert len(response.content) > 0
        mock_synthesize.assert_called_once()

    @patch("app.services.tts_service.TTSService.synthesize_speech")
    async def test_synthesize_speech_no_auth(self, mock_synthesize, client: AsyncClient):
        """Test synthesis without authentication fails."""
        response = await client.post(
            "/speech/synthesize",
            json={
                "text": "Hello world",
                "language": "en"
            }
        )

        assert response.status_code == 401
        mock_synthesize.assert_not_called()

    @patch("app.services.tts_service.TTSService.synthesize_speech")
    async def test_synthesize_empty_text(
        self, mock_synthesize, client: AsyncClient, test_user, auth_headers
    ):
        """Test synthesis with empty text."""
        response = await client.post(
            "/speech/synthesize",
            headers=auth_headers,
            json={
                "text": "",
                "language": "en"
            }
        )

        assert response.status_code == 422  # Validation error

    @patch("app.services.tts_service.TTSService.synthesize_speech")
    async def test_synthesize_long_text(
        self, mock_synthesize, client: AsyncClient, test_user, auth_headers
    ):
        """Test synthesis with long text."""
        long_text = "Hello, this is a long text. " * 100
        fake_audio = b"fake audio data for long text"
        mock_synthesize.return_value = fake_audio

        response = await client.post(
            "/speech/synthesize",
            headers=auth_headers,
            json={
                "text": long_text,
                "language": "en",
                "voice": "male"
            }
        )

        assert response.status_code == 200
        assert len(response.content) > 0

    @patch("app.services.tts_service.TTSService.synthesize_speech")
    async def test_synthesize_different_voices(
        self, mock_synthesize, client: AsyncClient, test_user, auth_headers
    ):
        """Test synthesis with different voice options."""
        voices = ["female", "male"]

        for voice in voices:
            fake_audio = f"fake audio for {voice} voice".encode()
            mock_synthesize.return_value = fake_audio

            response = await client.post(
                "/speech/synthesize",
                headers=auth_headers,
                json={
                    "text": "Test message",
                    "language": "en",
                    "voice": voice
                }
            )

            assert response.status_code == 200
            assert len(response.content) > 0


@pytest.mark.asyncio
class TestSpeechServices:
    """Test the STT and TTS service classes directly."""

    @patch("httpx.AsyncClient.post")
    async def test_stt_service_whisper_api_call(self, mock_post):
        """Test STTService makes correct API call to Whisper."""
        from app.services.stt_service import STTService
        from app.core.config import settings

        # Mock successful API response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "text": "Hello world",
            "language": "en"
        }
        mock_post.return_value = mock_response

        # Create service
        service = STTService()
        audio_data = b"fake audio"

        # Test transcription (only if API key is configured)
        if settings.OPENAI_API_KEY:
            result = await service.transcribe_audio(audio_data, language="en")
            assert result["text"] == "Hello world"

    @patch("httpx.AsyncClient.post")
    async def test_tts_service_elevenlabs_api_call(self, mock_post):
        """Test TTSService makes correct API call to ElevenLabs."""
        from app.services.tts_service import TTSService
        from app.core.config import settings

        # Mock successful API response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = b"fake audio content"
        mock_post.return_value = mock_response

        # Create service
        service = TTSService()

        # Test synthesis (only if API key is configured)
        if settings.ELEVENLABS_API_KEY:
            result = await service.synthesize_speech(
                text="Hello",
                language="en",
                voice="female"
            )
            assert len(result) > 0

    async def test_stt_service_no_api_key_error(self):
        """Test STTService raises error when API key is missing."""
        from app.services.stt_service import STTService
        from app.core.config import settings

        original_key = settings.OPENAI_API_KEY
        settings.OPENAI_API_KEY = None

        service = STTService()

        with pytest.raises(Exception):
            await service.transcribe_audio(b"audio", language="en")

        settings.OPENAI_API_KEY = original_key

    async def test_tts_service_no_api_key_error(self):
        """Test TTSService raises error when API key is missing."""
        from app.services.tts_service import TTSService
        from app.core.config import settings

        original_key = settings.ELEVENLABS_API_KEY
        settings.ELEVENLABS_API_KEY = None

        service = TTSService()

        with pytest.raises(Exception):
            await service.synthesize_speech(
                text="Hello",
                language="en",
                voice="female"
            )

        settings.ELEVENLABS_API_KEY = original_key


@pytest.mark.asyncio
class TestPronunciationAssessment:
    """Test pronunciation assessment functionality."""

    @patch("app.services.stt_service.STTService.assess_pronunciation")
    async def test_assess_pronunciation(
        self, mock_assess, client: AsyncClient, test_user, auth_headers
    ):
        """Test pronunciation assessment endpoint."""
        mock_assess.return_value = {
            "score": 85,
            "feedback": "Good pronunciation overall",
            "word_scores": [
                {"word": "hola", "score": 90},
                {"word": "buenos", "score": 80},
                {"word": "días", "score": 85}
            ]
        }

        audio_data = b"fake audio data"
        files = {"audio": ("test.wav", io.BytesIO(audio_data), "audio/wav")}

        response = await client.post(
            "/speech/assess-pronunciation",
            headers=auth_headers,
            files=files,
            data={
                "text": "hola buenos días",
                "language": "es"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["score"] == 85
        assert "word_scores" in data
        assert len(data["word_scores"]) == 3
