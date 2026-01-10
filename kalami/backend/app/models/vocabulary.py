"""Vocabulary tracking models with spaced repetition."""
import uuid
from datetime import datetime
from sqlalchemy import String, Integer, DateTime, ForeignKey, Float, JSON, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import Optional

from ..core.database import Base


class VocabularyItem(Base):
    """A vocabulary word/phrase in the learning database."""

    __tablename__ = "vocabulary_items"
    __table_args__ = (
        UniqueConstraint("language", "word", name="uq_language_word"),
    )

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    language: Mapped[str] = mapped_column(String(10), nullable=False)
    word: Mapped[str] = mapped_column(String(255), nullable=False)
    translation: Mapped[dict] = mapped_column(JSON, nullable=False)  # Multi-language translations
    pronunciation_guide: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    difficulty_level: Mapped[str] = mapped_column(String(2), default="A1")  # A1-C2
    context_examples: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)

    # Relationships
    user_progress: Mapped[list["UserVocabulary"]] = relationship(
        "UserVocabulary", back_populates="vocabulary_item"
    )

    def __repr__(self) -> str:
        return f"<Vocabulary {self.word} ({self.language})>"


class UserVocabulary(Base):
    """User's progress on a specific vocabulary item (spaced repetition)."""

    __tablename__ = "user_vocabulary"
    __table_args__ = (
        UniqueConstraint("user_id", "vocabulary_item_id", name="uq_user_vocab"),
    )

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id"), nullable=False
    )
    vocabulary_item_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("vocabulary_items.id"), nullable=False
    )
    times_encountered: Mapped[int] = mapped_column(Integer, default=0)
    times_used_correctly: Mapped[int] = mapped_column(Integer, default=0)
    last_reviewed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    next_review_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    ease_factor: Mapped[float] = mapped_column(Float, default=2.5)  # SM-2 algorithm
    interval_days: Mapped[int] = mapped_column(Integer, default=1)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="vocabulary_progress")
    vocabulary_item: Mapped["VocabularyItem"] = relationship(
        "VocabularyItem", back_populates="user_progress"
    )

    def __repr__(self) -> str:
        return f"<UserVocabulary user={self.user_id[:8]} item={self.vocabulary_item_id[:8]}>"
