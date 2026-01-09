"""
FREE Text-to-Speech using Piper TTS
Fast, local, neural TTS - no API costs
"""
import subprocess
import io
from typing import Optional
from pathlib import Path


class PiperTTSService:
    """
    FREE Text-to-Speech using Piper

    Piper is a fast, local neural TTS system.
    Download from: https://github.com/rhasspy/piper

    Voice models download from:
    https://huggingface.co/rhasspy/piper-voices/tree/main
    """

    def __init__(self, piper_path: str = "piper", voices_dir: str = "./models/piper_voices"):
        """
        Initialize Piper TTS

        Args:
            piper_path: Path to piper executable
            voices_dir: Directory containing voice models
        """
        self.piper_path = piper_path
        self.voices_dir = Path(voices_dir)
        self.voices_dir.mkdir(parents=True, exist_ok=True)

        # Language to voice mapping
        self.language_voices = {
            "en": "en_US-lessac-medium",
            "es": "es_ES-mls_10246-medium",
            "fr": "fr_FR-mls_1840-medium",
            "de": "de_DE-thorsten-medium"
        }

    async def synthesize(
        self,
        text: str,
        language: str = "en",
        voice: Optional[str] = None
    ) -> bytes:
        """
        Convert text to speech using Piper

        Args:
            text: Text to convert to speech
            language: ISO-639-1 language code
            voice: Optional specific voice model name

        Returns:
            Audio bytes (WAV format)
        """
        try:
            # Get voice model for language
            if voice is None:
                voice = self.language_voices.get(language, self.language_voices["en"])

            model_path = self.voices_dir / f"{voice}.onnx"
            config_path = self.voices_dir / f"{voice}.onnx.json"

            # Check if voice model exists
            if not model_path.exists():
                raise Exception(
                    f"Voice model not found: {model_path}\n"
                    f"Download from: https://huggingface.co/rhasspy/piper-voices/tree/main"
                )

            # Run Piper to generate speech
            process = subprocess.Popen(
                [
                    self.piper_path,
                    "--model", str(model_path),
                    "--config", str(config_path),
                    "--output_file", "-"  # Output to stdout
                ],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )

            # Send text and get audio
            audio_data, error = process.communicate(input=text.encode())

            if process.returncode != 0:
                raise Exception(f"Piper TTS failed: {error.decode()}")

            return audio_data

        except FileNotFoundError:
            raise Exception(
                "Piper not found. Install from: https://github.com/rhasspy/piper\n"
                "Or use fallback pyttsx3 service"
            )
        except Exception as e:
            raise Exception(f"Speech synthesis failed: {str(e)}")

    def list_available_voices(self):
        """List downloaded voice models"""
        voices = list(self.voices_dir.glob("*.onnx"))
        return [v.stem for v in voices]


# Fallback: Simple TTS using pyttsx3 (works offline but robotic)
class Pyttsx3TTSService:
    """
    Fallback FREE TTS using pyttsx3
    Works offline, no setup needed, but robotic voice quality
    """

    def __init__(self):
        """Initialize pyttsx3"""
        try:
            import pyttsx3
            self.engine = pyttsx3.init()
            # Set properties
            self.engine.setProperty('rate', 150)  # Speed
            self.engine.setProperty('volume', 0.9)  # Volume
        except Exception as e:
            raise Exception(f"pyttsx3 initialization failed: {str(e)}")

    async def synthesize(self, text: str, language: str = "en") -> bytes:
        """
        Convert text to speech using pyttsx3

        Args:
            text: Text to convert
            language: Language code (limited support)

        Returns:
            Audio bytes
        """
        try:
            import tempfile
            import pyttsx3

            # Save to temporary file
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp_file:
                tmp_path = tmp_file.name

            # Generate speech
            self.engine.save_to_file(text, tmp_path)
            self.engine.runAndWait()

            # Read audio file
            with open(tmp_path, 'rb') as f:
                audio_data = f.read()

            # Clean up
            import os
            os.unlink(tmp_path)

            return audio_data

        except Exception as e:
            raise Exception(f"pyttsx3 synthesis failed: {str(e)}")


# Installation instructions as comments:
"""
PIPER TTS SETUP:

1. Download Piper for your OS:
   https://github.com/rhasspy/piper/releases

2. Download voice models:
   https://huggingface.co/rhasspy/piper-voices/tree/main

   Example for Spanish:
   wget https://huggingface.co/rhasspy/piper-voices/resolve/main/es/es_ES/mls_10246/medium/es_ES-mls_10246-medium.onnx
   wget https://huggingface.co/rhasspy/piper-voices/resolve/main/es/es_ES/mls_10246/medium/es_ES-mls_10246-medium.onnx.json

3. Place voice models in: ./models/piper_voices/

4. Test:
   echo "Hello world" | ./piper --model ./models/piper_voices/en_US-lessac-medium.onnx --output_file test.wav
"""
