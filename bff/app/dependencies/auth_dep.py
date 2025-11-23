import json
from typing import Any

import httpx
from app.dependencies.redis_dep import get_redis_client
from app.dependencies.services_dep import get_auth_service_proxy
from app.services.auth.schemas import SUserInfo
from app.services.auth.service import AuthServiceProxy
from fastapi import Depends, HTTPException, Request, status


async def get_current_user(
    request: Request,
    redis_client: Any = Depends(get_redis_client),
    auth_service: AuthServiceProxy = Depends(get_auth_service_proxy),
) -> SUserInfo:
    """
    Извлекает access-токен из cookie, проверяет кэш Redis и при отсутствии —
    валидирует пользователя через auth-сервис. Успешный результат кэшируется.
    """
    token = request.cookies.get("user_access_token")
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Не авторизован",
        )

    cache_key = f"token:{token}"

    try:
        cached = await redis_client.get(cache_key)
        if cached:
            data = json.loads(cached)
            return SUserInfo(**data)

        # Валидация через auth-сервис
        user_info = await auth_service.get_me(token)

        # Кэшируем на 5 минут
        await redis_client.setex(
            cache_key, 300, json.dumps(user_info.model_dump())
        )
        return user_info
    except httpx.RequestError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Сервис авторизации недоступен",
        )
    except httpx.HTTPStatusError:
        # Невалидный токен или ошибка ответа от auth-сервиса
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Токен невалиден",
        )
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Внутренняя ошибка при аутентификации",
        )
