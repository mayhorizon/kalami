"""Text-to-Speech services for Kalami.

Supports:
- ElevenLabs (primary - high quality, natural voices)
- OpenAI TTS (fallback)
"""
import io
import httpx
from abc import ABC, abstractmethod
from typing import Optional, AsyncIterator
from dataclasses import dataclass
from enum import Enum

from ..core.config import settings


class VoiceStyle(str, Enum):
    """Available voice styles for language tutoring."""
    NEUTRAL = "neutral"
    FRIENDLY = "friendly"
    ENCOURAGING = "encouraging"
    SLOW = "slow"  # For beginners


@dataclass
class SynthesisResult:
    """Result from text-to-speech synthesis."""
    audio_data: bytes
    format: str = "mp3"
    duration_seconds: Optional[float] = None
    sample_rate: int = 44100


class TTSService(ABC):
    """Abstract base class for Text-to-Speech services."""

    @abstractmethod
    async def synthesize(
        self,
        text: str,
        language: Optional[str] = None,
        voice_id: Optional[str] = None,
        style: VoiceStyle = VoiceStyle.NEUTRAL,
        speed: float = 1.0
    ) -> SynthesisResult:
        """Synthesize text to speech.

        Args:
            text: Text to convert to speech
            language: Target language code
            voice_id: Specific voice to use
            style: Voice style/emotion
            speed: Speech speed multiplier (0.5-2.0)

        Returns:
            SynthesisResult with audio data
        """
        pass

    @abstractmethod
    async def synthesize_stream(
        self,
        text: str,
        language: Optional[str] = None,
        voice_id: Optional[str] = None
    ) -> AsyncIterator[bytes]:
        """Stream audio synthesis for lower latency.

        Yields audio chunks as they're generated.
        """
        pass


class ElevenLabsTTS(TTSService):
    """ElevenLabs API implementation for high-quality TTS.

    Best for:
    - Natural, human-like voices
    - Multilingual support (32+ languages)
    - Low latency streaming (~75-135ms TTFA)
    - Voice cloning capabilities
    """

    # Pre-configured voices for different languages
    VOICE_MAP = {
        "en": "21m00Tcm4TlvDq8ikWAM",  # Rachel - American English
        "es": "ThT5KcBeYPX3keUQqHPh",  # Laura - Spanish
        "fr": "XB0fDUnXU5powFXDhCwa",  # Charlotte - French
        "de": "pNInz6obpgDQGcFmaJgB",  # Adam - German
        "it": "EXAVITQu4vr4xnSDxMaL",  # Bella - Italian
        "pt": "ODq5zmih8GrVes37Dizd",  # Patrick - Portuguese
        "ja": "Xb7hH8MSUJpSbSDYk0k2",  # Yuki - Japanese
        "zh": "g5CIjZEefAph4nQFvHAz",  # Wei - Chinese
        "ko": "AZnzlk1XvdvUeBnXmlld",  # Soo - Korean
    }

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or settings.ELEVENLABS_API_KEY
        self.model = settings.ELEVENLABS_MODEL
        self.default_voice = settings.ELEVENLABS_VOICE_ID
        self.base_url = "https://api.elevenlabs.io/v1"

    def _get_voice_for_language(self, language: Optional[str]) -> str:
        """Get appropriate voice ID for a language."""
        if language and language in self.VOICE_MAP:
            return self.VOICE_MAP[language]
        return self.default_voice

    def _style_to_settings(self, style: VoiceStyle) -> dict:
        """Convert voice style to ElevenLabs voice settings."""
        settings_map = {
            VoiceStyle.NEUTRAL: {
                "stability": 0.5,
                "similarity_boost": 0.75,
                "style": 0.0,
                "use_speaker_boost": True
            },
            VoiceStyle.FRIENDLY: {
                "stability": 0.4,
                "similarity_boost": 0.8,
                "style": 0.3,
                "use_speaker_boost": True
            },
            VoiceStyle.ENCOURAGING: {
                "stability": 0.35,
                "similarity_boost": 0.85,
                "style": 0.5,
                "use_speaker_boost": True
            },
            VoiceStyle.SLOW: {
                "stability": 0.7,
                "similarity_boost": 0.7,
                "style": 0.0,
                "use_speaker_boost": False
            },
        }
        return settings_map.get(style, settings_map[VoiceStyle.NEUTRAL])

    async def synthesize(
        self,
        text: str,
        language: Optional[str] = None,
        voice_id: Optional[str] = None,
        style: VoiceStyle = VoiceStyle.NEUTRAL,
        speed: float = 1.0
    ) -> SynthesisResult:
        """Synthesize text using ElevenLabs API.

        Args:
            text: Text to speak
            language: Language code (used to select appropriate voice)
            voice_id: Override voice selection
            style: Voice style preset
            speed: Speed multiplier (ElevenLabs doesn't directly support this,
                   but we can use stability settings to approximate)

        Returns:
            SynthesisResult with MP3 audio data
        """
        if not self.api_key:
            raise ValueError("ElevenLabs API key not configured. Set ELEVENLABS_API_KEY.")

        # Select voice
        selected_voice = voice_id or self._get_voice_for_language(language)
        voice_settings = self._style_to_settings(style)

        # Adjust for speed (using stability as proxy)
        if speed < 1.0:
            voice_settings["stability"] = min(0.9, voice_settings["stability"] + 0.2)
        elif speed > 1.0:
            voice_settings["stability"] = max(0.2, voice_settings["stability"] - 0.1)

        payload = {
            "text": text,
            "model_id": self.model,
            "voice_settings": voice_settings
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/text-to-speech/{selected_voice}",
                headers={
                    "xi-api-key": self.api_key,
                    "Content-Type": "application/json",
                    "Accept": "audio/mpeg"
                },
                json=payload,
                timeout=30.0
            )

            if response.status_code != 200:
                error_detail = response.text
                raise Exception(f"ElevenLabs API error ({response.status_code}): {error_detail}")

            return SynthesisResult(
                audio_data=response.content,
                format="mp3",
                sample_rate=44100
            )

    async def synthesize_stream(
        self,
        text: str,
        language: Optional[str] = None,
        voice_id: Optional[str] = None
    ) -> AsyncIterator[bytes]:
        """Stream audio synthesis for lower latency.

        Uses ElevenLabs streaming endpoint for immediate audio playback.
        """
        if not self.api_key:
            raise ValueError("ElevenLabs API key not configured.")

        selected_voice = voice_id or self._get_voice_for_language(language)

        payload = {
            "text": text,
            "model_id": self.model,
            "voice_settings": self._style_to_settings(VoiceStyle.NEUTRAL)
        }

        async with httpx.AsyncClient() as client:
            async with client.stream(
                "POST",
                f"{self.base_url}/text-to-speech/{selected_voice}/stream",
                headers={
                    "xi-api-key": self.api_key,
                    "Content-Type": "application/json",
                    "Accept": "audio/mpeg"
                },
                json=payload,
                timeout=30.0
            ) as response:
                if response.status_code != 200:
                    raise Exception(f"ElevenLabs streaming error: {response.status_code}")

                async for chunk in response.aiter_bytes(chunk_size=1024):
                    yield chunk

    async def list_voices(self) -> list:
        """Get available voices from ElevenLabs."""
        if not self.api_key:
            raise ValueError("ElevenLabs API key not configured.")

        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/voices",
                headers={"xi-api-key": self.api_key},
                timeout=10.0
            )

            if response.status_code != 200:
                raise Exception(f"Failed to list voices: {response.text}")

            data = response.json()
            return data.get("voices", [])


class OpenAITTS(TTSService):
    """OpenAI TTS API as fallback option.

    Good for:
    - Simple, reliable TTS
    - Consistent quality
    - Lower cost at scale
    """

    VOICES = ["alloy", "echo", "fable", "onyx", "nova", "shimmer"]

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or settings.OPENAI_API_KEY
        self.base_url = "https://api.openai.com/v1/audio"

    async def synthesize(
        self,
        text: str,
        language: Optional[str] = None,
        voice_id: Optional[str] = None,
        style: VoiceStyle = VoiceStyle.NEUTRAL,
        speed: float = 1.0
    ) -> SynthesisResult:
        """Synthesize text using OpenAI TTS API."""
        if not self.api_key:
            raise ValueError("OpenAI API key not configured.")

        voice = voice_id or "nova"  # Default to nova (friendly female voice)
        if voice not in self.VOICES:
            voice = "nova"

        # Clamp speed to valid range
        speed = max(0.25, min(4.0, speed))

        payload = {
            "model": "tts-1",  # or "tts-1-hd" for higher quality
            "input": text,
            "voice": voice,
            "speed": speed,
            "response_format": "mp3"
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/speech",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json=payload,
                timeout=30.0
            )

            if response.status_code != 200:
                raise Exception(f"OpenAI TTS error: {response.text}")

            return SynthesisResult(
                audio_data=response.content,
                format="mp3",
                sample_rate=24000
            )

    async def synthesize_stream(
        self,
        text: str,
        language: Optional[str] = None,
        voice_id: Optional[str] = None
    ) -> AsyncIterator[bytes]:
        """OpenAI TTS doesn't support true streaming.

        This fetches the full audio and yields it in chunks.
        """
        result = await self.synthesize(text, language, voice_id)

        # Yield in chunks for consistent interface
        chunk_size = 4096
        audio_io = io.BytesIO(result.audio_data)

        while True:
            chunk = audio_io.read(chunk_size)
            if not chunk:
                break
            yield chunk


def get_tts_service(provider: str = "elevenlabs") -> TTSService:
    """Factory function to get the appropriate TTS service.

    Args:
        provider: 'elevenlabs' or 'openai'

    Returns:
        Configured TTSService instance
    """
    if provider == "openai":
        return OpenAITTS()
    return ElevenLabsTTS()
