from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "Elephant API"
    API_V1_STR: str = "/api/v1"

    # Database settings
    DATABASE_URL: str = "data/tasks.db"

    # OpenAI settings
    OPENAI_API_KEY: str
    OPENAI_MODEL: str = "gpt-4o-mini"

    model_config = SettingsConfigDict(env_file=".env")


settings = Settings()
