from app.api.llm import router as llm_router
from app.core.logging_config import setup_logging
from app.core.middleware import LLMRateLimitMiddleware
from fastapi import FastAPI

setup_logging()
app = FastAPI(title="LLM Service")

# Middleware
app.add_middleware(LLMRateLimitMiddleware)

# Роуты
app.include_router(llm_router)


@app.get("/health")
async def health():
    return {"status": "ok"}
