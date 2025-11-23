"""
Сервис для управления JWT токенами и их инвалидацией через Redis
"""

from datetime import datetime, timezone

from jose import jwt
from loguru import logger

from app.config import settings


class TokenService:
    def __init__(self, redis_client):
        self.redis = redis_client

    async def invalidate_token(
        self, token: str, token_type: str = "access"
    ) -> bool:
        """
        Добавляет токен в черный список (Redis)
        """
        try:
            # Декодируем токен чтобы получить exp и user_id
            payload = jwt.decode(
                token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
            )

            user_id = payload.get("sub")
            exp = payload.get("exp")

            if not exp:
                logger.warning("Токен не содержит exp, не можем инвалидировать")
                return False

            # Время жизни в Redis = время до истечения токена
            current_time = datetime.now(timezone.utc).timestamp()
            ttl = int(exp - current_time)

            if ttl <= 0:
                logger.info("Токен уже истек, не добавляем в blacklist")
                return True

            # blacklist:{token_type}:{user_id}:{jti_or_token_hash}
            token_id = token[-20:]
            key = f"blacklist:{token_type}:{user_id}:{token_id}"

            await self.redis.setex(key, ttl, "1")
            logger.info(f"Токен добавлен в blacklist: {key} (TTL: {ttl}s)")

            return True

        except Exception as e:
            logger.error(f"Ошибка при инвалидации токена: {e}")
            return False

    async def is_token_blacklisted(
        self, token: str, token_type: str = "access"
    ) -> bool:
        """
        Проверяет, находится ли токен в blacklist
        """
        try:
            payload = jwt.decode(
                token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
            )

            user_id = payload.get("sub")
            token_id = token[-20:]
            key = f"blacklist:{token_type}:{user_id}:{token_id}"

            exists = await self.redis.exists(key)

            if exists:
                logger.info(f"Токен найден в blacklist: {key}")
                return True

            return False

        except Exception as e:
            logger.error(f"Ошибка при проверке blacklist: {e}")
            return True

    async def invalidate_all_user_tokens(self, user_id: str) -> bool:
        """
        Инвалидирует ВСЕ токены пользователя
        """
        try:
            key = f"blacklist:user:{str(user_id)}:all"
            await self.redis.setex(key, 7 * 24 * 60 * 60, "1")

            logger.info(f"Все токены пользователя {user_id} инвалидированы")
            return True

        except Exception as e:
            logger.error(f"Ошибка при инвалидации всех токенов пользователя: {e}")
            return False

    async def is_user_tokens_invalidated(self, user_id: str) -> bool:
        """
        Проверяет, инвалидированы ли все токены пользователя
        """
        try:
            key = f"blacklist:user:{str(user_id)}:all"
            exists = await self.redis.exists(key)
            return bool(exists)

        except Exception as e:
            logger.error(f"Ошибка при проверке инвалидации пользователя: {e}")
            return True

    async def store_refresh_token(
        self, user_id: int, refresh_token: str, ttl: int = 7 * 24 * 60 * 60
    ) -> bool:
        """
        Сохраняет refresh token в Redis
        """
        try:
            token_id = refresh_token[-20:]
            key = f"refresh:{user_id}:{token_id}"

            await self.redis.setex(key, ttl, refresh_token)
            logger.info(f"Refresh token сохранен: {key}")

            return True

        except Exception as e:
            logger.error(f"Ошибка при сохранении refresh token: {e}")
            return False

    async def validate_refresh_token(
        self, user_id: int, refresh_token: str
    ) -> bool:
        """
        Проверяет валидность refresh token через Redis
        """
        try:
            token_id = refresh_token[-20:]
            key = f"refresh:{user_id}:{token_id}"

            stored_token = await self.redis.get(key)

            if stored_token == refresh_token:
                logger.info(f"Refresh token валиден: {key}")
                return True

            logger.warning(f"Refresh token не найден или не совпадает: {key}")
            return False

        except Exception as e:
            logger.error(f"Ошибка при валидации refresh token: {e}")
            return False

    async def remove_refresh_token(self, user_id: int, refresh_token: str) -> bool:
        """
        Удаляет refresh token из Redis (при logout)
        """
        try:
            token_id = refresh_token[-20:]
            key = f"refresh:{user_id}:{token_id}"

            await self.redis.delete(key)
            logger.info(f"Refresh token удален: {key}")

            return True

        except Exception as e:
            logger.error(f"Ошибка при удалении refresh token: {e}")
            return False
