from typing import Optional

from app.core.http_client import HTTPXClient
from app.services.habr_adapter.schemas import SArticleParsed, SArticleParseRequest
from config import settings
from loguru import logger


async def get_article_from_habr(url: str) -> Optional[SArticleParsed]:
    """Делает HTTP-запрос к habr_adapter для парсинга статьи."""

    async with HTTPXClient() as client:
        try:
            payload = SArticleParseRequest(url=url).model_dump(mode="json")
            resp = await client.request(
                "POST",
                f"{settings.HABR_ADAPTER_BASE_URL}/api/habr/parse",
                json=payload,
            )
            resp.raise_for_status()
            data = resp.json()
            return SArticleParsed(**data)
        except Exception as e:
            logger.error(f"Ошибка при запросе к habr_adapter: {e}")
            return None
