from app.dependencies.auth_dep import get_current_user
from app.dependencies.services_dep import get_auth_service_proxy
from app.services.auth.schemas import SUserAuth, SUserInfo, SUserRegister
from app.services.auth.service import AuthServiceProxy
from fastapi import APIRouter, Cookie, Depends, HTTPException, Response
from loguru import logger

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/register/", status_code=201)
async def register_user(
    user_data: SUserRegister,
    auth_service: AuthServiceProxy = Depends(get_auth_service_proxy),
) -> dict:
    """Регистрация нового пользователя"""
    try:
        result = await auth_service.register_user(user_data)
        logger.debug("User registered successfully")
        return result
    except Exception as e:
        logger.error(f"Registration failed with error: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/login/")
async def login_user(
    response: Response,
    user_data: SUserAuth,
    auth_service: AuthServiceProxy = Depends(get_auth_service_proxy),
) -> dict:
    """Авторизация пользователя"""
    try:
        # Получаем полный response от auth_service с cookies
        auth_response = await auth_service.login_user(user_data)
        logger.debug("Login successful")

        # Пробрасываем cookies от auth_service к клиенту
        for cookie_name in ["user_access_token", "user_refresh_token"]:
            if cookie_name in auth_response.cookies:
                cookie_value = auth_response.cookies[cookie_name]
                response.set_cookie(
                    key=cookie_name,
                    value=cookie_value,
                    httponly=True,
                    secure=True,
                    samesite="lax",
                )

        return auth_response.json()
    except Exception as e:
        logger.error(f"Login failed with error: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/logout/")
async def logout(response: Response):
    """Выход пользователя из системы"""
    response.delete_cookie("user_access_token")
    response.delete_cookie("user_refresh_token")
    return {"message": "Пользователь успешно вышел из системы"}


@router.get("/me/", response_model=SUserInfo)
async def get_me(current_user: SUserInfo = Depends(get_current_user)):
    """Возвращает информацию о текущем пользователе через зависимость"""
    return current_user


@router.post("/refresh")
async def process_refresh_token(
    response: Response,
    user_refresh_token: str = Cookie(None),
    auth_service: AuthServiceProxy = Depends(get_auth_service_proxy),
):
    """Обновляет JWT-токены с использованием refresh-токена"""
    if not user_refresh_token:
        raise HTTPException(status_code=401, detail="Refresh токен не найден")

    try:
        # Получаем полный response от auth_service с новыми cookies
        auth_response = await auth_service.refresh_token(user_refresh_token)

        # Пробрасываем обновленные cookies к клиенту
        for cookie_name in ["user_access_token", "user_refresh_token"]:
            if cookie_name in auth_response.cookies:
                cookie_value = auth_response.cookies[cookie_name]
                response.set_cookie(
                    key=cookie_name,
                    value=cookie_value,
                    httponly=True,
                    secure=True,
                    samesite="lax",
                )

        return auth_response.json()
    except Exception as e:
        logger.error(f"Token refresh failed with error: {e}")
        raise HTTPException(status_code=401, detail="Не удалось обновить токен")
