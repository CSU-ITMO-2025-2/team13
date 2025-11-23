from app.core.decorators import exception_handler, rate_limiter
from app.core.http_client import HTTPXClient
from app.gemini.shemas import SGeminiHeaders, SGeminiTextResponse
from config import settings


class GeminiService:
    REQUEST_LIMIT = settings.REQUESTS_PER_MINUTE
    REQUEST_PERIOD = 60

    def __init__(
        self, model: str | None = None, requester: HTTPXClient | None = None
    ):
        headers = SGeminiHeaders().model_dump(by_alias=True)
        self._model = model or "gemini-2.5-flash"
        self.base_url = settings.GEMINI_API_BASE_URL
        self.requester = requester or HTTPXClient(
            headers=headers, proxy=settings.PROXY_URL, base_url=self.base_url
        )

    @property
    def model(self):
        return self._model

    def set_model(self, model: str):
        self._model = model

    def _resolve_refs(self, schema: dict, defs: dict | None = None) -> dict:
        if defs is None:
            defs = schema.get("$defs", {})

        if isinstance(schema, dict):
            if "$ref" in schema:
                ref_name = schema["$ref"].split("/")[-1]
                if ref_name in defs:
                    return self._resolve_refs(defs[ref_name], defs)

            return {
                k: self._resolve_refs(v, defs)
                for k, v in schema.items()
                if k != "$defs"
            }
        elif isinstance(schema, list):
            return [self._resolve_refs(item, defs) for item in schema]

        return schema

    @exception_handler
    @rate_limiter(max_calls=REQUEST_LIMIT, period=REQUEST_PERIOD)
    async def generate_text(
        self, prompt: str, model: str | None = None, response_schema=None
    ) -> SGeminiTextResponse:
        """
        Генерация текста
        """
        if not model:
            model = self._model

        url = f"{self.base_url}/{model}:generateContent"
        payload = {"contents": [{"role": "user", "parts": [{"text": prompt}]}]}

        if response_schema:
            resolved_schema = self._resolve_refs(response_schema)
            payload["generationConfig"] = {}
            payload["generationConfig"]["responseMimeType"] = "application/json"
            payload["generationConfig"]["responseSchema"] = resolved_schema

        return await self.requester.request("POST", url, json=payload)

    async def close(self):
        await self.requester.close()
