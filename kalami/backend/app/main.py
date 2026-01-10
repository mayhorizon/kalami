"""Kalami Backend - FastAPI Application

A vocal AI assistant for language learning through conversation.
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .core.config import settings
from .core.database import init_db
from .routers import auth_router, users_router, conversations_router, speech_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    # Startup
    print(f"Starting {settings.APP_NAME}...")
    await init_db()
    print("Database initialized")
    yield
    # Shutdown
    print(f"Shutting down {settings.APP_NAME}...")


app = FastAPI(
    title=settings.APP_NAME,
    description="Vocal AI assistant for language learning through natural conversation",
    version="0.1.0",
    lifespan=lifespan
)

# CORS middleware for mobile app
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth_router)
app.include_router(users_router)
app.include_router(conversations_router)
app.include_router(speech_router)


@app.get("/")
async def root():
    """Health check endpoint."""
    return {
        "name": settings.APP_NAME,
        "status": "healthy",
        "version": "0.1.0"
    }


@app.get("/health")
async def health():
    """Detailed health check."""
    return {
        "status": "healthy",
        "services": {
            "database": "connected",
            "stt": "whisper" if settings.OPENAI_API_KEY else "not configured",
            "tts": "elevenlabs" if settings.ELEVENLABS_API_KEY else "not configured",
            "llm": "anthropic" if settings.ANTHROPIC_API_KEY else (
                "openai" if settings.OPENAI_API_KEY else "not configured"
            )
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
