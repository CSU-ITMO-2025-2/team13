from app.article_parser.parser import HabrParser
from app.article_parser.schemas import SArticleParsed, SParseRequest
from fastapi import APIRouter, Depends, HTTPException

router = APIRouter(prefix="/api/habr", tags=["habr"])


async def get_parser():
    parser = HabrParser()
    try:
        yield parser
    finally:
        await parser.aclose()


@router.post("/parse", response_model=SArticleParsed)
async def parse_article(
    body: SParseRequest, parser: HabrParser = Depends(get_parser)
):
    data = await parser.get_article(str(body.url))
    if not data:
        raise HTTPException(
            status_code=400,
            detail="Не удалось распарсить статью по указанному URL",
        )
    try:
        return SArticleParsed(**data)
    except Exception as e:
        raise HTTPException(
            status_code=502, detail=f"Неверный формат распарсенных данных: {e}"
        )
