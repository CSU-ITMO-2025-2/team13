from app.core.logging_config import setup_logging
from app.gemini.api import router as gemini_router
from fastapi import FastAPI

setup_logging()
app = FastAPI(title="LLM Service")

# Роуты
app.include_router(gemini_router)


@app.get("/health")
async def health():
    return {"status": "ok"}
