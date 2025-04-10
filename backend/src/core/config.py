# src/core/config.py
from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path # Import Path
import os # Import os

class Settings(BaseSettings):
    PROJECT_NAME: str = "Elephant API"
    API_V1_STR: str = "/api/v1"

    # Database settings
    DATABASE_URL: str = "../data/tasks.db"

    # OpenAI settings
    OPENAI_API_KEY: str = "no key"
    OPENAI_MODEL: str = "gpt-4o-mini"

    # Filesystem Tool Settings
    # Define base directory relative to the project root (backend/..)
    PROJECT_ROOT: Path = Path(__file__).resolve().parent.parent.parent.parent
    ALLOWED_BASE_DIR: Path = PROJECT_ROOT / ".data"
    ALLOWED_BASE_DIR_RESOLVED: Path | None = None

    model_config = SettingsConfigDict(env_file=".env")

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