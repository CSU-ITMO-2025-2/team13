import json

from app.gemini.client import GeminiService
from app.gemini.shemas import SArticleTextRequest
from app.sgr.habr import SUMMARY_SYS_PROMPT, SHabrArticleSummary
from config import settings
from fastapi import APIRouter, Depends, HTTPException
from loguru import logger
from redis import asyncio as aioredis

router = APIRouter(prefix="/api/gemini", tags=["gemini"])

# Redis client
redis_url = f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}"
logger.info(f"Connecting to Redis at {redis_url}")
redis = aioredis.from_url(redis_url)


async def get_gemini_service():
    service = GeminiService()
    try:
        yield service
    finally:
        await service.close()


@router.post("/summary", response_model=SHabrArticleSummary)
async def summarize_article(
    payload: SArticleTextRequest,
    service: GeminiService = Depends(get_gemini_service),
):
    if not payload.text or not payload.text.strip():
        raise HTTPException(
            status_code=400, detail="Поле 'text' не должно быть пустым"
        )

    prompt = (
        f"{SUMMARY_SYS_PROMPT}\n\n"
        "Проанализируй следующую статью и верни ТОЛЬКО JSON, строго соответствующий схеме.\n"
        "Текст статьи ниже между тройными кавычками.\n\n"
        f'"""\n{payload.text}\n"""'
    )

    schema = SHabrArticleSummary.model_json_schema()

    model = payload.model
    if model == "string":
        model = None

    resp = await service.generate_text(
        prompt=prompt, model=model, response_schema=schema
    )

    if resp is None:
        raise HTTPException(
            status_code=502, detail="LLM-сервис недоступен или вернул ошибку"
        )

    # Ожидаем стандартный ответ Gemini: candidates -> content.parts[0].text (JSON-строка)
    try:
        data = resp.json()
        candidates = data.get("candidates") or []
        if not candidates:
            raise ValueError(f"Пустой список candidates: {data}")

        parts = candidates[0].get("content", {}).get("parts", [])
        if not parts or "text" not in parts[0]:
            raise ValueError(f"В ответе отсутствует text c JSON: {data}")

        raw_json = parts[0]["text"]
        structured = json.loads(raw_json)
        summary = SHabrArticleSummary.model_validate(structured)
        return summary
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=502, detail=f"Не удалось распарсить ответ LLM: {e}"
        )


@router.get("/tasks/{task_id}")
async def get_task_result(task_id: str):
    """Вернуть сохранённый результат обработки статьи по task_id."""

    logger.info(f"Requesting task_id: {task_id} from Redis")
    try:
        result_raw = await redis.get(task_id)
        logger.info(f"Redis response for {task_id}: {result_raw}")
    except Exception as e:
        logger.error(f"Redis error: {e}")
        raise HTTPException(status_code=500, detail=f"Redis error: {e}")

    if not result_raw:
        raise HTTPException(status_code=404, detail="Результат не найден")

    return json.loads(result_raw)
