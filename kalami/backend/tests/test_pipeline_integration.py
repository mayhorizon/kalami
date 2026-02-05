"""Integration test for the full conversation pipeline.

Tests the complete flow:
1. User text input → LLM response → TTS synthesis (ElevenLabs)
2. Verifies audio output is valid MP3

Run with: pytest tests/test_pipeline_integration.py -v -s
"""
import pytest
import base64
import os
from httpx import AsyncClient, ASGITransport

from app.main import app
from app.core.database import Base
from app.models.user import User
from app.models.learning_profile import LearningProfile
from app.models.conversation import ConversationSession
from app.services.auth_service import AuthService
from app.services.conversation_service import ConversationService
from app.services.tts_service import get_tts_service, VoiceStyle
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker


# Test database
TEST_DATABASE_URL = "sqlite+aiosqlite:///./test_pipeline.db"


class TestElevenLabsTTS:
    """Test ElevenLabs TTS directly."""

    @pytest.mark.asyncio
    async def test_tts_synthesize_simple(self):
        """Test basic TTS synthesis."""
        tts = get_tts_service("elevenlabs")

        result = await tts.synthesize(
            text="Hola, ¿cómo estás?",
            language="es",
            style=VoiceStyle.FRIENDLY
        )

        assert result.audio_data is not None
        assert len(result.audio_data) > 1000  # Should have substantial audio data
        assert result.format == "mp3"

        # Verify it's a valid MP3 (starts with ID3 or MP3 frame sync)
        assert result.audio_data[:3] == b'ID3' or result.audio_data[:2] == b'\xff\xfb'

        print(f"✓ TTS generated {len(result.audio_data)} bytes of audio")

    @pytest.mark.asyncio
    async def test_tts_multiple_languages(self):
        """Test TTS with different languages."""
        tts = get_tts_service("elevenlabs")

        test_cases = [
            ("en", "Hello, how are you today?"),
            ("es", "Buenos días, ¿qué tal?"),
            ("fr", "Bonjour, comment allez-vous?"),
        ]

        for lang, text in test_cases:
            result = await tts.synthesize(text=text, language=lang)
            assert result.audio_data is not None
            assert len(result.audio_data) > 500
            print(f"✓ {lang}: {len(result.audio_data)} bytes")


class TestFullPipeline:
    """Test the complete conversation pipeline."""

    @pytest.mark.asyncio
    async def test_text_to_response_with_audio(self):
        """Test: User text → LLM → TTS audio response."""
        # Setup test database
        engine = create_async_engine(TEST_DATABASE_URL, echo=False)
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        async_session = async_sessionmaker(
            engine,
            class_=AsyncSession,
            expire_on_commit=False
        )

        async with async_session() as db:
            # Create test user
            user = User(
                email="pipeline_test@example.com",
                hashed_password=AuthService.hash_password("testpass123"),
                native_language="en"
            )
            db.add(user)
            await db.commit()
            await db.refresh(user)

            # Create learning profile
            profile = LearningProfile(
                user_id=user.id,
                target_language="es",
                cefr_level="A2"
            )
            db.add(profile)
            await db.commit()
            await db.refresh(profile)

            # Create conversation session
            session = ConversationSession(
                user_id=user.id,
                learning_profile_id=profile.id,
                topic="Greeting practice"
            )
            db.add(session)
            await db.commit()
            await db.refresh(session)

            # Create conversation service
            service = ConversationService(
                db=db,
                stt_service=None,  # Not needed for text input
                tts_service=get_tts_service("elevenlabs")
            )

            # Process user text input
            user_input = "Hola, me llamo Juan. ¿Cómo te llamas?"

            print(f"\n{'='*60}")
            print(f"User: {user_input}")
            print(f"{'='*60}")

            turn = await service.process_user_text(
                session=session,
                user_text=user_input,
                generate_audio=True
            )

            # Verify response
            assert turn.user_text == user_input
            assert turn.assistant_text is not None
            assert len(turn.assistant_text) > 0

            print(f"\nAssistant: {turn.assistant_text}")

            # Verify corrections (might be empty if no errors)
            print(f"Corrections: {turn.corrections}")
            print(f"New vocabulary: {turn.vocabulary_introduced}")

            # Verify audio was generated
            assert turn.assistant_audio is not None
            assert len(turn.assistant_audio) > 1000

            # Verify it's valid MP3
            assert turn.assistant_audio[:3] == b'ID3' or turn.assistant_audio[:2] == b'\xff\xfb'

            # Save audio for manual verification
            output_path = "/tmp/pipeline_test_response.mp3"
            with open(output_path, "wb") as f:
                f.write(turn.assistant_audio)

            print(f"\n✓ Audio saved to: {output_path}")
            print(f"✓ Audio size: {len(turn.assistant_audio)} bytes")
            print(f"{'='*60}")

        # Cleanup
        await engine.dispose()
        if os.path.exists("./test_pipeline.db"):
            os.remove("./test_pipeline.db")

    @pytest.mark.asyncio
    async def test_conversation_flow_multiple_turns(self):
        """Test a multi-turn conversation."""
        # Setup test database
        engine = create_async_engine(TEST_DATABASE_URL, echo=False)
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        async_session = async_sessionmaker(
            engine,
            class_=AsyncSession,
            expire_on_commit=False
        )

        async with async_session() as db:
            # Create test user and profile
            user = User(
                email="multi_turn_test@example.com",
                hashed_password=AuthService.hash_password("testpass123"),
                native_language="en"
            )
            db.add(user)
            await db.commit()
            await db.refresh(user)

            profile = LearningProfile(
                user_id=user.id,
                target_language="es",
                cefr_level="A2"
            )
            db.add(profile)
            await db.commit()
            await db.refresh(profile)

            session = ConversationSession(
                user_id=user.id,
                learning_profile_id=profile.id,
                topic="Daily conversation"
            )
            db.add(session)
            await db.commit()
            await db.refresh(session)

            service = ConversationService(
                db=db,
                tts_service=get_tts_service("elevenlabs")
            )

            conversation_turns = [
                "Hola, buenos días.",
                "¿Qué hora es?",
                "Gracias, adiós."
            ]

            print(f"\n{'='*60}")
            print("Multi-turn Conversation Test")
            print(f"{'='*60}")

            for i, user_text in enumerate(conversation_turns):
                print(f"\n[Turn {i+1}]")
                print(f"User: {user_text}")

                turn = await service.process_user_text(
                    session=session,
                    user_text=user_text,
                    generate_audio=True
                )

                print(f"Assistant: {turn.assistant_text}")

                assert turn.assistant_text is not None
                assert turn.assistant_audio is not None

                # Save each turn's audio
                output_path = f"/tmp/pipeline_test_turn_{i+1}.mp3"
                with open(output_path, "wb") as f:
                    f.write(turn.assistant_audio)
                print(f"✓ Audio saved: {output_path} ({len(turn.assistant_audio)} bytes)")

            print(f"\n{'='*60}")
            print(f"✓ Completed {len(conversation_turns)} turns successfully")
            print(f"{'='*60}")

        # Cleanup
        await engine.dispose()
        if os.path.exists("./test_pipeline.db"):
            os.remove("./test_pipeline.db")


class TestAPIEndpoints:
    """Test the HTTP API endpoints."""

    @pytest.mark.asyncio
    async def test_tts_endpoint_no_auth(self):
        """Test the public TTS test endpoint."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get(
                "/speech/test-speak",
                params={
                    "text": "This is a test of the ElevenLabs integration.",
                    "language": "en"
                }
            )

            assert response.status_code == 200
            assert len(response.content) > 1000

            # Save for verification
            with open("/tmp/api_test_speak.mp3", "wb") as f:
                f.write(response.content)

            print(f"\n✓ API /speech/test-speak: {len(response.content)} bytes")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
