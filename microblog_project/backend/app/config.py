import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Настройки приложения и базы данных."""
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "postgresql+psycopg2://microuser:micropassword@db:5432/microblog"
    )


settings = Settings()
