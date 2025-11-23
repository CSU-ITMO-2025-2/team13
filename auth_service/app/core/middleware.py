import time
from typing import Callable

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from loguru import logger
from starlette.middleware.sessions import SessionMiddleware

from app.config import settings
from app.exceptions import RateLimitExceeded


def setup_middleware(app: FastAPI) -> None:
    # custom middleware
    add_security_headers_middleware(app)
    add_timing_middleware(app)
    add_logging_middleware(app)
    add_rate_limiting_middleware(app)

    # builtin middleware
    add_builtin_middleware(app)


def add_security_headers_middleware(app: FastAPI) -> None:
    """Заголовки безопасности"""

    @app.middleware("http")
    async def security_headers(request: Request, call_next: Callable):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"

        # Строгие заголовки только в продакшене
        if not settings.DEV_MODE:
            response.headers["Strict-Transport-Security"] = (
                "max-age=31536000; includeSubDomains"
            )
            response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        else:
            # В разработке более мягкие настройки
            response.headers["Referrer-Policy"] = "no-referrer-when-downgrade"

        return response


def add_timing_middleware(app: FastAPI) -> None:
    """Измерение времени выполнения запросов"""

    @app.middleware("http")
    async def add_process_time_header(request: Request, call_next: Callable):
        start_time = time.time()
        response = await call_next(request)
        process_time = time.time() - start_time
        response.headers["X-Process-Time"] = f"{process_time:.4f}"
        return response


def add_logging_middleware(app: FastAPI) -> None:
    """Логирование запросов"""

    @app.middleware("http")
    async def log_requests(request: Request, call_next: Callable):
        start_time = time.time()

        client_ip = request.client.host if request.client else "unknown"
        logger.info(f"{request.method} {request.url.path} from {client_ip}")

        response = await call_next(request)

        process_time = time.time() - start_time
        logger.info(
            f"{request.method} {request.url.path} "
            f"Status: {response.status_code} Time: {process_time:.4f}s"
        )

        return response


def add_rate_limiting_middleware(
    app: FastAPI, max_requests: int = 100, window_seconds: int = 60
) -> None:
    """Базовая защита от спама"""
    # TODO: Сделать реализацию на Redis

    request_counts = {}

    @app.middleware("http")
    async def rate_limit_middleware(request: Request, call_next: Callable):
        client_ip = request.client.host if request.client else "unknown"
        current_time = time.time()

        if client_ip in request_counts:
            request_counts[client_ip] = [
                t
                for t in request_counts[client_ip]
                if t > current_time - window_seconds
            ]
        else:
            request_counts[client_ip] = []

        if len(request_counts[client_ip]) >= max_requests:
            raise RateLimitExceeded

        request_counts[client_ip].append(current_time)

        response = await call_next(request)
        return response


def add_builtin_middleware(app: FastAPI) -> None:
    """Добавляет встроенные middleware FastAPI."""

    # Trusted Host
    allowed_hosts = ["localhost", "127.0.0.1", "test"]
    if not settings.DEV_MODE:
        # В продакшене добавляем только конкретные домены
        allowed_hosts.extend(["*.your-production-domain.com"])
    else:
        # В разработке разрешаем все
        allowed_hosts.append("*")

    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=allowed_hosts,
    )

    # GZIP compression
    app.add_middleware(GZipMiddleware, minimum_size=1000)

    # Session middleware
    app.add_middleware(
        SessionMiddleware,
        secret_key=settings.SECRET_KEY,
        max_age=3600,  # 1 час
        https_only=not settings.DEV_MODE,  # В продакшене только HTTPS
        same_site="lax",
    )

    # CORS
    cors_origins = []
    if settings.DEV_MODE:
        # В режиме разработки разрешаем localhost
        cors_origins = [
            "http://localhost:3000",
            "http://127.0.0.1:3000",
            "http://localhost:8080",  # Для альтернативных портов
            "http://127.0.0.1:8080",
        ]
    else:
        # В продакшене указываем конкретные домены
        cors_origins = [
            "https://your-frontend-domain.com",
            "https://www.your-frontend-domain.com",
        ]

    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["*"],
        expose_headers=["X-Process-Time"],
    )
