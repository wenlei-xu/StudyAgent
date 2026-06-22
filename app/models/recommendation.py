from pydantic import BaseModel, Field


class ResourceCard(BaseModel):
    title: str
    url: str
    summary: str = Field(..., description="资源简介（1-2 句）")
    relevance: str = Field(..., description="与此知识点/错题的相关性说明")
