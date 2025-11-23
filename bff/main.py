from contextlib import asynccontextmanager

from app.api import router
from app.core.logging_config import setup_logging
from app.dao.database import Base, engine
from fastapi import FastAPI

setup_logging()


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    await engine.dispose()


app = FastAPI(title="BFF", lifespan=lifespan)

app.include_router(router)


@app.get("/health")
async def health():
    return {"status": "ok"}
