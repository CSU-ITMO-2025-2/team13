from fastapi import APIRouter, Depends, Response
from loguru import logger

from app.auth.models import User
from app.auth.schemas import SUserAuth, SUserInfo, SUserRegister
from app.auth.service import AuthService
from app.auth.token_service import TokenService
from app.auth.utils import create_tokens, set_tokens
from app.dependencies.auth_dep import (
    check_refresh_token,
    get_access_token,
    get_current_user,
    get_refresh_token,
)
from app.dependencies.services_dep import (
    get_auth_service_with_commit,
    get_auth_service_without_commit,
    get_token_service,
)

router = APIRouter()


@router.post("/register/", status_code=201)
async def register_user(
    user_data: SUserRegister,
    auth_service: AuthService = Depends(get_auth_service_with_commit),
) -> dict:
    """Регистрация нового пользователя"""
    try:
        await auth_service.register_user(user_data)
        return {"message": "Вы успешно зарегистрированы!"}
    except Exception as e:
        logger.error(f"Ошибка при регистрации: {e}")
        raise


@router.post("/login/")
async def login_user(
    response: Response,
    user_data: SUserAuth,
    auth_service: AuthService = Depends(get_auth_service_without_commit),
) -> dict:
    """Авторизация пользователя"""
    try:
        user = await auth_service.login_user(user_data)

        # Создаем токены
        tokens = create_tokens(data={"sub": str(user.id)})

        # Устанавливаем токены в cookies
        set_tokens(response, user.id)

        return {
            "ok": True,
            "message": "Вы успешно авторизованы!",
            # "access_token": tokens["access_token"],
            # "token_type": "bearer",
        }
    except Exception as e:
        logger.error(f"Ошибка при авторизации: {e}")
        raise


@router.post("/logout/")
async def logout(
    response: Response,
    user: User = Depends(get_current_user),
    token_service: TokenService = Depends(get_token_service),
    access_token: str = Depends(get_access_token),
    refresh_token: str = Depends(get_refresh_token),
):
    """
    Выход пользователя из системы
    """
    try:
        # Инвалидируем access token
        await token_service.invalidate_token(access_token, "access")

        # Инвалидируем refresh token
        await token_service.invalidate_token(refresh_token, "refresh")

        # Удаляем cookies
        response.delete_cookie("user_access_token")
        response.delete_cookie("user_refresh_token")

        return {"message": "Вы успешно вышли из системы"}

    except Exception as e:
        logger.error(f"Ошибка при выходе из системы: {e}")
        # Даже если Redis недоступен, удаляем cookies
        response.delete_cookie("user_access_token")
        response.delete_cookie("user_refresh_token")
        return {"message": "Вы вышли из системы"}


@router.post("/logout-all/")
async def logout_all_devices(
    response: Response,
    user: User = Depends(get_current_user),
    token_service: TokenService = Depends(get_token_service),
):
    """
    Выход из всех устройств, инвалидирует ВСЕ токены пользователя
    """
    try:
        # Инвалидируем все токены пользователя
        await token_service.invalidate_all_user_tokens(user.id)

        # Удаляем cookies текущей сессии
        response.delete_cookie("user_access_token")
        response.delete_cookie("user_refresh_token")

        logger.info(f"User {user.id} logged out from all devices")
        return {
            "message": "Вы вышли из системы на всех устройствах",
            "invalidated_tokens": "all",
        }

    except Exception as e:
        logger.error(f"Logout all error: {e}")
        # Даже если Redis недоступен, удаляем cookies
        response.delete_cookie("user_access_token")
        response.delete_cookie("user_refresh_token")
        return {"message": "Вы вышли из системы"}


@router.get("/me/", response_model=SUserInfo)
async def get_me(user_data: User = Depends(get_current_user)):
    """
    Возвращает информацию о текущем пользователе
    """
    return SUserInfo.model_validate(user_data)


@router.post("/refresh")
async def process_refresh_token(
    response: Response, user: User = Depends(check_refresh_token)
):
    """Обновляет JWT-токены с использованием refresh-токена"""
    set_tokens(response, user.id)
    return {"message": "Токены успешно обновлены"}


@router.get("/all_users/", response_model=list[SUserInfo])
async def get_all_users(
    auth_service: AuthService = Depends(get_auth_service_without_commit),
):
    """Возвращает информацию о всех пользователях"""
    users = await auth_service.get_all_users()
    return [SUserInfo.model_validate(user) for user in users]
