"""User and learning profile routes."""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ..core.database import get_db
from ..models.user import User
from ..models.learning_profile import LearningProfile
from .auth import get_current_user

router = APIRouter(prefix="/users", tags=["Users"])


class LearningProfileCreate(BaseModel):
    """Request model for creating a learning profile."""
    target_language: str
    cefr_level: str = "A1"


class LearningProfileResponse(BaseModel):
    """Response model for learning profile."""
    id: str
    target_language: str
    cefr_level: str
    total_practice_time: int  # in seconds
    conversation_count: int
    current_streak: int
    vocabulary_mastered: int

    class Config:
        from_attributes = True


class LearningProfileUpdate(BaseModel):
    """Request model for updating a learning profile."""
    cefr_level: str | None = None


class UserStats(BaseModel):
    """User statistics summary."""
    total_sessions: int
    total_speaking_minutes: int
    total_vocabulary_mastered: int
    languages_learning: List[str]
    current_streak: int


@router.get("/profiles", response_model=List[LearningProfileResponse])
async def get_learning_profiles(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get all learning profiles for the current user."""
    from ..models.conversation import ConversationSession

    result = await db.execute(
        select(LearningProfile).where(LearningProfile.user_id == current_user.id)
    )
    profiles = list(result.scalars().all())

    # Get session counts per profile
    sessions_result = await db.execute(
        select(ConversationSession).where(ConversationSession.user_id == current_user.id)
    )
    sessions = list(sessions_result.scalars().all())

    # Build response with calculated fields
    response = []
    for profile in profiles:
        session_count = sum(1 for s in sessions if s.learning_profile_id == profile.id)
        response.append(LearningProfileResponse(
            id=profile.id,
            target_language=profile.target_language,
            cefr_level=profile.cefr_level,
            total_practice_time=profile.total_speaking_time_seconds or 0,
            conversation_count=session_count,
            current_streak=profile.streak_days or 0,
            vocabulary_mastered=profile.vocabulary_mastered or 0,
        ))

    return response


@router.post("/profiles", response_model=LearningProfileResponse, status_code=status.HTTP_201_CREATED)
async def create_learning_profile(
    profile_data: LearningProfileCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a new learning profile for a target language."""
    # Check if profile already exists for this language
    existing = await db.execute(
        select(LearningProfile).where(
            LearningProfile.user_id == current_user.id,
            LearningProfile.target_language == profile_data.target_language
        )
    )

    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Profile for {profile_data.target_language} already exists"
        )

    profile = LearningProfile(
        user_id=current_user.id,
        target_language=profile_data.target_language,
        cefr_level=profile_data.cefr_level
    )

    db.add(profile)
    await db.commit()
    await db.refresh(profile)

    return LearningProfileResponse(
        id=profile.id,
        target_language=profile.target_language,
        cefr_level=profile.cefr_level,
        total_practice_time=0,
        conversation_count=0,
        current_streak=0,
        vocabulary_mastered=0,
    )


@router.get("/profiles/{profile_id}", response_model=LearningProfileResponse)
async def get_learning_profile(
    profile_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get a specific learning profile."""
    result = await db.execute(
        select(LearningProfile).where(
            LearningProfile.id == profile_id,
            LearningProfile.user_id == current_user.id
        )
    )

    profile = result.scalar_one_or_none()
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profile not found"
        )

    return profile


@router.patch("/profiles/{profile_id}", response_model=LearningProfileResponse)
async def update_learning_profile(
    profile_id: str,
    update_data: LearningProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update a learning profile."""
    result = await db.execute(
        select(LearningProfile).where(
            LearningProfile.id == profile_id,
            LearningProfile.user_id == current_user.id
        )
    )

    profile = result.scalar_one_or_none()
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profile not found"
        )

    if update_data.cefr_level:
        if update_data.cefr_level not in ["A1", "A2", "B1", "B2", "C1", "C2"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid CEFR level"
            )
        profile.cefr_level = update_data.cefr_level

    await db.commit()
    await db.refresh(profile)

    return profile


@router.delete("/profiles/{profile_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_learning_profile(
    profile_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete a learning profile."""
    result = await db.execute(
        select(LearningProfile).where(
            LearningProfile.id == profile_id,
            LearningProfile.user_id == current_user.id
        )
    )

    profile = result.scalar_one_or_none()
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profile not found"
        )

    await db.delete(profile)
    await db.commit()


@router.get("/stats", response_model=UserStats)
async def get_user_stats(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get user statistics across all learning profiles."""
    from ..models.conversation import ConversationSession

    # Get all profiles
    profiles_result = await db.execute(
        select(LearningProfile).where(LearningProfile.user_id == current_user.id)
    )
    profiles = list(profiles_result.scalars().all())

    # Get session count
    sessions_result = await db.execute(
        select(ConversationSession).where(ConversationSession.user_id == current_user.id)
    )
    sessions = list(sessions_result.scalars().all())

    total_speaking_seconds = sum(p.total_speaking_time_seconds for p in profiles)
    total_vocabulary = sum(p.vocabulary_mastered for p in profiles)
    max_streak = max((p.streak_days for p in profiles), default=0)

    return UserStats(
        total_sessions=len(sessions),
        total_speaking_minutes=total_speaking_seconds // 60,
        total_vocabulary_mastered=total_vocabulary,
        languages_learning=[p.target_language for p in profiles],
        current_streak=max_streak
    )
