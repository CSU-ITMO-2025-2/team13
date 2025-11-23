import httpx
from app.core.http_client import HTTPXClient
from app.services.auth.schemas import SUserAuth, SUserInfo, SUserRegister
from loguru import logger


class AuthServiceProxy:
    def __init__(self, client: HTTPXClient):
        self.client = client

    async def register_user(self, user_data: SUserRegister) -> dict:
        """Регистрация нового пользователя"""
        logger.debug(f"Proxying registration request for: {user_data.email}")
        response = await self.client.request(
            "POST",
            "/api/v1/auth/register/",
            json=user_data.model_dump(),
        )
        response.raise_for_status()
        return response.json()

    async def login_user(self, user_data: SUserAuth) -> httpx.Response:
        """Авторизация пользователя - возвращает полный response с cookies"""
        logger.debug(f"Proxying login request for: {user_data.phone_number}")
        response = await self.client.request(
            "POST",
            "/api/v1/auth/login/",
            json=user_data.model_dump(),
        )
        response.raise_for_status()
        return response

    async def logout_user(self) -> dict:
        """Выход пользователя"""
        logger.debug("Proxying logout request")
        response = await self.client.request("POST", "/api/v1/auth/logout/")
        response.raise_for_status()
        return response.json()

    async def get_me(self, access_token: str) -> SUserInfo:
        """Получение информации о текущем пользователе"""
        logger.debug("Proxying get_me request")
        response = await self.client.request(
            "GET",
            "/api/v1/auth/me/",
            cookies={"user_access_token": access_token},
        )
        response.raise_for_status()
        return SUserInfo(**response.json())

    async def refresh_token(self, refresh_token: str) -> httpx.Response:
        """Обновление токенов - возвращает полный response с cookies"""
        logger.debug("Proxying refresh token request")
        response = await self.client.request(
            "POST",
            "/api/v1/auth/refresh",
            cookies={"user_refresh_token": refresh_token},
        )
        response.raise_for_status()
        return response
