"""
Speech-to-Text service using OpenAI Whisper
"""
import io
from typing import Optional
import openai
from app.core.config import settings


class WhisperSTTService:
    """Speech-to-Text service using OpenAI Whisper API"""

    def __init__(self):
        """Initialize Whisper STT service"""
        self.client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = "whisper-1"

    async def transcribe(
        self,
        audio_data: bytes,
        language: Optional[str] = None,
        prompt: Optional[str] = None
    ) -> str:
        """
        Transcribe audio to text

        Args:
            audio_data: Audio file bytes (wav, mp3, m4a, etc.)
            language: ISO-639-1 language code (e.g., 'es', 'fr', 'de')
            prompt: Optional text to guide the model's style

        Returns:
            Transcribed text
        """
        try:
            # Create file-like object from bytes
            audio_file = io.BytesIO(audio_data)
            audio_file.name = "audio.wav"

            # Call Whisper API
            transcript = self.client.audio.transcriptions.create(
                model=self.model,
                file=audio_file,
                language=language,
                prompt=prompt,
                response_format="text"
            )

            return transcript.strip()

        except Exception as e:
            raise Exception(f"Transcription failed: {str(e)}")

    async def transcribe_streaming(
        self,
        audio_stream,
        language: Optional[str] = None
    ):
        """
        Transcribe streaming audio (for real-time use)

        Args:
            audio_stream: Async generator of audio chunks
            language: ISO-639-1 language code

        Yields:
            Transcribed text chunks
        """
        # TODO: Implement streaming transcription
        # Note: OpenAI Whisper doesn't support streaming yet
        # Consider using AssemblyAI for real-time streaming
        raise NotImplementedError("Streaming transcription not yet implemented")
