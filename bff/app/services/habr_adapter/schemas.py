from pydantic import AnyUrl, BaseModel, Field


class SArticleParseRequest(BaseModel):
    url: AnyUrl = Field(
        "https://habr.com/ru/companies/selectel/articles/967092",
        description="URL статьи на Habr",
    )


class SArticleParsed(BaseModel):
    title: str
    author: str | None = None
    publish_time: str | None = None
    url: AnyUrl
    text: str
