"""DevInsight configuration module."""
import os
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # App
    APP_NAME: str = "DevInsight"
    APP_ENV: str = "development"
    SECRET_KEY: str = "devinsight-secret-key-change-in-production"
    BACKEND_URL: str = "http://localhost:8000"
    FRONTEND_URL: str = "http://localhost:5173"

    # Google OAuth
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""

    # GitHub
    GITHUB_TOKEN: str = ""

    # Redis
    REDIS_URL: str = "redis://localhost:6379"

    # Supabase
    SUPABASE_URL: str = ""
    SUPABASE_ANON_KEY: str = ""
    SUPABASE_SERVICE_ROLE_KEY: str = ""

    # Analysis
    CLONE_DIR: str = "/tmp/cloned_repos" if os.getenv("VERCEL") else os.path.join(os.path.dirname(os.path.dirname(__file__)), "cloned_repos")
    MAX_FILE_SIZE_KB: int = 500
    SUPPORTED_EXTENSIONS: list[str] = [".py", ".js", ".jsx", ".ts", ".tsx", ".java", ".c", ".cpp", ".h"]

    class Config:
        env_file = ".env"
        extra = "allow"


settings = Settings()
