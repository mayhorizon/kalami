"""Direct speech processing routes (STT/TTS)."""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.responses import Response
from pydantic import BaseModel
import base64

from ..models.user import User
from ..services.stt_service import get_stt_service
from ..services.tts_service import get_tts_service, VoiceStyle
from .auth import get_current_user

router = APIRouter(prefix="/speech", tags=["Speech"])


class TranscriptionResponse(BaseModel):
    """Response model for transcription result."""
    text: str
    language: Optional[str] = None
    confidence: Optional[float] = None
    duration_seconds: Optional[float] = None


class SynthesisRequest(BaseModel):
    """Request model for text-to-speech synthesis."""
    text: str
    language: Optional[str] = None
    voice_id: Optional[str] = None
    style: str = "neutral"
    speed: float = 1.0


class SynthesisResponse(BaseModel):
    """Response model for synthesis result."""
    audio_base64: str
    format: str
    duration_seconds: Optional[float] = None


@router.post("/transcribe", response_model=TranscriptionResponse)
async def transcribe_audio(
    audio: UploadFile = File(...),
    language: Optional[str] = None,
    provider: str = "whisper",
    current_user: User = Depends(get_current_user)
):
    """Transcribe audio to text using STT service.

    Args:
        audio: Audio file (wav, mp3, webm, m4a)
        language: Optional language hint (e.g., 'en', 'es', 'fr')
        provider: STT provider ('whisper' or 'deepgram')

    Returns:
        Transcription result with text and metadata
    """
    # Validate provider
    if provider not in ["whisper", "deepgram"]:
        raise HTTPException(
            status_code=400,
            detail="Invalid provider. Use 'whisper' or 'deepgram'"
        )

    # Determine audio format
    audio_format = "wav"
    if audio.filename:
        ext = audio.filename.split(".")[-1].lower()
        if ext in ["mp3", "webm", "m4a", "ogg", "flac"]:
            audio_format = ext

    # Read audio data
    audio_data = await audio.read()

    # Get STT service
    stt = get_stt_service(provider)

    try:
        result = await stt.transcribe(
            audio_data=audio_data,
            language=language,
            format=audio_format
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Transcription failed: {str(e)}")

    return TranscriptionResponse(
        text=result.text,
        language=result.language,
        confidence=result.confidence,
        duration_seconds=result.duration_seconds
    )


@router.post("/synthesize", response_model=SynthesisResponse)
async def synthesize_speech(
    request: SynthesisRequest,
    provider: str = "elevenlabs",
    current_user: User = Depends(get_current_user)
):
    """Synthesize text to speech.

    Args:
        request: Text and voice settings
        provider: TTS provider ('elevenlabs' or 'openai')

    Returns:
        Base64-encoded audio data
    """
    if provider not in ["elevenlabs", "openai"]:
        raise HTTPException(
            status_code=400,
            detail="Invalid provider. Use 'elevenlabs' or 'openai'"
        )

    # Map style string to enum
    style_map = {
        "neutral": VoiceStyle.NEUTRAL,
        "friendly": VoiceStyle.FRIENDLY,
        "encouraging": VoiceStyle.ENCOURAGING,
        "slow": VoiceStyle.SLOW
    }

    style = style_map.get(request.style.lower(), VoiceStyle.NEUTRAL)

    # Get TTS service
    tts = get_tts_service(provider)

    try:
        result = await tts.synthesize(
            text=request.text,
            language=request.language,
            voice_id=request.voice_id,
            style=style,
            speed=request.speed
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Synthesis failed: {str(e)}")

    audio_base64 = base64.b64encode(result.audio_data).decode("utf-8")

    return SynthesisResponse(
        audio_base64=audio_base64,
        format=result.format,
        duration_seconds=result.duration_seconds
    )


@router.post("/synthesize/stream")
async def synthesize_speech_stream(
    request: SynthesisRequest,
    provider: str = "elevenlabs",
    current_user: User = Depends(get_current_user)
):
    """Stream synthesized speech for lower latency.

    Returns audio directly as binary response for immediate playback.
    """
    if provider not in ["elevenlabs", "openai"]:
        raise HTTPException(
            status_code=400,
            detail="Invalid provider. Use 'elevenlabs' or 'openai'"
        )

    tts = get_tts_service(provider)

    try:
        # For streaming, we collect chunks and return as single response
        # In production, you'd use StreamingResponse
        chunks = []
        async for chunk in tts.synthesize_stream(
            text=request.text,
            language=request.language,
            voice_id=request.voice_id
        ):
            chunks.append(chunk)

        audio_data = b"".join(chunks)

        return Response(
            content=audio_data,
            media_type="audio/mpeg",
            headers={
                "Content-Disposition": "attachment; filename=speech.mp3"
            }
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Streaming synthesis failed: {str(e)}")


@router.get("/test-speak")
async def test_speak(
    text: str = "Hola, bienvenido a Kalami. ¿Cómo estás hoy?",
    language: str = "es",
    provider: str = "elevenlabs"
):
    """Public test endpoint - no auth required!

    Try it in your browser:
    http://localhost:8000/speech/test-speak?text=Hello%20world&language=en
    """
    if provider not in ["elevenlabs", "openai"]:
        raise HTTPException(status_code=400, detail="Invalid provider")

    tts = get_tts_service(provider)

    try:
        result = await tts.synthesize(
            text=text,
            language=language,
            style=VoiceStyle.FRIENDLY
        )

        return Response(
            content=result.audio_data,
            media_type="audio/mpeg",
            headers={
                "Content-Disposition": "inline; filename=test.mp3"
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"TTS failed: {str(e)}")


@router.get("/speak")
async def speak_text(
    text: str,
    language: str = "es",
    provider: str = "elevenlabs",
    style: str = "friendly",
    current_user: User = Depends(get_current_user)
):
    """Convert text to speech and return audio directly.

    Open this URL in a browser to hear the audio!

    Args:
        text: Text to speak
        language: Language code (es, en, fr, etc.)
        provider: TTS provider ('elevenlabs' or 'openai')
        style: Voice style (neutral, friendly, encouraging, slow)

    Returns:
        MP3 audio file
    """
    if provider not in ["elevenlabs", "openai"]:
        raise HTTPException(status_code=400, detail="Invalid provider")

    style_map = {
        "neutral": VoiceStyle.NEUTRAL,
        "friendly": VoiceStyle.FRIENDLY,
        "encouraging": VoiceStyle.ENCOURAGING,
        "slow": VoiceStyle.SLOW
    }

    tts = get_tts_service(provider)

    try:
        result = await tts.synthesize(
            text=text,
            language=language,
            style=style_map.get(style.lower(), VoiceStyle.FRIENDLY)
        )

        return Response(
            content=result.audio_data,
            media_type="audio/mpeg",
            headers={
                "Content-Disposition": f"inline; filename=speech.mp3"
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"TTS failed: {str(e)}")


@router.get("/voices")
async def list_voices(
    provider: str = "elevenlabs",
    current_user: User = Depends(get_current_user)
):
    """List available voices for TTS.

    Only ElevenLabs supports dynamic voice listing.
    """
    if provider == "elevenlabs":
        from ..services.tts_service import ElevenLabsTTS

        tts = ElevenLabsTTS()
        try:
            voices = await tts.list_voices()
            return {
                "provider": "elevenlabs",
                "voices": [
                    {
                        "voice_id": v.get("voice_id"),
                        "name": v.get("name"),
                        "labels": v.get("labels", {})
                    }
                    for v in voices
                ]
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to list voices: {str(e)}")

    elif provider == "openai":
        return {
            "provider": "openai",
            "voices": [
                {"voice_id": "alloy", "name": "Alloy"},
                {"voice_id": "echo", "name": "Echo"},
                {"voice_id": "fable", "name": "Fable"},
                {"voice_id": "onyx", "name": "Onyx"},
                {"voice_id": "nova", "name": "Nova"},
                {"voice_id": "shimmer", "name": "Shimmer"}
            ]
        }

    else:
        raise HTTPException(status_code=400, detail="Invalid provider")
