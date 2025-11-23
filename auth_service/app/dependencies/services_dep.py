from typing import AsyncGenerator

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.service import AuthService
from app.auth.token_service import TokenService
from app.dependencies.dao_dep import (
    get_session_with_commit,
    get_session_without_commit,
)
from app.dependencies.redis_dep import get_redis_client


async def get_auth_service_with_commit(
    session: AsyncSession = Depends(get_session_with_commit),
):
    return AuthService(session)


async def get_auth_service_without_commit(
    session: AsyncSession = Depends(get_session_without_commit),
):
    return AuthService(session)


async def get_token_service(
    redis_client=Depends(get_redis_client),
) -> AsyncGenerator[TokenService, None]:
    yield TokenService(redis_client)
