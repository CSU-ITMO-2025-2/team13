from pydantic import BaseModel


class SArticleForLLM(BaseModel):
    title: str
    text: str


class SArticleTaskResponse(BaseModel):
    task_id: str
    status: str
