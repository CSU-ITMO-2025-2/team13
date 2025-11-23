import uuid
from datetime import datetime, timezone

from fastapi import Depends, Request
from jose import ExpiredSignatureError, JWTError, jwt
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dao import UserDAO
from app.auth.models import User
from app.auth.token_service import TokenService
from app.config import settings
from app.dependencies.dao_dep import get_session_without_commit
from app.dependencies.services_dep import get_token_service
from app.exceptions import (
    ForbiddenException,
    NoJwtException,
    NoUserIdException,
    TokenExpiredException,
    TokenNoFound,
    UserNotFoundException,
)


def get_access_token(request: Request) -> str:
    """Извлекает access_token из кук"""
    token = request.cookies.get("user_access_token")
    if not token:
        raise TokenNoFound
    return token


def get_refresh_token(request: Request) -> str:
    """Извлекает refresh_token из кук"""
    token = request.cookies.get("user_refresh_token")
    if not token:
        raise TokenNoFound
    return token


async def check_refresh_token(
    token: str = Depends(get_refresh_token),
    session: AsyncSession = Depends(get_session_without_commit),
    token_service: TokenService = Depends(get_token_service),
) -> User:
    """Проверяет refresh_token и возвращает пользователя"""
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        user_id = payload.get("sub")
        if not user_id:
            raise NoJwtException

        # Проверяем, не в blacklist ли токен
        try:
            if await token_service.is_token_blacklisted(token, "refresh"):
                logger.warning(
                    f"Refresh token в blacklist для пользователя {user_id}"
                )
                raise TokenExpiredException

            # Проверяем глобальную инвалидацию всех токенов пользователя
            if await token_service.is_user_tokens_invalidated(str(user_id)):
                logger.warning(
                    f"Все токены инвалидированы для пользователя {user_id}"
                )
                raise TokenExpiredException
        except Exception as e:
            # Если Redis недоступен, логируем но продолжаем работу
            logger.warning(
                f"Проверка Redis не удалась, продолжаем без проверки blacklist: {e}"
            )

        # Ищем пользователя по UUID
        user_uuid = uuid.UUID(str(user_id))
        user = await UserDAO(session).find_one_or_none_by_id(data_id=user_uuid)
        if not user:
            raise NoJwtException

        return user
    except ExpiredSignatureError:
        raise TokenExpiredException
    except TokenExpiredException:
        raise
    except JWTError:
        raise NoJwtException


async def get_current_user(
    token: str = Depends(get_access_token),
    session: AsyncSession = Depends(get_session_without_commit),
    token_service: TokenService = Depends(get_token_service),
) -> User:
    """Проверяет access_token и возвращает пользователя"""
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
    except ExpiredSignatureError:
        raise TokenExpiredException
    except JWTError:
        raise NoJwtException

    expire: str = payload.get("exp")
    expire_time = datetime.fromtimestamp(int(expire), tz=timezone.utc)
    if (not expire) or (expire_time < datetime.now(timezone.utc)):
        raise TokenExpiredException

    user_id: str = payload.get("sub")
    if not user_id:
        raise NoUserIdException

    # Проверяем, не в blacklist ли токен
    try:
        if await token_service.is_token_blacklisted(token, "access"):
            logger.warning(f"Access token в blacklist для пользователя {user_id}")
            raise TokenExpiredException

        # Проверяем глобальную инвалидацию всех токенов пользователя
        if await token_service.is_user_tokens_invalidated(str(user_id)):
            logger.warning(f"Все токены инвалидированы для пользователя {user_id}")
            raise TokenExpiredException
    except TokenExpiredException:
        raise
    except Exception as e:
        # Если Redis недоступен, логируем но продолжаем работу
        logger.warning(
            f"Проверка Redis не удалась, продолжаем без проверки blacklist: {e}"
        )

    user_uuid = uuid.UUID(str(user_id))
    user = await UserDAO(session).find_one_or_none_by_id(data_id=user_uuid)
    if not user:
        raise UserNotFoundException
    return user


async def get_current_admin_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """Проверяем права пользователя как администратора"""
    if current_user.role.id in [3, 4]:
        return current_user
    raise ForbiddenException
