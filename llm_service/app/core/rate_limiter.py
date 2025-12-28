import time

from loguru import logger
from redis.asyncio import Redis


class RateLimiter:
    def __init__(self, redis_client: Redis):
        self.redis = redis_client

    async def check_and_acquire(
        self, key_prefix: str, limit: int, window_seconds: int
    ) -> bool:
        """
        Проверяет лимит для заданного окна времени
        """
        current_window_start = int(time.time() // window_seconds)
        key = f"{key_prefix}:{window_seconds}:{current_window_start}"

        try:
            current_count = await self.redis.incr(key)

            if current_count == 1:
                await self.redis.expire(key, window_seconds + 10)

            if current_count > limit:
                logger.warning(
                    f"Rate limit exceeded for {key_prefix}: {current_count}/{limit} (Window: {window_seconds}s)"
                )
                return False

            return True
        except Exception as e:
            logger.error(f"Redis rate limiter error: {e}")
            return False
