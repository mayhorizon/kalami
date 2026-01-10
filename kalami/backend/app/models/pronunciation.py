"""Pronunciation analysis model."""
import uuid
from datetime import datetime
from sqlalchemy import String, DateTime, ForeignKey, Float, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import Optional

from ..core.database import Base


class PronunciationAnalysis(Base):
    """Detailed pronunciation analysis for a user message."""

    __tablename__ = "pronunciation_analyses"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    message_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("conversation_messages.id"), nullable=False
    )
    overall_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    phoneme_scores: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    problem_areas: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    improvement_suggestions: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    message: Mapped["ConversationMessage"] = relationship(
        "ConversationMessage", back_populates="pronunciation_analysis"
    )

    def __repr__(self) -> str:
        return f"<PronunciationAnalysis score={self.overall_score}>"
