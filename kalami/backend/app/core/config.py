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

    # AI Services (PAID - Optional)
    OPENAI_API_KEY: str = ""
    ANTHROPIC_API_KEY: str = ""
    ASSEMBLYAI_API_KEY: str = ""
    ELEVENLABS_API_KEY: str = ""

    # Voice Processing Provider Selection
    # FREE options: whisper-local, ollama, piper
    # PAID options: openai, assemblyai, anthropic, elevenlabs
    STT_PROVIDER: str = "whisper-local"  # whisper-local (FREE), faster-whisper (FREE), openai (PAID)
    LLM_PROVIDER: str = "ollama"  # ollama (FREE), openai (PAID), anthropic (PAID)
    TTS_PROVIDER: str = "piper"  # piper (FREE), pyttsx3 (FREE), openai (PAID)

    # FREE Model Configuration
    WHISPER_MODEL_SIZE: str = "base"  # tiny, base, small, medium, large
    OLLAMA_MODEL: str = "llama3.2:3b"  # llama3.2:1b, llama3.2:3b, llama3.2, mistral
    PIPER_VOICES_DIR: str = "./models/piper_voices"

    # PAID Model Configuration (if using paid services)
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
