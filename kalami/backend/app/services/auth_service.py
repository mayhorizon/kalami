"""Authentication service for Kalami."""
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
import bcrypt
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ..core.config import settings
from ..models.user import User


class AuthService:
    """Handles user authentication and JWT token management."""

    def __init__(self, db: AsyncSession):
        self.db = db

    @staticmethod
    def hash_password(password: str) -> str:
        """Hash a password using bcrypt."""
        password_bytes = password.encode('utf-8')
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password_bytes, salt)
        return hashed.decode('utf-8')

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash."""
        password_bytes = plain_password.encode('utf-8')
        hashed_bytes = hashed_password.encode('utf-8')
        return bcrypt.checkpw(password_bytes, hashed_bytes)

    @staticmethod
    def create_access_token(
        data: dict,
        expires_delta: Optional[timedelta] = None
    ) -> str:
        """Create a JWT access token.

        Args:
            data: Payload data (should include 'sub' for user ID)
            expires_delta: Token expiration time

        Returns:
            Encoded JWT token string
        """
        to_encode = data.copy()

        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(
                minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
            )

        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(
            to_encode,
            settings.SECRET_KEY,
            algorithm=settings.ALGORITHM
        )
        return encoded_jwt

    @staticmethod
    def decode_token(token: str) -> Optional[dict]:
        """Decode and validate a JWT token.

        Args:
            token: JWT token string

        Returns:
            Decoded payload or None if invalid
        """
        try:
            payload = jwt.decode(
                token,
                settings.SECRET_KEY,
                algorithms=[settings.ALGORITHM]
            )
            return payload
        except JWTError:
            return None

    async def get_user_by_email(self, email: str) -> Optional[User]:
        """Get a user by email address."""
        result = await self.db.execute(
            select(User).where(User.email == email)
        )
        return result.scalar_one_or_none()

    async def get_user_by_id(self, user_id: str) -> Optional[User]:
        """Get a user by ID."""
        result = await self.db.execute(
            select(User).where(User.id == user_id)
        )
        return result.scalar_one_or_none()

    async def create_user(
        self,
        email: str,
        password: str,
        native_language: str = "en"
    ) -> User:
        """Create a new user account.

        Args:
            email: User's email address
            password: Plain text password (will be hashed)
            native_language: User's native language code

        Returns:
            Created User object
        """
        hashed_password = self.hash_password(password)

        user = User(
            email=email,
            hashed_password=hashed_password,
            native_language=native_language
        )

        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)

        return user

    async def authenticate_user(
        self,
        email: str,
        password: str
    ) -> Optional[User]:
        """Authenticate a user with email and password.

        Args:
            email: User's email address
            password: Plain text password

        Returns:
            User object if authentication successful, None otherwise
        """
        user = await self.get_user_by_email(email)

        if not user:
            return None

        if not self.verify_password(password, user.hashed_password):
            return None

        return user

    async def get_current_user(self, token: str) -> Optional[User]:
        """Get the current user from a JWT token.

        Args:
            token: JWT access token

        Returns:
            User object or None if invalid token
        """
        payload = self.decode_token(token)

        if not payload:
            return None

        user_id = payload.get("sub")
        if not user_id:
            return None

        return await self.get_user_by_id(user_id)
