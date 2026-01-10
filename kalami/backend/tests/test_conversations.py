"""Tests for conversation endpoints."""
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.asyncio
class TestConversationSessions:
    """Test conversation session management."""

    async def test_start_conversation_session(
        self, client: AsyncClient, test_user, auth_headers, db_session
    ):
        """Test starting a new conversation session."""
        # First create a learning profile
        from app.models.learning_profile import LearningProfile

        profile = LearningProfile(
            user_id=test_user.id,
            target_language="es",
            cefr_level="A1"
        )
        db_session.add(profile)
        await db_session.commit()
        await db_session.refresh(profile)

        response = await client.post(
            "/conversations/sessions",
            headers=auth_headers,
            json={
                "profile_id": profile.id,
                "topic": "travel"
            }
        )

        assert response.status_code == 201
        data = response.json()
        assert data["topic"] == "travel"
        assert "id" in data
        assert data["words_spoken"] == 0

    async def test_list_conversation_sessions(
        self, client: AsyncClient, test_user, auth_headers, db_session
    ):
        """Test listing user's conversation sessions."""
        # Create learning profile
        from app.models.learning_profile import LearningProfile

        profile = LearningProfile(
            user_id=test_user.id,
            target_language="fr",
            cefr_level="B1"
        )
        db_session.add(profile)
        await db_session.commit()
        await db_session.refresh(profile)

        # Start a session
        await client.post(
            "/conversations/sessions",
            headers=auth_headers,
            json={
                "profile_id": profile.id,
                "topic": "food"
            }
        )

        # List sessions
        response = await client.get("/conversations/sessions", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1

    async def test_get_conversation_session(
        self, client: AsyncClient, test_user, auth_headers, db_session
    ):
        """Test getting a specific conversation session."""
        # Create learning profile
        from app.models.learning_profile import LearningProfile

        profile = LearningProfile(
            user_id=test_user.id,
            target_language="de",
            cefr_level="A1"
        )
        db_session.add(profile)
        await db_session.commit()
        await db_session.refresh(profile)

        # Start session
        create_response = await client.post(
            "/conversations/sessions",
            headers=auth_headers,
            json={
                "profile_id": profile.id,
                "topic": "restaurant"
            }
        )
        session_id = create_response.json()["id"]

        # Get session
        response = await client.get(
            f"/conversations/sessions/{session_id}",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == session_id
        assert data["topic"] == "restaurant"

    async def test_end_conversation_session(
        self, client: AsyncClient, test_user, auth_headers, db_session
    ):
        """Test ending a conversation session."""
        # Create learning profile
        from app.models.learning_profile import LearningProfile

        profile = LearningProfile(
            user_id=test_user.id,
            target_language="it",
            cefr_level="A1"
        )
        db_session.add(profile)
        await db_session.commit()
        await db_session.refresh(profile)

        # Start session
        create_response = await client.post(
            "/conversations/sessions",
            headers=auth_headers,
            json={
                "profile_id": profile.id,
                "topic": "shopping"
            }
        )
        session_id = create_response.json()["id"]

        # End session
        response = await client.post(
            f"/conversations/sessions/{session_id}/end",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["ended_at"] is not None


@pytest.mark.asyncio
class TestConversationMessages:
    """Test conversation message handling."""

    async def test_get_session_messages(
        self, client: AsyncClient, test_user, auth_headers, db_session
    ):
        """Test retrieving all messages in a session."""
        # Create learning profile and session
        from app.models.learning_profile import LearningProfile

        profile = LearningProfile(
            user_id=test_user.id,
            target_language="fr",
            cefr_level="B1"
        )
        db_session.add(profile)
        await db_session.commit()
        await db_session.refresh(profile)

        session_response = await client.post(
            "/conversations/sessions",
            headers=auth_headers,
            json={
                "profile_id": profile.id,
                "topic": "culture"
            }
        )
        session_id = session_response.json()["id"]

        # Get messages
        response = await client.get(
            f"/conversations/sessions/{session_id}/messages",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
