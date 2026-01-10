"""Tests for user and learning profile endpoints."""
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.asyncio
class TestUserProfiles:
    """Test user profile endpoints."""

    async def test_get_user_stats(self, client: AsyncClient, test_user, auth_headers):
        """Test getting user statistics."""
        response = await client.get("/users/stats", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert "total_sessions" in data
        assert "total_speaking_minutes" in data
        assert "total_vocabulary_mastered" in data
        assert "languages_learning" in data
        assert "current_streak" in data


@pytest.mark.asyncio
class TestLearningProfiles:
    """Test learning profile management."""

    async def test_create_learning_profile(
        self, client: AsyncClient, test_user, auth_headers
    ):
        """Test creating a new learning profile."""
        response = await client.post(
            "/users/profiles",
            headers=auth_headers,
            json={
                "target_language": "es",
                "cefr_level": "A1"
            }
        )

        assert response.status_code == 201
        data = response.json()
        assert data["target_language"] == "es"
        assert data["cefr_level"] == "A1"
        assert data["total_speaking_time_seconds"] == 0
        assert data["vocabulary_mastered"] == 0

    async def test_list_learning_profiles(
        self, client: AsyncClient, test_user, auth_headers
    ):
        """Test listing user's learning profiles."""
        # Create a learning profile first
        await client.post(
            "/users/profiles",
            headers=auth_headers,
            json={
                "target_language": "es",
                "cefr_level": "A1"
            }
        )

        response = await client.get(
            "/users/profiles",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        assert data[0]["target_language"] == "es"

    async def test_get_learning_profile(
        self, client: AsyncClient, test_user, auth_headers
    ):
        """Test getting a specific learning profile."""
        # Create profile
        create_response = await client.post(
            "/users/profiles",
            headers=auth_headers,
            json={
                "target_language": "fr",
                "cefr_level": "B1"
            }
        )
        profile_id = create_response.json()["id"]

        # Get profile
        response = await client.get(
            f"/users/profiles/{profile_id}",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == profile_id
        assert data["target_language"] == "fr"

    async def test_update_learning_profile(
        self, client: AsyncClient, test_user, auth_headers
    ):
        """Test updating a learning profile."""
        # Create profile
        create_response = await client.post(
            "/users/profiles",
            headers=auth_headers,
            json={
                "target_language": "de",
                "cefr_level": "A1"
            }
        )
        profile_id = create_response.json()["id"]

        # Update profile
        response = await client.patch(
            f"/users/profiles/{profile_id}",
            headers=auth_headers,
            json={
                "cefr_level": "A2"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["cefr_level"] == "A2"

    async def test_delete_learning_profile(
        self, client: AsyncClient, test_user, auth_headers
    ):
        """Test deleting a learning profile."""
        # Create profile
        create_response = await client.post(
            "/users/profiles",
            headers=auth_headers,
            json={
                "target_language": "it",
                "cefr_level": "A1"
            }
        )
        profile_id = create_response.json()["id"]

        # Delete profile
        response = await client.delete(
            f"/users/profiles/{profile_id}",
            headers=auth_headers
        )

        assert response.status_code == 204

        # Verify it's deleted
        get_response = await client.get(
            f"/users/profiles/{profile_id}",
            headers=auth_headers
        )
        assert get_response.status_code == 404

    async def test_create_duplicate_language_profile(
        self, client: AsyncClient, test_user, auth_headers
    ):
        """Test that creating duplicate language profiles fails."""
        # Create first profile
        await client.post(
            "/users/profiles",
            headers=auth_headers,
            json={
                "target_language": "es",
                "cefr_level": "A1"
            }
        )

        # Try to create another profile for same language
        response = await client.post(
            "/users/profiles",
            headers=auth_headers,
            json={
                "target_language": "es",
                "cefr_level": "A2"
            }
        )

        # Should fail with 400
        assert response.status_code == 400
        assert "already exists" in response.json()["detail"].lower()
