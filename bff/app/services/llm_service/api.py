import json
import uuid

from app.services.llm_service.schemas import (
    SArticleForLLM,
    SArticleTaskResponse,
)
from config import settings
from loguru import logger
from publisher import Publisher


async def send_article_to_queue(article) -> SArticleTaskResponse:
    """Публикация статьи в очередь RabbitMQ для последующей обработки LLM-сервисом"""

    task_id = str(uuid.uuid4())
    payload = SArticleForLLM(title=article.title, text=article.text)
    body = json.dumps(
        {"task_id": task_id, **payload.model_dump()}, ensure_ascii=False
    )

    publisher = Publisher(settings.RABBITMQ_URL)
    async with publisher:
        await publisher.publish(settings.ARTICLE_QUEUE_NAME, body)
        logger.info(
            "Статья отправлена в очередь '{}' (task_id={}): {}",
            settings.ARTICLE_QUEUE_NAME,
            task_id,
            article.title,
        )

    return SArticleTaskResponse(task_id=task_id, status="queued")
