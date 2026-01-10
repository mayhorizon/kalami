"""Tests for authentication endpoints."""
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.asyncio
class TestRegistration:
    """Test user registration endpoint."""

    async def test_register_new_user(self, client: AsyncClient):
        """Test successful user registration."""
        response = await client.post(
            "/auth/register",
            json={
                "email": "newuser@example.com",
                "password": "securepassword123",
                "native_language": "en"
            }
        )

        assert response.status_code == 201
        data = response.json()
        assert data["email"] == "newuser@example.com"
        assert data["native_language"] == "en"
        assert "id" in data
        assert "password" not in data

    async def test_register_duplicate_email(self, client: AsyncClient, test_user):
        """Test registration with existing email fails."""
        response = await client.post(
            "/auth/register",
            json={
                "email": test_user.email,
                "password": "anotherpassword",
                "native_language": "en"
            }
        )

        assert response.status_code == 400
        assert "already registered" in response.json()["detail"].lower()

    async def test_register_invalid_email(self, client: AsyncClient):
        """Test registration with invalid email format."""
        response = await client.post(
            "/auth/register",
            json={
                "email": "not-an-email",
                "password": "password123",
                "native_language": "en"
            }
        )

        assert response.status_code == 422  # Validation error

    async def test_register_missing_password(self, client: AsyncClient):
        """Test registration without password fails."""
        response = await client.post(
            "/auth/register",
            json={
                "email": "test@example.com",
                "native_language": "en"
            }
        )

        assert response.status_code == 422  # Validation error


@pytest.mark.asyncio
class TestLogin:
    """Test login endpoint."""

    async def test_login_success(self, client: AsyncClient, test_user):
        """Test successful login."""
        response = await client.post(
            "/auth/login",
            data={
                "username": test_user.email,  # OAuth2 uses 'username' field
                "password": "testpassword123"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert len(data["access_token"]) > 0

    async def test_login_wrong_password(self, client: AsyncClient, test_user):
        """Test login with incorrect password."""
        response = await client.post(
            "/auth/login",
            data={
                "username": test_user.email,
                "password": "wrongpassword"
            }
        )

        assert response.status_code == 401
        assert "Invalid" in response.json()["detail"]

    async def test_login_nonexistent_user(self, client: AsyncClient):
        """Test login with non-existent email."""
        response = await client.post(
            "/auth/login",
            data={
                "username": "nonexistent@example.com",
                "password": "somepassword"
            }
        )

        assert response.status_code == 401

    async def test_login_missing_credentials(self, client: AsyncClient):
        """Test login without credentials."""
        response = await client.post("/auth/login", data={})

        assert response.status_code == 422  # Validation error


@pytest.mark.asyncio
class TestJWTAuthentication:
    """Test JWT token generation and validation."""

    async def test_get_current_user(self, client: AsyncClient, test_user, auth_headers):
        """Test getting current user with valid token."""
        response = await client.get("/auth/me", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["email"] == test_user.email
        assert data["id"] == test_user.id

    async def test_invalid_token(self, client: AsyncClient):
        """Test accessing protected endpoint with invalid token."""
        response = await client.get(
            "/auth/me",
            headers={"Authorization": "Bearer invalid_token"}
        )

        assert response.status_code == 401

    async def test_missing_token(self, client: AsyncClient):
        """Test accessing protected endpoint without token."""
        response = await client.get("/auth/me")

        assert response.status_code == 401

    async def test_expired_token(self, client: AsyncClient, test_user, db_session):
        """Test accessing endpoint with expired token."""
        from datetime import timedelta
        from app.services.auth_service import AuthService

        auth_service = AuthService(db_session)
        # Create token that expired 1 hour ago
        expired_token = auth_service.create_access_token(
            data={"sub": test_user.id},
            expires_delta=timedelta(hours=-1)
        )

        response = await client.get(
            "/auth/me",
            headers={"Authorization": f"Bearer {expired_token}"}
        )

        assert response.status_code == 401


@pytest.mark.asyncio
class TestPasswordHashing:
    """Test password hashing functionality."""

    async def test_password_is_hashed(self, db_session: AsyncSession):
        """Test that passwords are properly hashed in database."""
        from app.services.auth_service import AuthService

        auth_service = AuthService(db_session)
        plain_password = "mysecretpassword"

        user = await auth_service.create_user(
            email="hashtest@example.com",
            password=plain_password,
            native_language="en"
        )

        # Password should not be stored in plain text
        assert user.hashed_password != plain_password
        # Should be able to verify
        assert auth_service.verify_password(plain_password, user.hashed_password)

    async def test_different_passwords_different_hashes(self, db_session: AsyncSession):
        """Test that same password creates different hashes (salt)."""
        from app.services.auth_service import AuthService

        auth_service = AuthService(db_session)
        password = "samepassword"

        user1 = await auth_service.create_user(
            email="user1@example.com",
            password=password,
            native_language="en"
        )

        user2 = await auth_service.create_user(
            email="user2@example.com",
            password=password,
            native_language="en"
        )

        # Same password should produce different hashes due to salt
        assert user1.hashed_password != user2.hashed_password
