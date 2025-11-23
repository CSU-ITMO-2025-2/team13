import importlib
from typing import Any, AsyncGenerator, Optional

from config import settings
from loguru import logger


async def get_redis_client() -> AsyncGenerator[Any, None]:
    """Предоставляет асинхронный клиент Redis"""
    redis_client: Optional[Any] = None
    try:
        redis_module = importlib.import_module("redis.asyncio")
        redis_client = redis_module.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=0,
            decode_responses=True,
        )
        await redis_client.ping()
        logger.info("Подключение к Redis успешно установлено.")
    except Exception as e:
        logger.error(f"Не удалось подключиться к Redis: {e}")
        raise e

    try:
        yield redis_client
    finally:
        if redis_client is not None:
            await redis_client.close()
            logger.info("Подключение к Redis закрыто.")
