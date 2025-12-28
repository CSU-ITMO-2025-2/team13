from app.core.rate_limiter import RateLimiter
from config import settings
from fastapi import Request
from fastapi.responses import JSONResponse
from redis import asyncio as aioredis
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp


class LLMRateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self.redis = aioredis.from_url(settings.REDIS_URL)
        self.limiter = RateLimiter(self.redis)

    async def dispatch(self, request: Request, call_next):
        if (
            request.url.path.startswith("/api/llm/summary")
            and request.method == "POST"
        ):
            allowed = await self.limiter.check_and_acquire(
                key_prefix="api_llm_limit",
                limit=settings.LLM_RATE_LIMIT,
                window_seconds=60,
            )

            if not allowed:
                return JSONResponse(
                    status_code=429,
                    content={
                        "detail": "Rate limit exceeded. Please try again later."
                    },
                )

        response = await call_next(request)
        return response
