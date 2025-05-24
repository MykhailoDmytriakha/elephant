# src/core/config.py
from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path # Import Path
import os # Import os
from typing import List

class Settings(BaseSettings):
    PROJECT_NAME: str = "Elephant API"
    API_V1_STR: str = "/api/v1"

    # Database settings
    DATABASE_URL: str = "../data/tasks.db"

    # OpenAI settings (for use with Google ADK via LiteLLM)
    OPENAI_API_KEY: str = "no key"
    OPENAI_MODEL: str = "gpt-4o-mini"
    
    # CORS settings - will be parsed from comma-separated string in .env
    FRONTEND_CORS_ORIGINS: str = "http://localhost:3000"

    # Filesystem Tool Settings
    # Define base directory relative to the project root (backend/..)
    PROJECT_ROOT: Path = Path(__file__).resolve().parent.parent.parent.parent
    ALLOWED_BASE_DIR: Path = PROJECT_ROOT / ".data"
    ALLOWED_BASE_DIR_RESOLVED: Path | None = None

    model_config = SettingsConfigDict(env_file=".env")
    
    @property
    def cors_origins(self) -> List[str]:
        """Parse CORS origins from comma-separated string"""
        if isinstance(self.FRONTEND_CORS_ORIGINS, str):
            return [origin.strip() for origin in self.FRONTEND_CORS_ORIGINS.split(",")]
        return self.FRONTEND_CORS_ORIGINS

settings = Settings()

# Ensure the allowed base directory exists
try:
    settings.ALLOWED_BASE_DIR.mkdir(parents=True, exist_ok=True)
    # Store the resolved absolute path for security checks
    settings.ALLOWED_BASE_DIR_RESOLVED = settings.ALLOWED_BASE_DIR.resolve()
    print(f"File system tools allowed base directory: {settings.ALLOWED_BASE_DIR_RESOLVED}")
except Exception as e:
    print(f"Error creating or accessing allowed base directory {settings.ALLOWED_BASE_DIR}: {e}")
    # Decide if you want to raise an error or proceed without filesystem tools
    # raise e
    settings.ALLOWED_BASE_DIR_RESOLVED = None # Indicate failure

# --- Expose OpenAI API key for Google ADK LiteLLM integration ---
import os as _os
_os.environ["OPENAI_API_KEY"] = settings.OPENAI_API_KEY
print(f"OpenAI API key configured for Google ADK")