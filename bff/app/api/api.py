import json
from uuid import UUID

from app.core.http_client import HTTPXClient
from app.dao.database import get_async_session
from app.dao.models import Article, UserArticles
from app.dependencies.auth_dep import get_current_user
from app.dependencies.redis_dep import get_redis_client
from app.services.auth.schemas import SUserInfo
from app.services.habr_adapter.api import get_article_from_habr
from app.services.habr_adapter.schemas import SArticleParseRequest
from app.services.llm_service.api import send_article_to_queue
from config import settings
from fastapi import APIRouter, Depends, HTTPException
from loguru import logger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/api", tags=["bff"])


@router.post("/articles/process")
async def process_article(
    body: SArticleParseRequest,
    current_user: SUserInfo = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session),
    redis_client=Depends(get_redis_client),
):
    try:
        user_uuid = UUID(current_user.id)
        url_str = str(body.url)

        stmt = select(Article).where(Article.url == url_str)
        result = await session.execute(stmt)
        article_db = result.scalar_one_or_none()

        if not article_db:
            article = await get_article_from_habr(url_str)
            if not article or not article.text:
                raise HTTPException(
                    status_code=400, detail="Не удалось получить текст статьи"
                )

            task = await send_article_to_queue(article)
            article_db = Article(url=url_str, task_id=task.task_id)
            session.add(article_db)
            await session.flush()

        link_stmt = select(UserArticles).where(
            UserArticles.user_id == user_uuid,
            UserArticles.article_id == article_db.id,
        )
        link_res = await session.execute(link_stmt)
        link = link_res.scalar_one_or_none()

        if not link:
            link = UserArticles(user_id=user_uuid, article_id=article_db.id)
            session.add(link)
            await session.commit()

        cached_result = await redis_client.get(f"article:{url_str}")
        if cached_result:
            return {
                "task_id": article_db.task_id,
                "status": "done",
                "summary": json.loads(cached_result),
            }

        if article_db.parsed_content:
            await redis_client.setex(
                f"article:{url_str}", 3600, json.dumps(article_db.parsed_content)
            )
            return {
                "task_id": article_db.task_id,
                "status": "done",
                "summary": article_db.parsed_content,
            }

        return {"task_id": article_db.task_id, "status": "queued"}
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Ошибка при обработке статьи")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/articles/result/{task_id}")
async def get_article_result(
    task_id: str,
    current_user: SUserInfo = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session),
    redis_client=Depends(get_redis_client),
):
    """Получить результат обработки статьи по task_id"""

    stmt = select(Article).where(Article.task_id == task_id)
    db_res = await session.execute(stmt)
    article_db = db_res.scalar_one_or_none()

    if article_db and article_db.parsed_content:
        await redis_client.setex(
            f"article:{article_db.url}",
            3600,
            json.dumps(article_db.parsed_content),
        )
        return {"status": "done", "summary": article_db.parsed_content}

    async with HTTPXClient() as client:
        resp = await client.request(
            "GET",
            f"{settings.LLM_SERVICE_BASE_URL}/api/gemini/tasks/{task_id}",
        )

        if resp.status_code == 404:
            raise HTTPException(status_code=404, detail="Результат не найден")

        resp.raise_for_status()
        result = resp.json()

        if result.get("status") == "done" and article_db:
            article_db.parsed_content = result.get("summary")
            await session.commit()

            await redis_client.setex(
                f"article:{article_db.url}",
                3600,
                json.dumps(result.get("summary")),
            )

        return result


@router.get("/articles")
async def get_user_articles(
    current_user: SUserInfo = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session),
):
    """Получить все статьи пользователя"""
    user_uuid = UUID(current_user.id)
    stmt = (
        select(Article).join(UserArticles).where(UserArticles.user_id == user_uuid)
    )
    result = await session.execute(stmt)
    articles = result.scalars().all()
    return articles
