"""Speech-to-Text services for Kalami.

Supports:
- OpenAI Whisper API (primary)
- Deepgram (alternative for real-time streaming)
"""
import io
import httpx
from abc import ABC, abstractmethod
from typing import Optional, AsyncIterator
from dataclasses import dataclass

from ..core.config import settings


@dataclass
class TranscriptionResult:
    """Result from speech-to-text transcription."""
    text: str
    language: Optional[str] = None
    confidence: Optional[float] = None
    duration_seconds: Optional[float] = None
    is_final: bool = True


class STTService(ABC):
    """Abstract base class for Speech-to-Text services."""

    @abstractmethod
    async def transcribe(
        self,
        audio_data: bytes,
        language: Optional[str] = None,
        format: str = "wav"
    ) -> TranscriptionResult:
        """Transcribe audio data to text.

        Args:
            audio_data: Raw audio bytes
            language: Optional language code (e.g., 'en', 'es', 'fr')
            format: Audio format (wav, mp3, webm, etc.)

        Returns:
            TranscriptionResult with transcribed text
        """
        pass

    @abstractmethod
    async def transcribe_stream(
        self,
        audio_stream: AsyncIterator[bytes],
        language: Optional[str] = None
    ) -> AsyncIterator[TranscriptionResult]:
        """Stream transcription for real-time results.

        Args:
            audio_stream: Async iterator of audio chunks
            language: Optional language code

        Yields:
            TranscriptionResult objects (interim and final)
        """
        pass


class WhisperSTT(STTService):
    """OpenAI Whisper API implementation for speech-to-text.

    Best for:
    - High accuracy transcription
    - Multilingual support (97+ languages)
    - Audio files up to 25MB

    Note: Not suitable for real-time streaming (use Deepgram for that).
    """

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or settings.OPENAI_API_KEY
        self.model = settings.WHISPER_MODEL
        self.base_url = "https://api.openai.com/v1/audio"

    async def transcribe(
        self,
        audio_data: bytes,
        language: Optional[str] = None,
        format: str = "wav"
    ) -> TranscriptionResult:
        """Transcribe audio using Whisper API.

        Args:
            audio_data: Raw audio bytes
            language: ISO-639-1 language code (e.g., 'en', 'es')
            format: Audio format (wav, mp3, webm, m4a, etc.)

        Returns:
            TranscriptionResult with transcribed text
        """
        if not self.api_key:
            raise ValueError("OpenAI API key not configured. Set OPENAI_API_KEY.")

        # Prepare multipart form data
        files = {
            "file": (f"audio.{format}", io.BytesIO(audio_data), f"audio/{format}"),
            "model": (None, self.model),
        }

        if language:
            files["language"] = (None, language)

        # Optional: request word-level timestamps for pronunciation analysis
        files["response_format"] = (None, "verbose_json")

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/transcriptions",
                headers={"Authorization": f"Bearer {self.api_key}"},
                files=files,
                timeout=60.0
            )

            if response.status_code != 200:
                error_detail = response.text
                raise Exception(f"Whisper API error ({response.status_code}): {error_detail}")

            data = response.json()

            return TranscriptionResult(
                text=data.get("text", "").strip(),
                language=data.get("language"),
                duration_seconds=data.get("duration"),
                confidence=None,  # Whisper doesn't return confidence
                is_final=True
            )

    async def transcribe_stream(
        self,
        audio_stream: AsyncIterator[bytes],
        language: Optional[str] = None
    ) -> AsyncIterator[TranscriptionResult]:
        """Whisper doesn't support real-time streaming.

        This implementation buffers audio and transcribes periodically.
        For true real-time streaming, use DeepgramSTT.
        """
        buffer = bytearray()
        chunk_duration_seconds = 5  # Process every 5 seconds of audio

        # Assuming 16kHz, 16-bit mono audio
        bytes_per_second = 16000 * 2
        chunk_size = chunk_duration_seconds * bytes_per_second

        async for chunk in audio_stream:
            buffer.extend(chunk)

            if len(buffer) >= chunk_size:
                # Transcribe the buffer
                result = await self.transcribe(
                    bytes(buffer),
                    language=language,
                    format="wav"
                )
                result.is_final = False
                yield result
                buffer.clear()

        # Final transcription of remaining audio
        if buffer:
            result = await self.transcribe(
                bytes(buffer),
                language=language,
                format="wav"
            )
            result.is_final = True
            yield result


class DeepgramSTT(STTService):
    """Deepgram API implementation for real-time speech-to-text.

    Best for:
    - Real-time streaming transcription (<300ms latency)
    - WebSocket-based continuous transcription
    - Cost-effective at scale
    """

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or settings.DEEPGRAM_API_KEY
        self.base_url = "https://api.deepgram.com/v1"
        self.ws_url = "wss://api.deepgram.com/v1/listen"

    async def transcribe(
        self,
        audio_data: bytes,
        language: Optional[str] = None,
        format: str = "wav"
    ) -> TranscriptionResult:
        """Transcribe audio using Deepgram pre-recorded API."""
        if not self.api_key:
            raise ValueError("Deepgram API key not configured. Set DEEPGRAM_API_KEY.")

        params = {
            "model": "nova-2",
            "smart_format": "true",
        }
        if language:
            params["language"] = language

        content_type = f"audio/{format}"
        if format == "wav":
            content_type = "audio/wav"
        elif format == "mp3":
            content_type = "audio/mpeg"

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/listen",
                headers={
                    "Authorization": f"Token {self.api_key}",
                    "Content-Type": content_type,
                },
                params=params,
                content=audio_data,
                timeout=60.0
            )

            if response.status_code != 200:
                raise Exception(f"Deepgram API error: {response.text}")

            data = response.json()
            result = data.get("results", {}).get("channels", [{}])[0]
            alternative = result.get("alternatives", [{}])[0]

            return TranscriptionResult(
                text=alternative.get("transcript", "").strip(),
                language=data.get("metadata", {}).get("detected_language"),
                confidence=alternative.get("confidence"),
                duration_seconds=data.get("metadata", {}).get("duration"),
                is_final=True
            )

    async def transcribe_stream(
        self,
        audio_stream: AsyncIterator[bytes],
        language: Optional[str] = None
    ) -> AsyncIterator[TranscriptionResult]:
        """Real-time streaming transcription using Deepgram WebSocket.

        This provides true real-time results with interim transcriptions.
        """
        import websockets

        if not self.api_key:
            raise ValueError("Deepgram API key not configured.")

        params = "model=nova-2&smart_format=true&interim_results=true"
        if language:
            params += f"&language={language}"

        url = f"{self.ws_url}?{params}"

        async with websockets.connect(
            url,
            extra_headers={"Authorization": f"Token {self.api_key}"}
        ) as ws:
            import asyncio
            import json

            # Task to send audio
            async def send_audio():
                async for chunk in audio_stream:
                    await ws.send(chunk)
                # Signal end of audio
                await ws.send(json.dumps({"type": "CloseStream"}))

            # Start sending audio in background
            send_task = asyncio.create_task(send_audio())

            try:
                # Receive transcriptions
                async for message in ws:
                    data = json.loads(message)

                    if data.get("type") == "Results":
                        channel = data.get("channel", {})
                        alternatives = channel.get("alternatives", [{}])
                        if alternatives:
                            alt = alternatives[0]
                            yield TranscriptionResult(
                                text=alt.get("transcript", ""),
                                confidence=alt.get("confidence"),
                                is_final=data.get("is_final", False)
                            )
            finally:
                send_task.cancel()


def get_stt_service(provider: str = "whisper") -> STTService:
    """Factory function to get the appropriate STT service.

    Args:
        provider: 'whisper' or 'deepgram'

    Returns:
        Configured STTService instance
    """
    if provider == "deepgram":
        return DeepgramSTT()
    return WhisperSTT()
