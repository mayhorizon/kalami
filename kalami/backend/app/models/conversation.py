"""Conversation models for tracking chat sessions and messages."""
import uuid
from datetime import datetime
from sqlalchemy import String, Integer, DateTime, ForeignKey, Text, Float, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import Optional, List

from ..core.database import Base


class ConversationSession(Base):
    """A conversation practice session."""

    __tablename__ = "conversation_sessions"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id"), nullable=False
    )
    learning_profile_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("learning_profiles.id"), nullable=False
    )
    topic: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    started_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    ended_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    duration_seconds: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    words_spoken: Mapped[int] = mapped_column(Integer, default=0)
    corrections_made: Mapped[int] = mapped_column(Integer, default=0)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="conversation_sessions")
    learning_profile: Mapped["LearningProfile"] = relationship(
        "LearningProfile", back_populates="sessions"
    )
    messages: Mapped[List["ConversationMessage"]] = relationship(
        "ConversationMessage", back_populates="session", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<ConversationSession {self.id[:8]}... ({self.topic})>"


class ConversationMessage(Base):
    """A single message in a conversation."""

    __tablename__ = "conversation_messages"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    session_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("conversation_sessions.id"), nullable=False
    )
    role: Mapped[str] = mapped_column(String(20), nullable=False)  # 'user' or 'assistant'
    content: Mapped[str] = mapped_column(Text, nullable=False)
    audio_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    pronunciation_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    grammar_errors: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    session: Mapped["ConversationSession"] = relationship(
        "ConversationSession", back_populates="messages"
    )
    pronunciation_analysis: Mapped[Optional["PronunciationAnalysis"]] = relationship(
        "PronunciationAnalysis", back_populates="message", uselist=False
    )

    def __repr__(self) -> str:
        return f"<Message {self.role}: {self.content[:30]}...>"
