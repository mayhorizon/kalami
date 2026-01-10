"""Conversation session routes."""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import base64

from ..core.database import get_db
from ..models.user import User
from ..models.learning_profile import LearningProfile
from ..models.conversation import ConversationSession, ConversationMessage
from ..services.conversation_service import ConversationService
from .auth import get_current_user

router = APIRouter(prefix="/conversations", tags=["Conversations"])


class SessionCreate(BaseModel):
    """Request model for starting a session."""
    profile_id: str
    topic: Optional[str] = None


class SessionResponse(BaseModel):
    """Response model for a conversation session."""
    id: str
    topic: Optional[str]
    started_at: str
    ended_at: Optional[str]
    duration_seconds: Optional[int]
    words_spoken: int
    corrections_made: int

    class Config:
        from_attributes = True


class MessageResponse(BaseModel):
    """Response model for a conversation message."""
    id: str
    role: str
    content: str
    created_at: str

    class Config:
        from_attributes = True


class TextInput(BaseModel):
    """Request model for text-based conversation."""
    text: str
    generate_audio: bool = True


class ConversationTurnResponse(BaseModel):
    """Response model for a conversation turn."""
    user_text: str
    assistant_text: str
    assistant_audio_base64: Optional[str] = None
    corrections: Optional[List[dict]] = None
    vocabulary_introduced: Optional[List[str]] = None


@router.post("/sessions", response_model=SessionResponse, status_code=status.HTTP_201_CREATED)
async def start_session(
    session_data: SessionCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Start a new conversation session."""
    # Verify profile belongs to user
    result = await db.execute(
        select(LearningProfile).where(
            LearningProfile.id == session_data.profile_id,
            LearningProfile.user_id == current_user.id
        )
    )
    profile = result.scalar_one_or_none()

    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Learning profile not found"
        )

    service = ConversationService(db)
    session = await service.create_session(
        user=current_user,
        learning_profile=profile,
        topic=session_data.topic
    )

    return SessionResponse(
        id=session.id,
        topic=session.topic,
        started_at=session.started_at.isoformat(),
        ended_at=None,
        duration_seconds=None,
        words_spoken=session.words_spoken,
        corrections_made=session.corrections_made
    )


@router.get("/sessions", response_model=List[SessionResponse])
async def list_sessions(
    limit: int = 20,
    offset: int = 0,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List user's conversation sessions."""
    result = await db.execute(
        select(ConversationSession)
        .where(ConversationSession.user_id == current_user.id)
        .order_by(ConversationSession.started_at.desc())
        .limit(limit)
        .offset(offset)
    )

    sessions = result.scalars().all()

    return [
        SessionResponse(
            id=s.id,
            topic=s.topic,
            started_at=s.started_at.isoformat(),
            ended_at=s.ended_at.isoformat() if s.ended_at else None,
            duration_seconds=s.duration_seconds,
            words_spoken=s.words_spoken,
            corrections_made=s.corrections_made
        )
        for s in sessions
    ]


@router.get("/sessions/{session_id}", response_model=SessionResponse)
async def get_session(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get a specific session."""
    result = await db.execute(
        select(ConversationSession).where(
            ConversationSession.id == session_id,
            ConversationSession.user_id == current_user.id
        )
    )

    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )

    return SessionResponse(
        id=session.id,
        topic=session.topic,
        started_at=session.started_at.isoformat(),
        ended_at=session.ended_at.isoformat() if session.ended_at else None,
        duration_seconds=session.duration_seconds,
        words_spoken=session.words_spoken,
        corrections_made=session.corrections_made
    )


@router.post("/sessions/{session_id}/end", response_model=SessionResponse)
async def end_session(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """End a conversation session."""
    result = await db.execute(
        select(ConversationSession).where(
            ConversationSession.id == session_id,
            ConversationSession.user_id == current_user.id
        )
    )

    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )

    service = ConversationService(db)
    session = await service.end_session(session)

    return SessionResponse(
        id=session.id,
        topic=session.topic,
        started_at=session.started_at.isoformat(),
        ended_at=session.ended_at.isoformat() if session.ended_at else None,
        duration_seconds=session.duration_seconds,
        words_spoken=session.words_spoken,
        corrections_made=session.corrections_made
    )


@router.get("/sessions/{session_id}/messages", response_model=List[MessageResponse])
async def get_session_messages(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get all messages in a session."""
    # Verify session belongs to user
    session_result = await db.execute(
        select(ConversationSession).where(
            ConversationSession.id == session_id,
            ConversationSession.user_id == current_user.id
        )
    )

    if not session_result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )

    result = await db.execute(
        select(ConversationMessage)
        .where(ConversationMessage.session_id == session_id)
        .order_by(ConversationMessage.created_at)
    )

    messages = result.scalars().all()

    return [
        MessageResponse(
            id=m.id,
            role=m.role,
            content=m.content,
            created_at=m.created_at.isoformat()
        )
        for m in messages
    ]


@router.post("/sessions/{session_id}/audio", response_model=ConversationTurnResponse)
async def send_audio_message(
    session_id: str,
    audio: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Send an audio message and get a response.

    This is the main conversation endpoint for voice practice.
    """
    # Verify session belongs to user
    result = await db.execute(
        select(ConversationSession).where(
            ConversationSession.id == session_id,
            ConversationSession.user_id == current_user.id
        )
    )

    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )

    if session.ended_at:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Session has ended"
        )

    # Read audio data
    audio_data = await audio.read()

    # Determine format from filename
    audio_format = "wav"
    if audio.filename:
        if audio.filename.endswith(".mp3"):
            audio_format = "mp3"
        elif audio.filename.endswith(".webm"):
            audio_format = "webm"
        elif audio.filename.endswith(".m4a"):
            audio_format = "m4a"

    service = ConversationService(db)

    try:
        turn = await service.process_user_audio(
            session=session,
            audio_data=audio_data,
            audio_format=audio_format
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing audio: {str(e)}"
        )

    # Encode audio response as base64
    audio_base64 = None
    if turn.assistant_audio:
        audio_base64 = base64.b64encode(turn.assistant_audio).decode("utf-8")

    return ConversationTurnResponse(
        user_text=turn.user_text,
        assistant_text=turn.assistant_text,
        assistant_audio_base64=audio_base64,
        corrections=turn.corrections,
        vocabulary_introduced=turn.vocabulary_introduced
    )


@router.post("/sessions/{session_id}/text", response_model=ConversationTurnResponse)
async def send_text_message(
    session_id: str,
    input_data: TextInput,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Send a text message and get a response.

    Useful for typing practice or testing without audio.
    """
    # Verify session belongs to user
    result = await db.execute(
        select(ConversationSession).where(
            ConversationSession.id == session_id,
            ConversationSession.user_id == current_user.id
        )
    )

    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )

    if session.ended_at:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Session has ended"
        )

    service = ConversationService(db)

    try:
        turn = await service.process_user_text(
            session=session,
            user_text=input_data.text,
            generate_audio=input_data.generate_audio
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing message: {str(e)}"
        )

    audio_base64 = None
    if turn.assistant_audio:
        audio_base64 = base64.b64encode(turn.assistant_audio).decode("utf-8")

    return ConversationTurnResponse(
        user_text=turn.user_text,
        assistant_text=turn.assistant_text,
        assistant_audio_base64=audio_base64,
        corrections=turn.corrections,
        vocabulary_introduced=turn.vocabulary_introduced
    )
