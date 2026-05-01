"""
Application Configuration
All settings are loaded from environment variables with sensible defaults.
"""

from pydantic_settings import BaseSettings
from typing import List
import os


class Settings(BaseSettings):
    # API
    API_VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"

    # Groq - free LLM API powering all AI features
    # Get your free key at https://console.groq.com
    GROQ_API_KEY: str = ""

    # CORS - allow Vite dev server + production domains
    CORS_ORIGINS: List[str] = [
    "http://localhost:5173",
    "http://localhost:3000",
    "http://127.0.0.1:5173",
    "https://path-nova.vercel.app",
    "https://path-nova-frontend.vercel.app",
]

    # File upload limits
    MAX_FILE_SIZE_MB: int = 10
    UPLOAD_DIR: str = "/tmp/pathnova_uploads"

    # Rate limiting (requests per minute per IP)
    RATE_LIMIT_RPM: int = 30

    # GitHub API (optional, for GitHub profile analysis)
    GITHUB_TOKEN: str = ""

    # Session / in-memory cache TTL (seconds)
    CACHE_TTL: int = 3600

    model_config = {"env_file": ".env", "case_sensitive": False}


settings = Settings()

# Ensure upload directory exists
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
