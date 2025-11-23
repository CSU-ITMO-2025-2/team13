from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field

SUMMARY_SYS_PROMPT = """
Ты - технический редактор Habr.com с глубоким пониманием IT.
Твоя задача - проанализировать предоставленный текст статьи и извлечь структурированную информацию.

Следуй этим правилам Reasoning (рассуждения):
1. Сначала определи тип статьи (туториал, мнение, кейс).
2. Выдели конкретные технологии. Не пиши "базы данных", пиши "PostgreSQL".
3. Если статья содержит код, не копируй его, а объясни его логику в поле code_analysis.
4. В поле 'pros' и 'cons' будь критичен. Если автор "изобретает велосипед", укажи это в cons.
5. TL;DR должен быть понятен CTO, у которого есть 30 секунд.

Игнорируй рекламные вступления и призывы подписаться на Telegram-каналы.
"""


class EDifficultyLevel(str, Enum):
    EASY = "Для начинающих"
    MEDIUM = "Средний уровень"
    HARD = "Hardcore / Deep Tech"


class EArticleType(str, Enum):
    TUTORIAL = "Туториал / How-to"
    CASE_STUDY = "Кейс / История успеха (или провала)"
    OPINION = "Мнение / Аналитика"
    NEWS = "Новости"
    TRANSLATION = "Перевод"


class STechStack(BaseModel):
    languages: List[str] = Field(
        ...,
        description="Языки программирования, упомянутые в контексте использования (Python, Go, JS...)",
    )
    tools: List[str] = Field(
        ...,
        description="Фреймворки, библиотеки, БД, инструменты (Django, Kubernetes, Redis...)",
    )


class SKeyInsight(BaseModel):
    headline: str = Field(..., description="Краткий заголовок инсайта")
    explanation: str = Field(
        ..., description="Развернутое объяснение сути (2-3 предложения)"
    )
    relevance_score: int = Field(
        ..., ge=1, le=10, description="Оценка полезности этого инсайта от 1 до 10"
    )


class SCodeConcept(BaseModel):
    description: str = Field(
        ..., description="Что делает код в статье (без самого кода)"
    )
    importance: str = Field(
        ...,
        description="Зачем этот код приведен (демонстрация бага, решение, бенчмарк)",
    )


class SHabrArticleSummary(BaseModel):
    title: str = Field(
        ...,
        description="Оригинальное или улучшенное (более точное) название статьи",
    )

    # Классификация
    article_type: EArticleType = Field(..., description="Тип материала")
    difficulty: EDifficultyLevel = Field(
        ..., description="Оценка сложности материала"
    )

    # Основная информация
    tldr: str = Field(
        ...,
        description="TL;DR: Суть статьи в 3-4 предложениях. О чем, для кого, какой итог.",
    )

    # Техническая часть
    stack: STechStack = Field(..., description="Технический стек")

    # Структурированные выводы
    main_points: List[SKeyInsight] = Field(
        ...,
        min_items=3,
        max_items=7,
        description="Основные тезисы и выводы статьи",
    )

    # Анализ кода (если есть)
    code_analysis: Optional[List[SCodeConcept]] = Field(
        None, description="Анализ приведенных примеров кода, если они есть"
    )

    # Критика и польза
    pros: List[str] = Field(
        ..., description="Что автор сделал хорошо / плюсы решения"
    )
    cons: List[str] = Field(
        ..., description="Спорные моменты, недостатки решения или упущенные детали"
    )

    target_audience: str = Field(
        ...,
        description="Кому конкретно стоит читать (напр. 'DevOps инженерам, работающим с highload')",
    )
