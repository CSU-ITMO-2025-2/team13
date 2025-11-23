import asyncio
import os
import time
from contextlib import asynccontextmanager

from fastapi import APIRouter, FastAPI
from fastapi.openapi.utils import get_openapi
from loguru import logger

from app.api.v1 import v1_router
from app.config import settings
from app.core.init_db import init_database
from app.core.logging import setup_logging
from app.core.middleware import setup_middleware

# Настройка логирования
setup_logging()


def ensure_dirs():
    dirs = [
        settings.LOGS_DIR,
        settings.DATA_DIR,
    ]
    for d in dirs:
        logger.info(f"Проверка и создание директории: {d}")
        os.makedirs(d, exist_ok=True)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Управление жизненным циклом приложения"""
    try:
        logger.info("Инициализация приложения...")
        ensure_dirs()

        # Инициализация БД
        logger.info(f"Используемая база данных: {settings.POSTGRES_DB_URL}")
        database_init_data_path = os.path.join(
            settings.DATA_DIR, "initial_data.yaml"
        )
        await init_database(
            data_file_path=database_init_data_path, create_tables=True
        )

        logger.info("Приложение успешно запущено")
        yield

    except Exception as e:
        logger.error(f"Ошибка при инициализации: {e}")
        raise
    finally:
        try:
            logger.info("Завершение работы приложения...")

            # TODO: Очистка ресурсов, закрытие соединений с БД

            # Время на завершение фоновых задач
            await asyncio.sleep(0.1)

            logger.info("Работа корректно завершена")
        except Exception as e:
            logger.error(f"Ошибка при завершении: {e}")


def create_app() -> FastAPI:
    """
    Создание и конфигурация FastAPI приложения
    """
    app = FastAPI(
        title="Auth Service",
        description=("My FastAPI Template"),
        version="1.0.0",
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
        swagger_ui_parameters={
            "persistAuthorization": True,  # Сохранять токен между перезагрузками
        },
    )

    def custom_openapi():
        if app.openapi_schema:
            return app.openapi_schema

        openapi_schema = get_openapi(
            title=app.title,
            version=app.version,
            description=app.description,
            routes=app.routes,
        )

        # Схема безопасности Bearer JWT
        openapi_schema["components"]["securitySchemes"] = {
            "BearerAuth": {
                "type": "http",
                "scheme": "bearer",
                "bearerFormat": "JWT",
                "description": "Введите JWT токен (без префикса 'Bearer')",
            }
        }

        app.openapi_schema = openapi_schema
        return app.openapi_schema

    app.openapi = custom_openapi

    # Настройка middleware
    setup_middleware(app)

    # Регистрация роутеров
    register_routers(app)

    return app


def register_routers(app: FastAPI) -> None:
    """Регистрация роутеров приложения"""
    root_router = APIRouter(tags=["root"])

    @root_router.get("/")
    def home_page():
        return {
            "message": "My FastAPI Template",
            "status": "running",
            "docs": "/docs",
            "redoc": "/redoc",
        }

    @root_router.get("/health")
    def health_check():
        return {"status": "healthy", "timestamp": time.time()}

    app.include_router(root_router)
    app.include_router(v1_router)


app = create_app()
