"""
FREE Speech-to-Text service using local OpenAI Whisper
No API costs - runs completely locally on your machine
"""
import io
from typing import Optional
import whisper
import numpy as np
from pydub import AudioSegment


class WhisperLocalSTTService:
    """
    FREE Speech-to-Text using local Whisper model

    Models available (download automatically on first use):
    - tiny: ~1GB RAM, fastest, less accurate
    - base: ~1GB RAM, fast, good for testing
    - small: ~2GB RAM, good balance
    - medium: ~5GB RAM, better accuracy
    - large: ~10GB RAM, best accuracy
    """

    def __init__(self, model_size: str = "base"):
        """
        Initialize local Whisper model

        Args:
            model_size: Model size (tiny, base, small, medium, large)
        """
        print(f"Loading Whisper {model_size} model (first time will download ~{self._get_model_size(model_size)})...")
        self.model = whisper.load_model(model_size)
        print(f"✓ Whisper {model_size} model loaded")

    def _get_model_size(self, model_size: str) -> str:
        """Get approximate model download size"""
        sizes = {
            "tiny": "75MB",
            "base": "150MB",
            "small": "500MB",
            "medium": "1.5GB",
            "large": "3GB"
        }
        return sizes.get(model_size, "unknown")

    async def transcribe(
        self,
        audio_data: bytes,
        language: Optional[str] = None,
        task: str = "transcribe"
    ) -> str:
        """
        Transcribe audio to text using local Whisper

        Args:
            audio_data: Audio file bytes (wav, mp3, m4a, etc.)
            language: ISO-639-1 language code (e.g., 'es', 'fr', 'de')
            task: 'transcribe' or 'translate' (translate to English)

        Returns:
            Transcribed text
        """
        try:
            # Convert audio bytes to WAV format
            audio = AudioSegment.from_file(io.BytesIO(audio_data))

            # Export as WAV to temporary buffer
            wav_buffer = io.BytesIO()
            audio.export(wav_buffer, format="wav")
            wav_buffer.seek(0)

            # Save to temp file (Whisper needs file path)
            import tempfile
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp_file:
                tmp_file.write(wav_buffer.read())
                tmp_path = tmp_file.name

            # Transcribe with Whisper
            result = self.model.transcribe(
                tmp_path,
                language=language,
                task=task,
                fp16=False  # Use FP32 for CPU compatibility
            )

            # Clean up temp file
            import os
            os.unlink(tmp_path)

            return result["text"].strip()

        except Exception as e:
            raise Exception(f"Whisper transcription failed: {str(e)}")

    def get_supported_languages(self):
        """Get list of supported languages"""
        # Whisper supports 99+ languages
        return [
            "en", "es", "fr", "de", "it", "pt", "ru", "zh",
            "ja", "ko", "ar", "hi", "nl", "tr", "pl", "sv"
            # ... and many more
        ]


# Alternative: Using faster-whisper (optimized, 4x faster)
class FasterWhisperSTTService:
    """
    Faster Whisper implementation using CTranslate2
    Up to 4x faster than standard Whisper with same accuracy
    """

    def __init__(self, model_size: str = "base", device: str = "cpu"):
        """
        Initialize faster-whisper model

        Args:
            model_size: Model size (tiny, base, small, medium, large-v2)
            device: 'cpu' or 'cuda' (if you have GPU)
        """
        try:
            from faster_whisper import WhisperModel

            print(f"Loading Faster-Whisper {model_size} on {device}...")
            self.model = WhisperModel(
                model_size,
                device=device,
                compute_type="int8"  # Optimized for speed
            )
            print(f"✓ Faster-Whisper {model_size} loaded")
        except ImportError:
            raise Exception("faster-whisper not installed. Run: pip install faster-whisper")

    async def transcribe(
        self,
        audio_data: bytes,
        language: Optional[str] = None
    ) -> str:
        """
        Transcribe audio using faster-whisper

        Args:
            audio_data: Audio file bytes
            language: ISO-639-1 language code

        Returns:
            Transcribed text
        """
        try:
            # Convert audio bytes to WAV
            audio = AudioSegment.from_file(io.BytesIO(audio_data))

            import tempfile
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp_file:
                audio.export(tmp_file.name, format="wav")
                tmp_path = tmp_file.name

            # Transcribe
            segments, info = self.model.transcribe(
                tmp_path,
                language=language,
                beam_size=5
            )

            # Combine all segments
            text = " ".join([segment.text for segment in segments])

            # Clean up
            import os
            os.unlink(tmp_path)

            return text.strip()

        except Exception as e:
            raise Exception(f"Faster-Whisper transcription failed: {str(e)}")
