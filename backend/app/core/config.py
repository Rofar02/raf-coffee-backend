from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    DATABASE_URL: str
    REDIS_URL: str
    ADMIN_TOKEN: str
    SMTP_HOST: str | None = None
    SMTP_PORT: int = 587
    SMTP_USER: str | None = None
    SMTP_PASSWORD: str | None = None
    SMTP_FROM: str | None = None
    VACANCY_EMAIL_TO: str | None = None
    SMTP_USE_TLS: bool = True

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

@lru_cache
def get_settings():
    return Settings()