"""User model."""
import uuid
from datetime import datetime
from sqlalchemy import String, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import List

from ..core.database import Base


class User(Base):
    """User account model."""

    __tablename__ = "users"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    native_language: Mapped[str] = mapped_column(String(10), nullable=False, default="en")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationships
    learning_profiles: Mapped[List["LearningProfile"]] = relationship(
        "LearningProfile", back_populates="user", cascade="all, delete-orphan"
    )
    conversation_sessions: Mapped[List["ConversationSession"]] = relationship(
        "ConversationSession", back_populates="user", cascade="all, delete-orphan"
    )
    vocabulary_progress: Mapped[List["UserVocabulary"]] = relationship(
        "UserVocabulary", back_populates="user", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<User {self.email}>"
