from datetime import datetime
from typing import Optional
from uuid import UUID

from app.dao.database import Base
from sqlalchemy import JSON, TIMESTAMP, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column


class Article(Base):
    __tablename__ = "articles"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP,
        server_default=func.now(),
        onupdate=func.now(),
    )

    url: Mapped[str] = mapped_column(
        String, unique=True, index=True, nullable=False
    )
    task_id: Mapped[Optional[str]] = mapped_column(
        String, index=True, nullable=True
    )
    parsed_content: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)


class UserArticles(Base):
    __tablename__ = "user_articles"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP,
        server_default=func.now(),
        onupdate=func.now(),
    )

    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), nullable=False, index=True
    )
    article_id: Mapped[int] = mapped_column(
        ForeignKey("articles.id"), nullable=False, index=True
    )
