from app.article_parser.api import router as habr_router
from app.core.logging_config import setup_logging
from fastapi import FastAPI

setup_logging()
app = FastAPI(title="Habr Adapter")

app.include_router(habr_router)


@app.get("/health")
async def health():
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=7000)