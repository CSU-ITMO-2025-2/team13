import os
from functools import lru_cache
from urllib.parse import quote_plus

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Environment
    DEV_MODE: bool = True
    USE_SQLITE: bool = False

    # Cypher
    SECRET_KEY: str = "your-secret-key"
    ALGORITHM: str = "HS256"

    # Database
    POSTGRES_DB: str = "auth_db"
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432

    REDIS_HOST: str = "redis"
    REDIS_PORT: int = 6379

    TEST_DATABASE_URL: str = "sqlite+aiosqlite:///:memory:"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def BASE_DIR(self):
        return os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

    @property
    def LOGS_DIR(self):
        return os.path.join(self.BASE_DIR, "logs")

    @property
    def DATA_DIR(self):
        return os.path.join(self.BASE_DIR, "data")

    @property
    def SQLITE_DB_URL(self):
        return f"sqlite+aiosqlite:///{self.BASE_DIR}/data/db.sqlite3"

    @property
    def POSTGRES_DB_URL(self):
        return (
            f"postgresql+asyncpg://{self.POSTGRES_USER}:"
            f"{quote_plus(self.POSTGRES_PASSWORD)}@{self.POSTGRES_HOST}:"
            f"{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )


@lru_cache()
def get_settings():
    return Settings()


settings = get_settings()
database_url = (
    settings.SQLITE_DB_URL if settings.USE_SQLITE else settings.POSTGRES_DB_URL
)
