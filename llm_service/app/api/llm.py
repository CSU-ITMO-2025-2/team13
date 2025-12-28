import json

from app.gemini.client import GeminiService
from app.gemini.shemas import SArticleTextRequest
from app.services.openai_service import OpenAIService
from app.sgr.habr import SUMMARY_SYS_PROMPT, SHabrArticleSummary
from config import settings
from fastapi import APIRouter, HTTPException
from loguru import logger
from redis import asyncio as aioredis

router = APIRouter(prefix="/api/llm", tags=["llm"])


redis = aioredis.from_url(settings.REDIS_URL)


@router.post("/summary", response_model=SHabrArticleSummary)
async def summarize_article(payload: SArticleTextRequest):
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

    try:
        if settings.LLM_PROVIDER == "openai":
            service = OpenAIService()
            summary = await service.generate_summary(prompt, schema)
            if not summary:
                raise HTTPException(
                    status_code=502, detail="OpenAI provider returned empty result"
                )
            return summary

        else:
            # Fallback to Google Gemini
            gemini = GeminiService(model=payload.model)
            try:
                resp = await gemini.generate_text(
                    prompt=prompt, response_schema=schema
                )

                if resp is None:
                    raise HTTPException(
                        status_code=502, detail="Gemini service unavailable"
                    )

                data = resp.json()
                candidates = data.get("candidates") or []
                if not candidates:
                    raise ValueError("No candidates returned")

                parts = candidates[0].get("content", {}).get("parts", [])
                if not parts:
                    raise ValueError("No parts in content")

                raw_json = parts[0]["text"]
                structured = json.loads(raw_json)
                return SHabrArticleSummary.model_validate(structured)
            finally:
                await gemini.close()

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in API summary: {e}")
        raise HTTPException(status_code=502, detail=f"LLM processing failed: {e}")


@router.get("/tasks/{task_id}")
async def get_task_result(task_id: str):
    """Вернуть сохранённый результат обработки статьи по task_id."""
    try:
        result_raw = await redis.get(task_id)
    except Exception as e:
        logger.error(f"Redis error: {e}")
        raise HTTPException(status_code=500, detail=f"Redis error: {e}")

    if not result_raw:
        raise HTTPException(status_code=404, detail="Результат не найден")

    return json.loads(result_raw)
