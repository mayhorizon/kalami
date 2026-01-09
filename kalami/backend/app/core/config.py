"""
Configuration settings for Kalami API
"""
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings"""

    # Application
    APP_NAME: str = "Kalami"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = True

    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:8000"]

    # Database
    DATABASE_URL: str = "postgresql://kalami:kalami@localhost/kalami"

    # Redis
    REDIS_URL: str = "redis://localhost:6379"

    # Security
    SECRET_KEY: str = "your-secret-key-change-this-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # AI Services
    OPENAI_API_KEY: str = ""
    ANTHROPIC_API_KEY: str = ""
    ASSEMBLYAI_API_KEY: str = ""
    ELEVENLABS_API_KEY: str = ""

    # Voice Processing
    STT_PROVIDER: str = "openai"  # openai, assemblyai
    LLM_PROVIDER: str = "openai"  # openai, anthropic
    TTS_PROVIDER: str = "openai"  # openai, elevenlabs

    # Model Configuration
    OPENAI_MODEL: str = "gpt-4-turbo-preview"
    ANTHROPIC_MODEL: str = "claude-3-opus-20240229"

    # WebSocket
    WS_HEARTBEAT_INTERVAL: int = 30  # seconds

    # Supported Languages
    SUPPORTED_LANGUAGES: List[str] = ["es", "fr", "de"]  # Spanish, French, German

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True
    )


settings = Settings()
