from typing import AsyncGenerator

from app.core.http_client import HTTPXClient
from app.services.auth.service import AuthServiceProxy
from config import settings


async def get_auth_service_proxy() -> AsyncGenerator[AuthServiceProxy, None]:
    async with HTTPXClient(base_url=settings.AUTH_SERVICE_BASE_URL) as client:
        yield AuthServiceProxy(client)
