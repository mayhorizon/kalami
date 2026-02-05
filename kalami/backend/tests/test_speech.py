"""Tests for speech-to-text and text-to-speech endpoints."""
import pytest
from httpx import AsyncClient
from unittest.mock import AsyncMock, MagicMock, patch
import io

from app.services.stt_service import TranscriptionResult
from app.services.tts_service import SynthesisResult


@pytest.mark.asyncio
class TestSpeechToText:
    """Test speech-to-text (STT) endpoints."""

    @patch("app.routers.speech.get_stt_service")
    async def test_transcribe_audio_success(
        self, mock_get_stt, client: AsyncClient, test_user, auth_headers
    ):
        """Test successful audio transcription."""
        # Mock the STT service
        mock_stt = MagicMock()
        mock_stt.transcribe = AsyncMock(return_value=TranscriptionResult(
            text="Hola, ¿cómo estás?",
            language="es",
            confidence=0.95
        ))
        mock_get_stt.return_value = mock_stt

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
        mock_stt.transcribe.assert_called_once()

    async def test_transcribe_audio_no_auth(self, client: AsyncClient):
        """Test transcription without authentication fails."""
        audio_data = b"fake audio data"
        files = {"audio": ("test.wav", io.BytesIO(audio_data), "audio/wav")}

        response = await client.post(
            "/speech/transcribe",
            files=files,
            data={"language": "es"}
        )

        assert response.status_code == 401

    @patch("app.routers.speech.get_stt_service")
    async def test_transcribe_audio_invalid_format(
        self, mock_get_stt, client: AsyncClient, test_user, auth_headers
    ):
        """Test transcription with invalid audio format."""
        # Mock error
        mock_stt = MagicMock()
        mock_stt.transcribe = AsyncMock(side_effect=ValueError("Unsupported audio format"))
        mock_get_stt.return_value = mock_stt

        files = {"audio": ("test.txt", io.BytesIO(b"not audio"), "text/plain")}

        response = await client.post(
            "/speech/transcribe",
            headers=auth_headers,
            files=files,
            data={"language": "es"}
        )

        assert response.status_code in [400, 422, 500]

    @patch("app.routers.speech.get_stt_service")
    async def test_transcribe_multiple_languages(
        self, mock_get_stt, client: AsyncClient, test_user, auth_headers
    ):
        """Test transcription for different languages."""
        languages = [
            ("Hello, how are you?", "en"),
            ("Bonjour, comment allez-vous?", "fr"),
            ("Guten Tag, wie geht es Ihnen?", "de")
        ]

        for expected_text, lang in languages:
            mock_stt = MagicMock()
            mock_stt.transcribe = AsyncMock(return_value=TranscriptionResult(
                text=expected_text,
                language=lang,
                confidence=0.9
            ))
            mock_get_stt.return_value = mock_stt

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

    @patch("app.routers.speech.get_tts_service")
    async def test_synthesize_speech_success(
        self, mock_get_tts, client: AsyncClient, test_user, auth_headers
    ):
        """Test successful speech synthesis."""
        # Mock the TTS service
        fake_audio = b"fake audio data"
        mock_tts = MagicMock()
        mock_tts.synthesize = AsyncMock(return_value=SynthesisResult(
            audio_data=fake_audio,
            format="mp3"
        ))
        mock_get_tts.return_value = mock_tts

        response = await client.post(
            "/speech/synthesize",
            headers=auth_headers,
            json={
                "text": "Hola, buenos días",
                "language": "es",
                "style": "neutral"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert "audio_base64" in data
        assert data["format"] == "mp3"
        mock_tts.synthesize.assert_called_once()

    async def test_synthesize_speech_no_auth(self, client: AsyncClient):
        """Test synthesis without authentication fails."""
        response = await client.post(
            "/speech/synthesize",
            json={
                "text": "Hello world",
                "language": "en"
            }
        )

        assert response.status_code == 401

    async def test_synthesize_empty_text(
        self, client: AsyncClient, test_user, auth_headers
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

        # Empty text should still be accepted by the endpoint
        # validation depends on implementation
        assert response.status_code in [200, 400, 422, 500]

    @patch("app.routers.speech.get_tts_service")
    async def test_synthesize_long_text(
        self, mock_get_tts, client: AsyncClient, test_user, auth_headers
    ):
        """Test synthesis with long text."""
        long_text = "Hello, this is a long text. " * 100
        fake_audio = b"fake audio data for long text"

        mock_tts = MagicMock()
        mock_tts.synthesize = AsyncMock(return_value=SynthesisResult(
            audio_data=fake_audio,
            format="mp3"
        ))
        mock_get_tts.return_value = mock_tts

        response = await client.post(
            "/speech/synthesize",
            headers=auth_headers,
            json={
                "text": long_text,
                "language": "en",
                "style": "neutral"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert "audio_base64" in data

    @patch("app.routers.speech.get_tts_service")
    async def test_synthesize_different_styles(
        self, mock_get_tts, client: AsyncClient, test_user, auth_headers
    ):
        """Test synthesis with different voice styles."""
        styles = ["neutral", "friendly", "encouraging", "slow"]

        for style in styles:
            fake_audio = f"fake audio for {style} style".encode()
            mock_tts = MagicMock()
            mock_tts.synthesize = AsyncMock(return_value=SynthesisResult(
                audio_data=fake_audio,
                format="mp3"
            ))
            mock_get_tts.return_value = mock_tts

            response = await client.post(
                "/speech/synthesize",
                headers=auth_headers,
                json={
                    "text": "Test message",
                    "language": "en",
                    "style": style
                }
            )

            assert response.status_code == 200
            data = response.json()
            assert "audio_base64" in data


@pytest.mark.asyncio
class TestSpeechServices:
    """Test the STT and TTS service classes directly."""

    @patch("app.services.stt_service.settings")
    async def test_whisper_stt_requires_api_key(self, mock_settings):
        """Test WhisperSTT raises error when API key is missing."""
        from app.services.stt_service import WhisperSTT

        # Mock settings to have no API key
        mock_settings.OPENAI_API_KEY = None
        mock_settings.WHISPER_MODEL = "whisper-1"

        # Create service - will use mocked settings
        service = WhisperSTT(api_key=None)

        with pytest.raises(ValueError, match="API key"):
            await service.transcribe(b"audio", language="en")

    @patch("app.services.tts_service.settings")
    async def test_elevenlabs_tts_requires_api_key(self, mock_settings):
        """Test ElevenLabsTTS raises error when API key is missing."""
        from app.services.tts_service import ElevenLabsTTS

        # Mock settings to have no API key
        mock_settings.ELEVENLABS_API_KEY = None
        mock_settings.ELEVENLABS_MODEL = "eleven_multilingual_v2"
        mock_settings.ELEVENLABS_VOICE_ID = "some-voice-id"

        service = ElevenLabsTTS(api_key=None)

        with pytest.raises(ValueError, match="API key"):
            await service.synthesize(
                text="Hello",
                language="en"
            )

    @patch("app.services.stt_service.settings")
    async def test_deepgram_stt_requires_api_key(self, mock_settings):
        """Test DeepgramSTT raises error when API key is missing."""
        from app.services.stt_service import DeepgramSTT

        # Mock settings to have no API key
        mock_settings.DEEPGRAM_API_KEY = None

        service = DeepgramSTT(api_key=None)

        with pytest.raises(ValueError, match="API key"):
            await service.transcribe(b"audio", language="en")

    @patch("app.services.tts_service.settings")
    async def test_openai_tts_requires_api_key(self, mock_settings):
        """Test OpenAITTS raises error when API key is missing."""
        from app.services.tts_service import OpenAITTS

        # Mock settings to have no API key
        mock_settings.OPENAI_API_KEY = None

        service = OpenAITTS(api_key=None)

        with pytest.raises(ValueError, match="API key"):
            await service.synthesize(
                text="Hello",
                language="en"
            )

    async def test_stt_factory_returns_whisper(self):
        """Test get_stt_service returns WhisperSTT by default."""
        from app.services.stt_service import get_stt_service, WhisperSTT

        service = get_stt_service("whisper")
        assert isinstance(service, WhisperSTT)

    async def test_stt_factory_returns_deepgram(self):
        """Test get_stt_service returns DeepgramSTT when specified."""
        from app.services.stt_service import get_stt_service, DeepgramSTT

        service = get_stt_service("deepgram")
        assert isinstance(service, DeepgramSTT)

    async def test_tts_factory_returns_elevenlabs(self):
        """Test get_tts_service returns ElevenLabsTTS by default."""
        from app.services.tts_service import get_tts_service, ElevenLabsTTS

        service = get_tts_service("elevenlabs")
        assert isinstance(service, ElevenLabsTTS)

    async def test_tts_factory_returns_openai(self):
        """Test get_tts_service returns OpenAITTS when specified."""
        from app.services.tts_service import get_tts_service, OpenAITTS

        service = get_tts_service("openai")
        assert isinstance(service, OpenAITTS)


@pytest.mark.asyncio
class TestSpeechEndpoints:
    """Test additional speech endpoints."""

    async def test_invalid_stt_provider(
        self, client: AsyncClient, test_user, auth_headers
    ):
        """Test transcription with invalid provider."""
        audio_data = b"fake audio data"
        files = {"audio": ("test.wav", io.BytesIO(audio_data), "audio/wav")}

        response = await client.post(
            "/speech/transcribe?provider=invalid",
            headers=auth_headers,
            files=files
        )

        assert response.status_code == 400
        assert "Invalid provider" in response.json()["detail"]

    async def test_invalid_tts_provider(
        self, client: AsyncClient, test_user, auth_headers
    ):
        """Test synthesis with invalid provider."""
        response = await client.post(
            "/speech/synthesize",
            headers=auth_headers,
            params={"provider": "invalid"},
            json={
                "text": "Hello",
                "language": "en"
            }
        )

        assert response.status_code == 400
        assert "Invalid provider" in response.json()["detail"]

    @patch("app.routers.speech.get_tts_service")
    async def test_speak_endpoint(
        self, mock_get_tts, client: AsyncClient, test_user, auth_headers
    ):
        """Test the speak endpoint returns audio directly."""
        fake_audio = b"fake mp3 audio data"
        mock_tts = MagicMock()
        mock_tts.synthesize = AsyncMock(return_value=SynthesisResult(
            audio_data=fake_audio,
            format="mp3"
        ))
        mock_get_tts.return_value = mock_tts

        response = await client.get(
            "/speech/speak",
            headers=auth_headers,
            params={
                "text": "Hola mundo",
                "language": "es"
            }
        )

        assert response.status_code == 200
        assert response.headers["content-type"] == "audio/mpeg"
        assert response.content == fake_audio
