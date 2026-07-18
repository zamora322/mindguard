from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List

class Settings(BaseSettings):
    PROJECT_NAME: str = "MindGuard"
    API_V1_STR: str = "/api/v1"
    
    # CORS Origins (Next.js typically runs on http://localhost:3000)
    BACKEND_CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]

    # Google OAuth Configuration
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    GOOGLE_REDIRECT_URI: str = ""

    # Database Configuration
    DATABASE_URL: str = ""

    # JWT Security Configuration
    SECRET_KEY: str = "secret-fallback-do-not-use-in-production"

    # Gmail Sync Configuration
    GMAIL_SYNC_DAYS: int = 8

    # Calendar Sync Configuration
    CALENDAR_SYNC_DAYS: int = 8

    model_config = SettingsConfigDict(
        case_sensitive=True,
        env_file=".env",
        env_file_encoding="utf-8"
    )

settings = Settings()
