"""API Routers for Kalami."""
from .auth import router as auth_router
from .users import router as users_router
from .conversations import router as conversations_router
from .speech import router as speech_router

__all__ = ["auth_router", "users_router", "conversations_router", "speech_router"]
