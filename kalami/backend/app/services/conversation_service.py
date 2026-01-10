"""Conversation service for AI-powered language learning.

This is the core service that:
- Manages conversation sessions
- Generates tutor responses using LLM
- Tracks learning progress
- Provides pronunciation and grammar feedback
"""
import json
from datetime import datetime
from typing import Optional, List, AsyncIterator
from dataclasses import dataclass
import httpx
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ..core.config import settings
from ..models.user import User
from ..models.learning_profile import LearningProfile
from ..models.conversation import ConversationSession, ConversationMessage
from .stt_service import STTService, get_stt_service, TranscriptionResult
from .tts_service import TTSService, get_tts_service, SynthesisResult, VoiceStyle


@dataclass
class ConversationTurn:
    """A single turn in the conversation."""
    user_text: str
    assistant_text: str
    user_audio: Optional[bytes] = None
    assistant_audio: Optional[bytes] = None
    corrections: Optional[List[dict]] = None
    vocabulary_introduced: Optional[List[str]] = None


class ConversationService:
    """Manages AI-powered language learning conversations."""

    # System prompt template for the language tutor
    SYSTEM_PROMPT_TEMPLATE = """You are Kalami, a patient and encouraging language tutor helping the user practice {target_language} through natural conversation.

USER PROFILE:
- Native language: {native_language}
- Proficiency level: {cefr_level} (A1-C2 scale)
- Target language: {target_language}

CONVERSATION RULES:
1. Speak primarily in {target_language} at a complexity appropriate for {cefr_level} level
2. When the user makes errors, provide gentle corrections using the sandwich method (positive - correction - positive)
3. Introduce 2-3 new vocabulary items naturally in each response
4. Ask follow-up questions to extend the conversation
5. Adjust difficulty based on user's responses
6. For beginners (A1-A2), include translations in parentheses for new words
7. Be encouraging and celebrate progress

CORRECTION FORMAT:
- Minor errors: Continue naturally, correct inline
- Major errors: Pause, explain briefly, provide the correct form
- Pronunciation hints: Use simple phonetic guides when helpful

RESPONSE FORMAT:
Always respond in this JSON structure:
{{
    "response": "Your conversational response in {target_language}",
    "translation": "English translation (only for A1-A2 levels)",
    "corrections": [
        {{
            "original": "what user said wrong",
            "corrected": "correct form",
            "explanation": "brief explanation"
        }}
    ],
    "new_vocabulary": [
        {{
            "word": "new word",
            "translation": "translation",
            "example": "example sentence"
        }}
    ],
    "encouragement": "brief encouraging note (optional)"
}}

Current topic: {topic}
"""

    def __init__(
        self,
        db: AsyncSession,
        stt_service: Optional[STTService] = None,
        tts_service: Optional[TTSService] = None
    ):
        self.db = db
        self.stt = stt_service or get_stt_service("whisper")
        self.tts = tts_service or get_tts_service("elevenlabs")

    async def create_session(
        self,
        user: User,
        learning_profile: LearningProfile,
        topic: Optional[str] = None
    ) -> ConversationSession:
        """Start a new conversation session.

        Args:
            user: The user starting the session
            learning_profile: The language learning profile to use
            topic: Optional conversation topic

        Returns:
            Created ConversationSession
        """
        session = ConversationSession(
            user_id=user.id,
            learning_profile_id=learning_profile.id,
            topic=topic or "General conversation"
        )

        self.db.add(session)
        await self.db.commit()
        await self.db.refresh(session)

        return session

    async def end_session(self, session: ConversationSession) -> ConversationSession:
        """End a conversation session and calculate metrics.

        Args:
            session: The session to end

        Returns:
            Updated ConversationSession with final metrics
        """
        session.ended_at = datetime.utcnow()

        if session.started_at:
            delta = session.ended_at - session.started_at
            session.duration_seconds = int(delta.total_seconds())

        await self.db.commit()
        await self.db.refresh(session)

        return session

    async def get_session_messages(
        self,
        session_id: str
    ) -> List[ConversationMessage]:
        """Get all messages in a session."""
        result = await self.db.execute(
            select(ConversationMessage)
            .where(ConversationMessage.session_id == session_id)
            .order_by(ConversationMessage.created_at)
        )
        return list(result.scalars().all())

    def _build_system_prompt(
        self,
        profile: LearningProfile,
        user: User,
        topic: str
    ) -> str:
        """Build the system prompt for the LLM."""
        return self.SYSTEM_PROMPT_TEMPLATE.format(
            target_language=profile.target_language,
            native_language=user.native_language,
            cefr_level=profile.cefr_level,
            topic=topic
        )

    def _build_messages(
        self,
        system_prompt: str,
        history: List[ConversationMessage],
        user_input: str
    ) -> List[dict]:
        """Build the message list for the LLM API."""
        messages = [{"role": "system", "content": system_prompt}]

        for msg in history:
            messages.append({
                "role": msg.role,
                "content": msg.content
            })

        messages.append({"role": "user", "content": user_input})

        return messages

    async def _call_llm(self, messages: List[dict]) -> dict:
        """Call the LLM API to generate a response.

        Supports both OpenAI and Anthropic APIs.
        """
        if settings.ANTHROPIC_API_KEY:
            return await self._call_anthropic(messages)
        elif settings.OPENAI_API_KEY:
            return await self._call_openai(messages)
        else:
            raise ValueError("No LLM API key configured. Set ANTHROPIC_API_KEY or OPENAI_API_KEY.")

    async def _call_openai(self, messages: List[dict]) -> dict:
        """Call OpenAI API."""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {settings.OPENAI_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": settings.LLM_MODEL,
                    "messages": messages,
                    "temperature": 0.7,
                    "response_format": {"type": "json_object"}
                },
                timeout=60.0
            )

            if response.status_code != 200:
                raise Exception(f"OpenAI API error: {response.text}")

            data = response.json()
            content = data["choices"][0]["message"]["content"]
            return json.loads(content)

    async def _call_anthropic(self, messages: List[dict]) -> dict:
        """Call Anthropic Claude API."""
        # Convert messages to Anthropic format
        system_content = ""
        anthropic_messages = []

        for msg in messages:
            if msg["role"] == "system":
                system_content = msg["content"]
            else:
                anthropic_messages.append({
                    "role": msg["role"],
                    "content": msg["content"]
                })

        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": settings.ANTHROPIC_API_KEY,
                    "anthropic-version": "2023-06-01",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "claude-3-sonnet-20240229",
                    "max_tokens": 1024,
                    "system": system_content,
                    "messages": anthropic_messages
                },
                timeout=60.0
            )

            if response.status_code != 200:
                raise Exception(f"Anthropic API error: {response.text}")

            data = response.json()
            content = data["content"][0]["text"]

            # Try to parse as JSON, fallback to wrapping in response object
            try:
                return json.loads(content)
            except json.JSONDecodeError:
                return {"response": content, "corrections": [], "new_vocabulary": []}

    async def process_user_audio(
        self,
        session: ConversationSession,
        audio_data: bytes,
        audio_format: str = "wav"
    ) -> ConversationTurn:
        """Process user audio input and generate tutor response.

        This is the main conversation flow:
        1. Transcribe user audio (STT)
        2. Generate tutor response (LLM)
        3. Synthesize response audio (TTS)

        Args:
            session: Active conversation session
            audio_data: User's recorded audio
            audio_format: Audio file format

        Returns:
            ConversationTurn with all data
        """
        # Get session context
        profile_result = await self.db.execute(
            select(LearningProfile).where(
                LearningProfile.id == session.learning_profile_id
            )
        )
        profile = profile_result.scalar_one()

        user_result = await self.db.execute(
            select(User).where(User.id == session.user_id)
        )
        user = user_result.scalar_one()

        # Step 1: Transcribe user audio
        transcription = await self.stt.transcribe(
            audio_data,
            language=profile.target_language,
            format=audio_format
        )

        # Save user message
        user_message = ConversationMessage(
            session_id=session.id,
            role="user",
            content=transcription.text
        )
        self.db.add(user_message)

        # Step 2: Get conversation history
        history = await self.get_session_messages(session.id)

        # Step 3: Build prompt and call LLM
        system_prompt = self._build_system_prompt(profile, user, session.topic)
        messages = self._build_messages(system_prompt, history, transcription.text)
        llm_response = await self._call_llm(messages)

        # Extract response text
        response_text = llm_response.get("response", "")
        corrections = llm_response.get("corrections", [])
        new_vocabulary = llm_response.get("new_vocabulary", [])

        # Save assistant message
        assistant_message = ConversationMessage(
            session_id=session.id,
            role="assistant",
            content=response_text,
            grammar_errors={"corrections": corrections} if corrections else None
        )
        self.db.add(assistant_message)

        # Update session metrics
        session.words_spoken = (session.words_spoken or 0) + len(transcription.text.split())
        session.corrections_made = (session.corrections_made or 0) + len(corrections)

        await self.db.commit()

        # Step 4: Synthesize response audio
        # Use slow style for beginners
        style = VoiceStyle.SLOW if profile.cefr_level in ["A1", "A2"] else VoiceStyle.FRIENDLY

        synthesis = await self.tts.synthesize(
            response_text,
            language=profile.target_language,
            style=style
        )

        return ConversationTurn(
            user_text=transcription.text,
            assistant_text=response_text,
            user_audio=audio_data,
            assistant_audio=synthesis.audio_data,
            corrections=corrections,
            vocabulary_introduced=[v.get("word") for v in new_vocabulary]
        )

    async def process_user_text(
        self,
        session: ConversationSession,
        user_text: str,
        generate_audio: bool = True
    ) -> ConversationTurn:
        """Process text input (for typing practice or testing).

        Similar to process_user_audio but skips STT step.
        """
        # Get session context
        profile_result = await self.db.execute(
            select(LearningProfile).where(
                LearningProfile.id == session.learning_profile_id
            )
        )
        profile = profile_result.scalar_one()

        user_result = await self.db.execute(
            select(User).where(User.id == session.user_id)
        )
        user = user_result.scalar_one()

        # Save user message
        user_message = ConversationMessage(
            session_id=session.id,
            role="user",
            content=user_text
        )
        self.db.add(user_message)

        # Get history and generate response
        history = await self.get_session_messages(session.id)
        system_prompt = self._build_system_prompt(profile, user, session.topic)
        messages = self._build_messages(system_prompt, history, user_text)
        llm_response = await self._call_llm(messages)

        response_text = llm_response.get("response", "")
        corrections = llm_response.get("corrections", [])
        new_vocabulary = llm_response.get("new_vocabulary", [])

        # Save assistant message
        assistant_message = ConversationMessage(
            session_id=session.id,
            role="assistant",
            content=response_text,
            grammar_errors={"corrections": corrections} if corrections else None
        )
        self.db.add(assistant_message)

        session.words_spoken = (session.words_spoken or 0) + len(user_text.split())
        session.corrections_made = (session.corrections_made or 0) + len(corrections)

        await self.db.commit()

        # Generate audio if requested
        assistant_audio = None
        if generate_audio:
            style = VoiceStyle.SLOW if profile.cefr_level in ["A1", "A2"] else VoiceStyle.FRIENDLY
            synthesis = await self.tts.synthesize(
                response_text,
                language=profile.target_language,
                style=style
            )
            assistant_audio = synthesis.audio_data

        return ConversationTurn(
            user_text=user_text,
            assistant_text=response_text,
            assistant_audio=assistant_audio,
            corrections=corrections,
            vocabulary_introduced=[v.get("word") for v in new_vocabulary]
        )
