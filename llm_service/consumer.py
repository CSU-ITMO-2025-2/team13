import asyncio
import json
import socket
import uuid

from aio_pika import connect_robust
from aio_pika.abc import AbstractIncomingMessage
from app.core.rate_limiter import RateLimiter
from app.gemini.client import GeminiService
from app.services.openai_service import OpenAIService
from app.sgr.habr import SUMMARY_SYS_PROMPT, SHabrArticleSummary
from config import settings
from loguru import logger
from redis import asyncio as aioredis

redis = aioredis.from_url(settings.REDIS_URL)
rate_limiter = RateLimiter(redis)


WORKER_ID = f"{socket.gethostname()}-{str(uuid.uuid4())[:4]}"
logger.info(f"Worker started with ID: {WORKER_ID}")


async def process_message(message: AbstractIncomingMessage):
    try:
        is_hourly_allowed = await rate_limiter.check_and_acquire(
            key_prefix="global_llm_budget",
            limit=settings.LLM_HOURLY_LIMIT,
            window_seconds=3600,
        )

        if not is_hourly_allowed:
            logger.warning(
                f"[{WORKER_ID}] Global HOURLY limit exceeded ({settings.LLM_HOURLY_LIMIT}/hour). Re-queueing with long delay."
            )
            await message.nack(requeue=True)
            await asyncio.sleep(30)
            return

        is_minute_allowed = await rate_limiter.check_and_acquire(
            key_prefix=f"worker_llm_throttle:{WORKER_ID}",
            limit=settings.LLM_RATE_LIMIT,
            window_seconds=60,
        )

        if not is_minute_allowed:
            logger.warning(
                f"[{WORKER_ID}] Worker MINUTE limit exceeded ({settings.LLM_RATE_LIMIT}/min). Re-queueing."
            )
            await message.nack(requeue=True)
            await asyncio.sleep(5)
            return

        body = message.body.decode()
        data = json.loads(body)
        task_id = data.get("task_id")
        title = data.get("title", "")
        text = data.get("text", "")

        if not task_id:
            logger.warning(f"[{WORKER_ID}] No task_id in message, acking.")
            await message.ack()
            return

        logger.info(f"[{WORKER_ID}] Processing task {task_id}")

        await redis.set(
            task_id,
            json.dumps({"status": "in_progress"}),
            ex=3600,
        )

        if not text:
            logger.warning(f"[{WORKER_ID}] Empty text, failing task.")
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

        schema_dict = SHabrArticleSummary.model_json_schema()

        summary = None
        error_msg = None

        try:
            if settings.LLM_PROVIDER == "openai":
                logger.info(
                    f"[{WORKER_ID}] Processing via OpenAI-like provider..."
                )
                service = OpenAIService()
                summary = await service.generate_summary(prompt, schema_dict)
            else:
                logger.info(f"[{WORKER_ID}] Processing via Google Gemini...")
                gemini = GeminiService()
                try:
                    resp = await gemini.generate_text(
                        prompt=prompt, response_schema=schema_dict
                    )
                    if resp:
                        resp_data = resp.json()
                        candidates = resp_data.get("candidates", [])
                        if candidates:
                            parts = (
                                candidates[0].get("content", {}).get("parts", [])
                            )
                            if parts:
                                raw_json = parts[0]["text"]
                                structured = json.loads(raw_json)
                                summary = SHabrArticleSummary.model_validate(
                                    structured
                                )
                finally:
                    await gemini.close()

        except Exception as e:
            error_msg = str(e)
            logger.error(f"[{WORKER_ID}] LLM processing error: {e}")

        if summary:
            await redis.set(
                task_id,
                json.dumps({"status": "done", "summary": summary.model_dump()}),
                ex=3600,
            )
            logger.success(
                f"[{WORKER_ID}] Task {task_id} done. Title: {summary.title}"
            )
        else:
            reason = error_msg or "Unknown LLM error or empty response"
            await redis.set(
                task_id,
                json.dumps({"status": "failed", "reason": reason}),
                ex=3600,
            )
            logger.error(f"[{WORKER_ID}] Task {task_id} failed. Reason: {reason}")

        await message.ack()

    except Exception as e:
        logger.error(f"[{WORKER_ID}] Consumer fatal error: {e}")
        await message.nack(requeue=False)


async def consume():
    connection = None
    while True:
        try:
            connection = await connect_robust(settings.RABBITMQ_URL)
            logger.info(f"[{WORKER_ID}] Connected to RabbitMQ")
            break
        except Exception as e:
            logger.warning(
                f"[{WORKER_ID}] RabbitMQ connect failed: {e}. Retrying in 5s..."
            )
            await asyncio.sleep(5)

    channel = await connection.channel()
    await channel.set_qos(prefetch_count=1)

    queue = await channel.declare_queue(
        settings.ARTICLE_QUEUE_NAME,
        durable=True,
    )

    logger.info(f"[{WORKER_ID}] Consumer started. Waiting for messages...")
    async with queue.iterator() as queue_iter:
        async for message in queue_iter:
            await process_message(message)


if __name__ == "__main__":
    asyncio.run(consume())
