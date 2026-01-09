"""
Kalami - AI Language Learning Assistant
Main FastAPI application
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings

# Initialize FastAPI app
app = FastAPI(
    title="Kalami API",
    description="AI-powered language learning assistant with real-time voice conversations",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Root endpoint - API health check"""
    return {
        "message": "Welcome to Kalami API",
        "version": "0.1.0",
        "status": "healthy"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring"""
    return JSONResponse(
        status_code=200,
        content={
            "status": "healthy",
            "service": "kalami-api"
        }
    )


@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    print("🚀 Kalami API starting up...")
    # TODO: Initialize database connection
    # TODO: Initialize Redis connection
    # TODO: Initialize AI service clients
    print("✅ Kalami API ready")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    print("👋 Kalami API shutting down...")
    # TODO: Close database connections
    # TODO: Close Redis connections
    print("✅ Cleanup complete")


# Import and include routers
# TODO: from app.api import auth, users, conversations, voice
# TODO: app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
# TODO: app.include_router(users.router, prefix="/api/users", tags=["users"])
# TODO: app.include_router(conversations.router, prefix="/api/conversations", tags=["conversations"])
# TODO: app.include_router(voice.router, prefix="/api/voice", tags=["voice"])

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
