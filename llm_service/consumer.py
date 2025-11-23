import asyncio
import json

from aio_pika import connect_robust
from aio_pika.abc import AbstractIncomingMessage
from app.gemini.client import GeminiService
from app.sgr.habr import SUMMARY_SYS_PROMPT, SHabrArticleSummary
from config import settings
from loguru import logger
from redis import asyncio as aioredis

# Redis client
redis = aioredis.from_url(f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}")


async def process_message(message: AbstractIncomingMessage):
    try:
        body = message.body.decode()
        data = json.loads(body)
        task_id = data.get("task_id")
        title = data.get("title", "")
        text = data.get("text", "")

        await redis.set(
            task_id,
            json.dumps({"status": "in_progress"}),
            ex=3600,
        )

        if not task_id:
            logger.warning("В сообщении отсутствует task_id, пропускаем")
            await message.ack()
            return

        if not text:
            logger.warning("Пустой текст в сообщении, помечаем задачу как failed")
            await redis.set(
                task_id,
                json.dumps({"status": "failed", "reason": "empty_text"}),
                ex=3600,
            )
            await message.ack()
            return

        prompt = (
            f"{SUMMARY_SYS_PROMPT}\n\n"
            "Проанализируй следующую статью и верни ТОЛЬКО JSON, строго соответствующий схеме.\n"
            "Текст статьи ниже между тройными кавычками.\n\n"
            f"Заголовок: {title}\n\n"
            f'"""\n{text}\n"""'
        )

        schema = SHabrArticleSummary.model_json_schema()

        service = GeminiService()
        try:
            resp = await service.generate_text(
                prompt=prompt, response_schema=schema
            )
        finally:
            await service.close()

        if resp is None:
            logger.error("GeminiService вернул None")
            await redis.set(
                task_id,
                json.dumps({"status": "failed", "reason": "llm_none"}),
                ex=3600,
            )
            await message.ack()
            return

        try:
            resp_data = resp.json()
            candidates = resp_data.get("candidates") or []
            if not candidates:
                raise ValueError(f"Пустой список candidates: {resp_data}")

            parts = candidates[0].get("content", {}).get("parts", [])
            raw_json = parts[0]["text"]
            structured = json.loads(raw_json)
            summary = SHabrArticleSummary.model_validate(structured)

            await redis.set(
                task_id,
                json.dumps({"status": "done", "summary": summary.model_dump()}),
                ex=3600,
            )
            logger.info(
                "Обработана статья (task_id={}): {}", task_id, summary.title
            )
        except Exception as e:
            logger.error("Ошибка парсинга ответа LLM: {}", e)
            await redis.set(
                task_id,
                json.dumps({"status": "failed", "reason": f"parse_error: {e}"}),
                ex=3600,
            )

        await message.ack()
    except Exception as e:
        logger.error("Ошибка при обработке сообщения: {}", e)
        await message.nack(requeue=False)


async def consume():
    connection = None
    while True:
        try:
            connection = await connect_robust(settings.RABBITMQ_URL)
            logger.info("Успешное подключение к RabbitMQ")
            break
        except Exception as e:
            logger.warning(
                f"Не удалось подключиться к RabbitMQ, повторная попытка через 5 секунд: {e}"
            )
            await asyncio.sleep(5)

    channel = await connection.channel()
    queue = await channel.declare_queue(
        settings.ARTICLE_QUEUE_NAME,
        durable=True,
    )

    async with queue.iterator() as queue_iter:
        async for message in queue_iter:
            await process_message(message)


if __name__ == "__main__":
    asyncio.run(consume())
