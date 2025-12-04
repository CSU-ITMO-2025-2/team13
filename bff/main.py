import asyncio
from contextlib import asynccontextmanager

from app.api import router
from app.core.logging_config import setup_logging
from app.dao.database import Base, engine
from fastapi import FastAPI
from loguru import logger

setup_logging()


async def init_db(max_retries: int = 3, retry_delay: int = 5):
    for attempt in range(1, max_retries + 1):
        try:
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            logger.info("Подключение к базе данных успешно установлено")
            return True
        except Exception as e:
            logger.warning(
                f"Попытка подключения к базе данных {attempt}/{max_retries} не удалась: {e}"
            )
            if attempt < max_retries:
                logger.info(f"Повторная попытка через {retry_delay} секунд...")
                await asyncio.sleep(retry_delay)
            else:
                logger.error(
                    "Не удалось подключиться к базе данных после всех попыток. "
                    "Сервис продолжит работу без подключения к базе данных."
                )
                return False


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield
    try:
        await engine.dispose()
    except Exception as e:
        logger.warning(f"Error disposing database engine: {e}")


app = FastAPI(title="BFF", lifespan=lifespan)

app.include_router(router)


@app.get("/health")
async def health():
    return {"status": "ok"}
