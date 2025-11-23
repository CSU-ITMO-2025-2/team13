from typing import Any

import httpx
from config import settings


class HTTPXClient:
    def __init__(
        self,
        headers: dict | None = None,
        proxy: str | None = None,
        timeout: int = 60,
        base_url: str | None = None,
        follow_redirects: bool = True,
    ) -> None:
        if proxy:
            transport = httpx.AsyncHTTPTransport(proxy=proxy)
            self._client = httpx.AsyncClient(
                timeout=timeout,
                transport=transport,
                follow_redirects=follow_redirects,
            )
        else:
            self._client = httpx.AsyncClient(
                timeout=timeout, follow_redirects=follow_redirects
            )
        self._headers = headers or {}
        self._proxy = proxy
        self._base_url = base_url
        self._follow_redirects = follow_redirects

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        await self.close()

    async def request(
        self, method: str, path: str, **kwargs: Any
    ) -> httpx.Response:
        url = self._build_url(path)
        if "headers" not in kwargs:
            kwargs["headers"] = self._headers
        return await self._client.request(method.upper(), url, **kwargs)

    async def close(self) -> None:
        await self._client.aclose()

    def _build_url(self, path: str) -> str:
        # Если абсолютный URL — вернуть как есть
        if path.startswith("http://") or path.startswith("https://"):
            return path
        if self._base_url:
            return f"{self._base_url.rstrip('/')}/{path.lstrip('/')}"
        return path


client = HTTPXClient(headers=None, proxy=settings.PROXY_URL)
