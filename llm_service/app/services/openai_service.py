from app.sgr.habr import SHabrArticleSummary
from config import settings
from langchain_openai import ChatOpenAI
from loguru import logger


class OpenAIService:
    def __init__(self):
        self.llm = ChatOpenAI(
            base_url=settings.LLM_BASE_URL,
            api_key=settings.LLM_API_KEY,
            model=settings.LLM_MODEL_NAME,
            temperature=0.3,
            max_tokens=4000,
        )

    async def generate_summary(
        self, prompt: str, schema: dict = None
    ) -> SHabrArticleSummary | None:
        try:
            structured_llm = self.llm.with_structured_output(schema)

            messages = [
                (
                    "system",
                    "You are a helpful AI assistant. Extract the information from the text based on the requested structure.",
                ),
                ("user", prompt),
            ]

            result = await structured_llm.ainvoke(messages)

            if isinstance(result, dict):
                return SHabrArticleSummary.model_validate(result)

            return result

        except Exception as e:
            logger.error(f"OpenAI-like API Service error: {e}")
            return None
