"""Learning profile model for tracking language learning progress."""
import uuid
from datetime import datetime
from sqlalchemy import String, Integer, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..core.database import Base


class LearningProfile(Base):
    """Language learning profile for a specific target language."""

    __tablename__ = "learning_profiles"
    __table_args__ = (
        UniqueConstraint("user_id", "target_language", name="uq_user_language"),
    )

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id"), nullable=False
    )
    target_language: Mapped[str] = mapped_column(String(10), nullable=False)
    cefr_level: Mapped[str] = mapped_column(String(2), default="A1")  # A1-C2
    total_speaking_time_seconds: Mapped[int] = mapped_column(Integer, default=0)
    vocabulary_mastered: Mapped[int] = mapped_column(Integer, default=0)
    streak_days: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="learning_profiles")
    sessions: Mapped[list["ConversationSession"]] = relationship(
        "ConversationSession", back_populates="learning_profile"
    )

    def __repr__(self) -> str:
        return f"<LearningProfile {self.target_language} ({self.cefr_level})>"
