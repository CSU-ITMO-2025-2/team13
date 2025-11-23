from typing import Optional

from config import settings
from pydantic import BaseModel, Field


class SGeminiContentPart(BaseModel):
    text: str = Field(..., description="Сгенерированный текст модели")


class SGeminiContent(BaseModel):
    parts: list[SGeminiContentPart] = Field(
        ..., description="Части сгенерированного контента"
    )
    role: str = Field(..., description="Роль, например, 'model'")


class SGeminiCandidate(BaseModel):
    content: SGeminiContent = Field(..., description="Сгенерированный контент")
    finishReason: str = Field(..., description="Причина завершения генерации")
    index: int = Field(..., description="Индекс кандидатуры")


class SGeminiUsageMetadata(BaseModel):
    promptTokenCount: int = Field(
        ..., description="Количество токенов в подсказке"
    )
    candidatesTokenCount: int = Field(
        ..., description="Количество токенов в кандидатурах"
    )
    totalTokenCount: int = Field(..., description="Общее количество токенов")
    promptTokensDetails: list[dict] = Field(
        ..., description="Детали токенов подсказки"
    )
    thoughtsTokenCount: int = Field(..., description="Количество токенов мыслей")


class SGeminiTextResponse(BaseModel):
    candidates: list[SGeminiCandidate] = Field(
        ..., description="Список сгенерированных кандидатур текста"
    )
    usageMetadata: SGeminiUsageMetadata = Field(
        ..., description="Метаданные использования токенов"
    )
    modelVersion: str = Field(
        ..., description="Версия модели, использованной для генерации"
    )
    responseId: str = Field(..., description="Уникальный идентификатор ответа")


class SGeminiHeaders(BaseModel):
    content_type: str = Field(default="application/json", alias="Content-Type")
    x_goog_api_key: str = Field(
        default=settings.GEMINI_API_KEY, alias="x-goog-api-key"
    )


class SArticleTextRequest(BaseModel):
    text: str
    model: Optional[str] = Field(default=None, examples=["gemini-2.5-flash"])
