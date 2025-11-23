from typing import Dict

from app.core.http_client import HTTPXClient
from bs4 import BeautifulSoup
from config import settings
from loguru import logger

DEFAULT_HEADERS = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
}


class HabrParser:
    def __init__(self, client: HTTPXClient | None = None) -> None:
        self.client = client or HTTPXClient(
            headers=DEFAULT_HEADERS, proxy=settings.PROXY_URL
        )

    async def aclose(self):
        await self.client.close()

    async def get_article(self, url: str) -> Dict:
        logger.info(f"Начинаем обработку URL: {url}")
        try:
            resp = await self.client.request("GET", url)
            resp.raise_for_status()
            html_content = resp.text

            parsed_data = await self.parse(html_content, url)

            if parsed_data.get("title"):
                logger.success(
                    f"Успешно извлечена статья: '{parsed_data['title']}'"
                )
            else:
                logger.warning(f"Не удалось извлечь заголовок для URL: {url}")

            return parsed_data
        except Exception as e:
            logger.error(
                f"Непредвиденная ошибка при обработке {url}: {e}", exc_info=True
            )
            return {}

    async def parse(self, html_content: str, url: str) -> Dict:
        logger.debug("Начинаем парсинг HTML-контента страницы Хабра.")
        soup = BeautifulSoup(html_content, "html.parser")

        # Основной блок статьи
        article_block = soup.find(
            "article", class_="tm-article-presenter__content"
        ) or soup.find("article")
        if not article_block:
            logger.warning("Не найден основной блок статьи ('article').")
            return {}

        # Заголовок, автор, время публикации
        title_tag = article_block.find("h1") or soup.find("h1")
        title = title_tag.get_text(strip=True) if title_tag else ""

        author_tag = article_block.find(
            "a", class_="tm-user-info__username"
        ) or soup.find("a", class_="tm-user-info__username")
        author = author_tag.get_text(strip=True) if author_tag else ""

        time_tag = article_block.find("time") or soup.find("time")
        publish_time = time_tag.get("datetime") if time_tag else ""

        # Контейнер с телом статьи
        article_body = article_block.find(
            "div", id="post-content-body"
        ) or soup.select_one("#post-content-body")
        if not article_body:
            logger.warning("Не найден контент статьи ('post-content-body').")
            return {
                "title": title,
                "author": author,
                "publish_time": publish_time,
                "url": url,
                "text": "",
            }

        parsed_content = []
        # Ищем основной контейнер, где лежит весь форматированный текст
        content_container = (
            article_body.find("div", class_="article-formatted-body")
            or article_body
        )

        if not content_container:
            logger.warning("Не найден контейнер 'article-formatted-body'.")
            return {
                "title": title,
                "author": author,
                "publish_time": publish_time,
                "url": url,
                "text": "",
            }

        # Итерация по всем основным тегам контента
        tags_to_parse = [
            "p",
            "h1",
            "h2",
            "h3",
            "h4",
            "h5",
            "h6",
            "pre",
            "ul",
            "ol",
            "figure",
            "blockquote",
        ]
        for tag in content_container.find_all(tags_to_parse):
            if tag.name.startswith("h"):
                level = int(tag.name[1])
                parsed_content.append(f"{'#' * level} {tag.get_text(strip=True)}")
            elif tag.name == "p":
                parsed_content.append(tag.get_text(strip=True))
            elif tag.name == "pre":
                code_text = tag.get_text()
                lang = ""
                code_tag = tag.find("code")
                if code_tag and code_tag.has_attr("class"):
                    # извлекаем язык из класса вида 'language-python'
                    for cls in code_tag["class"]:
                        if cls.startswith("language-"):
                            lang = cls.split("-", 1)[-1]
                            break
                lang_suffix = lang if lang else ""
                parsed_content.append(f"```{lang_suffix}\n{code_text}\n```")
            elif tag.name in ["ul", "ol"]:
                list_items = []
                for i, li in enumerate(tag.find_all("li"), 1):
                    prefix = f"{i}." if tag.name == "ol" else "*"
                    list_items.append(f"  {prefix} {li.get_text(strip=True)}")
                parsed_content.append("\n".join(list_items))
            elif tag.name == "figure":
                img = tag.find("img")
                if img and img.has_attr("src"):
                    caption_tag = tag.find("figcaption")
                    caption = (
                        caption_tag.get_text(strip=True)
                        if caption_tag
                        else "image"
                    )
                    parsed_content.append(f"![{caption}]({img['src']})")
            elif tag.name == "blockquote":
                quoted_text = "\n".join(
                    [f"> {line}" for line in tag.get_text(strip=True).split("\n")]
                )
                parsed_content.append(quoted_text)

        final_text = "\n\n".join(filter(None, parsed_content))

        logger.debug("Парсинг HTML-контента Хабра завершен.")
        return {
            "title": title,
            "author": author,
            "publish_time": publish_time,
            "url": url,
            "text": final_text,
        }
