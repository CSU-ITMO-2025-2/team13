import os
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class ELogLevel(str):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class Settings(BaseSettings):
    """
    Класс для хранения и валидации настроек приложения
    Загружает переменные из .env файла
    """

    # LLM
    GEMINI_API_KEY: str
    GEMINI_API_BASE_URL: str = (
        "https://generativelanguage.googleapis.com/v1beta/models"
    )
    PROXY_URL: str | None = None

    REQUESTS_PER_MINUTE: int = 10

    DEV_MODE: bool = True

    RABBITMQ_USER: str = "user"
    RABBITMQ_PASSWORD: str = "password"
    RABBITMQ_HOST: str = "rabbitmq"
    RABBITMQ_PORT: int = 5672

    REDIS_HOST: str = "redis"
    REDIS_PORT: int = 6379

    ARTICLE_QUEUE_NAME: str = "article_queue"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    @property
    def RABBITMQ_URL(self) -> str:
        return f"amqp://{self.RABBITMQ_USER}:{self.RABBITMQ_PASSWORD}@{self.RABBITMQ_HOST}:{self.RABBITMQ_PORT}/"

    @property
    def CONSOLE_LOG_LEVEL(self):
        return ELogLevel.DEBUG if self.DEV_MODE else ELogLevel.WARNING

    @property
    def BASE_DIR(self):
        return os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

    @property
    def LOGS_DIR(self):
        return os.path.join(self.BASE_DIR, "logs")


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
