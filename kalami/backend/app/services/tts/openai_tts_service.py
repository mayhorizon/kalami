"""
Text-to-Speech service using OpenAI TTS
"""
from typing import Literal
import openai
from app.core.config import settings


class OpenAITTSService:
    """Text-to-Speech service using OpenAI TTS API"""

    def __init__(self):
        """Initialize OpenAI TTS service"""
        self.client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = "tts-1"  # or "tts-1-hd" for higher quality

        # Voice options: alloy, echo, fable, onyx, nova, shimmer
        self.default_voice = "nova"

    async def synthesize(
        self,
        text: str,
        voice: str = None,
        speed: float = 1.0,
        response_format: Literal["mp3", "opus", "aac", "flac"] = "mp3"
    ) -> bytes:
        """
        Convert text to speech

        Args:
            text: Text to convert to speech
            voice: Voice to use (alloy, echo, fable, onyx, nova, shimmer)
            speed: Speed of speech (0.25 to 4.0)
            response_format: Audio format

        Returns:
            Audio bytes
        """
        try:
            if voice is None:
                voice = self.default_voice

            # Call OpenAI TTS API
            response = self.client.audio.speech.create(
                model=self.model,
                voice=voice,
                input=text,
                speed=speed,
                response_format=response_format
            )

            # Return audio bytes
            return response.content

        except Exception as e:
            raise Exception(f"Speech synthesis failed: {str(e)}")

    def get_voice_for_language(self, language: str) -> str:
        """
        Get recommended voice for a language

        Args:
            language: ISO-639-1 language code

        Returns:
            Voice name
        """
        # Map languages to voices
        # This is a simple mapping - can be made more sophisticated
        voice_map = {
            "es": "nova",     # Spanish - female voice
            "fr": "shimmer",  # French - female voice
            "de": "onyx",     # German - male voice
            "en": "alloy",    # English - neutral voice
        }

        return voice_map.get(language, self.default_voice)
